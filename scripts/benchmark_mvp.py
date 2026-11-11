"""Reproducible synthetic stress characterization, not real camera accuracy."""
from __future__ import annotations

import argparse
import json
import sys
import tempfile
import time
import tracemalloc
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from coffee_ops.config import Config
from coffee_ops.evaluation import evaluate
from coffee_ops.pos_adapter import MockPOSAdapter, import_orders
from coffee_ops.reconciliation import reconcile
from coffee_ops.schema import Detection
from coffee_ops.storage import SQLiteStore
from coffee_ops.tracker import KalmanTracker

START = "2026-01-01T09:00:00.000000Z"


def ledger_workload(order_count: int, event_count: int) -> dict:
    config = Config.load(ROOT / "config/example.json")
    with tempfile.TemporaryDirectory() as directory:
        store = SQLiteStore(Path(directory) / "stress.db")
        try:
            orders = [{"order_id": f"o{i}", "line_id": "1", "timestamp": START, "sku": "COFFEE",
                       "quantity": 1, "payment_status": "paid", "camera_id": "shop", "zone_id": f"counter-{i}"} for i in range(order_count)]
            started = time.perf_counter()
            import_orders(store, MockPOSAdapter(orders), config.data["pos"])
            import_seconds = time.perf_counter()-started
            with store.transaction():
                for i in range(event_count):
                    e = {"event_id": f"e{i}", "kind": "transferred", "timestamp": START, "camera_id": "shop",
                         "run_id": "stress", "track_id": i, "product_class": "coffee_cup", "confidence": .95,
                         "source_zone": "shelf", "destination_zone": f"counter-{i}", "evidence": {"frame": i}}
                    store.append("events", e["event_id"], START, e)
            tracemalloc.start()
            started = time.perf_counter()
            results = reconcile(store, config.data["pos"])
            elapsed = time.perf_counter()-started
            _, peak = tracemalloc.get_traced_memory()
            tracemalloc.stop()
            started = time.perf_counter()
            repeated = reconcile(store, config.data["pos"])
            repeat_seconds = time.perf_counter()-started
            if results.get("confirmed_sale") != event_count or repeated != results:
                raise AssertionError("Stress ledger quantity/idempotency invariant failed")
            return {"orders": order_count, "events": event_count, "import_seconds": import_seconds,
                    "reconcile_seconds": elapsed, "repeat_reconcile_seconds": repeat_seconds,
                    "events_per_second": event_count/elapsed, "python_peak_allocated_bytes": peak,
                    "confirmed_allocations": event_count, "idempotency": "passed"}
        finally:
            store.close()


def tracking_case(name: str, positions: list[list[tuple[int, int]]], seconds: list[float]) -> dict:
    config = Config.load(ROOT / "config/example.json")
    tracker = KalmanTracker(config.data["tracker"])
    truth, prediction = [], []
    for i, row in enumerate(positions):
        detections = [Detection(0, (x, 10, x+10, 30), .95) for _, x in row]
        tracks = tracker.update(detections, seconds[i])
        truth.append({"frame": i, "seconds": seconds[i], "detections": [{"class_id": 0, "bbox": list(d.bbox), "track_id": identity} for (identity, _), d in zip(row, detections)]})
        prediction.append({"frame": i, "seconds": seconds[i], "detections": [{"class_id": t.class_id, "bbox": list(t.bbox), "confidence": t.confidence, "track_id": t.track_id} for t in tracks if not t.missed]})
    result = evaluate({"frames": truth, "provenance": {"kind": "synthetic_stress"}}, {"frames": prediction})
    return {"scenario": name, **result["tracking"]}


def bounded_tracking(frames: int = 5000) -> dict:
    tracker = KalmanTracker(Config.load(ROOT / "config/example.json").data["tracker"])
    largest = 0
    tracemalloc.start()
    started = time.perf_counter()
    for frame in range(frames):
        x = frame*200
        active = tracker.update([Detection(0, (x, 0, x+10, 20), .9)], float(frame))
        largest = max(largest, len(active))
    _, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    if largest > 3:
        raise AssertionError("Expired tracks are accumulating")
    return {"frames": frames, "max_active_tracks": largest, "python_peak_allocated_bytes": peak,
            "elapsed_seconds": time.perf_counter()-started, "expiry_bound": "passed"}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    cases = [tracking_case("smooth_two_person_crossing", [[(1, a), (2, b)] for a, b in [(0, 100), (20, 80), (40, 60), (60, 40), (80, 20)]], list(range(5))),
             tracking_case("temporary_occlusion_within_expiry", [[(1, 20)], [], [(1, 20)]], [0, 1, 2]),
             tracking_case("occlusion_beyond_expiry", [[(1, 20)], [], [(1, 20)]], [0, 1, 4]),
             tracking_case("movement_beyond_distance_gate", [[(1, 0)], [(1, 150)], [(1, 300)]], [0, 1, 2])]
    result = {"purpose": "synthetic_robustness_characterization_not_model_accuracy",
              "ledger": [ledger_workload(1000, 100), ledger_workload(10000, 1000)],
              "tracking": cases, "tracking_expiry_stress": bounded_tracking(),
              "measurement_scope": "Single local process, SQLite on local disk. Python allocation peaks exclude native/OS memory. Tracemalloc affects timings.",
              "limitations": ["SQLite has one writer; distributed scale is untested.", "Identity is lost after long occlusions or movement outside the gate.", "No appearance recognition, real video accuracy, or production load claim."]}
    path = Path(args.output)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x", encoding="utf-8") as stream:
        json.dump(result, stream, indent=2, allow_nan=False)
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
