"""Class-aware Kalman motion prediction and global gated assignment."""
from __future__ import annotations

from dataclasses import dataclass
import math
from typing import Protocol

import numpy as np
from scipy.optimize import linear_sum_assignment

from .schema import Detection, Observation


def iou(a: tuple, b: tuple) -> float:
    overlap = max(0, min(a[2], b[2]) - max(a[0], b[0])) * max(0, min(a[3], b[3]) - max(a[1], b[1]))
    union = (a[2]-a[0]) * (a[3]-a[1]) + (b[2]-b[0]) * (b[3]-b[1]) - overlap
    return overlap / union if union else 0.0


class ObjectTracker(Protocol):
    def update(self, detections: list[Detection], timestamp: float) -> list[Observation]: ...
    def reset(self) -> None: ...


@dataclass
class _Track:
    id: int
    detection: Detection
    state: np.ndarray
    covariance: np.ndarray
    created_at: float
    last_seen: float
    hits: int = 1
    frames: int = 1


class KalmanTracker:
    def __init__(self, config: dict):
        self.config = config
        self.tracks: list[_Track] = []
        self.next_id = 1
        self.previous_time: float | None = None
        self.new_tracks = 0

    def reset(self) -> None:
        self.tracks.clear()
        self.previous_time = None
        # Never recycle IDs within a run, including after camera movement.

    @staticmethod
    def _measurement(det: Detection) -> np.ndarray:
        x1, y1, x2, y2 = det.bbox
        return np.array([(x1+x2)/2, (y1+y2)/2])

    def update(self, detections: list[Detection], timestamp: float) -> list[Observation]:
        if isinstance(timestamp, bool) or not math.isfinite(timestamp):
            raise ValueError("Tracker timestamp must be finite")
        if len(detections) > self.config["max_detections"]:
            raise ValueError("Tracker detection capacity exceeded")
        if self.previous_time is not None and timestamp <= self.previous_time:
            raise ValueError("Tracker timestamps must strictly increase")
        dt = timestamp - self.previous_time if self.previous_time is not None else 0
        self.previous_time = timestamp
        self.tracks = [t for t in self.tracks if timestamp-t.last_seen <= self.config["max_age_seconds"]]
        transition = np.eye(4)
        transition[0, 2] = transition[1, 3] = dt
        for track in self.tracks:
            track.state = transition @ track.state
            track.covariance = transition @ track.covariance @ transition.T + np.eye(4) * max(dt, 0.001)
            track.frames += 1
        cost = np.full((len(self.tracks), len(detections)), 1e6)
        for i, track in enumerate(self.tracks):
            for j, det in enumerate(detections):
                distance = float(np.linalg.norm(track.state[:2] - self._measurement(det)))
                if track.detection.class_id == det.class_id and distance <= self.config["max_distance_pixels"]:
                    old = track.detection.bbox
                    w, h = old[2]-old[0], old[3]-old[1]
                    cx, cy = track.state[:2]
                    predicted = (cx-w/2, cy-h/2, cx+w/2, cy+h/2)
                    cost[i, j] = 0.6 * distance/self.config["max_distance_pixels"] + 0.4 * (1-iou(predicted, det.bbox))
        rows, cols = linear_sum_assignment(cost)
        assigned: set[int] = set()
        hmat = np.eye(2, 4)
        for i, j in zip(rows, cols):
            if cost[i, j] >= 1e6:
                continue
            track, det = self.tracks[i], detections[j]
            innovation = self._measurement(det) - hmat @ track.state
            gain = track.covariance @ hmat.T @ np.linalg.inv(hmat @ track.covariance @ hmat.T + np.eye(2)*4)
            track.state += gain @ innovation
            track.covariance = (np.eye(4)-gain @ hmat) @ track.covariance
            track.detection = det
            track.last_seen = timestamp
            track.hits += 1
            assigned.add(int(j))
        self.new_tracks = len(detections)-len(assigned)
        if len(self.tracks) + self.new_tracks > self.config["max_tracks"]:
            raise ValueError("Tracker capacity exceeded")
        for j, det in enumerate(detections):
            if j not in assigned:
                state = np.r_[self._measurement(det), 0., 0.]
                self.tracks.append(_Track(self.next_id, det, state, np.eye(4)*100, timestamp, timestamp))
                self.next_id += 1
        return [Observation(t.id, t.detection.class_id, t.detection.bbox, t.detection.confidence,
                            t.created_at, t.last_seen, t.hits, t.last_seen != timestamp,
                            t.hits/t.frames) for t in self.tracks]
