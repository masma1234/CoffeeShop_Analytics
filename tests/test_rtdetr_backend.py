"""Actual isolated RT-DETR adapter, using locally generated untrained weights."""
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

import numpy as np

from coffee_ops.config import Config
from coffee_ops.detector import YOLODetector, rtdetr_image_processor_class
from coffee_ops.schema import file_hash

ROOT = Path(__file__).resolve().parents[1]


@unittest.skipUnless(importlib.util.find_spec("transformers"), "Optional RT-DETR backend is not installed")
class RTDetrBackendTests(unittest.TestCase):
    def test_resizing_uses_the_measured_pil_pixel_contract(self):
        from PIL import Image
        pixels = (np.arange(37*83*3).reshape(37, 83, 3) % 251).astype(np.uint8)
        image = Image.fromarray(pixels)
        processor = rtdetr_image_processor_class()(size={"height": 64, "width": 64},
            do_rescale=True, rescale_factor=1/255, do_normalize=False, do_pad=False)
        actual = processor(images=image, return_tensors="np")["pixel_values"][0]
        expected = np.asarray(image.resize((64, 64), Image.Resampling.BILINEAR), dtype=np.float32)
        expected = (expected * np.float32(1/255)).transpose(2, 0, 1)
        np.testing.assert_allclose(actual, expected, rtol=0, atol=1e-7)

    def test_isolated_rtdetr_loads_exact_checkpoint_and_infers_without_downloads(self):
        from transformers import RTDetrResNetConfig, RTDetrV2Config, RTDetrV2ForObjectDetection
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            names = {0: "person", 1: "coffee_cup", 2: "table"}
            backbone = RTDetrResNetConfig(embedding_size=16, hidden_sizes=[16, 32, 64, 128],
                                         depths=[1, 1, 1, 1], layer_type="basic", out_indices=[2, 3, 4])
            model = RTDetrV2ForObjectDetection(RTDetrV2Config(
                backbone_config=backbone, use_pretrained_backbone=False, num_labels=3,
                id2label=names, label2id={v: k for k, v in names.items()}, num_queries=10,
                encoder_hidden_dim=32, encoder_in_channels=[32, 64, 128], encoder_attention_heads=4,
                encoder_ffn_dim=64, encoder_layers=1, decoder_in_channels=[32, 32, 32],
                d_model=32, decoder_attention_heads=4, decoder_ffn_dim=64, decoder_layers=2))
            model.save_pretrained(root, safe_serialization=True)
            rtdetr_image_processor_class()(size={"height": 64, "width": 64}).save_pretrained(root)
            del model
            metadata = {"version": "untrained-interface-test", "dataset_version": "no-training",
                        "classes": {str(k): v for k, v in names.items()},
                        "sha256": file_hash(str(root / "model.safetensors")),
                        "checkpoint_files": {n: file_hash(str(root / n)) for n in ["config.json", "preprocessor_config.json"]}}
            (root / "metadata.json").write_text(json.dumps(metadata), encoding="utf8")
            config = Config.load(ROOT / "config/example.json")
            config.data["model"].update(backend="rtdetr_v2", checkpoint_directory=str(root),
                weights=str(root / "model.safetensors"), metadata=str(root / "metadata.json"),
                version=metadata["version"], device="cpu", image_size=64, half=False,
                load_timeout_seconds=120, inference_timeout_seconds=30)
            detector = YOLODetector(config, "shop")
            try:
                result = detector.detect(np.zeros((240, 320, 3), dtype=np.uint8), 0)
                self.assertIsInstance(result, list)
                self.assertEqual(detector.startup_metrics["status"], "ready")
                self.assertTrue(all(d.class_id in names for d in result))
            finally:
                detector.close()
            self.assertFalse(detector.process.is_alive())
            self.assertEqual(detector.process.exitcode, 0)


if __name__ == "__main__":
    unittest.main()
