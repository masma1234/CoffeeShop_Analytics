"""Strict JSON configuration; paths resolve relative to the config file."""
from __future__ import annotations

import json
import math
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .schema import key


def _keys(value: Any, required: set[str], optional: set[str] | None = None) -> None:
    if not isinstance(value, dict) or not required <= value.keys() or value.keys() - required - (optional or set()):
        raise ValueError(f"Expected keys {sorted(required)}; optional {sorted(optional or set())}")


def _unique_pairs(pairs: list[tuple]) -> dict:
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"Duplicate configuration key: {key}")
        result[key] = value
    return result


def number(value: Any, name: str, low: float = 0, high: float = float("inf")) -> float:
    if isinstance(value, bool) or not isinstance(value, (float, int)) or not math.isfinite(value) or not low <= value <= high:
        raise ValueError(f"Invalid {name}: expected finite value in [{low}, {high}]")
    return float(value)


@dataclass(frozen=True)
class Config:
    data: dict
    root: Path

    @classmethod
    def load(cls, path: str | Path) -> Config:
        path = Path(path).resolve()
        data = json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=_unique_pairs)
        config = cls(data, path.parent)
        config.validate()
        return config

    @property
    def digest(self) -> str:
        return key(self.data)

    @property
    def catalog(self) -> dict[int, dict]:
        return {item["id"]: item for item in self.data["classes"]}

    def path(self, value: str) -> Path:
        p = Path(value)
        return p if p.is_absolute() else (self.root / p).resolve()

    def camera(self, camera_id: str) -> dict:
        for camera in self.data["cameras"]:
            if camera["id"] == camera_id:
                return camera
        raise ValueError(f"Unknown camera: {camera_id}")

    def validate(self) -> None:
        d = self.data
        allowed = {"version", "classes", "cameras", "model", "tracker", "rules", "pos", "storage", "evidence", "promotion"}
        _keys(d, allowed)
        if not isinstance(d["version"], str) or not d["version"].strip():
            raise ValueError(f"Config requires exactly: {sorted(allowed)} and a version")
        if not isinstance(d["classes"], list) or not isinstance(d["cameras"], list) or not d["classes"] or not d["cameras"]:
            raise ValueError("Classes and cameras cannot be empty")
        ids, names = set(), set()
        for item in d["classes"]:
            _keys(item, {"id", "name", "kind", "enabled", "threshold"})
            cid = item["id"]
            if type(cid) is not int or cid < 0 or cid in ids or not isinstance(item["name"], str) or not item["name"].strip() or item["name"] in names:
                raise ValueError("Class IDs and names must be unique; IDs nonnegative integers")
            if item["kind"] not in {"person", "product", "fixture", "other"} or type(item["enabled"]) is not bool:
                raise ValueError("Invalid class kind/enabled")
            number(item["threshold"], "class threshold", 0, 1)
            ids.add(cid)
            names.add(item["name"])
        cameras = set()
        for camera in d["cameras"]:
            _keys(camera, {"id", "width", "height", "sample_every", "motion_threshold", "zones"}, {"thresholds", "crossing_lines"})
            if not isinstance(camera["id"], str) or not camera["id"].strip() or camera["id"] in cameras:
                raise ValueError("Camera IDs must be unique")
            cameras.add(camera["id"])
            for field in ("width", "height", "sample_every"):
                if type(camera[field]) is not int or camera[field] < 1:
                    raise ValueError(f"{field} must be a positive integer")
            number(camera["motion_threshold"], "motion threshold", 0, 1)
            line_ids = set()
            lines = camera.get("crossing_lines", [])
            if not isinstance(lines, list):
                raise ValueError("crossing_lines must be a list")
            for line in lines:
                _keys(line, {"id", "start", "end", "inside_side", "anchor", "hysteresis_pixels", "dwell_seconds", "max_gap_seconds"})
                if not isinstance(line["id"], str) or not line["id"].strip() or line["id"] in line_ids:
                    raise ValueError("Crossing line IDs must be nonempty and unique")
                line_ids.add(line["id"])
                for point in [line["start"], line["end"]]:
                    if not isinstance(point, list) or len(point) != 2:
                        raise ValueError("Crossing endpoints must be 2D lists")
                    number(point[0], "line x", 0, camera["width"])
                    number(point[1], "line y", 0, camera["height"])
                if line["start"] == line["end"]:
                    raise ValueError("Crossing line has zero length")
                if line["inside_side"] not in {"positive", "negative"} or line["anchor"] not in {"center", "bottom_center"}:
                    raise ValueError("Invalid crossing direction or anchor")
                number(line["hysteresis_pixels"], "line hysteresis", 0.001)
                number(line["dwell_seconds"], "line dwell", 0)
                number(line["max_gap_seconds"], "line observation gap", 0.001)
            zones = set()
            for zone in camera["zones"]:
                _keys(zone, {"id", "kind", "polygon"}, {"capacity"})
                if not isinstance(zone["id"], str) or not zone["id"].strip() or zone["id"] in zones or zone["kind"] not in {"table", "shelf", "counter", "exit", "queue", "restock", "preparation", "pickup"}:
                    raise ValueError("Invalid or duplicate zone")
                zones.add(zone["id"])
                poly = zone["polygon"]
                if len(poly) < 3 or any(len(p) != 2 for p in poly):
                    raise ValueError("Polygon needs at least three 2D vertices")
                for x, y in poly:
                    number(x, "polygon x", 0, camera["width"])
                    number(y, "polygon y", 0, camera["height"])
                from .zones import validate_polygon
                validate_polygon(poly)
                area = sum(poly[i][0] * poly[(i+1) % len(poly)][1] - poly[(i+1) % len(poly)][0] * poly[i][1] for i in range(len(poly)))
                if abs(area) < 1:
                    raise ValueError("Polygon has zero area")
                if zone["kind"] == "table" and (type(zone["capacity"]) is not int or zone["capacity"] < 1):
                    raise ValueError("Table capacity must be positive")
            if any(str(int(cid)) != cid or int(cid) not in ids for cid in camera.get("thresholds", {})):
                raise ValueError("Unknown camera threshold class")
            for threshold in camera.get("thresholds", {}).values():
                number(threshold, "camera threshold", 0, 1)
        _keys(d["tracker"], {"max_age_seconds", "max_distance_pixels", "min_hits", "max_tracks", "max_detections"})
        _keys(d["rules"], {"occupy_seconds", "empty_seconds", "movement_seconds", "disappear_seconds", "long_occupancy_seconds", "alert_cooldown_seconds", "low_confidence", "instability_ratio", "queue_limit", "authorized_product_zones"}, {"product_evidence"})
        if "product_evidence" in d["rules"]:
            evidence=d["rules"]["product_evidence"]
            _keys(evidence,{"interaction_distance_pixels","movement_pixels","minimum_interaction_seconds","max_gap_seconds"})
            for field in evidence:number(evidence[field],field,.001)
        _keys(d["model"], {"version", "weights", "metadata", "device", "load_timeout_seconds", "inference_timeout_seconds"}, {"backend","checkpoint_directory","image_size","half"})
        if d["model"].get("backend","yolo") not in {"yolo","rtdetr_v2"}:
            raise ValueError("Unsupported model backend")
        if d["model"].get("backend")=="rtdetr_v2" and not d["model"].get("checkpoint_directory"):
            raise ValueError("RT-DETR requires a local checkpoint_directory")
        if type(d["model"].get("half",False)) is not bool:
            raise ValueError("Model half must be boolean")
        if type(d["model"].get("image_size",512)) is not int or not 32<=d["model"].get("image_size",512)<=2048:
            raise ValueError("Model image_size must be 32..2048")
        _keys(d["pos"], {"mode", "window_seconds", "min_confidence", "quantity_tolerance", "sku_classes"})
        _keys(d["storage"], {"path"})
        _keys(d["evidence"], {"capture", "directory", "retention_days"})
        for field in ("max_age_seconds", "max_distance_pixels"):
            number(d["tracker"][field], field, 0.001)
        for field in ("min_hits", "max_tracks", "max_detections"):
            if type(d["tracker"][field]) is not int or d["tracker"][field] < 1:
                raise ValueError(f"Invalid tracker {field}")
        for field in ("occupy_seconds", "empty_seconds", "movement_seconds", "disappear_seconds", "long_occupancy_seconds", "alert_cooldown_seconds"):
            number(d["rules"][field], field, 0.001)
        number(d["rules"]["low_confidence"], "low confidence", 0, 1)
        number(d["rules"]["instability_ratio"], "instability ratio", 0, 1)
        if d["rules"]["disappear_seconds"] < d["tracker"]["max_age_seconds"]:
            raise ValueError("Disappearance timeout must be >= track expiration")
        if type(d["rules"]["queue_limit"]) is not int or d["rules"]["queue_limit"] < 1:
            raise ValueError("queue_limit must be positive")
        for name, targets in d["rules"]["authorized_product_zones"].items():
            if name not in names or any(z not in {z["id"] for c in d["cameras"] for z in c["zones"]} for z in targets):
                raise ValueError("Invalid authorized product zone mapping")
        if d["pos"]["mode"] not in {"camera_only", "file", "mock"}:
            raise ValueError("POS mode must be camera_only, file or mock")
        number(d["pos"]["window_seconds"], "POS window", 0.001)
        number(d["pos"]["min_confidence"], "POS confidence", 0, 1)
        if d["pos"]["quantity_tolerance"] != 0:
            raise ValueError("MVP requires zero quantity tolerance; never over-allocate a paid unit")
        if any(name not in names for name in d["pos"]["sku_classes"].values()):
            raise ValueError("SKU refers to unknown class")
        for field in ("load_timeout_seconds", "inference_timeout_seconds"):
            number(d["model"][field], field, 0.001)
        if not d["model"]["version"] or not d["model"]["weights"] or not d["model"]["metadata"]:
            raise ValueError("Explicit weights, metadata and model version required")
        number(d["evidence"]["retention_days"], "retention days", 0)
        if type(d["evidence"]["capture"]) is not bool:
            raise ValueError("Evidence capture must be boolean")
        if not isinstance(d["promotion"], dict) or not d["promotion"]:
            raise ValueError("Promotion thresholds cannot be empty")
        for metric, threshold in d["promotion"].items():
            if metric not in {"detection.precision", "detection.recall", "detection.f1", "detection.mAP50", "detection.mAP50_95", "tracking.IDF1", "tracking.MOTA", "occupancy.accuracy", "occupancy.empty_table_precision", "occupancy.occupied_table_recall", "counting.event_precision", "counting.event_recall", "reconciliation.confirmed_sale_precision"}:
                raise ValueError(f"Unknown promotion metric: {metric}")
            number(threshold, metric, 0, 1)

    def filter(self, detections: list, camera_id: str) -> list:
        camera = self.camera(camera_id)
        result = []
        for det in detections:
            if det.class_id not in self.catalog:
                raise ValueError(f"Detector returned unconfigured class {det.class_id}")
            item = self.catalog[det.class_id]
            if det.bbox[2] > camera["width"] or det.bbox[3] > camera["height"]:
                raise ValueError("Detection exceeds calibrated frame dimensions")
            threshold = camera.get("thresholds", {}).get(str(det.class_id), item["threshold"])
            if item["enabled"] and det.confidence >= threshold:
                result.append(det)
        if len(result) > self.data["tracker"]["max_detections"]:
            raise ValueError("Detection capacity exceeded; frame must be marked unknown")
        return result
