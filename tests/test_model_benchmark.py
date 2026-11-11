"""Offline boundary tests for the opt-in research downloader."""
import tempfile
import unittest
import contextlib
import io
from pathlib import Path
from unittest.mock import patch
import zipfile

from scripts.benchmark_models import prepare_coco8, download, clip_box, coco_class_map, main


class BenchmarkBoundaryTests(unittest.TestCase):
    def test_coco_synonyms_preserve_all_categories(self):
        self.assertEqual(coco_class_map({0: 'pottedplant', 1: 'sofa', 2: 'cup'},
                                       {41: 'cup', 57: 'couch', 58: 'potted plant'}),
                         {0: 58, 1: 57, 2: 41})

    def test_unknown_or_ambiguous_model_categories_fail_instead_of_disappearing(self):
        for actual in [{0: 'coffee_cup'}, {0: 'sofa', 1: 'couch'}]:
            with self.subTest(actual=actual), self.assertRaises(ValueError):
                coco_class_map(actual, {57: 'couch'})

    def test_cpu_fp16_is_rejected_before_creating_artifacts(self):
        with tempfile.TemporaryDirectory() as folder:
            output = Path(folder) / "result.json"
            with patch('sys.argv', ['benchmark_models', '--model', 'yolo26n', '--precision', 'fp16',
                                    '--output', str(output)]), contextlib.redirect_stderr(io.StringIO()):
                with self.assertRaises(SystemExit) as stopped:
                    main()
            self.assertEqual(stopped.exception.code, 2)
            self.assertFalse(output.exists())

    def test_transformer_boxes_are_clipped_for_shared_evaluation(self):
        self.assertEqual(clip_box([-5, 2, 110, 90], 100, 80), [0., 2., 100., 80.])
        self.assertIsNone(clip_box([-5, 0, -1, 8], 100, 80))
        with self.assertRaises(ValueError):
            clip_box([0, 0, float('nan'), 10], 100, 80)

    def test_missing_data_never_downloads_without_opt_in(self):
        with tempfile.TemporaryDirectory() as folder, patch("urllib.request.urlopen") as request:
            with self.assertRaises(FileNotFoundError):
                prepare_coco8(Path(folder), False)
            request.assert_not_called()

    def test_archive_cannot_escape_work_directory(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder) / "work"
            root.mkdir()
            with zipfile.ZipFile(root / "coco8.zip", "w") as archive:
                archive.writestr("../escape.txt", "do not extract")
            with self.assertRaisesRegex(ValueError, "Unsafe archive"):
                prepare_coco8(root, True)
            self.assertFalse((Path(folder) / "escape.txt").exists())

    def test_symlink_archive_rejected(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            member = zipfile.ZipInfo("coco8/link")
            member.external_attr = (0o120777 << 16)
            with zipfile.ZipFile(root / "coco8.zip", "w") as archive:
                archive.writestr(member, "outside")
            with self.assertRaisesRegex(ValueError, "links"):
                prepare_coco8(root, True)

    def test_existing_weight_is_not_overwritten_or_redownloaded(self):
        with tempfile.TemporaryDirectory() as folder, patch("urllib.request.urlopen") as request:
            weights = Path(folder) / "weights.pt"
            weights.write_bytes(b"existing")
            download("https://example.invalid/model", weights, 100)
            self.assertEqual(weights.read_bytes(), b"existing")
            request.assert_not_called()

    def test_download_limit_removes_partial_file(self):
        import io
        with tempfile.TemporaryDirectory() as folder, patch("urllib.request.urlopen", return_value=io.BytesIO(b"oversized")):
            target = Path(folder) / "weights.pt"
            with self.assertRaisesRegex(ValueError, "size limit"):
                download("https://example.invalid/model", target, 2)
            self.assertFalse(target.exists())
            self.assertFalse(target.with_suffix(".pt.partial").exists())
