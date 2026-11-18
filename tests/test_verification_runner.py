"""A failed or timed-out release runner must preserve evidence and stay failed."""
import contextlib
import io
import json
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

from scripts.verify_mvp import run_unit_suite


class VerificationRunnerTests(unittest.TestCase):
    def test_timeout_keeps_partial_output_and_nonzero_result_without_extending_gate(self):
        failure = subprocess.TimeoutExpired(["python"], 180, output=b"partial stdout\n", stderr=b"last test\n")
        with tempfile.TemporaryDirectory() as folder, patch("scripts.verify_mvp.subprocess.run", side_effect=failure) as run:
            root = Path(folder)
            with contextlib.redirect_stdout(io.StringIO()):
                code = run_unit_suite(root, root)
            self.assertEqual(code, 124)
            self.assertEqual(run.call_args.kwargs["timeout"], 180)
            self.assertEqual((root / "tests.txt").read_text(), "partial stdout\nlast test\n")
            self.assertEqual(json.loads((root / "unit-suite.json").read_text()),
                             {"exit_code": 124, "timed_out": True, "deadline_seconds": 180})

    def test_nonzero_child_exit_is_not_reported_as_success(self):
        failure = subprocess.CompletedProcess(["python"], 7, "test output\n", "failure\n")
        with tempfile.TemporaryDirectory() as folder, patch("scripts.verify_mvp.subprocess.run", return_value=failure):
            root = Path(folder)
            with contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(run_unit_suite(root, root), 7)
            self.assertFalse(json.loads((root / "unit-suite.json").read_text())["timed_out"])
            self.assertIn("failure", (root / "tests.txt").read_text())
