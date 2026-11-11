"""Offline evaluation export, isolated from command parsing."""
from __future__ import annotations

from .schema import key, utc
from .storage import SQLiteStore


def export_predictions(store: SQLiteStore, run_id: str, camera_id: str, all_events: bool = False) -> dict:
    with store.snapshot():
        run = store.get("runs", key(run_id, camera_id))
        if not run:
            raise ValueError("Unknown run/camera")
        start = utc(run["start"])
        frames, events, reconciliations = [], [], []
        for observation in store.scan_run("observations", run_id, camera_id):
            occupancy = store.get("occupancy", observation["_id"])
            if occupancy is None:
                raise ValueError("Incomplete frame record: occupancy missing")
            frames.append({"frame": occupancy["frame"], "seconds": (utc(observation["timestamp"])-start).total_seconds(),
                           "detections": [{"class_id": t["class_id"], "bbox": t["bbox"], "confidence": t["confidence"], "track_id": t["track_id"]} for t in observation["tracks"] if not t["missed"]],
                           "tables": occupancy["tables"]})
        for event in store.scan_run("events", run_id, camera_id):
            if all_events or event["kind"] in {"placed", "removed", "transferred", "disappeared"}:
                events.append({**event, "seconds": (utc(event["timestamp"])-start).total_seconds()})
                result = store.latest("reconciliations", "event_id", event["event_id"])
                if result:
                    reconciliations.append(result)
        health = next(store.scan_run("health", run_id, camera_id, reverse=True, limit=1), None)
        return {"camera_id":camera_id,"run_id":run_id,"frames": frames, "events": events, "reconciliations": reconciliations,
                "runtime": health["runtime"] if health else None, "model": run["model"], "source_identity": run["source_identity"]}
