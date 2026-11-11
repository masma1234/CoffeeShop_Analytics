"""Business-rule unit and integration tests, independent of detector weights."""
import copy
import json
import sqlite3
import tempfile
import unittest
from dataclasses import replace
from pathlib import Path

from coffee_ops.alerts import AlertEngine
from coffee_ops.config import Config
from coffee_ops.event_engine import EventEngine
from coffee_ops.reconciliation import reconcile
from coffee_ops.pipeline import Pipeline
from coffee_ops.pos_adapter import FilePOSAdapter, MockPOSAdapter, import_orders
from coffee_ops.reporting import active_alerts, current_status, daily_report
from coffee_ops.schema import Detection, Observation, key, utc
from coffee_ops.storage import SQLiteStore
from coffee_ops.tracker import KalmanTracker
from coffee_ops.zones import TableState, contains

ROOT = Path(__file__).resolve().parents[1]
START = "2026-01-01T09:00:00Z"


def config() -> Config:
    return Config.load(ROOT / "config/example.json")


def person(t: float, missed: bool = False, tid: int = 1) -> Observation:
    return Observation(tid, 0, (20, 20, 50, 80), .9, 0, t, 3, missed, 1)


def order(**changes) -> dict:
    return {"order_id": "o1", "line_id": "1", "timestamp": START, "sku": "COFFEE", "quantity": 1,
            "payment_status": "paid", "camera_id": "shop", "zone_id": "counter", **changes}


def event(eid: str = "e1", **changes) -> dict:
    return {"event_id": eid, "kind": "transferred", "timestamp": START, "camera_id": "shop", "run_id": "r1",
            "product_class": "coffee_cup", "track_id": 2, "source_zone": "shelf", "destination_zone": "counter",
            "confidence": .95, "evidence": {"frame": 3}, **changes}


class ConfigTests(unittest.TestCase):
    def test_invalid_settings_are_rejected(self):
        mutations = [lambda d: d["classes"].append(d["classes"][0]),
                     lambda d: d["classes"][0].update(threshold=1.1),
                     lambda d: d["cameras"][0].update(sample_every=0),
                     lambda d: d["cameras"][0]["zones"][0].update(capacity=0),
                     lambda d: d["cameras"][0]["zones"][0].update(polygon=[[0, 0], [1, 1], [2, 2]]),
                     lambda d: d["tracker"].update(max_tracks=-1),
                     lambda d: d["rules"].update(disappear_seconds=1),
                     lambda d: d["pos"].update(quantity_tolerance=1),
                     lambda d: d["model"].update(inference_timeout_seconds=float("nan")),
                     lambda d: d.update(typo=True)]
        for mutate in mutations:
            with self.subTest(mutate=mutate):
                c = config()
                mutate(c.data)
                with self.assertRaises(ValueError):
                    c.validate()

    def test_disabled_and_camera_specific_thresholds(self):
        c = config()
        c.data["classes"][1]["enabled"] = False
        c.data["cameras"][0]["thresholds"] = {"0": .95}
        self.assertEqual(c.filter([Detection(0, (0, 0, 5, 5), .9), Detection(1, (0, 0, 5, 5), 1)], "shop"), [])

    def test_unknown_class_and_outside_frame_fail(self):
        for det in (Detection(99, (0, 0, 1, 1), .9), Detection(0, (0, 0, 400, 10), .9)):
            with self.assertRaises(ValueError):
                config().filter([det], "shop")

    def test_invalid_detection_and_naive_time_fail(self):
        for box in ((0, 0, 0, 2), (0, 0, float("nan"), 2), (-1, 0, 2, 2)):
            with self.assertRaises(ValueError):
                Detection(0, box, .9)
        with self.assertRaises(ValueError):
            utc("2026-01-01T12:00:00")

    def test_detection_cap(self):
        c = config()
        c.data["tracker"]["max_detections"] = 1
        with self.assertRaisesRegex(ValueError, "capacity"):
            c.filter([Detection(0, (0, 0, 5, 5), .9)]*2, "shop")


