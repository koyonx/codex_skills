#!/usr/bin/env python3

import argparse
import json
import os
from collections import Counter
from pathlib import Path


def project_key(repo: Path) -> str:
    return str(repo.resolve()).replace("/", "_").lstrip("_")


def main() -> int:
    parser = argparse.ArgumentParser(description="Show summarized TODO marker counts.")
    parser.add_argument("--repo", default=".")
    args = parser.parse_args()

    repo = Path(args.repo).resolve()
    base_dir = Path(os.environ.get("TODO_TRACKER_HOME", str(Path.home() / ".codex" / "todo-tracker")))
    todo_file = base_dir / f"{project_key(repo)}.json"
    if not todo_file.is_file():
        print(f"No TODO scan found for {repo}")
        return 1

    entries = json.loads(todo_file.read_text(encoding="utf-8"))
    counts = Counter(entry["marker"] for entry in entries)
    print(f"Repo: {repo}")
    print(f"Total markers: {len(entries)}")
    for marker in ("FIXME", "TODO", "HACK", "XXX"):
        if counts[marker]:
            print(f"{marker}: {counts[marker]}")

    fixmes = [entry for entry in entries if entry["marker"] == "FIXME"][:10]
    if fixmes:
        print("")
        print("Top FIXME entries:")
        for entry in fixmes:
            print(f"- {entry['file']}:{entry['line']} {entry['content']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
