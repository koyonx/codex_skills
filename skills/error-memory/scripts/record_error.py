#!/usr/bin/env python3
"""Record an error pattern with its command and solution into the per-project error database."""

import argparse
import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

MAX_ENTRIES = 200


def sanitize_text(text: str, max_len: int = 500) -> str:
    """Remove control characters and HTML tags, truncate."""
    text = re.sub(r"<[^>]+>", "", text)
    text = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]", "", text)
    return text[:max_len]


def generate_error_key(command: str, error: str) -> str:
    """Generate a key from the command base and error message head."""
    cmd_base = re.sub(r"[^a-zA-Z0-9_.-]", "", command.split()[0]) if command.split() else "unknown"
    err_head = re.sub(r"[^a-zA-Z0-9 _.:/-]", "", error.split("\n")[0][:50])
    return f"{cmd_base}:{err_head}"


def project_name(repo_path: str) -> str:
    """Derive a safe project name from the repo path."""
    name = re.sub(r"[^a-zA-Z0-9/_.-]", "", repo_path).replace("/", "_").lstrip("_")
    return name or "default"


def main() -> None:
    parser = argparse.ArgumentParser(description="Record an error and its solution")
    parser.add_argument("--repo", required=True, help="Repository root path")
    parser.add_argument("--error", required=True, help="Error message")
    parser.add_argument("--command", required=True, help="Command that produced the error")
    parser.add_argument("--solution", required=True, help="Command that fixed the error")
    args = parser.parse_args()

    repo = Path(args.repo).resolve()
    if not repo.is_dir():
        print(f"Error: repository path does not exist: {args.repo}", file=sys.stderr)
        sys.exit(1)

    data_dir = Path.home() / ".codex" / "error-memory"
    data_dir.mkdir(parents=True, exist_ok=True)
    os.chmod(str(data_dir), 0o700)

    proj = project_name(str(repo))
    db_file = data_dir / f"{proj}.json"

    safe_cmd = sanitize_text(args.command)
    safe_error = sanitize_text(args.error)
    safe_solution = sanitize_text(args.solution)
    error_key = generate_error_key(args.command, args.error)
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    # Load existing database
    entries: list[dict] = []
    if db_file.is_file() and not db_file.is_symlink():
        try:
            entries = json.loads(db_file.read_text(encoding="utf-8"))
            if not isinstance(entries, list):
                entries = []
        except (json.JSONDecodeError, OSError):
            entries = []

    # Check if this error key already exists
    found = False
    for entry in entries:
        if entry.get("error_key") == error_key:
            entry["solution"] = safe_solution
            entry["resolved_count"] = entry.get("resolved_count", 0) + 1
            entry["last_seen"] = timestamp
            found = True
            break

    if not found:
        entries.append({
            "error_key": error_key,
            "error_command": safe_cmd,
            "error_message": safe_error,
            "solution": safe_solution,
            "resolved_count": 1,
            "first_seen": timestamp,
            "last_seen": timestamp,
        })

    # Cap at MAX_ENTRIES
    if len(entries) > MAX_ENTRIES:
        entries = entries[-MAX_ENTRIES:]

    # Write atomically
    tmp_file = db_file.with_suffix(".tmp")
    tmp_file.write_text(json.dumps(entries, indent=2, ensure_ascii=False), encoding="utf-8")
    tmp_file.rename(db_file)

    print(f"Recorded: {error_key}")
    print(f"Solution: {safe_solution}")
    print(f"Total entries: {len(entries)}")

    sys.exit(0)


if __name__ == "__main__":
    main()
