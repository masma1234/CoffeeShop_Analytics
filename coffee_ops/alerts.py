"""Neutral, deduplicated review alerts and health signals."""
from __future__ import annotations

from .schema import key


def alert(kind: str, timestamp: str, camera_id: str, reason: str, confidence: float,
          evidence: dict, related: list, identity: str, severity: str = "warning") -> dict:
    return {"alert_id": key(identity, kind), "kind": kind, "severity": severity,
            "reason": reason, "confidence": confidence, "camera_id": camera_id,
            "timestamp": timestamp, "evidence": evidence, "related_tracks_events": related,
            "resolution": "open", "false_positive": None, "human_review_required": True}


class AlertEngine:
    def __init__(self, rules: dict, camera_id: str, run_id: str):
        self.rules, self.camera_id, self.run_id = rules, camera_id, run_id
        self.last: dict[str, float] = {}

    def evaluate(self, events: list[dict], tables: list[dict], tracks: list, zones: list[dict],
                 timestamp: str, ts: float, frame: int, instability: float, reliable: bool) -> list[dict]:
        from .zones import contains
        candidates: list[tuple] = []
        evidence = {"run_id": self.run_id, "frame": frame, "timestamp": timestamp}
        for e in events:
            if e["kind"] in {"disappeared", "possible_unpaid_exit"}:
                name = "inventory_discrepancy" if e["kind"] == "disappeared" else "possible_unpaid_exit"
                candidates.append((name, "Visual evidence is incomplete; check orders, occlusion and staff activity.", e["confidence"], [e["event_id"], e["track_id"]], e["event_id"]))
            allowed = self.rules["authorized_product_zones"].get(e["product_class"])
            if e["kind"] in {"transferred", "removed"} and allowed is not None and e["destination_zone"] not in allowed:
                candidates.append(("product_outside_authorized_zone", "Observed movement outside configured product zones.", e["confidence"], [e["event_id"]], e["event_id"]))
        for table in tables:
            if table["full"]:
                candidates.append(("table_full", "Configured seating threshold reached.", table["confidence"], [], table["zone_id"]))
            if table["status"] == "occupied" and table["occupied_seconds"] >= self.rules["long_occupancy_seconds"]:
                candidates.append(("table_occupied_too_long", "Occupancy exceeds configured duration.", table["confidence"], [], table["zone_id"]))
        for zone in zones:
            if zone["kind"] == "queue" and sum(not t.missed and contains(zone["polygon"], t.center) for t in tracks) >= self.rules["queue_limit"]:
                candidates.append(("queue_congestion", "Queue exceeds configured person limit.", 0.7, [], zone["id"]))
        if not reliable:
            candidates.append(("low_detection_confidence", "Frame is unreliable; occupancy is unknown.", 0.0, [], "camera"))
        if instability > self.rules["instability_ratio"]:
            candidates.append(("high_tracking_instability", "High fraction of newly created tracks; IDs may have changed.", 1-instability, [], "tracker"))
        result = []
        for kind, reason, confidence, related, identity in candidates:
            throttle = f"{kind}:{identity}"
            if ts-self.last.get(throttle, float("-inf")) >= self.rules["alert_cooldown_seconds"]:
                result.append(alert(kind, timestamp, self.camera_id, reason, confidence, evidence, related, key(self.run_id, identity, frame)))
                self.last[throttle] = ts
        self.last = {k: v for k, v in self.last.items() if ts-v < self.rules["alert_cooldown_seconds"]*2}
        return result
