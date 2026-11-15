"""Propose, never delete, source-backed CPython bytecode inside this repository."""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import struct
import subprocess


def digest(path: Path) -> str:
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--inventory", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError(args.output)
    inventory = json.loads(args.inventory.read_text(encoding="utf-8"))
    root = Path(inventory["root"]).resolve()
    tracked = set(subprocess.check_output(["git", "-C", str(root), "ls-files", "-z"],
                  env=dict(os.environ, GIT_OPTIONAL_LOCKS="0")).decode().split("\0"))
    rows, skipped = [], []
    checked_parents: set[Path] = set()
    source_hashes: dict[Path, str] = {}
    for item in inventory["files"]:
        relative = item["path"]
        cache = root / relative
        if cache.suffix != ".pyc" or cache.parent.name != "__pycache__":
            continue
        # The candidate environment was still changing at the inventory checkpoint.
        if relative.startswith((".venv-candidate/", "var/")):
            continue
        try:
            source = Path(importlib.util.source_from_cache(str(cache)))
            if relative in tracked:
                raise ValueError("tracked, linked or missing source")
            if not cache.is_relative_to(root) or not source.is_relative_to(root):
                raise ValueError("outside workspace")
            for parent in cache.parents:
                if parent == root or parent in checked_parents:
                    break
                if getattr(parent.lstat(), "st_file_attributes", 0) & 0x400:
                    raise ValueError("reparse point")
                checked_parents.add(parent)
            stat = cache.stat()
            source_stat = source.stat()
            if any(getattr(s, "st_file_attributes", 0) & 0x400 for s in [stat, source_stat]):
                raise ValueError("linked file")
            with cache.open("rb") as stream:
                magic, flags, first, second = struct.unpack("<4sIII", stream.read(16))
            if magic != importlib.util.MAGIC_NUMBER or flags not in {0, 1, 3}:
                raise ValueError("unknown bytecode format")
            if flags == 0:
                if first != int(source_stat.st_mtime) & 0xFFFFFFFF or second != source_stat.st_size & 0xFFFFFFFF:
                    raise ValueError("source metadata differs")
            elif struct.pack("<II", first, second) != importlib.util.source_hash(source.read_bytes()):
                raise ValueError("source hash differs")
            if source not in source_hashes:
                source_hashes[source] = digest(source)
            rows.append({"path": relative, "bytes": stat.st_size, "sha256": digest(cache),
                         "source": source.relative_to(root).as_posix(), "source_sha256": source_hashes[source],
                         "reason": "reproducible CPython cache; matching source verified; not tracked",
                         "recovery": "CPython recompiles the retained matching source when bytecode writing is enabled"})
            if len(rows) % 1000 == 0:
                print(f"Verified {len(rows)} disposable cache files", flush=True)
        except (OSError, ValueError, struct.error) as exc:
            skipped.append({"path": relative, "reason": str(exc)})
    result = {"root": str(root), "status": "PROPOSED_ONLY", "logical_bytes": sum(row["bytes"] for row in rows),
              "count": len(rows), "files": rows, "skipped": skipped,
              "reference_review": "CPython cache names map to retained matching .py source. No tracked path is removed; imports can recompile. No model, data, database, log or unique audit artifact qualifies."}
    with args.output.open("x", encoding="utf-8") as stream:
        json.dump(result, stream, indent=2)
    print(json.dumps({key: result[key] for key in ["status", "count", "logical_bytes"]}))


if __name__ == "__main__":
    main()
