"""Offline fault tests for the actual portable notebook implementation."""
import contextlib
import io
import json
from pathlib import Path
import tempfile
import unittest

from PIL import Image


NOTEBOOK = Path(__file__).resolve().parents[1] / "notebooks/cafe_model_benchmark.ipynb"


def load_workbench():
    namespace = {"__name__": "notebook_test"}
    notebook = json.loads(NOTEBOOK.read_text(encoding="utf-8"))
    # Execute the shipped default workflow, not a test-only copy of its functions.
    with contextlib.redirect_stdout(io.StringIO()):
        for cell in notebook["cells"]:
            if cell["cell_type"] == "code":
                exec(compile("".join(cell["source"]), cell["id"], "exec"), namespace)
    return notebook, namespace


class TrainingNotebookTests(unittest.TestCase):
    def setUp(self):
        self.notebook, self.ns = load_workbench()
        self.ns["TARGET_CLASSES"] = ["cup"]
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)

    def call(self, name, *args, **kwargs):
        return self.ns[name](*args, **kwargs)

    def record(self, index, split=None, group=None):
        path = self.root / f"{index}.png"
        Image.new("RGB", (40, 30), (index * 17 % 255, index * 31 % 255, index)).save(path)
        return self.call("make_record", path, [[2, 3, 20, 25]], [0], ["cup"],
                         "test-fixture", split, group)

    def test_default_is_safe_and_outputs_are_empty(self):
        for flag in ["INSTALL_PACKAGES", "RUN_DOWNLOADS", "RUN_PRETRAINED", "RUN_TRAINING",
                     "RUN_FINAL_TEST", "RUN_EXPORT", "RUN_VIDEO"]:
            self.assertFalse(self.ns[flag])
        for cell in self.notebook["cells"]:
            if cell["cell_type"] == "code":
                self.assertEqual(cell["outputs"], [])
                self.assertIsNone(cell["execution_count"])

    def test_box_formats_are_explicit_and_equivalent(self):
        expected = [10., 20., 30., 40.]
        self.assertEqual(self.call("xyxy_box", expected, 100, 100), expected)
        self.assertEqual(self.call("xyxy_box", [10, 20, 20, 20], 100, 100, "xywh"), expected)
        converted = self.call("xyxy_box", [.2, .3, .2, .2], 100, 100, "yolo")
        for a, b in zip(expected, converted): self.assertAlmostEqual(a, b)
        for box in [[0, 0, 0, 1], [-2, 0, 5, 5], [0, 0, 101, 3], [0, 0, float("nan"), 4]]:
            with self.subTest(box=box), self.assertRaises(ValueError):
                self.call("xyxy_box", box, 100, 100)
        with self.assertRaises(ValueError): self.call("xyxy_box", [1, 2, 3, 4], 100, 100, "guess")

    def test_names_require_complete_explicit_target_mapping(self):
        self.assertEqual(self.call("class_mapping", {4: "diningtable", 7: "cup"}, ["cup"]), {7: 0})
        self.assertEqual(self.call("class_mapping", ["sofa"], ["couch"]), {0: 0})
        for source, target in [(["cup"], ["person", "cup"]), (["cup", "cup"], ["cup"]),
                               (["cup"], ["cup", "cup"])]:
            with self.assertRaises(ValueError): self.call("class_mapping", source, target)

    def test_cup_only_coverage_cannot_silently_train_other_classes(self):
        r = self.record(1)
        self.ns["TARGET_CLASSES"] = ["person", "cup", "bottle"]
        with self.assertRaisesRegex(ValueError, "coverage"):
            self.call("make_record", r["image"], [], [], ["cup"], "partial")
        with self.assertRaisesRegex(ValueError, "coverage"):
            self.call("split_and_audit", [r])

    def test_duplicate_pixels_detected_across_different_encodings(self):
        r = self.record(1, "train")
        copy = self.root / "same.bmp"
        with Image.open(r["image"]) as im: im.save(copy)
        second = self.call("make_record", copy, r["boxes"], [0], ["cup"], "fixture", "test")
        self.assertEqual(r["sha256_pixels"], second["sha256_pixels"])
        with self.assertRaisesRegex(ValueError, "Duplicate"):
            self.call("split_and_audit", [r, second])

    def test_recording_group_leakage_rejected(self):
        records = [self.record(1, "train", "same-session"), self.record(2, "test", "same-session")]
        with self.assertRaisesRegex(ValueError, "group crosses"):
            self.call("split_and_audit", records)

    def test_group_split_deterministic_and_fixed_test_preserved(self):
        records = [self.record(i, "train", f"session-{i // 2}") for i in range(1, 11)]
        records.append(self.record(12, "test", "held-out"))
        first, audit = self.call("split_and_audit", records, 17)
        second, _ = self.call("split_and_audit", records, 17)
        self.assertEqual([r["split"] for r in first], [r["split"] for r in second])
        self.assertEqual(first[-1]["split"], "test")
        self.assertEqual(set(audit["images"]), {"train", "val", "test"})
        for group in {r["group"] for r in first}:
            self.assertEqual(len({r["split"] for r in first if r["group"] == group}), 1)

    def test_missing_train_positive_and_too_few_groups_rejected(self):
        r = self.record(1)
        with self.assertRaises(ValueError): self.call("split_and_audit", [r])
        records = [self.record(i, split) for i, split in enumerate(["train", "val", "test"], 1)]
        records[0]["labels"] = []; records[0]["boxes"] = []
        with self.assertRaisesRegex(ValueError, "no training examples"):
            self.call("split_and_audit", records)

    def test_yolo_missing_empty_and_invalid_ids_are_distinct_failures(self):
        images = self.root / "images"; images.mkdir()
        labels = self.root / "labels"; labels.mkdir()
        Image.new("RGB", (40, 30)).save(images / "one.png")
        with self.assertRaisesRegex(ValueError, "Missing label"):
            self.call("import_yolo", self.root, ["cup"], ["cup"])
        label = labels / "one.txt"; label.write_text("")
        with self.assertRaisesRegex(ValueError, "Unverified negative"):
            self.call("import_yolo", self.root, ["cup"], ["cup"])
        rows = self.call("import_yolo", self.root, ["cup"], ["cup"], allow_empty=True)
        self.assertEqual(rows[0]["boxes"], [])
        for text in ["41 .5 .5 .2 .2", "0.5 .5 .5 .2 .2", "0 .5 .5 0 .2", "0 0 0 1"]:
            label.write_text(text)
            with self.subTest(text=text), self.assertRaises(ValueError):
                self.call("import_yolo", self.root, ["cup"], ["cup"])

    def test_kaggle_cup_sparse_id_and_flat_images_with_labels_subfolder(self):
        cup = self.root / "cup"; cup.mkdir()
        (cup / "labels").mkdir()
        Image.new("RGB", (40, 30), "red").save(cup / "31_10.jpg")
        (cup / "labels/31_10.txt").write_text("31 .5 .5 .2 .2")
        rows = self.call("import_yolo", self.root, {31: "cup"}, ["cup"])
        self.assertEqual(rows[0]["labels"], [0])
        self.assertEqual(rows[0]["boxes"], [[16., 12., 24., 18.]])
        (cup / "31_10.txt").write_text("31 .5 .5 .4 .4")
        with self.assertRaisesRegex(ValueError, "Ambiguous labels"):
            self.call("import_yolo", self.root, {31: "cup"}, ["cup"])

    def test_prepare_keeps_source_and_binds_images_labels_and_annotations(self):
        records, _ = self.call("split_and_audit", [self.record(i) for i in range(1, 9)])
        before = {r["image"]: Path(r["image"]).read_bytes() for r in records}
        prepared, digest = self.call("prepare_dataset", records, self.root / "prepared")
        self.assertEqual(digest, self.call("dataset_fingerprint", prepared))
        self.call("assert_dataset_unchanged", prepared)
        for path, content in before.items(): self.assertEqual(Path(path).read_bytes(), content)
        with self.assertRaises(FileExistsError):
            self.call("prepare_dataset", records, self.root / "prepared")
        Path(prepared[0]["label_file"]).write_text("0 .1 .1 .1 .1")
        with self.assertRaisesRegex(ValueError, "label changed"):
            self.call("assert_dataset_unchanged", prepared)
        old = digest
        prepared[1]["boxes"][0] = [1., 2., 10., 20.]
        self.assertNotEqual(old, self.call("dataset_fingerprint", prepared))

    def test_source_mutation_after_import_is_detected(self):
        records = [self.record(i) for i in range(1, 5)]
        Image.new("RGB", (40, 30), "white").save(records[0]["image"])
        with self.assertRaisesRegex(ValueError, "changed after import"):
            self.call("split_and_audit", records)

    def test_original_coco_sparse_categories_crowds_and_xywh(self):
        try:
            import ijson  # noqa: F401  # Optional notebook dependency.
        except ImportError:
            self.skipTest("Install requirements-notebook.txt to exercise streaming COCO import.")
        folder = self.root / "train2017"; folder.mkdir()
        for i in [1, 2]: Image.new("RGB", (40, 30), (i, 0, 0)).save(folder / f"{i}.png")
        annotations = self.root / "annotations"; annotations.mkdir()
        doc = {"categories": [{"id": 1, "name": "person"}, {"id": 47, "name": "cup"}],
               "images": [{"id": i, "file_name": f"{i}.png", "width": 40, "height": 30}
                          for i in [1, 2]],
               "annotations": [{"image_id": 1, "category_id": 47, "bbox": [2, 3, 10, 15]},
                               {"image_id": 2, "category_id": 47, "bbox": [1, 1, 10, 10], "iscrowd": 1}]}
        (annotations / "instances_train2017.json").write_text(json.dumps(doc))
        rows = self.call("import_coco_json", self.root)
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["boxes"], [[2., 3., 12., 18.]])
        self.assertEqual(rows[0]["labels"], [0])

    def test_same_class_matching_is_one_to_one(self):
        import torch
        truth = {"boxes": torch.tensor([[0., 0., 10., 10.]]), "labels": torch.tensor([0])}
        prediction = {"boxes": torch.tensor([[0., 0., 10., 10.], [0., 0., 10., 10.]]),
                      "labels": torch.tensor([0, 0]), "scores": torch.tensor([.9, .8])}
        self.assertEqual(self.call("matching_counts", prediction, truth, .25), {0: [1, 1, 0]})
        self.assertEqual(self.call("matching_counts", prediction, truth, .95), {0: [0, 0, 1]})

    def test_export_is_hash_bound_and_requires_supported_heldout_classes(self):
        weights = self.root / "candidate.pt"; weights.write_bytes(b"unit-test-only")
        digest = self.call("checkpoint_hash", weights)
        report = {"model": "yolo11s", "classes": ["cup"], "dataset_sha256": "data-v1",
                  "checkpoint_sha256": digest, "per_class": {"cup": {"tp": 1, "fp": 0, "fn": 1}}}
        val, test = dict(report, split="val"), dict(report, split="test")
        output = self.root / "candidate.zip"
        self.call("export_candidate", "yolo11s", weights, val, test, "data-v1", output)
        with self.assertRaises(FileExistsError):
            self.call("export_candidate", "yolo11s", weights, val, test, "data-v1", output)
        with self.assertRaises(ValueError):
            self.call("export_candidate", "yolo11s", weights, val, val, "data-v1", self.root / "bad.zip")
        weights.write_bytes(b"modified")
        with self.assertRaisesRegex(ValueError, "changed after evaluation"):
            self.call("export_candidate", "yolo11s", weights, val, test, "data-v1", self.root / "bad.zip")

    def test_rtdetr_export_stays_a_directory_adapter_candidate(self):
        import zipfile
        directory = self.root / "hf"; directory.mkdir()
        (directory / "model.safetensors").write_bytes(b"unit-test")
        digest = self.call("checkpoint_hash", directory)
        report = {"model": "rtdetr_v2_r18", "classes": ["cup"], "dataset_sha256": "d",
                  "checkpoint_sha256": digest, "per_class": {"cup": {"tp": 1, "fn": 0}}}
        dest = self.root / "rt.zip"
        self.call("export_candidate", "rtdetr_v2_r18", directory, dict(report, split="val"),
                  dict(report, split="test"), "d", dest)
        with zipfile.ZipFile(dest) as z:
            self.assertNotIn("model.pt", z.namelist())
            metadata = json.loads(z.read("metadata.json"))
            self.assertTrue(metadata["adapter_required"])
            self.assertFalse(metadata["promotion_eligible"])


if __name__ == "__main__":
    unittest.main()
