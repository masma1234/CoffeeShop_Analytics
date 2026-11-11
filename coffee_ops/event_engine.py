"""Track-confirmed movement; absence is uncertainty, never evidence of a sale."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone

from .config import Config
from .schema import Observation, key, stamp
from .traffic import TrafficEngine
from .product_evidence import ProductEvidenceEngine
from .zones import TableState, assign, contains


@dataclass
class ZoneTrack:
    class_id: int
    stable: str | None = None
    candidate: str | None = None
    candidate_since: float = 0
    initialized: bool = False
    last_seen: float = 0
    confidence: float = 0
    assigned_table: str | None = None
    table_entered_at: float | None = None


class EventEngine:
    def __init__(self, config: Config, camera_id: str, run_id: str):
        self.config, self.camera_id, self.run_id = config, camera_id, run_id
        self.zones = config.camera(camera_id)["zones"]
        self.rules = config.data["rules"]
        self.tables = {z["id"]: TableState(z, self.rules) for z in self.zones if z["kind"] == "table"}
        self.tracks: dict[int, ZoneTrack] = {}
        self.zone_kinds = {z["id"]: z["kind"] for z in self.zones}
        self.traffic = TrafficEngine(config, camera_id, run_id)
        self.product_evidence = ProductEvidenceEngine(config,camera_id,run_id)

    def reset(self) -> None:
        self.tracks.clear()
        self.traffic.reset()
        self.product_evidence.reset()
        for table in self.tables.values():
            table.status = "unknown"
            table.positive_since = table.empty_since = None
            table.occupied_since = table.last_seen = None

    def _event(self, kind: str, tid: int, state: ZoneTrack, frame: int, ts: float,
               source: str | None, destination: str | None) -> dict:
        timestamp = stamp(datetime.fromtimestamp(ts, timezone.utc))
        return {"event_id": key(self.run_id, self.camera_id, frame, kind, tid),
                "kind": kind, "timestamp": timestamp, "camera_id": self.camera_id,
                "run_id": self.run_id, "product_class": self.config.catalog[state.class_id]["name"],
                "track_id": tid, "source_zone": source, "destination_zone": destination,
                "confidence": state.confidence, "status": "review_required" if kind in {"disappeared", "possible_unpaid_exit"} else "observed",
                "linked_order_id": None, "evidence": {"run_id": self.run_id, "frame": frame, "timestamp": timestamp},
                "table_id": state.assigned_table, "table_entered_at": state.table_entered_at}

    def update(self, tracks: list[Observation], ts: float, frame: int, reliable: bool = True) -> tuple[list[dict], list[dict]]:
        events = self.traffic.update(tracks, ts, frame, reliable)
        confirmed = [t for t in tracks if t.hits >= self.config.data["tracker"]["min_hits"]]
        # Products use center points; configure table polygons around seated people, not just tabletops.
        table_zones = [z for z in self.zones if z["kind"] == "table"]
        assignments = {t.track_id: assign(table_zones, t) for t in confirmed}
        for t in confirmed:
            if t.missed or not reliable:
                if t.track_id in self.tracks:
                    self.tracks[t.track_id].initialized = False
                continue
            state = self.tracks.setdefault(t.track_id, ZoneTrack(t.class_id))
            state.last_seen, state.confidence = ts, t.confidence
            if sum(contains(z["polygon"], t.center) for z in self.zones) > 1:
                state.initialized = False
                continue
            zone = assign(self.zones, t)
            if not state.initialized or zone != state.candidate:
                state.candidate, state.candidate_since, state.initialized = zone, ts, True
            if ts-state.candidate_since >= self.rules["movement_seconds"] and zone != state.stable:
                previous = state.stable
                state.stable = zone
                kind = self.config.catalog[t.class_id]["kind"]
                if kind == "product":
                    event_kind = "placed" if previous is None else "removed" if zone is None else "transferred"
                    events.append(self._event(event_kind, t.track_id, state, frame, ts, previous, zone))
                elif kind == "person":
                    if self.zone_kinds.get(zone) == "table":
                        state.assigned_table, state.table_entered_at = zone, ts
                    events.append(self._event("person_zone_entered", t.track_id, state, frame, ts, previous, zone))
                    if self.zone_kinds.get(zone) == "exit" and state.assigned_table:
                        events.append(self._event("possible_unpaid_exit", t.track_id, state, frame, ts, previous, zone))
        # Prune by time even during unreliable frames. Never infer removals while unreliable.
        for tid, state in list(self.tracks.items()):
            if ts-state.last_seen > self.rules["disappear_seconds"]:
                if reliable and state.stable and self.config.catalog[state.class_id]["kind"] == "product":
                    events.append(self._event("disappeared", tid, state, frame, ts, state.stable, None))
                del self.tracks[tid]
        events.extend(self.product_evidence.update(confirmed,self.tracks,list(events),ts,frame,reliable))
        states = []
        for zid, table in self.tables.items():
            members = [t for t in confirmed if assignments[t.track_id] == zid]
            people = [t for t in members if self.config.catalog[t.class_id]["kind"] == "person"]
            products = [self.config.catalog[t.class_id]["name"] for t in members if self.config.catalog[t.class_id]["kind"] == "product" and not t.missed]
            ambiguous = any(self.config.catalog[t.class_id]["kind"] == "person" and
                            contains(table.zone["polygon"], t.center) and assignments[t.track_id] is None for t in confirmed)
            person_detection_enabled = any(c["enabled"] and c["kind"] == "person" for c in self.config.catalog.values())
            states.append(table.update(ts, people, products, reliable and not ambiguous and person_detection_enabled))
        return events, states
