#!/usr/bin/env python3
"""Display known error patterns and their solutions for a project."""

import argparse
import json
import re
import sys
from pathlib import Path


def sanitize_text(text: str, max_len: int = 200) -> str:
    """Remove control characters and HTML tags, truncate."""
    text = re.sub(r"<[^>]+>", "", text)
    text = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]", "", text)
    return text[:max_len]


def project_name(repo_path: str) -> str:
    """Derive a safe project name from the repo path."""
    name = re.sub(r"[^a-zA-Z0-9/_.-]", "", repo_path).replace("/", "_").lstrip("_")
    return name or "default"


def main() -> None:
    parser = argparse.ArgumentParser(description="Show known error patterns")
    parser.add_argument("--repo", required=True, help="Repository root path")
    parser.add_argument("--top", type=int, default=10, help="Number of top entries to show")
    args = parser.parse_args()

    repo = Path(args.repo).resolve()
    if not repo.is_dir():
        print(f"Error: repository path does not exist: {args.repo}", file=sys.stderr)
        sys.exit(1)

    data_dir = Path.home() / ".codex" / "error-memory"
    proj = project_name(str(repo))
    db_file = data_dir / f"{proj}.json"

    if not db_file.is_file() or db_file.is_symlink():
        print("No error patterns recorded for this project.")
        sys.exit(0)

    try:
        entries = json.loads(db_file.read_text(encoding="utf-8"))
        if not isinstance(entries, list):
            entries = []
    except (json.JSONDecodeError, OSError):
        print("Error reading error database.", file=sys.stderr)
        sys.exit(1)

    if not entries:
        print("No error patterns recorded for this project.")
        sys.exit(0)

    # Sort by resolved_count descending
    entries.sort(key=lambda e: e.get("resolved_count", 0), reverse=True)
    top_entries = entries[:args.top]

    print(f"=== error-memory: Known Error Patterns ({len(entries)} total) ===")
    print()

    for entry in top_entries:
        error_key = sanitize_text(entry.get("error_key", ""), 100)
        solution = sanitize_text(entry.get("solution", ""), 200)
        count = entry.get("resolved_count", 0)
        last_seen = entry.get("last_seen", "unknown")

        print(f"- Pattern: {error_key}")
        print(f"  Fix: {solution}")
        print(f"  Count: {count}, Last seen: {last_seen}")
        print()

    print(f"=== End of error-memory ===")

    sys.exit(0)


if __name__ == "__main__":
    main()
