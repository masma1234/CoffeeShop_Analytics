"""Benchmark integrity and deployment/measurement inference contract tests."""
import unittest
from unittest.mock import Mock, patch
from types import SimpleNamespace
import sys

from coffee_ops.detector import yolo_inference_options
from coffee_ops.detector import _worker
from scripts.benchmark_public import sample_records, counts, calibrate


class PublicBenchmarkTests(unittest.TestCase):
    def dataset(self):
        images = [{"id": i, "width": 100, "height": 100} for i in range(16)]
        annotations = [{"image_id": i, "category_id": [47, 44, 1][i//4],
                        "bbox": [1, 2, 10, 10], "iscrowd": 0} for i in range(12)]
        return {"images": images, "annotations": annotations}

    def test_source_split_is_deterministic_disjoint_and_has_negatives(self):
        rows = sample_records(self.dataset(), 4)
        self.assertEqual(rows, sample_records(self.dataset(), 4))
        cal = {x["id"] for x in rows if x["split"] == "calibration"}
        test = {x["id"] for x in rows if x["split"] == "test"}
        self.assertEqual(len(cal), 8)
        self.assertFalse(cal & test)
        self.assertEqual(sum(not r["truth"] for r in rows), 4)

    def test_crowds_and_duplicate_source_ids_cannot_silently_enter(self):
        d = self.dataset()
        d["annotations"][0]["iscrowd"] = 1
        self.assertNotIn(0, {r["id"] for r in sample_records(d, 2)})
        with self.assertRaises(ValueError):
            sample_records(d, 4)
        d["images"].append(d["images"][0])
        with self.assertRaisesRegex(ValueError, "Duplicate"):
            sample_records(d, 2)

    def test_nan_and_empty_boxes_fail_before_download(self):
        for box in [[0, 0, float("nan"), 10], [110, 0, 3, 3], [0, 0, 0, 3]]:
            with self.subTest(box=box):
                d = self.dataset()
                d["annotations"][0]["bbox"] = box
                with self.assertRaises(ValueError):
                    sample_records(d, 4)

    def test_duplicate_predictions_and_wrong_classes_are_not_true_positives(self):
        gt = [{"class_id": 47, "bbox": [0, 0, 10, 10]}]
        p = [dict(gt[0], confidence=.9), dict(gt[0], confidence=.8),
             {"class_id": 44, "bbox": [0, 0, 10, 10], "confidence": .95}]
        self.assertEqual(counts(gt, p, 47, .5), (1, 1, 0))
        self.assertEqual(counts([], p, 47, .5), (0, 2, 0))
        self.assertEqual(counts(gt, [], 47, .5), (0, 0, 1))

    def test_test_labels_cannot_be_used_to_select_thresholds(self):
        with self.assertRaisesRegex(ValueError, "calibration"):
            calibrate([{"split": "test"}])
        with self.assertRaisesRegex(ValueError, "lacks"):
            calibrate([{"split": "calibration", "truth": [], "predictions": []}])

    def test_calibration_balances_recall_and_false_positives(self):
        gt = [{"class_id": c, "bbox": [0, 0, 10, 10]} for c in [1, 44, 47]]
        pred = [dict(x, confidence=.6) for x in gt]
        pred += [{"class_id": c, "bbox": [20, 20, 30, 30], "confidence": .3} for c in [1, 44, 47]]
        result = calibrate([{"split": "calibration", "truth": gt, "predictions": pred}])
        self.assertTrue(all(.3 < x <= .6 for x in result.values()))

    def test_runtime_and_benchmark_have_explicit_identical_yolo_options(self):
        options = yolo_inference_options("cuda:0", .2, 512, True)
        self.assertEqual(options["imgsz"], 512)
        self.assertTrue(options["half"])
        self.assertFalse(options["rect"])
        self.assertEqual(options["max_det"], 300)
        self.assertFalse(yolo_inference_options("cpu", .2, 512, True)["half"])

    def test_worker_applies_configured_resolution_and_precision_to_model(self):
        connection = Mock()
        frame = object()
        connection.recv.side_effect = [frame, None]
        model = Mock(names={0: "person"})
        model.predict.return_value = [SimpleNamespace(boxes=[])]
        with patch.dict("os.environ", {}, clear=False), \
                patch.dict(sys.modules, {"ultralytics": SimpleNamespace(YOLO=Mock(return_value=model))}), \
                patch("coffee_ops.health.backend_health", return_value={}), patch.object(sys, "stdout"):
            _worker(connection, "trusted-local.pt", {0: "person"}, "cuda:0", .12, 512, True)
        model.predict.assert_called_once_with(frame, **yolo_inference_options("cuda:0", .12, 512, True))
        connection.send.assert_any_call(("ok", []))
        connection.close.assert_called_once()


if __name__ == "__main__":
    unittest.main()
