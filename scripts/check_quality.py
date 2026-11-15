"""Record final checks without hiding failures or overwriting old evidence."""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import subprocess
import sys
import time


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=False)
    root = Path(__file__).resolve().parents[1]
    commands = {
        "pip-check": ["-m", "pip", "check"],
        "doctor": ["-m", "coffee_ops", "doctor"],
        "config": ["-m", "coffee_ops", "validate-config"],
        "pytest-coverage": ["-m", "coverage", "run", "--source=coffee_ops", "-m", "pytest", "-q", "-o", "cache_dir=" + str(args.output.resolve() / ".pytest_cache"), "tests"],
        "coverage-report": ["-m", "coverage", "report"],
        "coverage-json": ["-m", "coverage", "json", "-o", str(args.output.resolve() / "coverage.json")],
        "ruff": ["-m", "ruff", "check", "--cache-dir", str(args.output.resolve() / ".ruff_cache"), "--select", "E9,F", "coffee_ops", "scripts", "tests"],
        "mypy": ["-m", "mypy", "--cache-dir", str(args.output.resolve() / ".mypy_cache"), "--show-traceback", "--check-untyped-defs", "--ignore-missing-imports", "coffee_ops"],
        "acceptance": ["scripts/verify_mvp.py", "--output", str(args.output.resolve() / "acceptance")],
    }
    results = []
    for name, arguments in commands.items():
        command = [sys.executable, "-B", *arguments]
        start = time.perf_counter()
        with (args.output / (name + ".log")).open("x", encoding="utf-8") as stream:
            process = subprocess.run(command, cwd=root, stdout=stream, stderr=subprocess.STDOUT,
                env=dict(os.environ, PYTHONDONTWRITEBYTECODE="1", COVERAGE_FILE=str(args.output.resolve() / ".coverage")), timeout=900)
        row = {"check": name, "command": command, "exit_code": process.returncode,
               "seconds": time.perf_counter() - start}
        results.append(row)
        (args.output / "checks.json").write_text(json.dumps(results, indent=2) + "\n", encoding="utf-8")
        print(json.dumps(row), flush=True)
    return int(any(row["exit_code"] for row in results))


if __name__ == "__main__":
    raise SystemExit(main())
