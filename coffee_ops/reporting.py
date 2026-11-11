"""Derived daily aggregates and paginated JSON read models."""
from __future__ import annotations

from collections import Counter
from datetime import date

from .schema import key, now
from .storage import SQLiteStore


def _daily_snapshot(store: SQLiteStore, day: str) -> dict:
    date.fromisoformat(day)
    sales: Counter = Counter()
    movement: Counter = Counter()
    reconciliations: Counter = Counter()
    for order in store.order_lines(day):
        if order["payment_status"] == "paid":
            sales[order["sku"]] += order["quantity"]
    for event in store.scan("inventory_movements", day):
        movement[f"{event['product_class']}:{event['kind']}"] += 1
    for row in store.latest_records("reconciliations", "event_id", day=day):
        reconciliations[row["status"]] += 1
    occupancy = {"occupied": 0, "empty": 0, "unknown": 0}
    duration_sum = duration_count = 0
    for sample in store.scan("occupancy", day):
        for table in sample["tables"]:
            occupancy[table["status"]] += 1
    for item in store.scan("occupancy_sessions", day):
        duration_sum += item["duration_seconds"]
        duration_count += 1
    known = occupancy["occupied"]+occupancy["empty"]
    result = {"date_utc": day, "confirmed_sales_source": "paid_POS_only", "confirmed_sold_units": dict(sales),
              "visual_movements": dict(movement), "reconciliation_statuses": dict(reconciliations),
              "occupancy_samples": occupancy,
              "table_utilization_percent": 100*occupancy["occupied"]/known if known else None,
              "utilization_method": "sample-weighted known states; unknown excluded",
              "average_completed_occupancy_seconds": duration_sum/duration_count if duration_count else None,
              "payment_notice": "Video alone cannot confirm payment. Alerts require human review."}
    return result


def daily_report(store: SQLiteStore, day: str) -> dict:
    with store.snapshot():
        result = _daily_snapshot(store, day)
    # A new aggregate version only when the underlying report changes.
    identity = key(day, result)
    if not store.get("daily_aggregates", identity):
        store.append("daily_aggregates", identity, now(), result)
    return result


def current_status(store: SQLiteStore, camera_id: str) -> dict:
    sample = store.latest("occupancy", "camera_id", camera_id)
    observation = store.latest("observations", "camera_id", camera_id)
    health = store.latest("health", "camera_id", camera_id)
    tables = sample["tables"] if sample else []
    from .schema import utc
    age = (utc(now())-utc(health["timestamp"])).total_seconds() if health else None
    active = bool(health and sample and observation and health["status"] == "running"
                  and health.get("processed_frames", 0) > 0 and 0 <= age < 60
                  and health["run_id"] == sample["run_id"] == observation["run_id"])
    if not active:
        tables = [{**t, "status": "unknown", "people": None, "full": False, "confidence": 0} for t in tables]
    known = sum(t["status"] != "unknown" for t in tables)
    return {"camera_id": camera_id, "as_of": sample["timestamp"] if sample else None,
            "tables": tables, "empty_tables": sum(t["status"] == "empty" for t in tables),
            "occupied_tables": sum(t["status"] == "occupied" for t in tables),
            "full_tables": sum(t["full"] for t in tables),
            "current_people_at_tables": sum(t["people"] or 0 for t in tables) if active and all(t["status"] != "unknown" for t in tables) else None,
            "table_utilization_percent": 100*sum(t["status"] == "occupied" for t in tables)/known if known else None,
            "observations": observation if active else None, "last_observations": observation,
            "health": health, "storage": store.health()}


def active_alerts(store: SQLiteStore, limit: int = 1000, after: int = 0) -> list[dict]:
    return store.active_alerts(limit, after)


def unresolved_events(store: SQLiteStore, limit: int = 1000, after: int = 0) -> list[dict]:
    result = []
    for item in store.unresolved(limit, after):
        item["visual_event"] = store.get("events", item["event_id"])
        result.append(item)
    return result
