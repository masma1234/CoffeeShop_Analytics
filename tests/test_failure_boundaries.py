"""Adversarial runtime/config inputs and recovery across process boundaries."""
import json
import multiprocessing as mp
import sqlite3
import time
import unittest
from unittest.mock import patch

import numpy as np

from coffee_ops.config import Config
from coffee_ops.detector import FixtureDetector, YOLODetector
from coffee_ops.exports import export_predictions
from coffee_ops.pipeline import Pipeline
from coffee_ops.reporting import current_status
from coffee_ops.schema import Detection
from test_operations import StoreCase, START, config


def hold_pipe(connection):
    """Simulate a worker that exists but never reads its input pipe."""
    time.sleep(20)
    connection.close()


class FailureBoundaryTests(StoreCase):
    def pipe(self, run="r", camera="shop"):
        return Pipeline(self.cfg, self.store, camera, run, START, "test-source", {"version": "fixture"})

    def test_failed_frame_rolls_back_and_poisoned_state_requires_replay(self):
        pipe = self.pipe()
        pipe.process(0, 0, [Detection(1, (20, 150, 40, 180), .9)])
        original = self.store.append
        def fail(kind, identity, ts, payload):
            if kind == "observations":
                raise sqlite3.OperationalError("injected disk failure")
            return original(kind, identity, ts, payload)
        with patch.object(self.store, "append", side_effect=fail), self.assertRaises(sqlite3.OperationalError):
            pipe.process(1, 1, [])
        self.assertEqual(len(self.store.records("frames")), 1)
        self.assertEqual(len(self.store.records("occupancy")), 1)
        with self.assertRaisesRegex(RuntimeError, "rebuilt"):
            pipe.process(2, 2, [])
        replay = self.pipe()
        replay.process(0, 0, [Detection(1, (20, 150, 40, 180), .9)])
        replay.process(1, 1, [])
        self.assertEqual(len(self.store.records("frames")), 2)

    def test_evidence_created_for_failed_frame_is_cleaned_up(self):
        self.cfg.data["evidence"].update(capture=True, directory=str(self.root / "evidence"))
        pipe = self.pipe()
        original = self.store.append
        def fail(kind, identity, ts, payload):
            if kind == "frames":
                raise sqlite3.OperationalError("write failure")
            return original(kind, identity, ts, payload)
        with patch.object(self.store, "append", side_effect=fail), self.assertRaises(sqlite3.OperationalError):
            pipe.process(0, 0, [], reliable=False, image=np.zeros((240, 320, 3), np.uint8))
        self.assertEqual(list((self.root / "evidence").glob("*.jpg")), [])

    def test_new_run_health_cannot_make_previous_session_occupancy_current(self):
        first = self.pipe("first")
        for i in range(3):
            first.process(i, i, [Detection(0, (20, 20, 40, 80), .9)])
        first.health("completed")
        second = self.pipe("second")
        second.health("running")
        status = current_status(self.store, "shop")
        self.assertEqual(status["tables"][0]["status"], "unknown")
        self.assertIsNone(status["observations"])

    def test_export_isolates_cameras_sharing_a_run_id(self):
        import copy
        other = copy.deepcopy(self.cfg.data["cameras"][0])
        other["id"] = "other"
        self.cfg.data["cameras"].append(other)
        first, second = self.pipe("shared"), self.pipe("shared", "other")
        first.process(0, 0, [])
        first.health("completed")
        second.process(0, 0, [Detection(0, (20, 20, 40, 80), .9)])
        second.process(1, 1, [])
        second.health("completed")
        result = export_predictions(self.store, "shared", "shop")
        self.assertEqual(len(result["frames"]), 1)
        self.assertEqual(result["frames"][0]["detections"], [])
        self.assertEqual(result["runtime"]["latency_window"], 1)

    def test_large_ipc_send_to_unresponsive_worker_has_a_deadline(self):
        detector = YOLODetector.__new__(YOLODetector)
        ctx = mp.get_context("spawn")
        detector.connection, child = ctx.Pipe()
        detector.timeout = .2
        detector.process = ctx.Process(target=hold_pipe, args=(child,), daemon=True)
        detector.process.start()
        child.close()
        started = time.perf_counter()
        try:
            with self.assertRaises(TimeoutError):
                detector.detect(np.zeros((1024, 1024, 3), np.uint8), 0)
            self.assertLess(time.perf_counter()-started, 4)
            self.assertFalse(detector.process.is_alive())
        finally:
            detector.close()

    def test_fixture_missing_frame_is_not_an_empty_observation(self):
        path = self.root / "fixture.json"
        path.write_text(json.dumps({"purpose": "pipeline_fixture_not_model_accuracy", "frames": [{"frame": 0, "detections": []}]}))
        with self.assertRaisesRegex(ValueError, "Missing fixture"):
            FixtureDetector(path).detect(None, 1)

    def test_duplicate_fixture_frames_are_rejected(self):
        path = self.root / "fixture.json"
        path.write_text(json.dumps({"purpose": "pipeline_fixture_not_model_accuracy", "frames": [{"frame": 0, "detections": []}]*2}))
        with self.assertRaisesRegex(ValueError, "unique"):
            FixtureDetector(path)


class AdversarialConfigTests(unittest.TestCase):
    def test_nonfinite_tracker_timestamp_and_capacity_fail_before_state_change(self):
        from coffee_ops.tracker import KalmanTracker
        tracker = KalmanTracker(config().data["tracker"])
        for ts in (float("nan"), float("inf"), True):
            with self.assertRaises(ValueError):
                tracker.update([], ts)
        with self.assertRaisesRegex(ValueError, "capacity"):
            tracker.update([Detection(0, (0, 0, 5, 5), .9)]*129, 0)
        self.assertIsNone(tracker.previous_time)

    def test_nested_typos_and_empty_promotion_gates_fail(self):
        for mutate in (lambda d: d["model"].update(infer_timeout=1), lambda d: d.update(promotion={}),
                       lambda d: d["promotion"].update({"detection.typographic_error": .9}),
                       lambda d: d["classes"][0].update(name=123),
                       lambda d: d["cameras"][0].update(thresholds={"00": .5})):
            c = config()
            mutate(c.data)
            with self.assertRaises(ValueError):
                c.validate()

    def test_self_intersecting_nonzero_area_polygon_fails(self):
        c = config()
        c.data["cameras"][0]["zones"][0]["polygon"] = [[0, 0], [80, 100], [100, 0], [0, 80]]
        with self.assertRaisesRegex(ValueError, "intersect"):
            c.validate()

    def test_repeated_polygon_vertices_fail(self):
        c = config()
        c.data["cameras"][0]["zones"][0]["polygon"] = [[0, 0], [100, 0], [100, 100], [0, 0]]
        with self.assertRaisesRegex(ValueError, "repeated"):
            c.validate()

    def test_duplicate_json_config_keys_fail(self):
        import tempfile
        from pathlib import Path
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "bad.json"
            path.write_text('{"version":"1","version":"2"}')
            with self.assertRaisesRegex(ValueError, "Duplicate"):
                Config.load(path)
