"""Transactional orchestration; no global counters or model-specific event rules."""
from __future__ import annotations

import logging
import time
from collections import deque
from dataclasses import asdict
from datetime import datetime, timedelta, timezone
from pathlib import Path

import cv2
import numpy as np
import psutil

from .alerts import AlertEngine, alert
from .config import Config
from .event_engine import EventEngine
from .inventory import record_movement
from .schema import Detection, key, now, stamp, utc
from .storage import SQLiteStore
from .tracker import KalmanTracker

logger = logging.getLogger("coffee_ops")


class Pipeline:
    def __init__(self, config: Config, store: SQLiteStore, camera_id: str, run_id: str,
                 start: str, source_identity: str, model_metadata: dict):
        self.config, self.store = config, store
        self.camera_id, self.run_id = camera_id, run_id
        self.start = utc(start)
        self.camera = config.camera(camera_id)
        self.tracker = KalmanTracker(config.data["tracker"])
        self.engine = EventEngine(config, camera_id, run_id)
        self.alerts = AlertEngine(config.data["rules"], camera_id, run_id)
        self.previous_frame = -1
        self.previous_ts: float | None = None
        self.previous_image: np.ndarray | None = None
        self.last_tables: dict = {}
        self.motion_latched = False
        self.failed = False
        self._pending_evidence: Path | None = None
        self.latencies: deque = deque(maxlen=10000)
        self.frames = 0
        self.reliable_frames = 0
        self.last_reliable_capture: str | None = None
        self.stage_latencies: dict[str, deque[float]] = {name:deque(maxlen=10000) for name in ("detection","tracking","events","storage")}
        self.started = time.perf_counter()
        self.process_handle = psutil.Process()
        self.cpu_started = time.process_time()
        ts = stamp(self.start)
        session = {"run_id": run_id, "camera_id": camera_id, "start": ts, "source_identity": source_identity,
                   "config_hash": config.digest, "model": model_metadata}
        with store.transaction():
            store.append("runs", key(run_id, camera_id), ts, session)
            if not store.get("cameras", key(camera_id, config.digest)):
                store.append("cameras", key(camera_id, config.digest), ts, self.camera)
            for z in self.camera["zones"]:
                if not store.get("zones", key(camera_id, config.digest, z["id"])):
                    store.append("zones", key(camera_id, config.digest, z["id"]), ts, {**z, "camera_id": camera_id})
            if not store.get("class_catalog", key(config.digest)):
                store.append("class_catalog", key(config.digest), ts, {"classes": config.data["classes"]})
            if not store.get("model_versions", key(model_metadata)):
                store.append("model_versions", key(model_metadata), ts, model_metadata)

    def health(self, status: str, reason: str | None = None, dropped: int = 0,
               component: str | None = None) -> dict:
        timestamp = now()
        running = status == "running"
        session = self.store.get("runs", key(self.run_id, self.camera_id))
        if session is None:
            raise RuntimeError("Pipeline run metadata is missing")
        record = {"camera_id": self.camera_id, "run_id": self.run_id, "timestamp": timestamp,
                  "status": status, "reason": reason, "camera": "ok" if running else status,
                  "detector": "fixture" if session["model"].get("version") == "fixture" else "ok" if running else status,
                  "tracker": "unstable" if self.motion_latched else "ok" if running else status,
                  "storage": self.store.health()["status"],
                  "pos": "disabled_camera_only" if self.config.data["pos"]["mode"] == "camera_only" else "snapshot_imported" if self.store.records("orders", limit=1) else "unavailable",
                  "event_queue": {"capacity": 2, "policy": "bounded_backpressure_or_live_newest", "dropped_frames": dropped},
                  "processed_frames": self.frames,
                  "last_capture_timestamp": stamp(datetime.fromtimestamp(self.previous_ts,timezone.utc)) if self.previous_ts is not None else None,
                  "reliable_frames": self.reliable_frames,"unreliable_frames":self.frames-self.reliable_frames,
                  "last_reliable_capture":self.last_reliable_capture,
                  "traffic_calibrated":bool(self.camera.get("crossing_lines")),
                  "runtime": {"fps": self.frames/max(0.001, time.perf_counter()-self.started),
                              "average_latency_ms": float(np.mean(self.latencies)) if self.latencies else None,
                              "p95_latency_ms": float(np.percentile(self.latencies, 95)) if self.latencies else None,
                              "p50_latency_ms": float(np.percentile(self.latencies,50)) if self.latencies else None,
                              "p99_latency_ms": float(np.percentile(self.latencies,99)) if self.latencies else None,
                              "stage_latency_ms":{name:{"samples":len(v),"p50":float(np.percentile(v,50)),"p95":float(np.percentile(v,95))} for name,v in self.stage_latencies.items() if v},
                              "latency_window": len(self.latencies), "gpu_usage": None,
                              "cpu_usage": 100*(time.process_time()-self.cpu_started)/max(0.001, time.perf_counter()-self.started),
                              "memory_bytes": self.process_handle.memory_info().rss,
                              "resource_scope": "orchestrator process; detector/decoder child resources excluded"}}
        if component:
            record[component] = "error"
        self.store.append("health", key(record), timestamp, record)
        if record["pos"] == "unavailable":
            identity = key(self.run_id, self.camera_id, "pos_unavailable")
            if not self.store.get("alerts", identity):
                item = alert("POS_integration_unavailable", timestamp, self.camera_id,
                             "No POS snapshot imported. Video cannot confirm payment.", 1, {"run_id": self.run_id}, [], identity)
                item["alert_id"] = identity
                self.store.append("alerts", identity, timestamp, item)
        if status == "error":
            item = alert("camera_offline" if component == "camera" else f"{component or 'pipeline'}_error", timestamp,
                         self.camera_id, reason or "Processing failed", 1.0,
                         {"run_id": self.run_id, "frame": self.previous_frame}, [], key(record), "error")
            self.store.append("alerts", item["alert_id"], timestamp, item)
        return record

    def process(self, frame_index: int, offset: float, detections: list[Detection],
                reliable: bool = True, image: np.ndarray | None = None) -> dict:
        if self.failed:
            raise RuntimeError("Failed pipeline must be rebuilt by replaying from frame zero")
        try:
            return self._process(frame_index, offset, detections, reliable, image)
        except BaseException:
            # State-machine changes cannot be continued after a failed DB transaction.
            # Rebuild from frame zero; never accept an in-memory partial frame.
            self.failed = True
            if self._pending_evidence is not None:
                self._pending_evidence.unlink(missing_ok=True)
                self._pending_evidence = None
            raise

    def _process(self, frame_index: int, offset: float, detections: list[Detection],
                 reliable: bool, image: np.ndarray | None) -> dict:
        started = time.perf_counter()
        if frame_index <= self.previous_frame or offset < 0:
            raise ValueError("Frames must be strictly ordered and offsets nonnegative")
        timestamp = stamp(self.start+timedelta(seconds=offset))
        ts = utc(timestamp).timestamp()
        if self.previous_ts is not None and ts <= self.previous_ts:
            raise ValueError("Capture timestamps must strictly increase")
        if self.previous_ts is not None and ts-self.previous_ts > self.config.data["tracker"]["max_age_seconds"]:
            reliable = False
            self.engine.reset()
        self.previous_frame, self.previous_ts = frame_index, ts
        if image is not None:
            if image.shape[:2] != (self.camera["height"], self.camera["width"]):
                raise ValueError("Frame dimensions differ from calibrated camera; recalibrate zones")
            gray = cv2.resize(cv2.cvtColor(image, cv2.COLOR_BGR2GRAY), (64, 48)).astype(np.float32)
            if self.previous_image is not None:
                shift, response = cv2.phaseCorrelate(self.previous_image, gray)
                motion = np.hypot(shift[0], shift[1])/max(gray.shape)
                if response > 0.3 and motion > self.camera["motion_threshold"]:
                    self.motion_latched = True
                    self.tracker.reset()
                    self.engine.reset()
            self.previous_image = gray
        reliable = reliable and not self.motion_latched
        if detections and np.mean([d.confidence for d in detections]) < self.config.data["rules"]["low_confidence"]:
            reliable = False
        for detection in detections:
            cls = self.config.catalog.get(detection.class_id)
            if cls and cls["enabled"] and cls["kind"] == "person":
                threshold = self.camera.get("thresholds", {}).get(str(detection.class_id), cls["threshold"])
                if detection.confidence < threshold:
                    reliable = False
        filtered = self.config.filter(detections, self.camera_id)
        stage_started=time.perf_counter()
        tracks = self.tracker.update(filtered if reliable else [], ts)
        self.stage_latencies["tracking"].append((time.perf_counter()-stage_started)*1000)
        stage_started=time.perf_counter()
        events, tables = self.engine.update(tracks, ts, frame_index, reliable)
        self.stage_latencies["events"].append((time.perf_counter()-stage_started)*1000)
        people = [t for t in tracks if self.config.catalog[t.class_id]["kind"] == "person"]
        instability = self.tracker.new_tracks/len(filtered) if filtered and self.frames > 0 else 0
        alerts = self.alerts.evaluate(events, tables, people, self.camera["zones"], timestamp, ts, frame_index, instability, reliable)
        if self.motion_latched:
            # Recalibration/restart required; do not silently resume shifted polygons.
            if not self.store.get("alerts", key(self.run_id, self.camera_id, "camera_moved")):
                moved = alert("camera_moved", timestamp, self.camera_id, "Camera movement detected; recalibrate zones and start a new run.", 1,
                              {"frame": frame_index, "run_id": self.run_id}, [], self.run_id)
                moved["alert_id"] = key(self.run_id, self.camera_id, "camera_moved")
                alerts.append(moved)
        evidence_path = None
        if alerts and image is not None and self.config.data["evidence"]["capture"]:
            root = self.config.path(self.config.data["evidence"]["directory"])
            root.mkdir(parents=True, exist_ok=True)
            path = root / f"{key(self.run_id, self.camera_id, frame_index)}.jpg"
            if not path.exists():
                self._pending_evidence = path
                if not cv2.imwrite(str(path), image):
                    raise OSError("Evidence write failed")
            evidence_path = str(path)
        snapshot = {"camera_id": self.camera_id, "run_id": self.run_id, "timestamp": timestamp, "frame": frame_index, "tables": tables}
        frame_id = key(self.run_id, self.camera_id, frame_index)
        stage_started=time.perf_counter()
        with self.store.transaction():
            self.store.append("frames", frame_id, timestamp, {"run_id": self.run_id, "camera_id": self.camera_id, "frame": frame_index, "input_hash": key([asdict(d) for d in detections]), "reliable": reliable})
            self.store.append("occupancy", frame_id, timestamp, snapshot)
            observations = {"camera_id": self.camera_id, "run_id": self.run_id, "timestamp": timestamp,
                            "tracks": [asdict(t) for t in tracks],
                            "visible_products": [asdict(t) for t in tracks if not t.missed and self.config.catalog[t.class_id]["kind"] == "product"]}
            self.store.append("observations", frame_id, timestamp, observations)
            for t in tracks:
                kind = self.config.catalog[t.class_id]["kind"]
                if kind in {"person", "product"}:
                    state = self.engine.tracks.get(t.track_id)
                    self.store.append("people_tracks" if kind == "person" else "product_tracks", key(frame_id, t.track_id), timestamp,
                                      {**asdict(t), "run_id": self.run_id, "camera_id": self.camera_id,
                                       "timestamp": timestamp, "age_seconds": ts-t.created_at,
                                       "assigned_table": state.assigned_table if state else None,
                                       "zone": state.stable if state else None,
                                       "zone_entered_at": state.candidate_since if state else None})
            for event in events:
                # Crossings are confirmed after dwell; aggregate by capture-event time.
                self.store.append("events", event["event_id"], event["timestamp"], event)
                record_movement(self.store, event)
            for item in alerts:
                if evidence_path:
                    item["evidence"]["image_path"] = evidence_path
                self.store.append("alerts", item["alert_id"], timestamp, item)
            for table in tables:
                previous = self.last_tables.get(table["zone_id"])
                if previous and previous["occupied_since"] is not None and table["status"] == "empty":
                    self.store.append("occupancy_sessions", key(frame_id, table["zone_id"]), timestamp,
                                      {"camera_id": self.camera_id, "zone_id": table["zone_id"], "timestamp": timestamp,
                                       "duration_seconds": ts-previous["occupied_since"]})
        self._pending_evidence = None
        self.stage_latencies["storage"].append((time.perf_counter()-stage_started)*1000)
        self.last_tables = {t["zone_id"]: t for t in tables}
        self.frames += 1
        if reliable:
            self.reliable_frames += 1
            self.last_reliable_capture = timestamp
        self.latencies.append((time.perf_counter()-started)*1000)
        return {"events": events, "tables": tables, "alerts": alerts, "tracks": observations["tracks"]}



def prune_evidence(config: Config) -> int:
    root = config.path(config.data["evidence"]["directory"]).resolve()
    cutoff = time.time()-config.data["evidence"]["retention_days"]*86400
    removed = 0
    for path in root.glob("*.jpg"):
        # Only files created by this pipeline; never traverse symlinks or arbitrary paths.
        if len(path.stem) == 32 and all(c in "0123456789abcdef" for c in path.stem) and not path.is_symlink() and path.resolve().parent == root and path.stat().st_mtime < cutoff:
            path.unlink()
            removed += 1
    return removed
