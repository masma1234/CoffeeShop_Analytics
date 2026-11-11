"""Versioned SQLite ledger and indexed projections; all SQL belongs to this adapter."""
from __future__ import annotations

import json
import sqlite3
import time
import uuid
from contextlib import contextmanager
from datetime import date, timedelta
from pathlib import Path
from typing import Iterator, Protocol

from .schema import canonical, key, now, stamp, utc

SCHEMA_VERSION = 2
HEAD_FIELDS = ("camera_id", "run_id", "event_id", "alert_id", "id")


class EventStore(Protocol):
    def append(self, kind: str, identity: str, timestamp: str, payload: dict) -> bool: ...
    def records(self, kind: str, *, day: str | None = None, limit: int = 1000, after: int = 0) -> list[dict]: ...


class SQLiteStore:
    """One connection per worker/thread. Transactions and projections commit together."""

    def __init__(self, path: str | Path, timeout: float = 10, read_only: bool = False):
        path = Path(path)
        if read_only:
            if not path.is_file():
                raise FileNotFoundError(path)
            self.db = sqlite3.connect(path.resolve().as_uri()+"?mode=ro",uri=True,isolation_level=None,timeout=timeout)
        else:
            path.parent.mkdir(parents=True, exist_ok=True)
            self.db = sqlite3.connect(path, isolation_level=None, timeout=timeout)
        self.db.row_factory = sqlite3.Row
        self._savepoint = 0
        try:
            version = self.db.execute("PRAGMA user_version").fetchone()[0]
            if version > SCHEMA_VERSION:
                raise ValueError(f"Database schema {version} is newer than supported {SCHEMA_VERSION}")
            if read_only:
                if version != SCHEMA_VERSION:
                    raise ValueError("Open with a writer to migrate the database before serving read-only reports")
                self.db.execute("PRAGMA query_only=ON")
                return
            self.db.execute("PRAGMA journal_mode=WAL")
            self.db.execute("PRAGMA foreign_keys=ON")
            self._migrate()
        except BaseException:
            self.db.close()
            raise

    def _migrate(self) -> None:
        statements = [
            """CREATE TABLE IF NOT EXISTS records (
              seq INTEGER PRIMARY KEY AUTOINCREMENT, kind TEXT NOT NULL, id TEXT NOT NULL,
              timestamp TEXT NOT NULL, payload TEXT NOT NULL, UNIQUE(kind,id))""",
            "CREATE INDEX IF NOT EXISTS records_kind_time ON records(kind,timestamp)",
            "CREATE INDEX IF NOT EXISTS records_kind_seq ON records(kind,seq)",
            "CREATE INDEX IF NOT EXISTS records_run_camera ON records(kind,json_extract(payload,'$.run_id'),json_extract(payload,'$.camera_id'),seq)",
            "CREATE INDEX IF NOT EXISTS records_camera_seq ON records(kind,json_extract(payload,'$.camera_id'),seq)",
            "CREATE TABLE IF NOT EXISTS allocation_events (id TEXT PRIMARY KEY)",
            """CREATE TABLE IF NOT EXISTS allocations (
              event_id TEXT PRIMARY KEY, order_line_id TEXT NOT NULL,
              FOREIGN KEY(event_id) REFERENCES allocation_events(id))""",
            "CREATE INDEX IF NOT EXISTS allocations_order ON allocations(order_line_id)",
            """CREATE TABLE IF NOT EXISTS sold_tracks (
              run_id TEXT NOT NULL, camera_id TEXT NOT NULL, track_id INTEGER NOT NULL,
              event_id TEXT NOT NULL, PRIMARY KEY(run_id,camera_id,track_id))""",
            """CREATE TABLE IF NOT EXISTS heads (
              kind TEXT NOT NULL, field TEXT NOT NULL, value TEXT NOT NULL, seq INTEGER NOT NULL,
              PRIMARY KEY(kind,field,value), FOREIGN KEY(seq) REFERENCES records(seq))""",
            """CREATE TABLE IF NOT EXISTS order_heads (
              id TEXT PRIMARY KEY, revision INTEGER NOT NULL, timestamp TEXT NOT NULL,
              camera_id TEXT NOT NULL, zone_id TEXT NOT NULL, product_class TEXT NOT NULL,
              payment_status TEXT NOT NULL, quantity INTEGER NOT NULL, payload TEXT NOT NULL)""",
            """CREATE INDEX IF NOT EXISTS orders_match
              ON order_heads(camera_id,zone_id,product_class,timestamp)""",
            "CREATE INDEX IF NOT EXISTS orders_exit ON order_heads(camera_id,zone_id,timestamp)",
            "CREATE INDEX IF NOT EXISTS orders_day ON order_heads(timestamp)",
            """CREATE TABLE IF NOT EXISTS camera_leases (
              camera_id TEXT PRIMARY KEY, owner TEXT NOT NULL, run_id TEXT NOT NULL, expires REAL NOT NULL)""",
            """CREATE TRIGGER IF NOT EXISTS records_no_update BEFORE UPDATE ON records
              BEGIN SELECT RAISE(ABORT, 'append-only records'); END""",
            """CREATE TRIGGER IF NOT EXISTS records_no_delete BEFORE DELETE ON records
              BEGIN SELECT RAISE(ABORT, 'append-only records'); END""",
        ]
        with self.transaction():
            version = self.db.execute("PRAGMA user_version").fetchone()[0]
            for sql in statements:
                self.db.execute(sql)
            if version < SCHEMA_VERSION:
                for row in self.db.execute("SELECT seq,kind,payload FROM records ORDER BY seq"):
                    self._project(row["seq"], row["kind"], json.loads(row["payload"]))
                # Earlier versions could contain allocations without the per-track projection.
                self.db.execute("""INSERT OR IGNORE INTO sold_tracks(run_id,camera_id,track_id,event_id)
                  SELECT json_extract(r.payload,'$.run_id'),json_extract(r.payload,'$.camera_id'),
                  json_extract(r.payload,'$.track_id'),a.event_id FROM allocations a
                  JOIN records r ON r.kind='events' AND r.id=a.event_id""")
                self.db.execute(f"PRAGMA user_version={SCHEMA_VERSION}")

    @contextmanager
    def transaction(self) -> Iterator[None]:
        nested = self.db.in_transaction
        self._savepoint += 1
        name = f"operation_{self._savepoint}"
        self.db.execute(f"SAVEPOINT {name}" if nested else "BEGIN IMMEDIATE")
        try:
            yield
        except BaseException:
            if nested:
                self.db.execute(f"ROLLBACK TO {name}")
                self.db.execute(f"RELEASE {name}")
            else:
                self.db.rollback()
            raise
        else:
            self.db.execute(f"RELEASE {name}") if nested else self.db.commit()

    def _project(self, seq: int, kind: str, payload: dict) -> None:
        for field in HEAD_FIELDS:
            value = payload.get(field)
            if isinstance(value, (str, int)):
                self.db.execute("""INSERT INTO heads(kind,field,value,seq) VALUES (?,?,?,?)
                  ON CONFLICT(kind,field,value) DO UPDATE SET seq=excluded.seq""",
                                (kind, field, str(value), seq))
        if kind == "orders":
            self.db.execute("""INSERT INTO order_heads VALUES (?,?,?,?,?,?,?,?,?)
              ON CONFLICT(id) DO UPDATE SET revision=excluded.revision,
              payment_status=excluded.payment_status,payload=excluded.payload
              WHERE excluded.revision>order_heads.revision""",
              (payload["id"], payload.get("revision", 1), payload["timestamp"], payload["camera_id"],
               payload["zone_id"], payload["product_class"], payload["payment_status"],
               payload["quantity"], canonical(payload)))

    def append(self, kind: str, identity: str, timestamp: str, payload: dict) -> bool:
        timestamp = stamp(utc(timestamp))
        encoded = canonical(payload)
        # Transaction protects both first-insert and projections across independent connections.
        with self.transaction():
            previous = self.db.execute("SELECT timestamp,payload FROM records WHERE kind=? AND id=?", (kind, identity)).fetchone()
            if previous:
                if previous["payload"] != encoded or stamp(utc(previous["timestamp"])) != timestamp:
                    raise ValueError(f"Conflicting immutable {kind}: {identity}")
                return False
            cursor = self.db.execute("INSERT INTO records(kind,id,timestamp,payload) VALUES (?,?,?,?)", (kind, identity, timestamp, encoded))
            self._project(cursor.lastrowid, kind, payload)
            return True

    @contextmanager
    def snapshot(self) -> Iterator[None]:
        """Consistent report reads without reserving the SQLite writer lock."""
        if self.db.in_transaction:
            yield
            return
        self.db.execute("BEGIN")
        try:
            yield
        finally:
            self.db.rollback()

    def scan_run(self, kind: str, run_id: str, camera_id: str, reverse: bool = False, limit: int | None = None) -> Iterator[dict]:
        query = "SELECT seq,id,payload FROM records WHERE kind=? AND json_extract(payload,'$.run_id')=? AND json_extract(payload,'$.camera_id')=? ORDER BY seq "
        query += "DESC" if reverse else "ASC"
        args: list = [kind, run_id, camera_id]
        if limit is not None:
            self._page(limit, 0)
            query += " LIMIT ?"
            args.append(limit)
        for row in self.db.execute(query, args):
            yield {**json.loads(row["payload"]), "_seq": row["seq"], "_id": row["id"]}

    def unresolved(self, limit: int = 1000, after: int = 0) -> list[dict]:
        self._page(limit, after)
        query = """SELECT r.seq,r.payload FROM heads h JOIN records r ON r.seq=h.seq
          WHERE h.kind='reconciliations' AND h.field='event_id' AND r.seq>?
          AND json_extract(r.payload,'$.status') IN ('payment_unmatched','inventory_discrepancy','needs_review')
          ORDER BY r.seq LIMIT ?"""
        return [{**json.loads(r["payload"]), "_seq": r["seq"]} for r in self.db.execute(query, (after, limit))]

    def recent(self, kind: str, camera_id: str, limit: int = 1000) -> Iterator[dict]:
        self._page(limit, 0)
        rows = self.db.execute("SELECT payload FROM records WHERE kind=? AND json_extract(payload,'$.camera_id')=? ORDER BY seq DESC LIMIT ?", (kind, camera_id, limit))
        for row in rows:
            yield json.loads(row[0])

    def event_page(self, camera_id: str, limit: int = 100, after: int = 0) -> list[dict]:
        self._page(limit,after)
        query="SELECT seq,payload FROM records WHERE kind='events' AND json_extract(payload,'$.camera_id')=? AND seq>? ORDER BY seq LIMIT ?"
        return [{**json.loads(r["payload"]),"_seq":r["seq"]} for r in self.db.execute(query,(camera_id,after,limit))]

    def review_crossing(self, event_id: str, decision: str, note: str) -> dict:
        """Append a correction; preserve the observation and keep POS independent."""
        if decision not in {"confirmed","rejected","uncertain"} or not isinstance(note,str) or not note.strip():
            raise ValueError("Crossing review requires a decision and nonempty evidence note")
        with self.transaction():
            event=self.get("events",event_id)
            if not event or event["kind"] not in {"person_entered","person_exited"}:
                raise ValueError("Only directional crossing events support this review workflow")
            previous=self.latest("traffic_reviews","event_id",event_id)
            if previous and (previous["decision"],previous["note"])==(decision,note):
                return previous
            timestamp=now()
            item={"event_id":event_id,"decision":decision,"note":note,"timestamp":timestamp,
                  "revision":previous["revision"]+1 if previous else 1,
                  "camera_id":event["camera_id"],"run_id":event["run_id"]}
            self.append("traffic_reviews",key(event_id,item["revision"]),timestamp,item)
            return item

    def get(self, kind: str, identity: str) -> dict | None:
        row = self.db.execute("SELECT payload FROM records WHERE kind=? AND id=?", (kind, identity)).fetchone()
        return json.loads(row[0]) if row else None

    @staticmethod
    def _page(limit: int, after: int) -> None:
        if type(limit) is not int or not 1 <= limit <= 10000 or type(after) is not int or after < 0:
            raise ValueError("limit must be 1..10000; after must be nonnegative")

    @staticmethod
    def _day(day: str) -> tuple[str, str]:
        start = date.fromisoformat(day)
        return start.isoformat(), (start+timedelta(days=1)).isoformat()

    def records(self, kind: str, *, day: str | None = None, limit: int = 1000, after: int = 0) -> list[dict]:
        self._page(limit, after)
        query, args = "SELECT * FROM records WHERE kind=? AND seq>?", [kind, after]
        if day:
            low, high = self._day(day)
            query += " AND timestamp>=? AND timestamp<?"
            args.extend((low, high))
        query += " ORDER BY seq LIMIT ?"
        args.append(limit)
        return [{**json.loads(r["payload"]), "_seq": r["seq"]} for r in self.db.execute(query, args)]

    def scan(self, kind: str, day: str | None = None) -> Iterator[dict]:
        after = 0
        while batch := self.records(kind, day=day, after=after):
            yield from batch
            after = batch[-1]["_seq"]

    def latest(self, kind: str, field: str, value: str) -> dict | None:
        if field not in HEAD_FIELDS:
            raise ValueError(f"Unsupported projection field: {field}")
        row = self.db.execute("""SELECT r.payload FROM heads h JOIN records r ON r.seq=h.seq
          WHERE h.kind=? AND h.field=? AND h.value=?""", (kind, field, str(value))).fetchone()
        return json.loads(row[0]) if row else None

    def between(self, kind: str, start: str, end: str, camera_id: str | None = None, run_id: str | None = None) -> Iterator[dict]:
        """Indexed half-open capture-time interval, streamed without a history list."""
        start, end = stamp(utc(start)), stamp(utc(end))
        if start >= end:
            raise ValueError("Invalid time interval")
        sql = "SELECT seq,timestamp,payload FROM records WHERE kind=? AND timestamp>=? AND timestamp<?"
        args: list = [kind,start,end]
        if camera_id is not None:
            sql += " AND json_extract(payload,'$.camera_id')=?"
            args.append(camera_id)
        if run_id is not None:
            sql += " AND json_extract(payload,'$.run_id')=?"
            args.append(run_id)
        for row in self.db.execute(sql+" ORDER BY timestamp,seq",args):
            yield {**json.loads(row["payload"]),"_seq":row["seq"],"_timestamp":row["timestamp"]}

    def orders_between(self, start: str, end: str, camera_id: str | None = None) -> Iterator[dict]:
        start, end = stamp(utc(start)), stamp(utc(end))
        if start >= end:
            raise ValueError("Invalid order time interval")
        sql, args = "SELECT payload FROM order_heads WHERE timestamp>=? AND timestamp<?", [start,end]
        if camera_id is not None:
            sql += " AND camera_id=?"
            args.append(camera_id)
        for row in self.db.execute(sql+" ORDER BY timestamp,id",args):
            yield json.loads(row[0])

    def latest_records(self, kind: str, field: str, *, day: str | None = None) -> Iterator[dict]:
        query = "SELECT r.seq,r.payload FROM heads h JOIN records r ON r.seq=h.seq WHERE h.kind=? AND h.field=?"
        args: list = [kind, field]
        if day:
            query += " AND r.timestamp>=? AND r.timestamp<?"
            args.extend(self._day(day))
        query += " ORDER BY r.seq"
        for row in self.db.execute(query, args):
            yield {**json.loads(row["payload"]), "_seq": row["seq"]}

    def watermark(self, kind: str) -> int:
        return self.db.execute("SELECT coalesce(max(seq),0) FROM records WHERE kind=?", (kind,)).fetchone()[0]

    def order_lines(self, day: str | None = None) -> Iterator[dict]:
        sql, args = "SELECT payload FROM order_heads", []
        if day:
            sql += " WHERE timestamp>=? AND timestamp<?"
            args.extend(self._day(day))
        for row in self.db.execute(sql+" ORDER BY timestamp,id", args):
            yield json.loads(row[0])

    def order(self, identity: str) -> dict | None:
        row = self.db.execute("SELECT payload FROM order_heads WHERE id=?", (identity,)).fetchone()
        return json.loads(row[0]) if row else None

    def candidates(self, event: dict, window: float) -> list[dict]:
        """At most two qualifying lines: enough to prove ambiguity."""
        timestamp = utc(event["timestamp"])
        low, high = stamp(timestamp-timedelta(seconds=window)), stamp(timestamp+timedelta(seconds=window))
        is_exit = event["kind"] == "possible_unpaid_exit"
        if is_exit:
            entered = event.get("table_entered_at")
            if entered is None or not event.get("table_id"):
                return []
            from datetime import datetime, timezone
            low = max(low, stamp(datetime.fromtimestamp(entered, timezone.utc)))
            # A future payment must not explain an earlier exit.
            high = min(high, stamp(timestamp))
            zones = [event["table_id"]]
        else:
            zones = sorted({z for z in (event.get("source_zone"), event.get("destination_zone")) if z})
        if not zones:
            return []
        placeholders = ",".join("?" for _ in zones)
        sql = f"""SELECT o.payload FROM order_heads o WHERE o.camera_id=?
          AND o.zone_id IN ({placeholders}) AND o.timestamp>=? AND o.timestamp<=?
          AND o.payment_status IN ('paid','pending')"""
        args: list = [event["camera_id"], *zones, low, high]
        if not is_exit:
            sql += """ AND o.product_class=? AND
              (SELECT count(*) FROM allocations a WHERE a.order_line_id=o.id)<o.quantity"""
            args.append(event["product_class"])
        sql += " ORDER BY o.timestamp,o.id LIMIT 2"
        return [json.loads(row[0]) for row in self.db.execute(sql, args)]

    def allocation(self, event_id: str) -> str | None:
        row = self.db.execute("SELECT order_line_id FROM allocations WHERE event_id=?", (event_id,)).fetchone()
        return row[0] if row else None

    def sold_event(self, event: dict) -> dict | None:
        row = self.db.execute("SELECT event_id FROM sold_tracks WHERE run_id=? AND camera_id=? AND track_id=?",
                              (event["run_id"], event["camera_id"], event["track_id"])).fetchone()
        return self.get("events", row[0]) if row else None

    def allocate(self, event: dict, order: dict) -> None:
        if not self.db.in_transaction:
            raise RuntimeError("Allocation requires a transaction")
        current = self.order(order["id"])
        used = self.db.execute("SELECT count(*) FROM allocations WHERE order_line_id=?", (order["id"],)).fetchone()[0]
        if not current or current["payment_status"] != "paid" or used >= current["quantity"]:
            raise ValueError("Paid order capacity unavailable")
        eid = event["event_id"]
        self.db.execute("INSERT INTO allocation_events(id) VALUES (?)", (eid,))
        self.db.execute("INSERT INTO allocations(event_id,order_line_id) VALUES (?,?)", (eid, order["id"]))
        self.db.execute("INSERT INTO sold_tracks VALUES (?,?,?,?)", (event["run_id"], event["camera_id"], event["track_id"], eid))

    def active_alerts(self, limit: int = 1000, after: int = 0) -> list[dict]:
        self._page(limit, after)
        rows = self.db.execute("""SELECT a.seq,a.payload,f.payload AS feedback
          FROM records a LEFT JOIN heads h ON h.kind='feedback' AND h.field='alert_id' AND h.value=a.id
          LEFT JOIN records f ON f.seq=h.seq WHERE a.kind='alerts' AND a.seq>?
          AND coalesce(json_extract(f.payload,'$.resolution'),json_extract(a.payload,'$.resolution'))='open'
          ORDER BY a.seq LIMIT ?""", (after, limit))
        result = []
        for row in rows:
            item = {**json.loads(row["payload"]), "_seq": row["seq"]}
            if row["feedback"]:
                feedback = json.loads(row["feedback"])
                item.update({k: feedback[k] for k in ("resolution", "false_positive")})
            result.append(item)
        return result

    def feedback(self, alert_id: str, resolution: str, false_positive: bool | None, note: str) -> dict:
        if not self.get("alerts", alert_id) or resolution not in {"open", "resolved", "dismissed"}:
            raise ValueError("Unknown alert or invalid resolution")
        if false_positive is not None and type(false_positive) is not bool:
            raise ValueError("false_positive must be boolean or null")
        ts = now()
        item = {"alert_id": alert_id, "resolution": resolution, "false_positive": false_positive, "note": note, "timestamp": ts}
        self.append("feedback", key(item), ts, item)
        return item

    @contextmanager
    def camera_lease(self, camera_id: str, run_id: str, ttl: float = 60) -> Iterator[str]:
        if ttl <= 0:
            raise ValueError("Lease TTL must be positive")
        owner = uuid.uuid4().hex
        with self.transaction():
            row = self.db.execute("SELECT expires FROM camera_leases WHERE camera_id=?", (camera_id,)).fetchone()
            if row and row[0] > time.time():
                raise RuntimeError(f"Camera {camera_id} already has an active worker")
            self.db.execute("INSERT OR REPLACE INTO camera_leases VALUES (?,?,?,?)", (camera_id, owner, run_id, time.time()+ttl))
        try:
            yield owner
        finally:
            with self.transaction():
                self.db.execute("DELETE FROM camera_leases WHERE camera_id=? AND owner=?", (camera_id, owner))

    def renew_lease(self, camera_id: str, owner: str, ttl: float) -> None:
        with self.transaction():
            cursor = self.db.execute("UPDATE camera_leases SET expires=? WHERE camera_id=? AND owner=? AND expires>?",
                                     (time.time()+ttl, camera_id, owner, time.time()))
            if cursor.rowcount != 1:
                raise RuntimeError("Camera lease expired or ownership changed; stop this worker")

    def health(self) -> dict:
        return {"status": "ok" if self.db.execute("SELECT 1").fetchone()[0] == 1 else "error", "schema_version": SCHEMA_VERSION}

    def close(self) -> None:
        self.db.close()
