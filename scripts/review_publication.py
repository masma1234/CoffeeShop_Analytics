"""Read-only candidate/history screening; findings need human review, not auto-deletion."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import zipfile

PATTERNS = {
    "private_key": rb"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----",
    "github_token": rb"\b(?:gh[pousr]_[A-Za-z0-9]{30,}|github_pat_[A-Za-z0-9_]{50,})\b",
    "aws_access_key": rb"\b(?:AKIA|ASIA)[A-Z0-9]{16}\b",
    "slack_token": rb"\bxox[baprs]-[A-Za-z0-9-]{20,}\b",
    "credential_in_url": rb"[a-zA-Z][a-zA-Z0-9+.-]*://[^\s/'\"<>]+:[^\s/'\"<>]+@",
    "assigned_secret_review": rb"(?i)(?:api[_-]?key|password|secret|access[_-]?token)\s*[:=]\s*['\"][^'\"\r\n]{12,}['\"]",
}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    env = dict(os.environ, GIT_OPTIONAL_LOCKS="0")
    def git(*arguments):
        return subprocess.check_output(["git", "--no-optional-locks", "-C", str(root), *arguments], env=env)
    names = sorted(set(git("ls-files", "--cached", "--others", "--exclude-standard", "-z").decode().strip("\0").split("\0")))
    rows, matches, review = [], [], []
    def scan(scope, data):
        for name, pattern in PATTERNS.items():
            for hit in re.finditer(pattern, data):
                matches.append({"scope": scope, "pattern": name, "line": data[:hit.start()].count(b"\n") + 1,
                                "disposition": "REVIEW_REQUIRED; values redacted"})
    for name in names:
        path = root / name
        if not path.is_file():
            review.append({"path": name, "reason": "missing candidate"})
            continue
        data = path.read_bytes()
        rows.append({"path": name, "bytes": len(data), "sha256": hashlib.sha256(data).hexdigest()})
        scan("candidate:" + name, data)
        if path.suffix.lower() == ".docx":
            with zipfile.ZipFile(path) as archive:
                for member in archive.infolist():
                    if member.filename.endswith(".xml") and member.file_size < 10_000_000:
                        scan("docx:" + name + ":" + member.filename, archive.read(member))
        if path.suffix.lower() in {".pdf", ".docx", ".png", ".jpg"}:
            review.append({"path": name, "reason": "Owner must review publication rights and visible/private content; signature screening does not inspect rendered content"})
        if len(data) > 10_000_000 or path.suffix.lower() in {".pt", ".pth", ".safetensors", ".sqlite3", ".db", ".mp4", ".avi"}:
            review.append({"path": name, "reason": "Large or operational artifact requires explicit review"})
    objects = git("rev-list", "--objects", "--all").decode().splitlines()
    blobs = 0
    for line in objects:
        oid, _, name = line.partition(" ")
        if git("cat-file", "-t", oid).strip() != b"blob":
            continue
        scan("history:" + oid + ":" + name, git("cat-file", "blob", oid))
        blobs += 1
    result = {"root": str(root), "candidate": rows, "reachable_blobs_scanned": blobs,
              "history_commits": git("rev-list", "--all").decode().splitlines(),
              "pattern_findings": matches, "owner_review": review,
              "limits": "Finite signature/assignment patterns, not exhaustive entropy or forensic scanning. PDFs/media not rendered; no home repository content included. No automatic secret clearance or deletion."}
    with args.output.open("x", encoding="utf-8") as stream:
        json.dump(result, stream, indent=2)
    print(json.dumps({"candidate_files": len(rows), "history_blobs": blobs, "pattern_findings": len(matches), "owner_review": len(review)}))


if __name__ == "__main__":
    main()
