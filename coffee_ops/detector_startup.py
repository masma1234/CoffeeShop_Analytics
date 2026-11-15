"""Bounded model-startup diagnostics under one absolute deadline."""
from __future__ import annotations

import logging
import time
from typing import Any


PHASES = frozenset({
    "backend_validation", "backend_import", "torch_import", "transformers_import",
    "checkpoint_validation", "model_load", "class_validation", "processor_load", "device_setup",
})


class DetectorStartupError(RuntimeError):
    def __init__(self, message: str, metrics: dict[str, Any]):
        super().__init__(message)
        self.startup_metrics = metrics


class DetectorStartupTimeout(TimeoutError):
    def __init__(self, message: str, metrics: dict[str, Any]):
        super().__init__(message)
        self.startup_metrics = metrics


class StartupDeadline:
    """Progress records never refresh the deadline or create an unbounded history."""

    def __init__(self, timeout: float):
        self.started = time.monotonic()
        self.deadline = self.started + timeout
        self.metrics: dict[str, Any] = {
            "status": "loading", "deadline_seconds": timeout, "total_seconds": None,
            "phases": [{"phase": "spawn", "elapsed_seconds": 0.0}],
            "scope": "Parent-observed process start through ready; excludes parent checkpoint hashing. Phase times mark operation starts, not isolated operation durations.",
        }

    @property
    def last_phase(self) -> str:
        return self.metrics["phases"][-1]["phase"]

    def _timeout(self) -> DetectorStartupTimeout:
        return DetectorStartupTimeout(
            f"Detector startup exceeded {self.metrics['deadline_seconds']}s deadline; last stage: {self.last_phase}",
            self.metrics,
        )

    def _record(self, phase: str) -> None:
        self.metrics["phases"].append({"phase": phase, "elapsed_seconds": time.monotonic()-self.started})
        logging.getLogger("coffee_ops").info("Detector startup: %s", phase)

    def wait(self, connection: Any) -> None:
        seen: set[str] = set()
        try:
            while True:
                remaining = self.deadline-time.monotonic()
                if remaining <= 0:
                    raise self._timeout()
                try:
                    available = connection.poll(remaining)
                    message = connection.recv() if available else None
                except (EOFError, OSError) as exc:
                    raise DetectorStartupError(f"Detector disconnected during startup; last stage: {self.last_phase}", self.metrics) from exc
                if not available:
                    raise self._timeout()
                if time.monotonic() >= self.deadline:
                    raise self._timeout()
                if not isinstance(message, tuple) or len(message) != 2:
                    raise DetectorStartupError("Invalid detector startup response", self.metrics)
                status, payload = message
                if status == "error" and isinstance(payload, str):
                    raise DetectorStartupError(f"Detector failed during {self.last_phase}: {payload}", self.metrics)
                if status == "ready" and payload is None:
                    self._record("ready")
                    self.metrics["status"] = "ready"
                    return
                if status != "loading" or not isinstance(payload, str) or payload not in PHASES or payload in seen:
                    raise DetectorStartupError("Invalid or repeated detector startup stage", self.metrics)
                seen.add(payload)
                self._record(payload)
        finally:
            self.metrics["total_seconds"] = time.monotonic()-self.started
            if self.metrics["status"] != "ready":
                self.metrics["status"] = "failed"
