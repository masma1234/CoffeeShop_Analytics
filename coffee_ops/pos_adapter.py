"""Immutable POS order lines. Paid POS quantities, not camera counts, define sales."""
from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Iterable, Protocol

from .schema import key, stamp, utc
from .storage import SQLiteStore


class POSAdapter(Protocol):
    def orders(self) -> Iterable[dict]: ...


class MockPOSAdapter:
    def __init__(self, rows: list[dict]):
        self.rows = rows

    def orders(self) -> Iterable[dict]:
        return iter(self.rows)


class FilePOSAdapter:
    def __init__(self, path: str | Path):
        self.path = Path(path)

    def orders(self) -> Iterable[dict]:
        if self.path.suffix.lower() == ".json":
            rows = json.loads(self.path.read_text(encoding="utf-8"))
            if not isinstance(rows, list):
                raise ValueError("POS JSON must be a list of order lines")
            yield from rows
        elif self.path.suffix.lower() == ".csv":
            with self.path.open(encoding="utf-8-sig", newline="") as stream:
                yield from csv.DictReader(stream)
        else:
            raise ValueError("POS file must be CSV or JSON")


def normalize(row: dict, sku_classes: dict) -> dict:
    required = {"order_id", "line_id", "timestamp", "sku", "quantity", "payment_status", "camera_id", "zone_id"}
    if not required <= row.keys():
        raise ValueError(f"Missing POS fields: {sorted(required-row.keys())}")
    if any(not isinstance(row[f], str) or not row[f] for f in ("order_id", "line_id", "sku", "camera_id", "zone_id")):
        raise ValueError("POS identifiers must be non-empty strings")
    quantity = int(row["quantity"])
    if isinstance(row["quantity"], bool) or str(quantity) != str(row["quantity"]) or quantity < 1:
        raise ValueError("POS quantity must be a positive integer")
    if row["payment_status"] not in {"paid", "pending", "cancelled", "refunded"}:
        raise ValueError("Invalid payment status")
    if row["sku"] not in sku_classes:
        raise ValueError(f"Unmapped SKU: {row['sku']}")
    revision = int(row.get("revision", 1))
    if str(revision) != str(row.get("revision", 1)) or revision < 1:
        raise ValueError("POS revision must be a positive integer")
    return {"id": key(row["order_id"], row["line_id"]), "order_id": row["order_id"], "line_id": row["line_id"],
            "timestamp": stamp(utc(row["timestamp"])), "sku": row["sku"], "quantity": quantity, "revision": revision,
            "payment_status": row["payment_status"], "camera_id": row["camera_id"], "zone_id": row["zone_id"],
            "product_class": sku_classes[row["sku"]], "channel": row.get("channel"), "terminal_id": row.get("terminal_id")}


def import_orders(store: SQLiteStore, adapter: POSAdapter, config: dict) -> int:
    count = 0
    with store.transaction():
        for raw in adapter.orders():
            row = normalize(raw, config["sku_classes"])
            prior = store.order(row["id"])
            if prior and any(prior[k] != row[k] for k in ("sku", "quantity", "camera_id", "zone_id", "timestamp", "product_class", "channel", "terminal_id")):
                raise ValueError("Order revision may change payment status only; corrections require a separate line")
            count += store.append("orders", key(row["id"], row["revision"]), row["timestamp"], row)
    return count