class TrackingTests(unittest.TestCase):
    def test_occlusion_recovery_and_expiration_before_matching(self):
        tracker = KalmanTracker(config().data["tracker"])
        d = Detection(0, (20, 20, 40, 60), .9)
        first = tracker.update([d], 0)[0].track_id
        self.assertTrue(tracker.update([], 1)[0].missed)
        self.assertEqual(tracker.update([d], 2)[0].track_id, first)
        self.assertNotEqual(tracker.update([d], 5)[0].track_id, first)

    def test_classes_do_not_swap(self):
        tracker = KalmanTracker(config().data["tracker"])
        tracker.update([Detection(0, (10, 10, 30, 30), .9)], 0)
        tracks = tracker.update([Detection(1, (10, 10, 30, 30), .9)], 1)
        self.assertEqual(len(tracks), 2)
        self.assertEqual(tracks[1].class_id, 1)

    def test_two_crossing_tracks_use_velocity(self):
        tracker = KalmanTracker(config().data["tracker"])
        for t, (a, b) in enumerate(((0, 100), (20, 80), (40, 60), (60, 40), (80, 20))):
            tracks = tracker.update([Detection(0, (a, 0, a+10, 20), .9), Detection(0, (b, 0, b+10, 20), .9)], t)
        self.assertEqual(tracks[0].bbox[0], 80)
        self.assertEqual(tracks[1].bbox[0], 20)

    def test_monotonic_time_and_capacity(self):
        c = config().data["tracker"]
        c["max_tracks"] = 1
        tracker = KalmanTracker(c)
        tracker.update([], 1)
        with self.assertRaises(ValueError):
            tracker.update([], 1)
        with self.assertRaisesRegex(ValueError, "capacity"):
            tracker.update([Detection(0, (0, 0, 2, 2), .9)]*2, 2)


class OccupancyTests(unittest.TestCase):
    def setUp(self):
        c = config()
        self.table = TableState(c.camera("shop")["zones"][0], c.data["rules"])

    def test_hysteresis_and_empty_timeout(self):
        self.assertEqual(self.table.update(0, [person(0)], [], True)["status"], "unknown")
        self.assertEqual(self.table.update(1, [person(1)], [], True)["status"], "occupied")
        self.assertEqual(self.table.update(2, [], [], True)["status"], "occupied")
        self.assertEqual(self.table.update(4, [], [], True)["status"], "empty")

    def test_occlusion_and_bad_frames_are_unknown(self):
        self.table.update(0, [person(0)], [], True)
        self.table.update(1, [person(1)], [], True)
        self.assertEqual(self.table.update(2, [person(1, True)], [], True)["status"], "unknown")
        self.assertEqual(self.table.update(3, [], [], False)["status"], "unknown")
        recovered = self.table.update(4, [person(4)], [], True)
        self.assertEqual(recovered["status"], "occupied")
        self.assertEqual(recovered["occupied_seconds"], 4)

    def test_full_threshold_and_products(self):
        people = [person(0), person(0, tid=2)]
        self.table.update(0, people, [], True)
        result = self.table.update(1, people, ["coffee_cup"], True)
        self.assertTrue(result["full"])
        self.assertEqual(result["people"], 2)
        self.assertEqual(result["products"], ["coffee_cup"])

    def test_polygon_boundaries(self):
        poly = [[0, 0], [10, 0], [10, 10], [0, 10]]
        self.assertTrue(contains(poly, (0, 5)))
        self.assertFalse(contains(poly, (11, 5)))

    def test_ambiguous_overlapping_tables_are_unknown(self):
        c = config()
        c.data["cameras"][0]["zones"].append({**c.camera("shop")["zones"][0], "id": "T2"})
        engine = EventEngine(c, "shop", "r")
        for i in range(4):
            _, tables = engine.update([person(i)], i, i)
        self.assertTrue(all(t["status"] == "unknown" for t in tables))

    def test_disabled_person_class_cannot_report_empty_tables(self):
        c = config()
        c.data["classes"][0]["enabled"] = False
        engine = EventEngine(c, "shop", "r")
        for i in range(5):
            _, tables = engine.update([], i, i)
        self.assertEqual(tables[0]["status"], "unknown")


