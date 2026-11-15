"""Concurrency, migration, transaction faults and bounded-query regressions."""
import sqlite3
import threading
from concurrent.futures import ThreadPoolExecutor
from unittest.mock import patch

from coffee_ops.alerts import alert
from coffee_ops.pos_adapter import MockPOSAdapter, import_orders
from coffee_ops.reconciliation import reconcile
from coffee_ops.reporting import active_alerts, daily_report
from coffee_ops.schema import canonical, key
from coffee_ops.storage import SQLiteStore, SCHEMA_VERSION
from test_operations import StoreCase, START, event, order


class StorageResilienceTests(StoreCase):
    def test_concurrent_identical_append_has_one_winner(self):
        barrier = threading.Barrier(6)
        def worker(_):
            store = SQLiteStore(self.root / "ops.db")
            try:
                barrier.wait(timeout=10)
                return store.append("test", "same", START, {"camera_id": "shop", "value": 1})
            finally:
                store.close()
        with ThreadPoolExecutor(max_workers=6) as pool:
            results = list(pool.map(worker, range(6)))
        self.assertEqual(sum(results), 1)
        self.assertEqual(self.store.latest("test", "camera_id", "shop")["value"], 1)

    def test_concurrent_reconciliation_never_oversells(self):
        self.import_order(quantity=3)
        for i in range(12):
            self.add_event(event(str(i), track_id=i))
        barrier = threading.Barrier(3)
        def worker(_):
            store = SQLiteStore(self.root / "ops.db")
            try:
                barrier.wait(timeout=10)
                return reconcile(store, self.cfg.data["pos"], batch_size=2)
            finally:
                store.close()
        with ThreadPoolExecutor(max_workers=3) as pool:
            list(pool.map(worker, range(3)))
        self.assertEqual(self.store.db.execute("SELECT count(*) FROM allocations").fetchone()[0], 3)
        self.assertEqual(len(list(self.store.latest_records("reconciliations", "event_id"))), 12)

    def test_nested_failure_rolls_back_its_projection_without_losing_outer_work(self):
        with self.store.transaction():
            self.store.append("test", "outer", START, {"camera_id": "shop", "value": 1})
            with self.assertRaises(RuntimeError):
                with self.store.transaction():
                    self.store.append("test", "inner", START, {"camera_id": "shop", "value": 2})
                    raise RuntimeError("fault")
            self.assertEqual(self.store.latest("test", "camera_id", "shop")["value"], 1)
        self.assertIsNone(self.store.get("test", "inner"))

    def test_full_disk_during_projection_rolls_back_record(self):
        with patch.object(self.store, "_project", side_effect=sqlite3.OperationalError("database or disk is full")):
            with self.assertRaises(sqlite3.OperationalError):
                self.store.append("test", "1", START, {"camera_id": "shop"})
        self.assertIsNone(self.store.get("test", "1"))
        self.assertIsNone(self.store.latest("test", "camera_id", "shop"))

    def test_lock_timeout_does_not_leave_partial_record(self):
        other = SQLiteStore(self.root / "ops.db", timeout=.05)
        try:
            with self.store.transaction():
                with self.assertRaisesRegex(sqlite3.OperationalError, "locked"):
                    other.append("test", "blocked", START, {})
            self.assertTrue(other.append("test", "blocked", START, {}))
        finally:
            other.close()

    def test_newer_schema_is_rejected_and_not_downgraded(self):
        path = self.root / "future.db"
        db = sqlite3.connect(path)
        db.execute("PRAGMA user_version=999")
        db.close()
        with self.assertRaisesRegex(ValueError, "newer"):
            SQLiteStore(path)
        db = sqlite3.connect(path)
        self.assertEqual(db.execute("PRAGMA user_version").fetchone()[0], 999)
        db.close()

    def test_version_one_migration_preserves_records_and_selects_latest_pos_revision(self):
        from coffee_ops.pos_adapter import normalize
        path = self.root / "legacy.db"
        db = sqlite3.connect(path)
        db.executescript("CREATE TABLE records(seq INTEGER PRIMARY KEY AUTOINCREMENT,kind TEXT,id TEXT,timestamp TEXT,payload TEXT,UNIQUE(kind,id)); PRAGMA user_version=1;")
        for revision, status in ((3, "refunded"), (1, "paid")):
            line = normalize(order(revision=revision, payment_status=status), self.cfg.data["pos"]["sku_classes"])
            db.execute("INSERT INTO records(kind,id,timestamp,payload) VALUES (?,?,?,?)", ("orders", key(line["id"], revision), line["timestamp"], canonical(line)))
        db.commit()
        db.close()
        migrated = SQLiteStore(path)
        try:
            self.assertEqual(migrated.db.execute("PRAGMA user_version").fetchone()[0], SCHEMA_VERSION)
            self.assertEqual(len(migrated.records("orders")), 2)
            self.assertEqual(list(migrated.order_lines())[0]["payment_status"], "refunded")
        finally:
            migrated.close()

    def test_camera_lease_exclusion_and_independent_cameras(self):
        other = SQLiteStore(self.root / "ops.db")
        try:
            with self.store.camera_lease("shop", "r") as owner:
                with self.assertRaisesRegex(RuntimeError, "active worker"):
                    with other.camera_lease("shop", "different-run"):
                        self.fail("second camera writer admitted")
                with other.camera_lease("other-camera", "r"):
                    self.store.renew_lease("shop", owner, 60)
            with other.camera_lease("shop", "replacement"):
                pass
        finally:
            other.close()

    def test_expired_owner_cannot_renew_or_delete_new_owners_lease(self):
        with patch("coffee_ops.storage.time.time", return_value=100):
            with self.store.camera_lease("shop", "first", ttl=1) as first:
                with patch("coffee_ops.storage.time.time", return_value=102):
                    with self.store.camera_lease("shop", "second", ttl=60) as second:
                        with self.assertRaisesRegex(RuntimeError, "ownership"):
                            self.store.renew_lease("shop", first, 60)
                        self.store.renew_lease("shop", second, 60)

    def test_read_snapshot_consistent_while_another_connection_commits(self):
        self.import_order()
        other = SQLiteStore(self.root / "ops.db")
        try:
            with self.store.snapshot():
                self.assertEqual(list(self.store.order_lines())[0]["payment_status"], "paid")
                import_orders(other, MockPOSAdapter([order(revision=2, payment_status="refunded")]), self.cfg.data["pos"])
                self.assertEqual(list(self.store.order_lines())[0]["payment_status"], "paid")
            self.assertEqual(list(self.store.order_lines())[0]["payment_status"], "refunded")
        finally:
            other.close()


