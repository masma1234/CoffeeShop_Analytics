"""Termination must unwind CLI resources and restore caller signal handlers."""
import signal
import unittest
from unittest.mock import patch

from coffee_ops.__main__ import interrupt, run


class EntrypointTests(unittest.TestCase):
    def test_sigterm_callback_uses_the_existing_interrupt_cleanup_path(self):
        with self.assertRaises(KeyboardInterrupt):
            interrupt(signal.SIGTERM, None)

    def test_success_restores_the_previous_signal_handler(self):
        original = signal.getsignal(signal.SIGTERM)
        with patch("coffee_ops.__main__.main", return_value=2):
            self.assertEqual(run(), 2)
        self.assertEqual(signal.getsignal(signal.SIGTERM), original)

    def test_interrupt_returns_nonzero_and_restores_the_handler(self):
        original = signal.getsignal(signal.SIGTERM)
        with patch("coffee_ops.__main__.main", side_effect=KeyboardInterrupt):
            self.assertEqual(run(), 130)
        self.assertEqual(signal.getsignal(signal.SIGTERM), original)
