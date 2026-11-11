"""Conservative directional crossings from continuous anonymous person tracks."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import math

from .schema import Observation, key, stamp


def signed_distance(point: tuple, line: dict) -> float:
    ax, ay = line["start"]
    bx, by = line["end"]
    return ((bx-ax)*(point[1]-ay)-(by-ay)*(point[0]-ax))/math.hypot(bx-ax, by-ay)


def intersection_fraction(a: tuple, b: tuple, line: dict) -> float | None:
    """Position along a->b where it intersects the finite calibrated segment."""
    c, d = line["start"], line["end"]
    rx, ry, sx, sy = b[0]-a[0], b[1]-a[1], d[0]-c[0], d[1]-c[1]
    denominator = rx*sy-ry*sx
    if abs(denominator) < 1e-10:
        return None
    qx, qy = c[0]-a[0], c[1]-a[1]
    t, u = (qx*sy-qy*sx)/denominator, (qx*ry-qy*rx)/denominator
    return t if 0 <= t <= 1 and 0 <= u <= 1 else None


@dataclass
class CrossingState:
    point: tuple
    seen: float
    stable: int | None = None
    candidate: int | None = None
    since: float = 0
    crossing_at: float | None = None
    confidence: float = 1


class TrafficEngine:
    def __init__(self, config, camera_id: str, run_id: str):
        self.catalog = config.catalog
        self.min_hits = config.data["tracker"]["min_hits"]
        self.camera_id, self.run_id = camera_id, run_id
        self.lines = config.camera(camera_id).get("crossing_lines", [])
        self.states: dict[tuple[str, int], CrossingState] = {}
        self.previous_ts: float | None = None

    def reset(self) -> None:
        self.states.clear()

    def update(self, tracks: list[Observation], ts: float, frame: int, reliable: bool = True) -> list[dict]:
        if not math.isfinite(ts) or self.previous_ts is not None and ts <= self.previous_ts:
            raise ValueError("Traffic timestamps must increase and be finite")
        self.previous_ts = ts
        if not reliable:
            self.reset()
            return []
        visible = {t.track_id: t for t in tracks if not t.missed and t.hits >= self.min_hits
                   and self.catalog[t.class_id]["kind"] == "person"}
        # Never bridge missing observations, a new ID, or an unreliable frame.
        self.states = {k:s for k,s in self.states.items() if k[1] in visible}
        result = []
        for line in self.lines:
            for tid, track in visible.items():
                point = track.center if line["anchor"] == "center" else (track.center[0], track.bbox[3])
                identity = (line["id"], tid)
                state = self.states.get(identity)
                if state is None or ts-state.seen > line["max_gap_seconds"]:
                    state = CrossingState(point, ts, since=ts, confidence=track.confidence)
                    self.states[identity] = state
                fraction = intersection_fraction(state.point, point, line)
                if fraction is not None and state.stable is not None and state.crossing_at is None:
                    state.crossing_at = state.seen + fraction*(ts-state.seen)
                distance = signed_distance(point, line)
                side = 1 if distance >= line["hysteresis_pixels"] else -1 if distance <= -line["hysteresis_pixels"] else 0
                if not side:
                    state.candidate = None
                elif side == state.stable:
                    state.candidate, state.crossing_at = None, None
                    state.confidence = track.confidence
                else:
                    if state.candidate != side:
                        state.candidate, state.since = side, ts
                        state.confidence = track.confidence
                    else:
                        state.confidence = min(state.confidence, track.confidence)
                    # Capture timestamps are serialized to microseconds; tolerate their rounding.
                    if ts-state.since >= line["dwell_seconds"]-1e-6:
                        if state.stable is not None and state.crossing_at is not None:
                            inside = 1 if line["inside_side"] == "positive" else -1
                            kind = "person_entered" if side == inside else "person_exited"
                            crossing = stamp(datetime.fromtimestamp(state.crossing_at, timezone.utc))
                            confirmed = stamp(datetime.fromtimestamp(ts, timezone.utc))
                            result.append({"event_id":key(self.run_id,self.camera_id,line["id"],tid,frame,kind),
                                "kind":kind,"timestamp":crossing,"confirmed_at":confirmed,
                                "camera_id":self.camera_id,"run_id":self.run_id,"line_id":line["id"],
                                "track_id":tid,"product_class":self.catalog[track.class_id]["name"],
                                "source_zone":None,"destination_zone":None,"status":"observed",
                                "role":"unknown","confidence":state.confidence,"schema_version":1,
                                "evidence":{"run_id":self.run_id,"frame":frame,"anchor":line["anchor"],
                                            "crossing_timestamp":crossing,"confirmation_timestamp":confirmed}})
                        # Re-arm after confirmed residence, even when crossing was outside the segment.
                        state.stable, state.candidate, state.crossing_at = side, None, None
                state.point, state.seen = point, ts
        return result