class EventTests(unittest.TestCase):
    def test_movement_confirmation_transfer_removal_and_disappearance(self):
        engine = EventEngine(config(), "shop", "r")
        t = Observation(2, 1, (20, 150, 40, 180), .9, 0, 0, 3, False, 1)
        self.assertEqual(engine.update([t], 0, 0)[0], [])
        self.assertEqual(engine.update([t], 1, 1)[0][0]["kind"], "placed")
        moved = replace(t, bbox=(100, 150, 120, 180))
        self.assertEqual(engine.update([moved], 2, 2)[0], [])
        self.assertEqual(engine.update([moved], 3, 3)[0][0]["kind"], "transferred")
        self.assertEqual(engine.update([], 5, 5)[0], [])
        event = engine.update([], 7, 7)[0][0]
        self.assertEqual(event["kind"], "disappeared")
        self.assertEqual(event["status"], "review_required")
        self.assertEqual(engine.update([], 8, 8)[0], [])

    def test_jitter_does_not_emit_transfer(self):
        engine = EventEngine(config(), "shop", "r")
        t = Observation(2, 1, (20, 150, 40, 180), .9, 0, 0, 3, False, 1)
        engine.update([t], 0, 0)
        engine.update([t], 1, 1)
        engine.update([replace(t, bbox=(100, 150, 120, 180))], 1.5, 2)
        self.assertEqual(engine.update([t], 2, 3)[0], [])

    def test_bad_frame_does_not_emit_disappearance(self):
        engine = EventEngine(config(), "shop", "r")
        t = Observation(2, 1, (20, 150, 40, 180), .9, 0, 0, 3, False, 1)
        engine.update([t], 0, 0)
        engine.update([t], 1, 1)
        self.assertEqual(engine.update([], 10, 10, reliable=False)[0], [])

    def test_occlusion_restarts_movement_confirmation(self):
        engine = EventEngine(config(), "shop", "r")
        t = Observation(2, 1, (20, 150, 40, 180), .9, 0, 0, 3, False, 1)
        engine.update([t], 0, 0)
        engine.update([replace(t, missed=True)], 1, 1)
        self.assertEqual(engine.update([t], 2, 2)[0], [])
        self.assertEqual(engine.update([t], 3, 3)[0][0]["kind"], "placed")

    def test_overlapping_product_zones_do_not_create_removal(self):
        c = config()
        c.data["cameras"][0]["zones"].append({"id": "overlap", "kind": "counter", "polygon": [[90, 140], [180, 140], [180, 240], [90, 240]]})
        engine = EventEngine(c, "shop", "r")
        t = Observation(2, 1, (20, 150, 40, 180), .9, 0, 0, 3, False, 1)
        engine.update([t], 0, 0)
        engine.update([t], 1, 1)
        t = replace(t, bbox=(100, 150, 120, 180))
        engine.update([t], 2, 2)
        self.assertEqual(engine.update([t], 3, 3)[0], [])

    def test_exit_requires_prior_table_and_is_review_only(self):
        engine = EventEngine(config(), "shop", "r")
        engine.update([person(0)], 0, 0)
        engine.update([person(1)], 1, 1)
        exit_person = replace(person(2), bbox=(240, 20, 270, 80))
        engine.update([exit_person], 2, 2)
        events, _ = engine.update([exit_person], 3, 3)
        candidate = next(e for e in events if e["kind"] == "possible_unpaid_exit")
        self.assertEqual(candidate["table_id"], "T1")
        self.assertEqual(candidate["status"], "review_required")


