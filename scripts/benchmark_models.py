"""Opt-in pretrained-model benchmark. Separate from the operational class catalog.

COCO8 contains COCO training images: diagnostic only, never held-out model accuracy.
Downloads require --download; artifacts are never overwritten. No remote model code.
"""
from __future__ import annotations

import argparse
from contextlib import contextmanager
import hashlib
import importlib.metadata
import json
import math
import os
from pathlib import Path
import platform
import sys
import threading
import time
import urllib.request
import zipfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
ASSET_BASE = "https://github.com/ultralytics/assets/releases/download/v8.4.0/"
DATA_URL = "https://github.com/ultralytics/assets/releases/download/v0.0.0/coco8.zip"
MODELS = ("yolov8n", "yolo11n", "yolo11s", "yolo26n", "yolo26s", "rtdetr-v2-r18", "dfine-nano", "dfine-small", "smolvlm2-500m")
COCO_ALIASES = {"motorbike": "motorcycle", "aeroplane": "airplane", "sofa": "couch",
                "pottedplant": "potted plant", "diningtable": "dining table", "tvmonitor": "tv"}


def download(url: str, path: Path, limit: int) -> None:
    if path.exists():
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".partial")
    try:
        request = urllib.request.Request(url, headers={"User-Agent": "coffee-ops-benchmark/1"})
        with urllib.request.urlopen(request, timeout=60) as response, temporary.open("xb") as output:
            size = 0
            while chunk := response.read(1024 * 1024):
                size += len(chunk)
                if size > limit:
                    raise ValueError("Download exceeds declared size limit")
                output.write(chunk)
        temporary.replace(path)
    finally:
        temporary.unlink(missing_ok=True)


def digest(path: Path) -> str:
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def clip_box(box, width: int, height: int):
    """Normalize framework outputs before shared evaluation; omit empty boxes."""
    if len(box) != 4 or not all(math.isfinite(float(value)) for value in box):
        raise ValueError("Detector returned a nonfinite/invalid box")
    result = [max(0., min(float(value), float(bound))) for value, bound in zip(box, [width, height, width, height])]
    return result if result[2] > result[0] and result[3] > result[1] else None


def coco_class_map(actual: dict, expected: dict) -> dict[int, int]:
    """Recognize explicit COCO synonyms; never silently omit an unknown category."""
    by_name = {name: int(cid) for cid, name in expected.items()}
    mapping = {}
    for cid, name in actual.items():
        canonical = COCO_ALIASES.get(name, name)
        if canonical not in by_name:
            raise ValueError(f"Unexpected model category: {name}")
        mapping[int(cid)] = by_name[canonical]
    if len(mapping) != len(by_name) or set(mapping.values()) != set(by_name.values()):
        raise ValueError("Model class catalog is incomplete or ambiguous")
    return mapping


def prepare_coco8(directory: Path, allow_download: bool) -> Path:
    target = directory / "coco8"
    if (target / "images/train").is_dir() and (target / "images/val").is_dir():
        return target
    if not allow_download:
        raise FileNotFoundError("COCO8 missing; opt in with --download")
    archive = directory / "coco8.zip"
    download(DATA_URL, archive, 10_000_000)
    directory.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(archive) as bundle:
        members = bundle.infolist()
        if sum(member.file_size for member in members) > 30_000_000:
            raise ValueError("Expanded dataset exceeds size limit")
        for member in members:
            destination = (directory / member.filename).resolve()
            if not destination.is_relative_to(directory.resolve()) or "\\" in member.filename:
                raise ValueError("Unsafe archive path")
            if (member.external_attr >> 16) & 0o170000 == 0o120000:
                raise ValueError("Archive links are unsupported")
        bundle.extractall(directory)
    return target


@contextmanager
def resources():
    import psutil
    process = psutil.Process()
    peak = [process.memory_info().rss]
    stop = threading.Event()
    def sample():
        while not stop.wait(.02):
            peak[0] = max(peak[0], process.memory_info().rss)
    sampler = threading.Thread(target=sample, daemon=True)
    sampler.start()
    try:
        yield peak
    finally:
        stop.set()
        sampler.join()
        peak[0] = max(peak[0], process.memory_info().rss)


