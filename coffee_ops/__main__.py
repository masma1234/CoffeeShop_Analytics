"""CLI entry point, including graceful container termination."""
import signal
from types import FrameType

from .cli import main


def interrupt(_signum: int, _frame: FrameType | None) -> None:
    raise KeyboardInterrupt


def run() -> int:
    previous = signal.signal(signal.SIGTERM, interrupt)
    try:
        return main()
    except KeyboardInterrupt:
        return 130
    finally:
        signal.signal(signal.SIGTERM, previous)


if __name__ == "__main__":
    raise SystemExit(run())
