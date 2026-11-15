"""Read-only size, ignore and SHA-256 duplicate inventory (no deletion).

Inventory local data separately from Git inputs. Symlinks/reparse-point directories
are recorded without following them. Exact content equality does not authorize
removal: models, data, source, credentials and unique evidence remain protected.
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import subprocess
import time


def filesystem_path(path: Path) -> Path:
    """Permit inspection of long wheel paths without changing Windows policy."""
    if os.name == "nt" and not str(path).startswith("\\\\?\\"):
        return Path("\\\\?\\" + str(path.absolute()))
    return path


def sha256(path: Path) -> str:
    with filesystem_path(path).open("rb") as stream:
        # file_digest reuses a small readinto buffer. Repeated 8 MiB read()
        # allocations caused excessive Windows page faults for tiny files.
        return hashlib.file_digest(stream, "sha256").hexdigest()


def category(name: str) -> str:
    parts = Path(name).parts
    suffix = Path(name).suffix.lower()
    if ".git" in parts:
        return "git_metadata"
    if suffix in {".pt", ".pth", ".safetensors", ".onnx", ".engine"}:
        return "model_artifact"
    if suffix in {".sqlite", ".sqlite3", ".db", ".db-wal", ".db-shm"}:
        return "database_or_security_cache"
    if suffix in {".mp4", ".avi", ".mov", ".mkv", ".jpg", ".jpeg", ".png"}:
        return "media_or_dataset"
    if "__pycache__" in parts or suffix in {".pyc", ".pyo"}:
        return "python_cache"
    if any(part.startswith(".venv") for part in parts):
        return "local_environment"
    if suffix in {".zip", ".tar", ".gz", ".zst", ".7z"}:
        return "archive"
    if name.startswith("var/"):
        return "local_data_or_evidence"
    if suffix in {".md", ".txt", ".pdf", ".docx"}:
        return "documentation_or_requirements"
    return "source_or_configuration"


def inventory(root: Path, previous: dict | None = None, quiet: bool = False) -> dict:
    started = time.perf_counter()
    captured_from = datetime.now(timezone.utc).isoformat()
    env = dict(os.environ, GIT_OPTIONAL_LOCKS="0")
    def git_files(*args):
        output = subprocess.check_output(["git", "-c", "core.longpaths=true", "--no-optional-locks", "-C", str(root), "ls-files", "-z", *args], env=env)
        return set(output.decode("utf-8", errors="surrogateescape").strip("\0").split("\0")) - {""}
    tracked = git_files()
    ignored = git_files("--others", "--ignored", "--exclude-standard")
    # Git reports an ignored nested repository as a directory, rather than
    # enumerating its private index/files. Inherit that ignored classification.
    ignored_prefixes = tuple(name for name in ignored if name.endswith("/"))
    files, errors, links = [], [], []
    # Keep DirEntry's cached Windows enumeration metadata. Calling Path.stat for
    # each file turned a read-only inventory into tens of thousands of extra I/O
    # operations. Reparse points are excluded before descending.
    scan_root = filesystem_path(root)
    pending = [scan_root]
    while pending:
        base = pending.pop()
        with os.scandir(base) as entries:
            for entry in entries:
                path = Path(entry.path)
                relative = path.relative_to(scan_root).as_posix()
                try:
                    stat = entry.stat(follow_symlinks=False)
                    if entry.is_symlink() or getattr(stat, "st_file_attributes", 0) & 0x400:
                        links.append(relative)
                        continue
                    if entry.is_dir(follow_symlinks=False):
                        pending.append(path)
                        continue
                    if not entry.is_file(follow_symlinks=False):
                        continue
                    files.append({"path": relative, "bytes": stat.st_size,
                              "mtime_ns": stat.st_mtime_ns, "category": category(relative),
                              "tracked": relative in tracked,
                              "ignored": relative in ignored or relative.startswith(ignored_prefixes)})
                except OSError as exc:
                    errors.append({"path": relative, "error": type(exc).__name__})
    sizes = defaultdict(list)
    directories = defaultdict(lambda: {"bytes": 0, "files": 0})
    extensions, categories, top_level = Counter(), Counter(), defaultdict(lambda: {"bytes": 0, "files": 0})
    for row in files:
        path = Path(row["path"])
        sizes[row["bytes"]].append(row)
        extensions[path.suffix.lower() or "<none>"] += 1
        categories[row["category"]] += 1
        key = path.parts[0] if len(path.parts) > 1 else "<root files>"
        top_level[key]["bytes"] += row["bytes"]; top_level[key]["files"] += 1
        parent = path.parent
        while str(parent) != ".":
            directories[parent.as_posix()]["bytes"] += row["bytes"]
            directories[parent.as_posix()]["files"] += 1
            parent = parent.parent
    duplicates = []
    cached = {row["path"]: row for row in (previous or {}).get("files", []) if row.get("sha256")}
    reused_hashes = fresh_hashes = 0
    candidates = [row for rows in sizes.values() if len(rows) > 1 for row in rows]
    groups: dict[tuple[int, str], list[str]] = defaultdict(list)
    def hash_row(row):
        old = cached.get(row["path"])
        reused = bool(old and old["bytes"] == row["bytes"] and old["mtime_ns"] == row["mtime_ns"])
        try:
            if reused:
                digest = old["sha256"]
            else:
                digest = sha256(root / row["path"])
                stat = filesystem_path(root / row["path"]).stat()
                if stat.st_size != row["bytes"] or stat.st_mtime_ns != row["mtime_ns"]:
                    return row, None, reused, "changed_during_hash"
            return row, digest, reused, None
        except OSError as exc:
            return row, None, reused, type(exc).__name__
    # Bound both I/O concurrency and queued futures. No mutations run in workers.
    with ThreadPoolExecutor(max_workers=4) as pool:
        for offset in range(0, len(candidates), 256):
            for row, digest, reused, error in pool.map(hash_row, candidates[offset:offset+256]):
                if error:
                    errors.append({"path": row["path"], "error": error})
                    continue
                reused_hashes += int(reused)
                fresh_hashes += int(not reused)
                row["sha256"] = digest
                groups[(row["bytes"], digest)].append(row["path"])
            if not quiet and offset % 10240 == 0:
                print(json.dumps({"hash_progress": min(offset+256, len(candidates)),
                                  "candidates": len(candidates), "fresh": fresh_hashes,
                                  "reused": reused_hashes}), flush=True)
    for (size, digest), paths in groups.items():
        if len(paths) > 1:
            duplicates.append({"bytes_each": size, "sha256": digest, "paths": paths,
                               "duplicate_logical_bytes": size * (len(paths) - 1)})
    total = sum(row["bytes"] for row in files)
    return {"root": str(root), "total_logical_bytes": total, "file_count": len(files),
            "captured_from_utc": captured_from, "captured_to_utc": datetime.now(timezone.utc).isoformat(),
            "top_level": dict(top_level), "directories": dict(directories),
            "largest_100_files": sorted(files, key=lambda row: row["bytes"], reverse=True)[:100],
            "largest_100_directories": sorted((dict(path=name, **value) for name, value in directories.items()), key=lambda row: row["bytes"], reverse=True)[:100],
            "extensions": dict(extensions), "categories": dict(categories),
            "ignored_bytes": sum(row["bytes"] for row in files if row["ignored"]),
            "tracked_bytes": sum(row["bytes"] for row in files if row["tracked"]),
            "duplicates": sorted(duplicates, key=lambda row: row["duplicate_logical_bytes"], reverse=True),
            "files": files, "links_not_followed": links, "errors": errors,
            "hashes": {"fresh": fresh_hashes, "reused_unchanged_size_mtime": reused_hashes},
            "seconds": time.perf_counter() - started,
            "measurement": "Logical file lengths, not filesystem allocation. Hardlinks can count more than once. Parent/child directory totals overlap; do not sum them. Git metadata is counted separately, not classified as tracked source."}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--previous", type=Path, help="Reuse SHA-256 only for unchanged path, size and nanosecond mtime; reuse is reported")
    parser.add_argument("--quiet", action="store_true", help="Write only the JSON output; avoid changing a log during the inventory")
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError(args.output)
    previous = json.loads(args.previous.read_text(encoding="utf-8")) if args.previous else None
    if previous and Path(previous["root"]).resolve() != args.root.resolve():
        raise ValueError("Previous hash inventory belongs to a different repository root")
    result = inventory(args.root.resolve(), previous, args.quiet)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("x", encoding="utf-8") as stream:
        json.dump(result, stream, indent=2, ensure_ascii=True)
        stream.write("\n")
    if not args.quiet:
        print(json.dumps({key: result[key] for key in ["total_logical_bytes", "file_count", "top_level", "ignored_bytes", "tracked_bytes", "seconds"]}))


if __name__ == "__main__":
    main()
