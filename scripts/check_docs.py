"""Check local Markdown link targets, excluding code examples and external URLs."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
from urllib.parse import unquote, urlsplit


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    files = list(root.glob("*.md")) + list((root / "docs").rglob("*.md")) + list((root / "notebooks").glob("*.md"))
    errors, checked = [], 0
    for path in files:
        text = re.sub(r"```[^\n]*\n.*?```", "", path.read_text(encoding="utf-8-sig"), flags=re.S)
        targets = re.findall(r"\[[^\]]*\]\(([^)]+)\)", text)
        targets += re.findall(r"(?m)^\[[^\]]+\]:\s*(\S+)", text)
        for target in targets:
            if target.startswith("<") and ">" in target:
                target = target[1:target.index(">")]
            else:
                target = target.split(' "', 1)[0]
            url = urlsplit(target)
            if url.scheme or target.startswith(("#", "//")):
                continue
            checked += 1
            destination = path.parent / unquote(url.path)
            if not destination.exists():
                errors.append({"file": path.relative_to(root).as_posix(), "target": target})
    result = {"markdown_files": len(files), "local_targets": checked, "missing": errors,
              "scope": "Local target existence only; fragments, external URLs and fenced examples are not validated"}
    with args.output.open("x", encoding="utf-8") as stream:
        json.dump(result, stream, indent=2)
    print(json.dumps(result))
    return int(bool(errors))


if __name__ == "__main__":
    raise SystemExit(main())
