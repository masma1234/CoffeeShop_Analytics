"""Visual inventory ledger, separate from POS sales and reconciliation."""
from __future__ import annotations

from .storage import SQLiteStore

MOVEMENTS = {"placed", "removed", "transferred", "disappeared"}


def record_movement(store: SQLiteStore, event: dict) -> None:
    if event["kind"] in MOVEMENTS:
        store.append("inventory_movements", event["event_id"], event["timestamp"], {
            **event, "quantity": 1, "ledger_type": "visual_movement", "sold_quantity": 0})
