"""Run model probes sequentially in separate, deadline-bounded processes."""
import argparse
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.benchmark_models import MODELS


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True, help="New results directory")
    parser.add_argument("--models", nargs="+", choices=MODELS, default=list(MODELS))
    parser.add_argument("--device", default="cpu")
    parser.add_argument("--precision", choices=["fp32", "fp16"], default="fp32")
    parser.add_argument("--download", action="store_true")
    parser.add_argument("--timeout", type=int, default=600)
    args = parser.parse_args()
    if args.timeout < 1 or len(set(args.models)) != len(args.models):
        parser.error("Positive timeout and unique models required")
    args.output.mkdir(parents=True, exist_ok=False)
    root = Path(__file__).resolve().parents[1]
    failures = []
    for name in args.models:
        command = [sys.executable, str(root / "scripts/benchmark_models.py"), "--model", name,
                   "--device", args.device, "--precision", args.precision,
                   "--output", str(args.output.resolve() / (name + ".json"))]
        if args.download:
            command.append("--download")
        print(f"Starting {name}", flush=True)
        try:
            result = subprocess.run(command, cwd=root, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=args.timeout)
            log = result.stdout + result.stderr
            if result.returncode:
                failures.append({"model": name, "exit_code": result.returncode})
        except subprocess.TimeoutExpired as exc:
            failures.append({"model": name, "reason": "deadline_exceeded", "seconds": args.timeout})
            log = str(exc)
        (args.output / (name + ".log")).write_text(log, encoding="utf-8")
        print(f"Finished {name}; result present: {(args.output / (name + '.json')).exists()}", flush=True)
    (args.output / "suite.json").write_text(json.dumps({"failures": failures, "models_requested": args.models}, indent=2), encoding="utf-8")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
