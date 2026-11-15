"""Resolve binary wheels on the current Python/platform and write a hashed lock.

Run separately on each supported platform. Review the diff before installing;
this invokes pip's resolver but does not install or upgrade the current environment.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import platform
import subprocess
import sys
import tempfile
from urllib.parse import urlsplit
from urllib.request import urlopen


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", action="append", required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--report", type=Path)
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError(args.output)
    with tempfile.TemporaryDirectory() as directory:
        report = Path(directory) / "resolution.json"
        command = [sys.executable, "-m", "pip", "install", "--dry-run", "--ignore-installed",
                   "--only-binary=:all:", "--report", str(report)]
        for source in args.input:
            command.extend(["-r", source])
        subprocess.run(command, check=True)
        result = json.loads(report.read_text(encoding="utf-8"))
    if args.report:
        with args.report.open("x", encoding="utf-8") as stream:
            json.dump(result, stream, indent=2)
    rows = []
    for item in result["install"]:
        download = item["download_info"]
        if not urlsplit(download["url"]).path.endswith(".whl"):
            raise ValueError("Non-wheel dependency requires explicit review")
        digest = download["archive_info"].get("hashes", {}).get("sha256")
        if digest is None:
            # Metadata-only resolutions can omit archive hashes. Hash the actual
            # wheel bytes over HTTPS instead of inventing a hash or weakening pip.
            hasher = hashlib.sha256()
            with urlopen(download["url"], timeout=180) as response:
                for block in iter(lambda: response.read(8 * 1024 * 1024), b""):
                    hasher.update(block)
            digest = hasher.hexdigest()
        metadata = item["metadata"]
        rows.append(f'{metadata["name"]}=={metadata["version"]} --hash=sha256:{digest}')
    header = (f"# Resolved on {platform.system()} {platform.machine()}, Python {platform.python_version()}\n"
              "# One verified wheel hash per package; use only on this platform/Python.\n"
              "--only-binary=:all:\n--extra-index-url https://download.pytorch.org/whl/cpu\n")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(header + "\n".join(sorted(rows, key=str.lower)) + "\n", encoding="utf-8")
    print(f"Locked {len(rows)} wheels to {args.output}")


if __name__ == "__main__":
    main()
