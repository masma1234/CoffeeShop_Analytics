"""Bounded, transactional POS matching through the storage adapter."""
from __future__ import annotations

from .alerts import alert
from .inventory import MOVEMENTS
from .schema import key, utc
from .storage import SQLiteStore


def _classify(store: SQLiteStore, event: dict, config: dict) -> tuple[str, dict | None, str]:
    kind, eid = event["kind"], event["event_id"]
    if kind == "placed":
        return "observed", None, "placement_is_not_a_sale"
    if config["mode"] == "camera_only":
        return ("inventory_discrepancy" if kind == "disappeared" else "needs_review"), None, "camera_only_no_payment_confirmation"
    allocated = store.allocation(eid)
    if allocated:
        order = store.order(allocated)
        return ("confirmed_sale", order, "existing_paid_allocation") if order and order["payment_status"] == "paid" else ("payment_unmatched", None, "allocated_order_no_longer_paid")
    sold = store.sold_event(event)
    if sold and sold["event_id"] != eid and kind in MOVEMENTS:
        order = store.order(store.allocation(sold["event_id"]))
        if utc(sold["timestamp"]) <= utc(event["timestamp"]) and order and order["payment_status"] == "paid":
            return "sale_correlated_movement", None, "same_track_already_allocated"
        return "needs_review", None, "track_has_another_allocation"
    if kind == "disappeared":
        return "inventory_discrepancy", None, "disappearance_has_no_observed_destination"
    if event["confidence"] < config["min_confidence"]:
        return "needs_review", None, "insufficient_visual_confidence"
    candidates = store.candidates(event, config["window_seconds"])
    if len(candidates) > 1:
        return "needs_review", None, "ambiguous_candidates"
    if not candidates:
        return "payment_unmatched", None, "no_qualifying_order"
    order = candidates[0]
    if kind == "possible_unpaid_exit":
        return ("order_correlated" if order["payment_status"] == "paid" else "payment_unmatched"), order, "table_order_correlation_only"
    return ("confirmed_sale" if order["payment_status"] == "paid" else "likely_sale"), order, "time_class_zone_quantity_rules"


def reconcile(store: SQLiteStore, config: dict, batch_size: int = 200) -> dict:
    """Each batch is atomic. New events after the initial watermark wait for next run.

    Repeat invocations revisit history using indexed candidate lookups; unchanged
    POS/config contexts skip matching. SQLite still serializes writers per batch.
    """
    if type(batch_size) is not int or not 1 <= batch_size <= 1000:
        raise ValueError("Reconciliation batch_size must be 1..1000")
    counts: dict[str, int] = {}
    after, watermark = 0, store.watermark("events")
    while after < watermark:
        with store.transaction():
            context = key(config, store.watermark("orders"))
            batch = store.records("events", limit=batch_size, after=after)
            if not batch:
                break
            for event in batch:
                after = event["_seq"]
                if after > watermark:
                    break
                if event["kind"] not in MOVEMENTS | {"possible_unpaid_exit"}:
                    continue
                eid = event["event_id"]
                previous = store.latest("reconciliations", "event_id", eid)
                if previous and previous.get("context") == context:
                    status = previous["status"]
                else:
                    status, order, reason = _classify(store, event, config)
                    result = {"event_id": eid, "timestamp": event["timestamp"], "status": status,
                              "context": context, "revision": previous.get("revision", 0)+1 if previous else 1,
                              "order_id": order["order_id"] if order else None,
                              "order_line_id": order["id"] if order else None,
                              "association_confidence": event["confidence"] if order else None,
                              "reason": reason, "payment_proof": "POS" if status == "confirmed_sale" else None}
                    if status == "confirmed_sale" and store.allocation(eid) is None:
                        store.allocate(event, order)
                    store.append("reconciliations", key(result), event["timestamp"], result)
                    if status in {"payment_unmatched", "inventory_discrepancy", "needs_review"}:
                        item = alert(status, event["timestamp"], event["camera_id"],
                                     "No unambiguous paid order association. Review evidence, POS availability and legitimate movements.",
                                     event["confidence"], event["evidence"], [eid], key(eid, status))
                        store.append("alerts", item["alert_id"], event["timestamp"], item)
                counts[status] = counts.get(status, 0)+1
    return counts
