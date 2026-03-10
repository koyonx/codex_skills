#!/usr/bin/env python3

import argparse
import json
import os
import re
from pathlib import Path
from typing import Optional

MARKER_RE = re.compile(r"\b(TODO|FIXME|HACK|XXX)\b[: ]?(.*)", re.IGNORECASE)
MAX_FILE_SIZE = 1 * 1024 * 1024


def project_key(repo: Path) -> str:
    return str(repo.resolve()).replace("/", "_").lstrip("_")


def scan_file(path: Path) -> list[dict]:
    if not path.is_file() or path.stat().st_size > MAX_FILE_SIZE:
        return []
    try:
        content = path.read_text(encoding="utf-8", errors="replace").splitlines()
    except OSError:
        return []

    results = []
    for index, line in enumerate(content, start=1):
        match = MARKER_RE.search(line)
        if not match:
            continue
        results.append(
            {
                "file": str(path),
                "line": index,
                "marker": match.group(1).upper(),
                "content": match.group(2).strip()[:200],
            }
        )
    return results


def iter_files(repo: Path, explicit_files: Optional[list[str]]) -> list[Path]:
    if explicit_files:
        return [Path(file_path).resolve() for file_path in explicit_files]
    return [path for path in repo.rglob("*") if path.is_file()]


def main() -> int:
    parser = argparse.ArgumentParser(description="Scan a repo for TODO markers.")
    parser.add_argument("--repo", default=".")
    parser.add_argument("--files", nargs="*")
    args = parser.parse_args()

    repo = Path(args.repo).resolve()
    if not repo.is_dir():
        print(f"Repo not found: {repo}")
        return 1

    results = []
    for path in iter_files(repo, args.files):
        try:
            resolved = path.resolve()
        except OSError:
            continue
        if not str(resolved).startswith(str(repo)):
            continue
        results.extend(scan_file(resolved))

    output_dir = Path(os.environ.get("TODO_TRACKER_HOME", str(Path.home() / ".codex" / "todo-tracker")))
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / f"{project_key(repo)}.json"
    output_path.write_text(json.dumps(results, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(output_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
