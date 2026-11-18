"""Actual CPU backend compatibility using a tiny, explicitly untrained test model.

No downloaded weights, training, real-world labels or accuracy claims.
"""
import contextlib
import importlib.util
import io
import json
import tempfile
import unittest
from pathlib import Path

import numpy as np

from coffee_ops.config import Config
from coffee_ops.detector import YOLODetector
from coffee_ops.schema import file_hash

ROOT = Path(__file__).resolve().parents[1]


@unittest.skipUnless(importlib.util.find_spec("ultralytics"), "Optional YOLO backend is not installed")
class DetectorBackendTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory()
        cls.root = Path(cls.temp.name)
        model_yaml = cls.root / "untrained.yaml"
        model_yaml.write_text("nc: 3\nbackbone:\n  - [-1, 1, Conv, [8, 3, 2]]\n  - [-1, 1, Conv, [16, 3, 2]]\nhead:\n  - [[1], 1, Detect, [nc]]\n")
        with contextlib.redirect_stdout(io.StringIO()):
            from ultralytics import YOLO
            model = YOLO(str(model_yaml), task="detect")
            model.model.names = {0: "person", 1: "coffee_cup", 2: "table"}
            model.save(str(cls.root / "untrained.pt"))

    @classmethod
    def tearDownClass(cls):
        cls.temp.cleanup()

    def configuration(self, mismatched=False):
        config = Config.load(ROOT / "config/example.json")
        weights = self.root / "untrained.pt"
        names = {str(cid): c["name"] for cid, c in config.catalog.items()}
        if mismatched:
            config.data["classes"][0]["name"] = "incompatible_name"
            names["0"] = "incompatible_name"
        metadata = self.root / ("mismatch.json" if mismatched else "metadata.json")
        metadata.write_text(json.dumps({"version": "untrained-test", "dataset_version": "no-training-interface-test",
                                        "sha256": file_hash(str(weights)), "classes": names}))
        config.data["model"].update(weights=str(weights), metadata=str(metadata), version="untrained-test", inference_timeout_seconds=30)
        return config

    def test_real_cpu_worker_loads_runs_inference_and_closes(self):
        detector = YOLODetector(self.configuration(), "shop")
        try:
            detections = detector.detect(np.zeros((240, 320, 3), np.uint8), 0)
            self.assertIsInstance(detections, list)
            self.assertTrue(all(d.class_id in {0, 1, 2} for d in detections))
            self.assertEqual(detector.metadata["version"], "untrained-test")
            self.assertEqual(detector.startup_metrics["status"], "ready")
            self.assertLess(detector.startup_metrics["total_seconds"], detector.startup_metrics["deadline_seconds"])
            self.assertEqual(detector.startup_metrics["phases"][-1]["phase"], "ready")
        finally:
            detector.close()
        self.assertFalse(detector.process.is_alive())
        self.assertEqual(detector.process.exitcode, 0)

    def test_embedded_weight_names_cannot_be_overridden_by_metadata(self):
        with self.assertRaisesRegex(RuntimeError, "class names/IDs mismatch"):
            YOLODetector(self.configuration(mismatched=True), "shop")
