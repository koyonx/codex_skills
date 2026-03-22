#!/usr/bin/env python3
"""Session Handoff: generate, load, and list session handoff notes for Codex."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Optional

STORE_DIR = Path.home() / ".codex" / "session-handoff"
CLEANUP_DAYS = 30
MAX_LIST = 10


def _run_git(repo: str, *args: str) -> str:
    """Run a git command in the given repo and return stripped stdout."""
    try:
        result = subprocess.run(
            ["git", "-C", repo] + list(args),
            capture_output=True,
            text=True,
            timeout=10,
        )
        return result.stdout.strip()
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return ""


def _project_key(repo: str) -> str:
    """Return a stable key derived from the absolute repo path."""
    return os.path.realpath(repo).replace("/", "_").strip("_")


def _cleanup_old_notes() -> None:
    """Remove handoff notes older than CLEANUP_DAYS."""
    if not STORE_DIR.exists():
        return
    cutoff = datetime.now(timezone.utc) - timedelta(days=CLEANUP_DAYS)
    for f in STORE_DIR.glob("*.json"):
        try:
            data = json.loads(f.read_text())
            ts = datetime.fromisoformat(data.get("timestamp", ""))
            if ts < cutoff:
                f.unlink()
        except (json.JSONDecodeError, ValueError, OSError):
            pass


def _notes_for_project(repo: str) -> list[Path]:
    """Return note paths for the given project, newest first."""
    if not STORE_DIR.exists():
        return []
    key = _project_key(repo)
    notes: list[tuple[str, Path]] = []
    for f in STORE_DIR.glob("*.json"):
        try:
            data = json.loads(f.read_text())
            if data.get("project_key") == key:
                notes.append((data.get("timestamp", ""), f))
        except (json.JSONDecodeError, OSError):
            pass
    notes.sort(key=lambda x: x[0], reverse=True)
    return [p for _, p in notes]


# ── Actions ──────────────────────────────────────────────────────────────


def action_generate(repo: str) -> None:
    """Generate a handoff note capturing the current git state."""
    STORE_DIR.mkdir(parents=True, exist_ok=True)
    _cleanup_old_notes()

    branch = _run_git(repo, "rev-parse", "--abbrev-ref", "HEAD")
    status = _run_git(repo, "status", "--short")
    recent_commits = _run_git(repo, "log", "--oneline", "-10")

    session_id = uuid.uuid4().hex[:12]
    note = {
        "session_id": session_id,
        "project_path": os.path.realpath(repo),
        "project_key": _project_key(repo),
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "git_branch": branch,
        "git_status": status,
        "recent_commits": recent_commits,
    }

    out_path = STORE_DIR / f"{session_id}.json"
    out_path.write_text(json.dumps(note, indent=2) + "\n")
    print(json.dumps(note, indent=2))


def action_load(repo: str, session_id: str | None, latest: bool) -> None:
    """Load a handoff note by session-id or latest."""
    _cleanup_old_notes()

    if latest:
        notes = _notes_for_project(repo)
        if not notes:
            print("No handoff notes found for this project.", file=sys.stderr)
            sys.exit(1)
        data = json.loads(notes[0].read_text())
    elif session_id:
        target = STORE_DIR / f"{session_id}.json"
        if not target.exists():
            print(f"Session {session_id} not found.", file=sys.stderr)
            sys.exit(1)
        data = json.loads(target.read_text())
    else:
        print("Specify --session-id <id> or --latest.", file=sys.stderr)
        sys.exit(1)

    print(json.dumps(data, indent=2))


def action_list(repo: str) -> None:
    """List available handoff notes for the project."""
    _cleanup_old_notes()
    notes = _notes_for_project(repo)
    if not notes:
        print("No handoff notes found for this project.")
        return

    for note_path in notes[:MAX_LIST]:
        data = json.loads(note_path.read_text())
        ts = data.get("timestamp", "unknown")
        sid = data.get("session_id", "unknown")
        branch = data.get("git_branch", "unknown")
        print(f"  {sid}  {ts}  branch:{branch}")


# ── CLI ──────────────────────────────────────────────────────────────────


def main() -> None:
    parser = argparse.ArgumentParser(description="Session Handoff for Codex")
    parser.add_argument("--repo", required=True, help="Project root path")
    parser.add_argument(
        "--action",
        required=True,
        choices=["generate", "load", "list"],
        help="Action to perform",
    )
    parser.add_argument("--session-id", default=None, help="Session ID to load")
    parser.add_argument(
        "--latest", action="store_true", help="Load the latest handoff note"
    )
    args = parser.parse_args()

    if not os.path.isdir(args.repo):
        print(f"Error: {args.repo} is not a valid directory.", file=sys.stderr)
        sys.exit(1)

    if args.action == "generate":
        action_generate(args.repo)
    elif args.action == "load":
        action_load(args.repo, args.session_id, args.latest)
    elif args.action == "list":
        action_list(args.repo)


if __name__ == "__main__":
    main()
