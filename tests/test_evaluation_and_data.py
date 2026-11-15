import copy
import json
import tempfile
import unittest
from pathlib import Path

import cv2
import numpy as np

from coffee_ops.config import Config
from coffee_ops.dataset import split_manifest, validate_dataset
from coffee_ops.detector import validate_metadata
from coffee_ops.evaluation import evaluate
from coffee_ops.mlops import promote, rollback
from coffee_ops.schema import file_hash
from coffee_ops.storage import SQLiteStore

ROOT = Path(__file__).resolve().parents[1]


class EvaluationTests(unittest.TestCase):
    def fixture(self):
        return {"provenance": {"kind": "synthetic_logic_fixture"}, "frames": [
            {"frame": 0, "seconds": 0, "detections": [{"class_id": 0, "bbox": [0, 0, 10, 10], "confidence": .9, "track_id": 1}]},
            {"frame": 1, "seconds": 1, "detections": [{"class_id": 0, "bbox": [0, 0, 10, 10], "confidence": .9, "track_id": 1}]}]}

    def test_perfect_detection_but_identity_switch_is_measured(self):
        truth = self.fixture()
        pred = copy.deepcopy(truth)
        pred["frames"][1]["detections"][0]["track_id"] = 2
        result = evaluate(truth, pred)
        self.assertEqual(result["detection"]["mAP50_95"], 1)
        self.assertEqual(result["tracking"]["ID_switches"], 1)
        self.assertEqual(result["tracking"]["IDF1"], .5)
        self.assertEqual(result["tracking"]["MOTA"], .5)

    def test_false_positive_false_negative_reduce_metrics(self):
        truth = self.fixture()
        pred = copy.deepcopy(truth)
        pred["frames"][0]["detections"][0]["bbox"] = [50, 50, 60, 60]
        result = evaluate(truth, pred)
        self.assertEqual(result["detection"]["precision"], .5)
        self.assertEqual(result["detection"]["recall"], .5)
        self.assertLess(result["detection"]["mAP50"], .51)
        self.assertIsNone(result["reconciliation"]["confirmed_sale_precision"])

    def test_no_predictions_reports_zero_recall_not_fake_precision(self):
        truth, pred = self.fixture(), self.fixture()
        for f in pred["frames"]:
            f["detections"] = []
        result = evaluate(truth, pred)
        self.assertEqual(result["detection"]["recall"], 0)
        self.assertIsNone(result["detection"]["precision"])
        self.assertEqual(result["detection"]["mAP50"], 0)

    def test_frame_coverage_mismatch_is_rejected(self):
        truth, pred = self.fixture(), self.fixture()
        pred["frames"].pop()
        with self.assertRaises(ValueError):
            evaluate(truth, pred)

    def test_event_matching_is_global_and_prediction_order_independent(self):
        truth, pred = self.fixture(), self.fixture()
        template = {"kind": "placed", "product_class": "coffee_cup", "source_zone": None, "destination_zone": "T1"}
        truth["events"] = [{**template, "seconds": 0}, {**template, "seconds": 1.4}]
        pred["events"] = [{**template, "seconds": .5}, {**template, "seconds": 0}]
        self.assertEqual(evaluate(truth, pred)["counting"]["event_recall"], 1)
        pred["events"].reverse()
        self.assertEqual(evaluate(truth, pred)["counting"]["event_recall"], 1)

    def test_missing_event_annotations_do_not_fabricate_zero_counting_error(self):
        result = evaluate(self.fixture(), self.fixture())
        self.assertIsNone(result["counting"]["absolute_error"])

    def test_calibration_bin_boundaries_do_not_double_count_confidence(self):
        truth, pred = self.fixture(), self.fixture()
        pred["frames"][0]["detections"][0]["confidence"] = .3
        pred["frames"][1]["detections"][0]["confidence"] = 1
        self.assertAlmostEqual(evaluate(truth, pred)["detection"]["calibration_ece"], .35)

    def test_duplicate_predictions_not_counted_as_multiple_true_positives(self):
        truth, pred = self.fixture(), self.fixture()
        duplicate = {**pred["frames"][0]["detections"][0], "track_id": 2}
        pred["frames"][0]["detections"].append(duplicate)
        self.assertAlmostEqual(evaluate(truth, pred)["detection"]["precision"], 2/3)

    def test_occupancy_delay_false_duration_and_sales_labels(self):
        truth, pred = self.fixture(), self.fixture()
        truth["frames"][0]["tables"] = [{"zone_id": "T1", "status": "empty"}]
        truth["frames"][1]["tables"] = [{"zone_id": "T1", "status": "occupied"}]
        for f in pred["frames"]:
            f["tables"] = [{"zone_id": "T1", "status": "occupied"}]
        truth["reconciliations"] = [{"event_id": "a", "status": "confirmed_sale"}, {"event_id": "b", "status": "payment_unmatched"}]
        pred["reconciliations"] = [{"event_id": "a", "status": "confirmed_sale"}, {"event_id": "b", "status": "confirmed_sale"}]
        result = evaluate(truth, pred)
        self.assertEqual(result["occupancy"]["accuracy"], .5)
        self.assertEqual(result["occupancy"]["false_occupancy_seconds"], 1)
        self.assertEqual(result["reconciliation"]["confirmed_sale_precision"], .5)


class DatasetTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.data = {"dataset_version": "test", "classes": {"0": "person"}, "images": []}
        for i, split in enumerate(("train", "val", "test")):
            image, label = f"{i}.png", f"{i}.txt"
            cv2.imwrite(str(self.root / image), np.full((10, 20, 3), i*50, np.uint8))
            (self.root / label).write_text("0 0.5 0.5 0.5 0.5\n")
            self.data["images"].append({"image": image, "label": label, "split": split, "width": 20, "height": 10,
                                        "camera_id": str(i), "environment_id": str(i), "video_id": str(i)})

    def tearDown(self):
        self.temp.cleanup()

    def write(self):
        path = self.root / "manifest.json"
        path.write_text(json.dumps(self.data))
        return str(path)

    def test_valid_manifest_and_grouped_split(self):
        path = self.write()
        self.assertTrue(validate_dataset(path, 1)["valid"])
        result = split_manifest(path)
        self.assertEqual({r["split"] for r in result["images"]}, {"train", "val", "test"})
        self.assertEqual(split_manifest(path), result)

    def test_leakage_duplicate_dimensions_and_missing_labels(self):
        self.data["images"][1]["camera_id"] = "0"
        self.data["images"][1]["image"] = "0.png"
        self.data["images"][2]["width"] = 99
        (self.root / "2.txt").unlink()
        result = validate_dataset(self.write(), 1)
        self.assertFalse(result["valid"])
        for phrase in ("leakage", "Duplicate", "dimensions", "Missing label"):
            self.assertTrue(any(phrase in e for e in result["errors"]))

    def test_invalid_boxes_class_mapping_empty_and_insufficient_labels(self):
        (self.root / "0.txt").write_text("0 0.1 0.1 1 1\n")
        (self.root / "1.txt").write_text("99 0.5 0.5 0.2 0.2\n")
        (self.root / "2.txt").write_text("")
        errors = validate_dataset(self.write(), 20)["errors"]
        for phrase in ("bounding box", "mapping mismatch", "Empty", "Insufficient"):
            self.assertTrue(any(phrase in e for e in errors))

    def test_connected_cameras_cannot_be_randomly_split(self):
        for row in self.data["images"]:
            row["environment_id"] = "same-shop"
        with self.assertRaisesRegex(ValueError, "three disjoint"):
            split_manifest(self.write())


class ModelLifecycleTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.config = Config.load(ROOT / "config/example.json")
        weights = self.root / "model.pt"
        weights.write_bytes(b"test metadata only, not real weights")
        metadata = self.root / "metadata.json"
        self.metadata = {"version": "shop-v1", "dataset_version": "real-v1", "sha256": file_hash(str(weights)),
                         "classes": {str(cid): c["name"] for cid, c in self.config.catalog.items()}}
        metadata.write_text(json.dumps(self.metadata))
        self.config.data["model"].update(weights=str(weights), metadata=str(metadata))
        self.store = SQLiteStore(self.root / "test.db")

    def tearDown(self):
        self.store.close()
        self.temp.cleanup()

    def test_metadata_checksum_and_mapping_validation(self):
        self.assertEqual(validate_metadata(self.config), self.metadata)
        self.config.path(self.config.data["model"]["weights"]).write_bytes(b"changed")
        with self.assertRaisesRegex(ValueError, "checksum"):
            validate_metadata(self.config)

    def test_missing_model_has_no_fallback(self):
        self.config.data["model"]["weights"] = str(self.root / "missing.pt")
        with self.assertRaisesRegex(FileNotFoundError, "no automatic fallback"):
            validate_metadata(self.config)

    def test_promotion_requires_real_data_and_all_thresholds_then_supports_rollback(self):
        report = {"provenance": {"kind": "synthetic_logic_fixture"}, "model_sha256": self.metadata["sha256"], "dataset_manifest_sha256": "audit"}
        audit = {"valid": True, "synthetic": False, "dataset_version": "real-v1", "manifest_sha256": "audit"}
        with self.assertRaisesRegex(ValueError, "held-out"):
            promote(self.store, self.config, report, audit)
        report["provenance"]["kind"] = "real_heldout"
        with self.assertRaisesRegex(ValueError, "Promotion failed"):
            promote(self.store, self.config, report, audit)
        for dotted in self.config.data["promotion"]:
            group, metric = dotted.split(".")
            report.setdefault(group, {})[metric] = 1.0
        entry = promote(self.store, self.config, report, audit)
        self.assertEqual(rollback(self.store, entry["registry_id"])["action"], "rollback")
        self.assertEqual(len(self.store.records("model_registry")), 2)

    def test_nan_cannot_pass_promotion(self):
        report = {"provenance": {"kind": "real_heldout"}, "model_sha256": self.metadata["sha256"], "dataset_manifest_sha256": "audit"}
        for dotted in self.config.data["promotion"]:
            group, metric = dotted.split(".")
            report.setdefault(group, {})[metric] = float("nan")
        with self.assertRaises(ValueError):
            promote(self.store, self.config, report, {"valid": True, "dataset_version": "real-v1", "manifest_sha256": "audit"})