def dataset(root: Path):
    import cv2
    import yaml
    import ultralytics
    names = yaml.safe_load((Path(ultralytics.__file__).parent / "cfg/datasets/coco.yaml").read_text(encoding="utf-8"))["names"]
    frames, images, hashes = [], [], {}
    for path in sorted(root.glob("images/*/*.jpg")):
        image = cv2.imread(str(path))
        if image is None:
            raise ValueError(f"Unreadable image: {path.name}")
        height, width = image.shape[:2]
        label_path = root / "labels" / path.parent.name / (path.stem + ".txt")
        labels = []
        for line in label_path.read_text(encoding="utf-8").splitlines():
            cid, x, y, w, h = map(float, line.split())
            labels.append({"class_id": int(cid), "bbox": [(x-w/2)*width, (y-h/2)*height, (x+w/2)*width, (y+h/2)*height]})
        frames.append({"frame": len(frames), "detections": labels})
        images.append(image)
        hashes[path.relative_to(root).as_posix()] = digest(path)
        hashes[label_path.relative_to(root).as_posix()] = digest(label_path)
    if not images:
        raise ValueError("Dataset has no images")
    return names, frames, images, hashes


def build_detector(args, names):
    import torch
    if args.model.startswith("yolo"):
        from ultralytics import YOLO
        path = args.work / "weights" / (args.model + ".pt")
        if not path.exists():
            if not args.download:
                raise FileNotFoundError(path)
            download(ASSET_BASE + path.name, path, 120_000_000)
        model = YOLO(str(path))
        if model.names != names:
            raise ValueError("COCO class catalog mismatch")
        def predict(image):
            result = model.predict(image, imgsz=args.imgsz, conf=args.confidence, iou=.7,
                                   device=args.device, rect=False, half=args.precision == "fp16", verbose=False)[0]
            return [{"class_id": int(box.cls.item()), "confidence": float(box.conf.item()),
                     "bbox": box.xyxy[0].tolist()} for box in result.boxes]
        return predict, {"weights_sha256": digest(path), "source": ASSET_BASE + path.name,
                         "parameters": sum(p.numel() for p in model.model.parameters())}
    from huggingface_hub import HfApi
    from transformers import AutoImageProcessor, AutoModelForObjectDetection
    repo = {"rtdetr-v2-r18": "PekingU/rtdetr_v2_r18vd", "dfine-nano": "ustc-community/dfine-nano-coco",
            "dfine-small": "ustc-community/dfine-small-coco"}[args.model]
    revision = args.revision
    if not revision:
        if not args.download:
            raise ValueError("Specify a cached --revision or use --download to resolve it")
        revision = HfApi().model_info(repo).sha
    model = AutoModelForObjectDetection.from_pretrained(repo, revision=revision, trust_remote_code=False,
        use_safetensors=True, local_files_only=not args.download).to(device=args.device,
        dtype=torch.float16 if args.precision == "fp16" else torch.float32).eval()
    processor = AutoImageProcessor.from_pretrained(repo, revision=revision, trust_remote_code=False,
        local_files_only=not args.download, use_fast=False)
    class_ids = coco_class_map(model.config.id2label, names)
    def predict(image):
        from PIL import Image
        inputs = processor(images=Image.fromarray(image[:, :, ::-1]), return_tensors="pt").to(args.device)
        if args.precision == "fp16":
            inputs = {name: value.half() if value.is_floating_point() else value for name, value in inputs.items()}
        with torch.inference_mode():
            output = model(**inputs)
        result = processor.post_process_object_detection(output, threshold=args.confidence,
            target_sizes=torch.tensor([image.shape[:2]], device=args.device))[0]
        detections = []
        for cid, score, box in zip(result["labels"], result["scores"], result["boxes"]):
            clipped = clip_box(box.tolist(), image.shape[1], image.shape[0])
            if clipped is not None:
                detections.append({"class_id": class_ids[int(cid)], "confidence": float(score), "bbox": clipped})
        return detections
    return predict, {"repository": repo, "revision": revision,
                     "class_mapping": "explicit COCO synonym validation; complete one-to-one catalog",
                     "parameters": sum(p.numel() for p in model.parameters()), "processor_size": processor.size}


