"""Shared value objects and canonical UTC serialization."""
from __future__ import annotations

import hashlib
import json
import math
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any


def utc(value: str | datetime) -> datetime:
    dt = datetime.fromisoformat(value.replace("Z", "+00:00")) if isinstance(value, str) else value
    if dt.tzinfo is None:
        raise ValueError("Timestamp must include UTC offset")
    return dt.astimezone(timezone.utc)


def stamp(value: datetime) -> str:
    return utc(value).isoformat(timespec="microseconds").replace("+00:00", "Z")


def now() -> str:
    return stamp(datetime.now(timezone.utc))


def canonical(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False)


def key(*parts: Any) -> str:
    return hashlib.sha256(canonical(parts).encode()).hexdigest()[:32]


def file_hash(path: str) -> str:
    digest = hashlib.sha256()
    with open(path, "rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


@dataclass(frozen=True)
class Detection:
    class_id: int
    bbox: tuple[float, float, float, float]
    confidence: float

    def __post_init__(self) -> None:
        if len(self.bbox) != 4 or not all(math.isfinite(x) for x in self.bbox):
            raise ValueError("Bounding box must contain four finite coordinates")
        x1, y1, x2, y2 = self.bbox
        if x2 <= x1 or y2 <= y1 or min(x1, y1) < 0:
            raise ValueError("Invalid bounding box")
        if not 0 <= self.confidence <= 1 or type(self.class_id) is not int or self.class_id < 0:
            raise ValueError("Invalid class or confidence")


@dataclass(frozen=True)
class Observation:
    track_id: int
    class_id: int
    bbox: tuple[float, float, float, float]
    confidence: float
    created_at: float
    last_seen: float
    hits: int
    missed: bool
    quality: float

    @property
    def center(self) -> tuple[float, float]:
        x1, y1, x2, y2 = self.bbox
        return ((x1 + x2) / 2, (y1 + y2) / 2)
