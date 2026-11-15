"""Startup protocol faults without heavyweight imports or timing-dependent sleeps."""
from pathlib import Path
import json
import tempfile
import unittest
from unittest.mock import Mock, patch

from coffee_ops.config import Config
from coffee_ops.detector import YOLODetector, _validate_rtdetr_checkpoint
from coffee_ops.detector_startup import DetectorStartupError, DetectorStartupTimeout, StartupDeadline

ROOT = Path(__file__).resolve().parents[1]


class Clock:
    def __init__(self):
        self.seconds = 0.0

    def __call__(self):
        return self.seconds


class Wire:
    def __init__(self, clock, messages, step=.1):
        self.clock, self.messages, self.step = clock, list(messages), step
        self.waits = []

    def poll(self, timeout):
        self.waits.append(timeout)
        if not self.messages:
            self.clock.seconds += timeout
            return False
        self.clock.seconds += self.step
        return True

    def recv(self):
        message = self.messages.pop(0)
        if isinstance(message, BaseException):
            raise message
        return message


class DetectorStartupTests(unittest.TestCase):
    def test_progress_and_ready_have_monotonic_parent_observed_times(self):
        clock = Clock()
        wire = Wire(clock, [("loading", "torch_import"), ("loading", "model_load"), ("ready", None)])
        with patch("coffee_ops.detector_startup.time.monotonic", clock):
            startup = StartupDeadline(1)
            startup.wait(wire)
        self.assertEqual(startup.metrics["status"], "ready")
        self.assertEqual([p["phase"] for p in startup.metrics["phases"]], ["spawn", "torch_import", "model_load", "ready"])
        self.assertAlmostEqual(startup.metrics["total_seconds"], .3)
        self.assertEqual(wire.waits, sorted(wire.waits, reverse=True))

    def test_progress_does_not_refresh_deadline(self):
        clock = Clock()
        wire = Wire(clock, [("loading", p) for p in ("torch_import", "transformers_import", "model_load")], step=.3)
        with patch("coffee_ops.detector_startup.time.monotonic", clock):
            startup = StartupDeadline(1)
            with self.assertRaisesRegex(DetectorStartupTimeout, "last stage: model_load") as failure:
                startup.wait(wire)
        self.assertAlmostEqual(clock.seconds, 1)
        self.assertAlmostEqual(wire.waits[-1], .1)
        self.assertEqual(failure.exception.startup_metrics["status"], "failed")
        self.assertEqual(len(startup.metrics["phases"]), 4)

    def test_ready_received_after_deadline_is_not_success(self):
        clock = Clock()
        with patch("coffee_ops.detector_startup.time.monotonic", clock):
            startup = StartupDeadline(.5)
            with self.assertRaises(DetectorStartupTimeout):
                startup.wait(Wire(clock, [("ready", None)], step=.6))
        self.assertEqual(startup.metrics["status"], "failed")

    def test_malformed_repeated_and_unknown_messages_fail_closed(self):
        cases = [
            [("ok", [])], [("ready", [])], ["ready"], [("loading", {})],
            [("loading", "arbitrary_stage")],
            [("loading", "model_load"), ("loading", "model_load")],
        ]
        for messages in cases:
            with self.subTest(messages=messages):
                clock = Clock()
                with patch("coffee_ops.detector_startup.time.monotonic", clock):
                    startup = StartupDeadline(1)
                    with self.assertRaises(DetectorStartupError):
                        startup.wait(Wire(clock, messages))
                self.assertEqual(startup.metrics["status"], "failed")

    def test_disconnected_worker_retains_last_stage(self):
        for error in (EOFError(), OSError("closed")):
            with self.subTest(error=type(error).__name__):
                clock = Clock()
                with patch("coffee_ops.detector_startup.time.monotonic", clock):
                    startup = StartupDeadline(1)
                    with self.assertRaisesRegex(DetectorStartupError, "disconnected.*model_load") as failure:
                        startup.wait(Wire(clock, [("loading", "model_load"), error]))
                self.assertEqual(failure.exception.startup_metrics["status"], "failed")

    def test_load_error_keeps_original_error_and_last_stage(self):
        clock = Clock()
        with patch("coffee_ops.detector_startup.time.monotonic", clock):
            startup = StartupDeadline(1)
            with self.assertRaisesRegex(DetectorStartupError, "processor_load: ValueError: invalid processor"):
                startup.wait(Wire(clock, [("loading", "processor_load"), ("error", "ValueError: invalid processor")]))

    def test_keyboard_interrupt_closes_both_pipe_ends_and_worker(self):
        context = Mock()
        connection, child = Mock(), Mock()
        context.Pipe.return_value = (connection, child)
        context.Process.return_value.pid = 123
        connection.poll.side_effect = KeyboardInterrupt
        with patch("coffee_ops.detector.validate_metadata", return_value={}), patch("coffee_ops.detector.mp.get_context", return_value=context):
            with self.assertRaises(KeyboardInterrupt):
                YOLODetector(Config.load(ROOT / "config/example.json"), "shop")
        context.Process.return_value.terminate.assert_called_once()
        context.Process.return_value.join.assert_called_once()
        connection.close.assert_called_once()
        self.assertTrue(child.close.called)

    def test_failed_process_start_closes_pipe_without_joining_unstarted_worker(self):
        context = Mock()
        connection, child = Mock(), Mock()
        context.Pipe.return_value = (connection, child)
        context.Process.return_value.pid = None
        context.Process.return_value.start.side_effect = OSError("process unavailable")
        with patch("coffee_ops.detector.validate_metadata", return_value={}), patch("coffee_ops.detector.mp.get_context", return_value=context):
            with self.assertRaisesRegex(OSError, "process unavailable"):
                YOLODetector(Config.load(ROOT / "config/example.json"), "shop")
        context.Process.return_value.join.assert_not_called()
        connection.close.assert_called_once()
        child.close.assert_called_once()

    def test_startup_message_cannot_be_mistaken_for_inference_output(self):
        detector = YOLODetector.__new__(YOLODetector)
        detector.connection = Mock()
        detector.connection.recv.return_value = ("loading", "model_load")
        detector.close = Mock()
        with self.assertRaisesRegex(RuntimeError, "Invalid detector inference"):
            detector._receive(1)
        detector.close.assert_called_once()


class RTDetrCheckpointTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.weights = self.root / "model.safetensors"
        self.names = {0: "person", 41: "cup"}
        self.configuration = {"model_type": "rt_detr_v2", "id2label": {"0": "person", "41": "cup"}}
        self.processor = {"image_processor_type": "RTDetrImageProcessor"}
        self.write()

    def write(self):
        (self.root / "config.json").write_text(json.dumps(self.configuration))
        (self.root / "preprocessor_config.json").write_text(json.dumps(self.processor))

    def test_exact_architecture_processor_and_sparse_class_ids_are_accepted(self):
        _validate_rtdetr_checkpoint(str(self.root), str(self.weights), self.names)

    def test_direct_class_cannot_coerce_another_architecture_or_renamed_catalog(self):
        for field, value in [("model_type", "rt_detr"), ("id2label", {"0": "customer", "41": "cup"})]:
            with self.subTest(field=field):
                original = self.configuration[field]
                self.configuration[field] = value
                self.write()
                with self.assertRaisesRegex(ValueError, "architecture or embedded catalog"):
                    _validate_rtdetr_checkpoint(str(self.root), str(self.weights), self.names)
                self.configuration[field] = original

    def test_different_processor_or_hashed_weight_path_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "actual model.safetensors"):
            _validate_rtdetr_checkpoint(str(self.root), str(self.root / "other.safetensors"), self.names)
        self.processor["image_processor_type"] = "DetrImageProcessor"
        self.write()
        with self.assertRaisesRegex(ValueError, "supported RTDetrImageProcessor"):
            _validate_rtdetr_checkpoint(str(self.root), str(self.weights), self.names)