def detector_benchmark(args, images, frames, names):
    import cv2
    import numpy as np
    import torch
    from coffee_ops.evaluation import evaluate
    started = time.perf_counter()
    predict, provenance = build_detector(args, names)
    load_seconds = time.perf_counter() - started
    def synchronize():
        if args.device != "cpu":
            torch.cuda.synchronize()
    warmup = []
    for _ in range(args.warmup):
        synchronize()
        started = time.perf_counter()
        predict(images[0])
        synchronize()
        warmup.append((time.perf_counter()-started)*1000)
    conditions = {}
    transforms = {"clean": lambda im: im, "dim_35_percent": lambda im: (im*.35).astype(np.uint8),
                  "gaussian_blur_9": lambda im: cv2.GaussianBlur(im, (9, 9), 0)}
    for name, transform in transforms.items():
        samples, predictions = [], []
        for repeat in range(args.repeats):
            for index, image in enumerate(images):
                transformed = transform(image)  # Transform time intentionally outside inference timing.
                synchronize()
                started = time.perf_counter()
                result = predict(transformed)
                synchronize()
                samples.append((time.perf_counter()-started)*1000)
                if repeat == 0:
                    predictions.append({"frame": index, "detections": result})
        metrics = evaluate({"frames": frames}, {"frames": predictions})["detection"]
        conditions[name] = {"samples": len(samples), "mean_ms": float(np.mean(samples)),
            "p50_ms": float(np.percentile(samples, 50)), "p95_ms": float(np.percentile(samples, 95)),
            "p99_ms": float(np.percentile(samples, 99)), "images_per_second_serial": 1000/float(np.mean(samples)),
            "diagnostic_detection_only": metrics, "latencies_ms": samples}
    return {"kind": "detector", "provenance": provenance, "load_seconds_includes_download": load_seconds,
            "warmup_ms": warmup, "conditions": conditions}


