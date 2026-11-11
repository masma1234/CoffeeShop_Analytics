"""Camera ownership, worker lifetime, deadlines and runtime health."""
from __future__ import annotations

import sqlite3
import time
import hashlib

import cv2

from .config import Config
from .detector import Detector
from .pipeline import Pipeline
from .schema import file_hash
from .storage import SQLiteStore
from .video_input import VideoInput


def replay(config: Config, store: SQLiteStore, detector: Detector, source: str | int,
           camera_id: str, run_id: str, start: str, model_metadata: dict,
           live: bool = False, max_frames: int | None = None) -> dict:
    """Replay is lossless at the sampling interval; live input drops stale frames."""
    reader = None
    try:
        # Camera URLs can contain passwords; retain a stable identity, never the URL.
        identity = "live:"+hashlib.sha256(str(source).encode()).hexdigest() if live else file_hash(str(source))
        ttl = max(60, config.data["model"]["inference_timeout_seconds"]+30)
        with store.camera_lease(camera_id, run_id, ttl) as owner:
            pipeline = Pipeline(config, store, camera_id, run_id, start, identity, model_metadata)
            reader = VideoInput(source, live=live)
            component = "camera"
            pipeline.health("running")
            heartbeat = time.monotonic()
            try:
                for index, offset, image in reader:
                    component = "camera"
                    store.renew_lease(camera_id, owner, ttl)
                    if index % config.camera(camera_id)["sample_every"]:
                        continue
                    started = time.perf_counter()
                    component = "detector"
                    detections = detector.detect(image, index)
                    detector_ms = (time.perf_counter()-started)*1000
                    component = "pipeline"
                    pipeline.process(index, offset, detections, image=image)
                    pipeline.stage_latencies["detection"].append(detector_ms)
                    pipeline.latencies[-1] = (time.perf_counter()-started)*1000
                    if pipeline.frames == 1 or time.monotonic()-heartbeat >= 5:
                        pipeline.health("running", dropped=reader.dropped.value)
                        heartbeat = time.monotonic()
                    if max_frames and pipeline.frames >= max_frames:
                        break
                    component = "camera"
            except KeyboardInterrupt:
                return pipeline.health("stopped", "Interrupted by operator", reader.dropped.value)
            except (ValueError, OSError, RuntimeError, EOFError, sqlite3.Error, cv2.error) as exc:
                if isinstance(exc, sqlite3.Error):
                    component = "storage"
                # If storage itself is unavailable, preserve the original failure.
                try:
                    pipeline.health("error", str(exc), reader.dropped.value, component)
                except sqlite3.Error:
                    import logging
                    logging.getLogger("coffee_ops").exception("Cannot persist pipeline failure health")
                raise
            return pipeline.health("completed", dropped=reader.dropped.value)
    finally:
        if reader is not None:
            reader.close()
        detector.close()
