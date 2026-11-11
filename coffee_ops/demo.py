"""Generate a marked synthetic logic fixture, never training/evaluation evidence."""
from __future__ import annotations

import json
from pathlib import Path

import cv2
import numpy as np

from .schema import key


def make_demo(directory: str) -> dict:
    root = Path(directory)
    root.mkdir(parents=True, exist_ok=True)
    video = root / "fixture.avi"
    if video.exists():
        raise FileExistsError("Demo exists; choose a new output directory")
    writer = cv2.VideoWriter(str(video), cv2.VideoWriter_fourcc(*"MJPG"), 1, (320, 240))
    if not writer.isOpened():
        raise OSError("MJPG video writer unavailable")
    frames, truth = [], []
    try:
        for index in range(12):
            detections = []
            if index < 10:
                x = 20 if index < 5 else min(240, 20+(index-4)*55)
                detections.append({"class_id": 0, "bbox": [x, 20, x+30, 80], "confidence": 0.95, "track_id": "person-a"})
            if index < 5:
                x = 20 if index < 3 else 100
                detections.append({"class_id": 1, "bbox": [x, 150, x+20, 180], "confidence": 0.95, "track_id": "cup-a"})
            detections.append({"class_id": 2, "bbox": [5, 5, 145, 120], "confidence": 0.9, "track_id": "table-a"})
            image = np.zeros((240, 320, 3), np.uint8)
            for det in detections:
                x1, y1, x2, y2 = det["bbox"]
                cv2.rectangle(image, (x1, y1), (x2, y2), (50, 140, 200), 1)
            cv2.putText(image, "LOGIC FIXTURE", (5, 135), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 255, 255), 1)
            writer.write(image)
            frames.append({"frame": index, "detections": [{k: v for k, v in d.items() if k != "track_id"} for d in detections]})
            truth.append({"frame": index, "seconds": index, "detections": detections,
                          "tables": [{"zone_id": "T1", "status": "occupied" if index <= 6 else "empty"}]})
    finally:
        writer.release()
    fixture = {"purpose": "pipeline_fixture_not_model_accuracy", "frames": frames}
    ground_truth = {"provenance": {"kind": "synthetic_logic_fixture"}, "frames": truth,
                    "event_tolerance_seconds": 0.1,
                    "events": [{"kind": "placed", "product_class": "coffee_cup", "source_zone": None, "destination_zone": "shelf", "seconds": 2},
                               {"kind": "transferred", "product_class": "coffee_cup", "source_zone": "shelf", "destination_zone": "counter", "seconds": 4},
                               {"kind": "disappeared", "product_class": "coffee_cup", "source_zone": "counter", "destination_zone": None, "seconds": 8}],
                    "reconciliations": [
                        {"event_id": key("demo", "shop", 2, "placed", 2), "status": "observed"},
                        {"event_id": key("demo", "shop", 4, "transferred", 2), "status": "confirmed_sale"},
                        {"event_id": key("demo", "shop", 8, "disappeared", 2), "status": "sale_correlated_movement"}]}
    orders = [{"order_id": "demo-order", "line_id": "1", "timestamp": "2026-01-01T09:00:04Z", "sku": "COFFEE",
               "quantity": 1, "payment_status": "paid", "camera_id": "shop", "zone_id": "counter", "terminal_id": "mock"}]
    for name, data in (("detections.json", fixture), ("ground-truth.json", ground_truth), ("orders.json", orders)):
        (root / name).write_text(json.dumps(data, indent=2), encoding="utf-8")
    return {"directory": str(root.resolve()), "video": str(video), "purpose": fixture["purpose"]}
