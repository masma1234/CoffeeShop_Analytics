"""Real OpenCV codec/process integration, using an explicitly synthetic detector."""
import contextlib
import io
import json
import multiprocessing as mp
import tempfile
import time
import unittest
from pathlib import Path
from unittest.mock import patch

from coffee_ops.cli import main
from coffee_ops.exports import export_predictions
from coffee_ops.config import Config
from coffee_ops.demo import make_demo
from coffee_ops.detector import FixtureDetector, YOLODetector
from coffee_ops.evaluation import evaluate
from coffee_ops.reconciliation import reconcile
from coffee_ops.pipeline import Pipeline
from coffee_ops.runtime import replay
from coffee_ops.pos_adapter import FilePOSAdapter, import_orders
from coffee_ops.reporting import daily_report
from coffee_ops.storage import SQLiteStore
from coffee_ops.video_input import VideoInput

ROOT = Path(__file__).resolve().parents[1]
START = "2026-01-01T09:00:00Z"


class VideoIntegrationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.config = Config.load(ROOT / "config/example.json")
        self.store = SQLiteStore(self.root / "ops.db")

    def tearDown(self):
        self.store.close()
        self.temp.cleanup()

    def test_existing_output_rejects_pos_import_before_ledger_changes(self):
        make_demo(str(self.root / "demo"))
        output = self.root / "result.json"
        output.write_text("keep this report", encoding="utf-8")
        with contextlib.redirect_stderr(io.StringIO()), contextlib.redirect_stdout(io.StringIO()):
            code = main(["--config", str(ROOT / "config/example.json"),
                         "--db", str(self.root / "ops.db"), "--output", str(output),
                         "import-pos", "--file", str(self.root / "demo/orders.json")])
        self.assertEqual(code, 2)
        self.assertEqual(self.store.records("orders"), [])
        self.assertEqual(self.store.records("failures"), [])
        self.assertEqual(output.read_text(encoding="utf-8"), "keep this report")

    def test_recorded_video_pos_ledger_report_and_evaluation_end_to_end(self):
        make_demo(str(self.root / "demo"))
        fixture = self.root / "demo/detections.json"
        for _ in range(2):
            detector = FixtureDetector(fixture)
            health = replay(self.config, self.store, detector, str(self.root / "demo/fixture.avi"), "shop", "demo", START, detector.metadata)
            self.assertEqual(health["processed_frames"], 12)
            self.assertEqual(health["status"], "completed")
        self.assertEqual(len(self.store.records("frames")), 12)
        import_orders(self.store, FilePOSAdapter(self.root / "demo/orders.json"), self.config.data["pos"])
        reconcile(self.store, self.config.data["pos"])
        report = daily_report(self.store, "2026-01-01")
        self.assertEqual(report["confirmed_sold_units"], {"COFFEE": 1})
        self.assertEqual(report["visual_movements"], {"coffee_cup:placed": 1, "coffee_cup:transferred": 1, "coffee_cup:disappeared": 1})
        detector = FixtureDetector(fixture)
        replay(self.config, self.store, detector, str(self.root / "demo/fixture.avi"), "shop", "demo", START, detector.metadata)
        reconcile(self.store, self.config.data["pos"])
        self.assertEqual(daily_report(self.store, "2026-01-01"), report)
        prediction = export_predictions(self.store, "demo", "shop")
        truth = json.loads((self.root / "demo/ground-truth.json").read_text())
        evaluation = evaluate(truth, prediction)
        self.assertEqual(evaluation["counting"]["event_recall"], 1)
        self.assertEqual(evaluation["tracking"]["ID_switches"], 0)
        self.assertEqual(evaluation["provenance"]["kind"], "synthetic_logic_fixture")

    def test_missing_video_fails_explicitly(self):
        reader = VideoInput(str(self.root / "missing.avi"), timeout=3)
        try:
            with self.assertRaises(OSError):
                list(reader)
        finally:
            reader.close()

    def test_detector_deadline_terminates_process(self):
        detector = YOLODetector.__new__(YOLODetector)
        ctx = mp.get_context("spawn")
        detector.connection, other = ctx.Pipe()
        detector.process = ctx.Process(target=time.sleep, args=(20,), daemon=True)
        detector.process.start()
        started = time.perf_counter()
        try:
            with self.assertRaises(TimeoutError):
                detector._receive(.1)
            self.assertFalse(detector.process.is_alive())
            self.assertLess(time.perf_counter()-started, 4)
        finally:
            other.close()
            detector.close()

    def test_camera_motion_latches_unknown_until_recalibration(self):
        import numpy as np
        pipe = Pipeline(self.config, self.store, "shop", "motion", START, "test", {"version": "fixture"})
        image = np.zeros((240, 320, 3), np.uint8)
        pipe.process(0, 0, [], image=image)
        with patch("coffee_ops.pipeline.cv2.phaseCorrelate", return_value=((30, 0), .9)):
            result = pipe.process(1, 1, [], image=image)
        self.assertTrue(pipe.motion_latched)
        self.assertEqual(result["tables"][0]["status"], "unknown")
        self.assertIn("camera_moved", {a["kind"] for a in result["alerts"]})

    def test_missing_model_cli_fails_without_download(self):
        make_demo(str(self.root / "demo"))
        with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            code = main(["--config", str(ROOT / "config/example.json"), "--db", str(self.root / "cli.db"),
                         "replay", "--source", str(self.root / "demo/fixture.avi"), "--camera", "shop", "--run-id", "missing", "--start", START])
        self.assertEqual(code, 2)
        store = SQLiteStore(self.root / "cli.db")
        try:
            self.assertEqual(store.latest("health", "camera_id", "shop")["status"], "error")
        finally:
            store.close()

    def test_bad_pos_returns_nonzero(self):
        with contextlib.redirect_stderr(io.StringIO()):
            code = main(["--config", str(ROOT / "config/example.json"), "--db", str(self.root / "cli.db"),
                         "import-pos", "--file", str(self.root / "missing.csv")])
        self.assertEqual(code, 2)
