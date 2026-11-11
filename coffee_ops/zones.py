"""Camera-calibrated polygon membership and conservative occupancy hysteresis."""
from __future__ import annotations

from dataclasses import dataclass

from .schema import Observation


def validate_polygon(polygon: list) -> None:
    """Reject repeated vertices and crossings, including non-adjacent edge touches."""
    if len(set(map(tuple, polygon))) != len(polygon):
        raise ValueError("Polygon has repeated vertices")
    def cross(a: list, b: list, c: list) -> float:
        return (b[0]-a[0])*(c[1]-a[1])-(b[1]-a[1])*(c[0]-a[0])
    def on(a: list, b: list, p: list) -> bool:
        return abs(cross(a, b, p)) < 1e-9 and min(a[0], b[0]) <= p[0] <= max(a[0], b[0]) and min(a[1], b[1]) <= p[1] <= max(a[1], b[1])
    n = len(polygon)
    for i in range(n):
        a, b = polygon[i], polygon[(i+1) % n]
        for j in range(i+1, n):
            if j == i+1 or (i == 0 and j == n-1):
                continue
            c, d = polygon[j], polygon[(j+1) % n]
            if (cross(a, b, c)*cross(a, b, d) < 0 and cross(c, d, a)*cross(c, d, b) < 0) or on(a, b, c) or on(a, b, d) or on(c, d, a) or on(c, d, b):
                raise ValueError("Polygon edges intersect")


def contains(polygon: list, point: tuple[float, float]) -> bool:
    x, y = point
    inside = False
    for i, (ax, ay) in enumerate(polygon):
        bx, by = polygon[(i+1) % len(polygon)]
        cross = (x-ax)*(by-ay) - (y-ay)*(bx-ax)
        if abs(cross) < 1e-6 and min(ax, bx) <= x <= max(ax, bx) and min(ay, by) <= y <= max(ay, by):
            return True
        if (ay > y) != (by > y) and x < (bx-ax)*(y-ay)/(by-ay)+ax:
            inside = not inside
    return inside


def assign(zones: list[dict], track: Observation) -> str | None:
    matches = [z["id"] for z in zones if contains(z["polygon"], track.center)]
    # Overlap is ambiguous, never double-count a customer at two tables.
    return matches[0] if len(matches) == 1 else None


@dataclass
class TableState:
    zone: dict
    rules: dict
    status: str = "unknown"
    positive_since: float | None = None
    empty_since: float | None = None
    occupied_since: float | None = None
    last_seen: float | None = None

    def update(self, timestamp: float, people: list[Observation], products: list[str], reliable: bool) -> dict:
        visible = [p for p in people if not p.missed]
        occluded = any(p.missed for p in people)
        if not reliable or occluded:
            self.status = "unknown"
            self.empty_since = self.positive_since = None
        elif visible:
            self.last_seen = timestamp
            self.empty_since = None
            if self.positive_since is None:
                self.positive_since = timestamp
            if self.occupied_since is not None or timestamp-self.positive_since >= self.rules["occupy_seconds"]:
                self.status = "occupied"
                if self.occupied_since is None:
                    self.occupied_since = self.positive_since
        else:
            self.positive_since = None
            if self.empty_since is None:
                self.empty_since = timestamp
            if timestamp-self.empty_since >= self.rules["empty_seconds"]:
                self.status = "empty"
                self.occupied_since = None
        return {"zone_id": self.zone["id"], "status": self.status,
                "people": len(visible) if reliable else None,
                "confidence": min((p.confidence for p in visible), default=1.0) if reliable and not occluded and self.status != "unknown" else 0.0,
                "occupied_since": self.occupied_since, "last_seen": self.last_seen,
                "occupied_seconds": timestamp-self.occupied_since if self.occupied_since is not None else 0.0,
                "full": self.status == "occupied" and len(visible) >= self.zone["capacity"],
                "products": products}
