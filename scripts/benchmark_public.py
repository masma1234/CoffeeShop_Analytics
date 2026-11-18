"""Frozen public detection benchmark with calibration/test separation.

Research only: COCO validation is not independent cafe footage. No implicit model
downloads or training. Run prepare with --download, then measure cached models.
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
import math
import os
from pathlib import Path
import random
import sys
import time
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
TARGETS = {1: "person", 44: "bottle", 47: "cup"}


def sha(path):
    with Path(path).open("rb") as f:
        return hashlib.file_digest(f, "sha256").hexdigest()


def write(path, data):
    with Path(path).open("x", encoding="utf8") as f:
        json.dump(data, f, indent=2, allow_nan=False)
        f.write("\n")


def sample_records(data, per_bucket=150, seed=42):
    """Disjoint, balanced source-ID strata; exclude all target-crowd images."""
    if per_bucket < 2:
        raise ValueError("Each stratum requires at least two images")
    objects = defaultdict(list)
    crowd = set()
    for ann in data["annotations"]:
        if ann["category_id"] in TARGETS:
            if ann.get("iscrowd", 0):
                crowd.add(ann["image_id"])
            objects[ann["image_id"]].append(ann)
    images = {r["id"]: r for r in data["images"]}
    if len(images) != len(data["images"]):
        raise ValueError("Duplicate source image IDs")
    pools = defaultdict(list)
    for iid in sorted(images):
        if iid in crowd:
            continue
        classes = {a["category_id"] for a in objects[iid]}
        bucket = next((c for c in [47, 44, 1] if c in classes), 0)
        pools[bucket].append(iid)
    rng = random.Random(seed)
    rows = []
    for bucket in [47, 44, 1, 0]:
        if len(pools[bucket]) < per_bucket:
            raise ValueError(f"Not enough images in stratum {bucket}")
        ids = rng.sample(pools[bucket], per_bucket)
        for j, iid in enumerate(ids):
            im = images[iid]
            boxes = []
            for a in objects[iid]:
                x, y, w, h = a["bbox"]
                if not all(math.isfinite(v) for v in [x, y, w, h]) or w <= 0 or h <= 0:
                    raise ValueError("Invalid COCO box")
                box = [max(0, x), max(0, y), min(im["width"], x+w), min(im["height"], y+h)]
                if box[2] <= box[0] or box[3] <= box[1]:
                    raise ValueError("Empty clipped COCO box")
                boxes.append({"class_id": a["category_id"], "bbox": box})
            rows.append({"id": iid, "file_name": f"{iid:012d}.jpg", "width": im["width"],
                         "height": im["height"], "license": im.get("license"),
                         "source_url": im.get("coco_url"), "stratum": bucket,
                         "split": "calibration" if j % 2 == 0 else "test", "truth": boxes})
    return sorted(rows, key=lambda r: r["id"])


def prepare(args):
    from PIL import Image
    data = json.loads(args.annotations.read_text(encoding="utf8"))
    rows = sample_records(data, args.per_bucket, args.seed)
    args.output.mkdir(parents=True, exist_ok=False)
    images = args.output / "images"
    images.mkdir()
    def acquire(row):
        path = images / row["file_name"]
        url = "https://s3.amazonaws.com/images.cocodataset.org/val2017/" + row["file_name"]
        with urllib.request.urlopen(url, timeout=45) as response, path.open("xb") as f:
            size = 0
            while chunk := response.read(65536):
                size += len(chunk)
                if size > 10_000_000:
                    raise ValueError("Image exceeds size limit")
                f.write(chunk)
        with Image.open(path) as im:
            rgb = im.convert("RGB")
            if rgb.size != (row["width"], row["height"]):
                raise ValueError("Downloaded image dimensions disagree with labels")
            row["pixel_sha256"] = hashlib.sha256(rgb.tobytes()).hexdigest()
        row["sha256"] = sha(path)
        row["download_url"] = url
        return row
    with ThreadPoolExecutor(max_workers=4) as pool:
        rows = list(pool.map(acquire, rows))
    if len({r["pixel_sha256"] for r in rows}) != len(rows):
        raise ValueError("Duplicate decoded images: resolve before measuring")
    manifest = {"source": "COCO 2017 original validation annotations", "seed": args.seed,
        "annotations_sha256": sha(args.annotations), "classes": TARGETS,
        "licenses": data.get("licenses", []), "images": rows,
        "selection": "equal cup/bottle/person/negative strata; target-crowd images excluded",
        "limitations": ["Public COCO validation, not cafe validation or official full COCO score",
            "No recording-session provenance; near-duplicate leakage is not excluded",
            "Publisher model selection/pretraining overlap cannot be ruled out"],
        "promotion_eligible": False}
    write(args.output / "manifest.json", manifest)
    print(json.dumps({"images": len(rows), "splits": Counter(r["split"] for r in rows)}), flush=True)


def counts(truth, predictions, cid, threshold):
    """Score-ordered, same-class IoU>=0.5 matching, no many-to-one credit."""
    from coffee_ops.tracker import iou
    gt = [x for x in truth if x["class_id"] == cid]
    pred = sorted((x for x in predictions if x["class_id"] == cid and x["confidence"] >= threshold),
                  key=lambda r: r["confidence"], reverse=True)
    used = set()
    tp = 0
    for row in pred:
        best = max(((iou(tuple(row["bbox"]), tuple(g["bbox"])), i) for i, g in enumerate(gt) if i not in used), default=(0, -1))
        if best[0] >= .5:
            used.add(best[1])
            tp += 1
    return tp, len(pred)-tp, len(gt)-tp


def operating_point(records, thresholds):
    result = {}
    for cid, name in TARGETS.items():
        totals = [0, 0, 0]
        for row in records:
            totals = [a+b for a, b in zip(totals, counts(row["truth"], row["predictions"], cid, thresholds[cid]))]
        tp, fp, fn = totals
        result[name] = {"tp": tp, "fp": fp, "fn": fn,
            "precision": tp/(tp+fp) if tp+fp else None, "recall": tp/(tp+fn) if tp+fn else None,
            "f1": 2*tp/(2*tp+fp+fn) if 2*tp+fp+fn else None}
    return result


def calibrate(records):
    if not records or any(r["split"] != "calibration" for r in records):
        raise ValueError("Threshold selection accepts calibration rows only")
    thresholds = {}
    for cid in TARGETS:
        if not any(g["class_id"] == cid for r in records for g in r["truth"]):
            raise ValueError("Calibration lacks a target class")
        scores = []
        for step in range(1, 19):
            threshold = step*.05
            tp = fp = fn = 0
            for r in records:
                a, b, c = counts(r["truth"], r["predictions"], cid, threshold)
                tp += a
                fp += b
                fn += c
            scores.append((2*tp/(2*tp+fp+fn), threshold))
        thresholds[cid] = max(scores)[1]
    return thresholds


def ap_metrics(records):
    import torch
    from torchmetrics.detection import MeanAveragePrecision
    metric = MeanAveragePrecision(box_format="xyxy", iou_type="bbox", class_metrics=True,
                                  backend="faster_coco_eval")
    for r in records:
        metric.update([{"boxes": torch.tensor([x["bbox"] for x in r["predictions"]]).reshape(-1, 4),
                        "scores": torch.tensor([x["confidence"] for x in r["predictions"]]),
                        "labels": torch.tensor([x["class_id"] for x in r["predictions"]], dtype=torch.int64)}],
                      [{"boxes": torch.tensor([x["bbox"] for x in r["truth"]]).reshape(-1, 4),
                        "labels": torch.tensor([x["class_id"] for x in r["truth"]], dtype=torch.int64)}])
    return {k: v.tolist() for k, v in metric.compute().items()}


def measure(args):
    import cv2
    import numpy as np
    import torch
    from scripts.benchmark_models import build_detector, clip_box
    from scripts.verify_training_notebook import load_namespace
    if args.precision == "fp16" and not args.device.startswith("cuda"):
        raise ValueError("FP16 measurements require CUDA")
    args.output.mkdir(parents=True, exist_ok=False)
    manifest = json.loads((args.dataset / "manifest.json").read_text(encoding="utf8"))
    for r in manifest["images"]:
        if sha(args.dataset / "images" / r["file_name"]) != r["sha256"]:
            raise ValueError("Dataset image changed after freezing")
    ns = load_namespace()
    names = dict(enumerate(ns["COCO_NAMES"]))
    mapping = {names_id: next(cid for cid, name in TARGETS.items() if name == label)
               for names_id, label in names.items() if label in TARGETS.values()}
    torch.set_num_threads(4)
    torch.set_num_interop_threads(1)
    torch.backends.cuda.matmul.allow_tf32 = False
    torch.backends.cudnn.allow_tf32 = False
    args.work = ROOT / "var/model-benchmark"
    args.download = False
    args.confidence = .001
    os.environ["HF_HUB_OFFLINE"] = "1"
    os.environ["HF_HOME"] = str(args.work / "huggingface")
    os.environ["YOLO_AUTOINSTALL"] = "false"
    started = time.perf_counter()
    print(args.model, "loading cached checkpoint", flush=True)
    predict, provenance = build_detector(args, names)
    load_seconds = time.perf_counter()-started
    print(args.model, "loaded", load_seconds, flush=True)
    synchronize = torch.cuda.synchronize if args.device.startswith("cuda") else lambda: None
    first = cv2.imread(str(args.dataset / "images" / manifest["images"][0]["file_name"]))
    for _ in range(10):
        predict(first)
    synchronize()
    if args.device.startswith("cuda"):
        torch.cuda.reset_peak_memory_stats()
    transforms = {"clean": lambda x: x, "dim": lambda x: (x*.35).astype(np.uint8),
                  "blur": lambda x: cv2.GaussianBlur(x, (9, 9), 0)}
    results = {}
    thresholds = None
    for condition, transform in transforms.items():
        rows = []
        for index, original in enumerate(manifest["images"]):
            if condition != "clean" and original["split"] != "test":
                continue
            begin = time.perf_counter()
            pixels = cv2.imread(str(args.dataset / "images" / original["file_name"]))
            if pixels is None:
                raise ValueError("Cannot decode frozen image")
            pixels = transform(pixels)
            synchronize()
            start = time.perf_counter()
            raw = predict(pixels)
            synchronize()
            inference_ms = (time.perf_counter()-start)*1000
            predictions = []
            for d in raw:
                if d["class_id"] not in mapping:
                    continue
                box = clip_box(d["bbox"], pixels.shape[1], pixels.shape[0])
                score = float(d["confidence"])
                if not math.isfinite(score) or not 0 <= score <= 1:
                    raise ValueError("Invalid model confidence")
                if box is not None:
                    predictions.append({"class_id": mapping[d["class_id"]], "bbox": box, "confidence": score})
            rows.append({"id": original["id"], "split": original["split"], "truth": original["truth"],
                         "predictions": predictions, "inference_ms": inference_ms,
                         "image_pipeline_ms": (time.perf_counter()-begin)*1000})
            if index % 100 == 0:
                print(args.model, condition, index, flush=True)
        write(args.output / (condition+"-predictions.json"), rows)
        if condition == "clean":
            thresholds = calibrate([r for r in rows if r["split"] == "calibration"])
        for split in {r["split"] for r in rows}:
            selected = [r for r in rows if r["split"] == split]
            results[condition+"-"+split] = {"images": len(selected), "ap": ap_metrics(selected),
                "operating_point": operating_point(selected, thresholds),
                "inference_ms": {"mean":float(np.mean([r["inference_ms"] for r in selected])),
                                 "p95":float(np.percentile([r["inference_ms"] for r in selected],95))},
                "image_pipeline_p95_ms":float(np.percentile([r["image_pipeline_ms"] for r in selected],95))}
    write(args.output / "result.json", {"model":args.model, "precision":args.precision,
        "image_size":args.imgsz, "device":args.device, "gpu":torch.cuda.get_device_name() if args.device.startswith("cuda") else None,
        "torch":torch.__version__, "provenance":provenance, "dataset_sha256":sha(args.dataset / "manifest.json"),
        "load_seconds":load_seconds, "thresholds":thresholds, "results":results,
        "gpu_peak_allocated_mib":torch.cuda.max_memory_allocated()/2**20 if args.device.startswith("cuda") else None,
        "limitations":manifest["limitations"]+["Image pipeline timing excludes tracking, SQLite, IPC and video decoding",
             "Synthetic brightness/blur are stress probes, not naturally labeled low-light data"], "promotion_eligible":False})


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    p = sub.add_parser("prepare")
    p.add_argument("--annotations", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    p.add_argument("--per-bucket", type=int, default=150)
    p.add_argument("--seed", type=int, default=42)
    p.add_argument("--download", action="store_true", required=True)
    p = sub.add_parser("measure")
    p.add_argument("--dataset", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    p.add_argument("--model", choices=["yolo11s","yolo26s","rtdetr-v2-r18","dfine-nano","dfine-small"], required=True)
    p.add_argument("--revision")
    p.add_argument("--device", default="cuda:0")
    p.add_argument("--precision", choices=["fp32","fp16"], default="fp16")
    p.add_argument("--imgsz", type=int, default=512)
    args = parser.parse_args()
    (prepare if args.command == "prepare" else measure)(args)


if __name__ == "__main__":
    main()