class StoreCase(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.store = SQLiteStore(self.root / "ops.db")
        self.cfg = config()

    def tearDown(self):
        self.store.close()
        self.temp.cleanup()

    def add_event(self, value: dict):
        self.store.append("events", value["event_id"], value["timestamp"], value)

    def import_order(self, **changes):
        return import_orders(self.store, MockPOSAdapter([order(**changes)]), self.cfg.data["pos"])

    def result(self, eid="e1"):
        return self.store.latest("reconciliations", "event_id", eid)


class StorageTests(StoreCase):
    def test_idempotent_append_and_immutable_conflict(self):
        self.assertTrue(self.store.append("test", "1", START, {"a": 1}))
        self.assertFalse(self.store.append("test", "1", START, {"a": 1}))
        with self.assertRaises(ValueError):
            self.store.append("test", "1", START, {"a": 2})
        with self.assertRaises(sqlite3.IntegrityError):
            self.store.db.execute("UPDATE records SET payload='{}'")

    def test_failed_transaction_rolls_back(self):
        with self.assertRaises(ValueError):
            with self.store.transaction():
                self.store.append("test", "1", START, {})
                raise ValueError("abort")
        self.assertEqual(self.store.records("test"), [])

    def test_pagination_has_no_skips(self):
        for i in range(5):
            self.store.append("test", str(i), START, {"n": i})
        first = self.store.records("test", limit=2)
        rest = self.store.records("test", after=first[-1]["_seq"])
        self.assertEqual([r["n"] for r in first+rest], list(range(5)))


class ReconciliationTests(StoreCase):
    def test_paid_quantity_and_reprocessing_are_idempotent(self):
        self.import_order()
        self.add_event(event())
        self.add_event(event("e2", track_id=3))
        reconcile(self.store, self.cfg.data["pos"])
        self.assertEqual(self.result()["status"], "confirmed_sale")
        self.assertEqual(self.result("e2")["status"], "payment_unmatched")
        count = len(self.store.records("reconciliations"))
        reconcile(self.store, self.cfg.data["pos"])
        self.assertEqual(len(self.store.records("reconciliations")), count)
        self.assertEqual(self.store.db.execute("SELECT count(*) FROM allocations").fetchone()[0], 1)

    def test_same_product_track_cannot_consume_two_paid_units(self):
        self.import_order(quantity=2)
        self.add_event(event())
        self.add_event(event("e2", kind="removed"))
        reconcile(self.store, self.cfg.data["pos"])
        self.assertEqual(self.result("e2")["status"], "sale_correlated_movement")
        self.assertEqual(self.store.db.execute("SELECT count(*) FROM allocations").fetchone()[0], 1)

    def test_ambiguous_orders_are_never_confirmed(self):
        self.import_order()
        self.import_order(order_id="o2")
        self.add_event(event())
        reconcile(self.store, self.cfg.data["pos"])
        self.assertEqual(self.result()["status"], "needs_review")
        self.assertEqual(self.result()["reason"], "ambiguous_candidates")

    def test_camera_only_never_confirms_payment(self):
        self.import_order()
        self.add_event(event())
        self.cfg.data["pos"]["mode"] = "camera_only"
        reconcile(self.store, self.cfg.data["pos"])
        self.assertEqual(self.result()["status"], "needs_review")

    def test_late_paid_order_resolves_previous_unmatched(self):
        self.add_event(event())
        reconcile(self.store, self.cfg.data["pos"])
        self.assertEqual(self.result()["status"], "payment_unmatched")
        self.import_order()
        reconcile(self.store, self.cfg.data["pos"])
        self.assertEqual(self.result()["status"], "confirmed_sale")
        from coffee_ops.reporting import unresolved_events
        self.assertEqual(unresolved_events(self.store), [])

    def test_pending_paid_refunded_revision_and_daily_sales(self):
        self.import_order(payment_status="pending")
        self.add_event(event())
        reconcile(self.store, self.cfg.data["pos"])
        self.assertEqual(self.result()["status"], "likely_sale")
        self.import_order(payment_status="paid", revision=2)
        reconcile(self.store, self.cfg.data["pos"])
        self.assertEqual(self.result()["status"], "confirmed_sale")
        self.assertEqual(daily_report(self.store, "2026-01-01")["confirmed_sold_units"], {"COFFEE": 1})
        self.import_order(payment_status="refunded", revision=3)
        reconcile(self.store, self.cfg.data["pos"])
        self.assertEqual(self.result()["status"], "payment_unmatched")
        self.assertEqual(daily_report(self.store, "2026-01-01")["confirmed_sold_units"], {})
        self.import_order(payment_status="paid", revision=4)
        reconcile(self.store, self.cfg.data["pos"])
        self.assertEqual(self.result()["status"], "confirmed_sale")

    def test_time_zone_class_and_confidence_gates(self):
        self.import_order()
        cases = [{"timestamp": "2026-01-01T11:00:00Z"}, {"camera_id": "other"},
                 {"source_zone": "T1", "destination_zone": "exit"}, {"product_class": "other"}, {"confidence": .1}]
        for i, changes in enumerate(cases):
            self.add_event(event(str(i), **changes))
        reconcile(self.store, self.cfg.data["pos"])
        for i in range(len(cases)):
            self.assertNotEqual(self.result(str(i))["status"], "confirmed_sale")

    def test_disappearance_is_not_paid_sale(self):
        self.import_order()
        self.add_event(event(kind="disappeared"))
        reconcile(self.store, self.cfg.data["pos"])
        self.assertEqual(self.result()["status"], "inventory_discrepancy")

    def test_pos_import_is_atomic_and_validated(self):
        for changes in ({"quantity": 0}, {"quantity": 1.5}, {"sku": "UNKNOWN"}, {"payment_status": "maybe"}, {"timestamp": "2026-01-01"}):
            with self.subTest(changes=changes), self.assertRaises(ValueError):
                import_orders(self.store, MockPOSAdapter([order(order_id="valid"), order(**changes)]), self.cfg.data["pos"])
            self.assertEqual(self.store.records("orders"), [])

    def test_csv_import_and_conflicting_revision(self):
        import csv
        path = self.root / "pos.csv"
        with path.open("w", newline="", encoding="utf-8") as out:
            writer = csv.DictWriter(out, fieldnames=list(order()))
            writer.writeheader()
            writer.writerow(order())
        self.assertEqual(import_orders(self.store, FilePOSAdapter(path), self.cfg.data["pos"]), 1)
        self.assertEqual(self.import_order(), 0)
        with self.assertRaises(ValueError):
            self.import_order(quantity=2)

    def test_exit_correlation_never_assigns_person_payment(self):
        self.import_order(zone_id="T1")
        self.add_event(event(kind="possible_unpaid_exit", table_id="T1", table_entered_at=utc(START).timestamp()-10))
        reconcile(self.store, self.cfg.data["pos"])
        self.assertEqual(self.result()["status"], "order_correlated")
        self.assertIsNone(self.result()["payment_proof"])


class AlertTests(StoreCase):
    def test_alert_rules_and_throttle(self):
        rules = self.cfg.data["rules"]
        rules["queue_limit"] = 1
        engine = AlertEngine(rules, "shop", "r")
        table = {"zone_id": "T1", "full": True, "status": "occupied", "occupied_seconds": 4000, "confidence": .9}
        moved = event(destination_zone="exit")
        queue_person = replace(person(0), bbox=(170, 20, 200, 80))
        alerts = engine.evaluate([moved], [table], [queue_person], self.cfg.camera("shop")["zones"], START, 0, 0, .9, False)
        kinds = {a["kind"] for a in alerts}
        self.assertEqual(kinds, {"product_outside_authorized_zone", "table_full", "table_occupied_too_long", "queue_congestion", "low_detection_confidence", "high_tracking_instability"})
        self.assertEqual(engine.evaluate([moved], [table], [queue_person], self.cfg.camera("shop")["zones"], START, 1, 1, .9, False), [])
        for item in alerts:
            self.assertIn("confidence", item)
            self.assertIn("evidence", item)
            self.assertTrue(item["human_review_required"])

    def test_false_positive_feedback_changes_active_projection(self):
        from coffee_ops.alerts import alert
        item = alert("review_required", START, "shop", "Check evidence", .5, {"frame": 1}, [], "a")
        self.store.append("alerts", item["alert_id"], START, item)
        self.assertEqual(len(active_alerts(self.store)), 1)
        self.store.feedback(item["alert_id"], "dismissed", True, "Staff restocking")
        self.assertEqual(active_alerts(self.store), [])


class PipelineTests(StoreCase):
    def pipeline(self, run="r", start=START):
        return Pipeline(self.cfg, self.store, "shop", run, start, "source", {"version": "fixture"})

    def test_replay_deduplicates_and_rebuilds_state(self):
        for _ in range(2):
            pipe = self.pipeline()
            for i in range(5):
                pipe.process(i, i, [Detection(1, (20, 150, 40, 180), .9)])
        self.assertEqual(len(self.store.records("events")), 1)
        self.assertEqual(len(self.store.records("frames")), 5)

    def test_restart_changed_input_or_config_fails(self):
        self.pipeline().process(0, 0, [])
        with self.assertRaisesRegex(ValueError, "Conflicting"):
            self.pipeline().process(0, 0, [Detection(0, (10, 10, 20, 20), .9)])
        self.cfg.data["version"] = "2"
        with self.assertRaises(ValueError):
            self.pipeline()

    def test_new_session_reuses_catalog_without_conflict(self):
        self.pipeline("first")
        self.pipeline("second", "2026-01-02T09:00:00Z")
        self.assertEqual(len(self.store.records("class_catalog")), 1)

    def test_finished_run_has_unknown_current_status(self):
        pipe = self.pipeline()
        pipe.process(0, 0, [])
        pipe.health("completed")
        status = current_status(self.store, "shop")
        self.assertTrue(all(t["status"] == "unknown" for t in status["tables"]))
        self.assertIsNone(status["observations"])

    def test_capture_gap_prevents_immediate_occupancy(self):
        pipe = self.pipeline()
        for i in range(2):
            pipe.process(i, i, [Detection(0, (20, 20, 50, 80), .9)])
        result = pipe.process(10, 10, [Detection(0, (20, 20, 50, 80), .9)])
        self.assertEqual(result["tables"][0]["status"], "unknown")

    def test_wrong_frame_dimensions_fail(self):
        import numpy as np
        with self.assertRaisesRegex(ValueError, "dimensions"):
            self.pipeline().process(0, 0, [], image=np.zeros((10, 10, 3), np.uint8))

    def test_low_person_confidence_is_not_hidden_by_confident_fixture(self):
        pipe = self.pipeline()
        for i in range(5):
            result = pipe.process(i, i, [Detection(0, (20, 20, 50, 80), .3), Detection(2, (5, 5, 145, 120), .99)])
        self.assertEqual(result["tables"][0]["status"], "unknown")

    def test_evidence_capture_and_safe_retention(self):
        import os
        import time
        import numpy as np
        from coffee_ops.pipeline import prune_evidence
        self.cfg.data["evidence"].update(capture=True, directory=str(self.root / "evidence"), retention_days=1)
        result = self.pipeline().process(0, 0, [], reliable=False, image=np.zeros((240, 320, 3), np.uint8))
        path = Path(result["alerts"][0]["evidence"]["image_path"])
        self.assertTrue(path.is_file())
        os.utime(path, (time.time()-172800,)*2)
        other = path.parent / "keep.jpg"
        other.write_bytes(b"keep")
        self.assertEqual(prune_evidence(self.cfg), 1)
        self.assertTrue(other.exists())