def vlm_benchmark(args, images):
    import torch
    from PIL import Image
    from huggingface_hub import HfApi
    from transformers import AutoProcessor, AutoModelForImageTextToText
    repo = "HuggingFaceTB/SmolVLM2-500M-Video-Instruct"
    revision = args.revision or (HfApi().model_info(repo).sha if args.download else None)
    if not revision:
        raise ValueError("Specify a cached revision or opt in with --download")
    started = time.perf_counter()
    processor = AutoProcessor.from_pretrained(repo, revision=revision, trust_remote_code=False,
                                              local_files_only=not args.download)
    model = AutoModelForImageTextToText.from_pretrained(repo, revision=revision, trust_remote_code=False,
        local_files_only=not args.download, use_safetensors=True,
        torch_dtype=torch.float16 if args.precision == "fp16" else torch.float32).to(args.device).eval()
    load_seconds = time.perf_counter()-started
    samples = []
    # Two independent still images; this is NOT a temporal action or video benchmark.
    for image in images[:2]:
        pil = Image.fromarray(image[:, :, ::-1])
        pil.thumbnail((512, 512))
        messages = [{"role": "user", "content": [{"type": "image", "image": pil}, {"type": "text",
            "text": args.prompt}]}]
        started = time.perf_counter()
        inputs = processor.apply_chat_template(messages, add_generation_prompt=True, tokenize=True,
            return_dict=True, return_tensors="pt").to(args.device)
        if args.precision == "fp16":
            inputs = {name: value.half() if value.is_floating_point() else value for name, value in inputs.items()}
        if args.device != "cpu":
            torch.cuda.synchronize()
        with torch.inference_mode():
            output = model.generate(**inputs, max_new_tokens=40, do_sample=False)
        if args.device != "cpu":
            torch.cuda.synchronize()
        elapsed = time.perf_counter()-started
        generated = output[:, inputs["input_ids"].shape[1]:]
        samples.append({"seconds_preprocess_and_generate": elapsed, "generated_tokens": generated.shape[1],
            "input_tokens": inputs["input_ids"].shape[1], "image_tensor_shape": list(inputs["pixel_values"].shape),
            "response": processor.batch_decode(generated, skip_special_tokens=True)[0]})
    return {"kind": "vlm", "provenance": {"repository": repo, "revision": revision},
        "load_seconds_includes_download": load_seconds, "prompt": args.prompt, "samples": samples,
        "scope": "Two still-image qualitative probes, first cold generation included; no event/count accuracy or video latency measured"}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model", required=True, choices=MODELS)
    parser.add_argument("--work", type=Path, default=ROOT / "var/model-benchmark")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--download", action="store_true")
    parser.add_argument("--revision")
    parser.add_argument("--device", default="cpu")
    parser.add_argument("--precision", choices=["fp32", "fp16"], default="fp32")
    parser.add_argument("--threads", type=int, default=4)
    parser.add_argument("--imgsz", type=int, default=640)
    parser.add_argument("--confidence", type=float, default=.25)
    parser.add_argument("--prompt", default="Describe this image in one sentence.", help="VLM probe only")
    parser.add_argument("--warmup", type=int, default=3)
    parser.add_argument("--repeats", type=int, default=3)
    args = parser.parse_args()
    if args.precision == "fp16" and args.device == "cpu":
        parser.error("FP16 comparison requires CUDA; CPU baseline uses FP32")
    if args.output.exists():
        parser.error("Output already exists")
    if args.threads < 1 or args.repeats < 1 or args.warmup < 1 or args.imgsz != 640 or not 0 < args.confidence < 1:
        parser.error("Positive counts, 640 input and confidence in (0,1) required")
    args.work = args.work.resolve()
    os.environ.setdefault("HF_HOME", str(args.work / "huggingface"))
    os.environ.setdefault("YOLO_AUTOINSTALL", "false")
    os.environ.setdefault("YOLO_CONFIG_DIR", str(args.work / "ultralytics-settings"))
    import torch
    if args.device != "cpu" and not torch.cuda.is_available():
        parser.error("CUDA requested but unavailable; no silent CPU fallback")
    torch.set_num_threads(args.threads)
    torch.set_num_interop_threads(1)
    torch.manual_seed(42)
    if args.device != "cpu":
        torch.backends.cuda.matmul.allow_tf32 = False
        torch.backends.cudnn.allow_tf32 = False
        torch.cuda.reset_peak_memory_stats()
    names, frames, images, hashes = dataset(prepare_coco8(args.work, args.download))
    with resources() as peak:
        result = vlm_benchmark(args, images) if args.model == "smolvlm2-500m" else detector_benchmark(args, images, frames, names)
    result.update({"model": args.model, "environment": {"python": platform.python_version(),
        "platform": platform.platform(), "torch": torch.__version__, "cuda_available": torch.cuda.is_available(),
        "device": args.device, "threads": args.threads, "ultralytics": importlib.metadata.version("ultralytics"),
        "transformers": importlib.metadata.version("transformers")},
        "input_size": args.imgsz if result["kind"] == "detector" else None,
        "vlm_thumbnail_max_size": [512, 512] if result["kind"] == "vlm" else None,
        "confidence": args.confidence if result["kind"] == "detector" else None,
        "precision": args.precision, "peak_process_rss_sampled_bytes": peak[0],
        "gpu": {"name": torch.cuda.get_device_name(),
                "peak_allocated_bytes": torch.cuda.max_memory_allocated(),
                "peak_reserved_bytes": torch.cuda.max_memory_reserved(),
                "cuda_runtime": torch.version.cuda, "precision": args.precision, "tf32": False} if args.device != "cpu" else None,
        "dataset": {"url": DATA_URL, "sha256_files": hashes, "images": len(images),
            "scope": "COCO8 smoke test, COCO train2017 images; training leakage expected. Not held-out accuracy or overhead CCTV."},
        "not_measured": ["cafe accuracy", "tracking", "handover/preparation events", "POS accuracy",
                         "RTSP/decode/IPC/storage latency", "multi-camera performance", "GPU VRAM"]})
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("x", encoding="utf-8") as output:
        json.dump(result, output, indent=2, allow_nan=False)
    print(json.dumps({"model": args.model, "output": str(args.output), "passed": True}))


if __name__ == "__main__":
    main()