class ComplexPOSAndReportTests(StoreCase):
    def test_future_payment_does_not_explain_prior_exit(self):
        self.import_order(timestamp="2026-01-01T09:00:30Z", zone_id="T1")
        self.add_event(event(kind="possible_unpaid_exit", table_id="T1", table_entered_at=0))
        reconcile(self.store, self.cfg.data["pos"])
        self.assertEqual(self.result()["status"], "payment_unmatched")

    def test_out_of_order_revision_does_not_restore_refunded_sale(self):
        self.import_order(revision=3, payment_status="refunded")
        self.import_order(revision=1)
        self.import_order(revision=2, payment_status="pending")
        self.assertEqual(daily_report(self.store, "2026-01-01")["confirmed_sold_units"], {})
        self.add_event(event())
        reconcile(self.store, self.cfg.data["pos"])
        self.assertEqual(self.result()["status"], "payment_unmatched")

    def test_changed_sku_mapping_cannot_reinterpret_existing_line(self):
        self.import_order()
        self.cfg.data["pos"]["sku_classes"]["COFFEE"] = "person"
        with self.assertRaises(ValueError):
            self.import_order(revision=2)

    def test_camera_only_mode_after_paid_allocation_stays_review_only(self):
        self.import_order()
        self.add_event(event())
        reconcile(self.store, self.cfg.data["pos"])
        self.cfg.data["pos"]["mode"] = "camera_only"
        reconcile(self.store, self.cfg.data["pos"])
        self.assertEqual(self.result()["status"], "needs_review")
        self.cfg.data["pos"]["mode"] = "file"
        reconcile(self.store, self.cfg.data["pos"])
        self.assertEqual(self.result()["status"], "confirmed_sale")

    def test_mid_batch_failure_rolls_back_sales_allocations_and_results(self):
        self.import_order(quantity=2)
        self.add_event(event())
        self.add_event(event("e2", track_id=3))
        original = self.store.append
        def fail(kind, identity, ts, payload):
            if kind == "reconciliations" and payload["event_id"] == "e2":
                raise sqlite3.OperationalError("injected write failure")
            return original(kind, identity, ts, payload)
        with patch.object(self.store, "append", side_effect=fail), self.assertRaises(sqlite3.OperationalError):
            reconcile(self.store, self.cfg.data["pos"])
        self.assertIsNone(self.store.allocation("e1"))
        self.assertEqual(self.store.records("reconciliations"), [])
        reconcile(self.store, self.cfg.data["pos"])
        self.assertEqual(self.result("e2")["status"], "confirmed_sale")

    def test_resolved_alerts_do_not_hide_active_alerts_beyond_page(self):
        for i in range(7):
            a = alert("review", START, "shop", "check", .8, {}, [], str(i))
            self.store.append("alerts", a["alert_id"], START, a)
            if i < 5:
                self.store.feedback(a["alert_id"], "resolved", False, "reviewed")
        first = active_alerts(self.store, limit=1)
        self.assertEqual(len(first), 1)
        second = active_alerts(self.store, limit=1, after=first[0]["_seq"])
        self.assertEqual(len(second), 1)
        self.assertNotEqual(first[0]["alert_id"], second[0]["alert_id"])

    def test_orders_across_midnight_are_reported_in_utc(self):
        self.import_order(timestamp="2026-01-02T00:15:00+01:00")
        self.assertEqual(daily_report(self.store, "2026-01-01")["confirmed_sold_units"], {"COFFEE": 1})
        self.assertEqual(daily_report(self.store, "2026-01-02")["confirmed_sold_units"], {})

    def test_reconciliation_uses_indexed_candidates_instead_of_order_history_scans(self):
        self.import_order()
        self.add_event(event())
        with patch.object(self.store, "order_lines", side_effect=AssertionError("full order scan forbidden")):
            reconcile(self.store, self.cfg.data["pos"])
        self.assertEqual(self.result()["status"], "confirmed_sale")
