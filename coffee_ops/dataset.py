"""Non-destructive collection and manifest checks for human-labeled real footage."""
from __future__ import annotations

import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path

import cv2

from .schema import file_hash


def extract_frames(video: str, output: str, every: int = 30) -> dict:
    if every < 1:
        raise ValueError("Frame interval must be positive")
    root = Path(output)
    root.mkdir(parents=True, exist_ok=True)
    capture = cv2.VideoCapture(video)
    if not capture.isOpened():
        raise OSError("Cannot open source video")
    index = written = 0
    prefix = file_hash(video)[:12]
    try:
        while True:
            ok, frame = capture.read()
            if not ok:
                total = int(capture.get(cv2.CAP_PROP_FRAME_COUNT))
                if total > 0 and index < total:
                    raise OSError(f"Corrupt video at frame {index}")
                break
            if index % every == 0:
                path = root / f"{prefix}_{index:08d}.jpg"
                if path.exists():
                    raise FileExistsError(f"Refusing to overwrite extracted frame: {path}")
                if not cv2.imwrite(str(path), frame):
                    raise OSError("Frame write failed")
                written += 1
            index += 1
    finally:
        capture.release()
    if not written:
        raise ValueError("No frames extracted")
    return {"source_sha256": file_hash(video), "frames_written": written, "interval": every}


def validate_dataset(path: str, minimum_examples: int = 20) -> dict:
    manifest_path = Path(path).resolve()
    data = json.loads(manifest_path.read_text(encoding="utf-8"))
    errors, warnings = [], []
    if not data.get("dataset_version") or not data.get("classes") or not data.get("images"):
        raise ValueError("Dataset manifest requires dataset_version, classes and images")
    counts: Counter = Counter()
    seen_hash: dict = {}
    groups: dict = defaultdict(set)
    splits: Counter = Counter()
    for row in data["images"]:
        image = manifest_path.parent / row["image"]
        label = manifest_path.parent / row["label"]
        split = row["split"]
        if split not in {"train", "val", "test"}:
            errors.append(f"Invalid split: {image}")
        splits[split] += 1
        for field in ("camera_id", "environment_id", "video_id"):
            if not row.get(field):
                errors.append(f"Missing {field}: {image}")
            else:
                groups[(field, row[field])].add(split)
        if not image.is_file():
            errors.append(f"Missing image: {image}")
            continue
        pixels = cv2.imread(str(image))
        if pixels is None:
            errors.append(f"Unreadable image: {image}")
            continue
        if pixels.shape[1] != row["width"] or pixels.shape[0] != row["height"]:
            errors.append(f"Incorrect image dimensions: {image}")
        digest = hashlib.sha256(pixels.tobytes()).hexdigest()
        if digest in seen_hash:
            errors.append(f"Duplicate image content: {image}, {seen_hash[digest]}")
        seen_hash[digest] = str(image)
        if not label.is_file():
            errors.append(f"Missing label: {label}")
            continue
        lines = label.read_text(encoding="utf-8").splitlines()
        if not lines:
            if not row.get("verified_negative", False):
                errors.append(f"Empty unverified annotation: {label}")
            else:
                warnings.append(f"Verified negative: {label}")
        for line in lines:
            try:
                fields = line.split()
                if len(fields) != 5:
                    raise ValueError("Expected class cx cy w h")
                cid = int(fields[0])
                x, y, w, h = map(float, fields[1:])
                if str(cid) not in data["classes"]:
                    raise ValueError("Class mapping mismatch")
                if not (0 < w <= 1 and 0 < h <= 1 and 0 <= x-w/2 <= x+w/2 <= 1 and 0 <= y-h/2 <= y+h/2 <= 1):
                    raise ValueError("Invalid bounding box")
                counts[cid] += 1
            except ValueError as exc:
                errors.append(f"{label}: {exc}")
    for group, group_splits in groups.items():
        if len(group_splits) > 1:
            errors.append(f"Split leakage: {group} in {sorted(group_splits)}")
    for cid in data["classes"]:
        if counts[int(cid)] < minimum_examples:
            errors.append(f"Insufficient examples for class {cid}: {counts[int(cid)]} < {minimum_examples}")
    if counts and max(counts.values())/max(1, min(counts.values())) > 20:
        warnings.append("Extreme class imbalance (>20:1)")
    if set(splits) != {"train", "val", "test"}:
        errors.append("All three splits train/val/test are required")
    return {"valid": not errors, "dataset_version": data["dataset_version"], "manifest_sha256": file_hash(path),
            "errors": errors, "warnings": warnings, "class_counts": dict(counts), "split_counts": dict(splits),
            "synthetic": data.get("synthetic", False)}


def split_manifest(path: str, seed: str = "42") -> dict:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    rows = data["images"]
    # Connected components keep shared cameras, environments AND videos together.
    parent = list(range(len(rows)))
    def find(i: int) -> int:
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i
    seen = {}
    for i, row in enumerate(rows):
        for field in ("camera_id", "environment_id", "video_id"):
            token = (field, row[field])
            if token in seen:
                parent[find(i)] = find(seen[token])
            seen[token] = i
    groups: dict = defaultdict(list)
    for i in range(len(rows)):
        groups[find(i)].append(i)
    if len(groups) < 3:
        raise ValueError("At least three disjoint camera/environment/video groups required")
    ordered = sorted(groups.values(), key=lambda group: hashlib.sha256((seed+min(rows[i]["image"] for i in group)).encode()).hexdigest())
    val_count = max(1, round(len(ordered)*0.2))
    test_count = max(1, round(len(ordered)*0.2))
    for n, group in enumerate(ordered):
        split = "test" if n < test_count else "val" if n < test_count+val_count else "train"
        for i in group:
            rows[i]["split"] = split
    return data
