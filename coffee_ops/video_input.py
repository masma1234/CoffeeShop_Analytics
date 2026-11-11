"""Isolated decoding with a bounded queue, explicit EOF, and read deadlines."""
from __future__ import annotations

import multiprocessing as mp
import math
import queue
import time
from typing import Any, Iterator


def _decode(source: str | int, live: bool, output: Any, stop: Any, dropped: Any) -> None:
    import cv2
    capture = cv2.VideoCapture(source)
    try:
        if not capture.isOpened():
            output.put(("error", "Camera/video could not be opened"))
            return
        fps = capture.get(cv2.CAP_PROP_FPS)
        total = int(capture.get(cv2.CAP_PROP_FRAME_COUNT))
        if not live and (not math.isfinite(fps) or fps <= 0):
            output.put(("error", "Recorded video has invalid FPS"))
            return
        output.put(("metadata", {"fps": fps, "total_frames": total}))
        index = 0
        started = time.monotonic()
        while not stop.is_set():
            ok, frame = capture.read()
            if not ok:
                if live or (total > 0 and index < total):
                    output.put(("error", f"Camera offline or corrupt video at frame {index}"))
                else:
                    output.put(("eof", index))
                return
            if frame is None or frame.size == 0:
                output.put(("error", f"Corrupt frame {index}"))
                return
            offset = time.monotonic()-started if live else index/fps
            item = ("frame", (index, offset, frame))
            if live:
                try:
                    output.put_nowait(item)
                except queue.Full:
                    try:
                        output.get_nowait()
                        with dropped.get_lock():
                            dropped.value += 1
                    except queue.Empty:
                        pass  # Consumer won the race; no frame was silently lost.
                    try:
                        output.put_nowait(item)
                    except queue.Full:
                        with dropped.get_lock():
                            dropped.value += 1
            else:
                while not stop.is_set():
                    try:
                        output.put(item, timeout=0.1)
                        break
                    except queue.Full:
                        continue  # Lossless replay backpressure.
            index += 1
    except (OSError, ValueError, cv2.error) as exc:
        output.put(("error", f"{type(exc).__name__}: {exc}"))
    finally:
        capture.release()


class VideoInput:
    def __init__(self, source: str | int, live: bool = False, timeout: float = 15):
        ctx = mp.get_context("spawn")
        self.queue = ctx.Queue(maxsize=2)
        self.stop = ctx.Event()
        self.dropped = ctx.Value("i", 0)
        self.timeout, self.live = timeout, live
        self.process = ctx.Process(target=_decode, args=(source, live, self.queue, self.stop, self.dropped), daemon=True)
        self.process.start()
        self.metadata: dict = {}

    def __iter__(self) -> Iterator[tuple]:
        while True:
            try:
                kind, data = self.queue.get(timeout=self.timeout)
            except queue.Empty as exc:
                raise TimeoutError("Camera read deadline exceeded") from exc
            if kind == "error":
                raise OSError(data)
            if kind == "eof":
                if data == 0:
                    raise ValueError("Video contains no readable frames")
                return
            if kind == "metadata":
                self.metadata = data
                continue
            yield data

    def close(self) -> None:
        self.stop.set()
        self.process.join(timeout=1)
        if self.process.is_alive():
            self.process.terminate()
            self.process.join(timeout=2)
        self.queue.close()
        self.queue.cancel_join_thread()
