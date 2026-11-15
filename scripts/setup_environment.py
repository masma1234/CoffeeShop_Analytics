"""Create an isolated CPU environment and install the reviewed platform lock.

Uses extended Windows paths for long Torch wheel filenames. No registry changes,
global package changes or modifications to an existing environment are performed.
"""
from __future__ import annotations

import argparse
import os
from pathlib import Path
import platform
import subprocess
import sys
import venv


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--directory", type=Path, default=Path(".venv-candidate"))
    parser.add_argument("--dev", action="store_true")
    parser.add_argument("--video", action="store_true")
    args = parser.parse_args()
    if sys.version_info[:2] != (3, 13) or platform.machine().lower() not in {"amd64", "x86_64"}:
        raise SystemExit("Reviewed locks support Python 3.13 on Windows/Linux x86-64 only")
    if platform.system() not in {"Windows", "Linux"}:
        raise SystemExit("No reviewed lock for this operating system")
    root = Path(__file__).resolve().parents[1]
    directory = args.directory.resolve()
    if directory.exists():
        raise FileExistsError("Choose a new environment directory; existing environments are preserved")
    venv.create(directory, with_pip=True)
    executable = directory / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
    python = "\\\\?\\" + str(executable) if os.name == "nt" else str(executable)
    def run(*arguments: str) -> None:
        subprocess.run([python, "-B", *arguments], cwd=root, check=True,
                       env=dict(os.environ, PYTHONDONTWRITEBYTECODE="1"))
    run("-m", "pip", "install", "--no-compile", "pip==26.3")
    lock = "requirements-lock-windows.txt" if os.name == "nt" else "requirements-lock-linux.txt"
    run("-m", "pip", "install", "--no-compile", "--require-hashes", "-r", lock)
    if args.dev:
        run("-m", "pip", "install", "--no-compile", "-r", "requirements-dev.txt")
    if args.video:
        run("-m", "pip", "install", "--no-compile", "-r", "requirements-video.txt")
    run("-m", "pip", "check")
    run("-m", "coffee_ops", "doctor")
    print(f"Environment ready: {executable}")


if __name__ == "__main__":
    main()
