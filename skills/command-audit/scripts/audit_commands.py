#!/usr/bin/env python3
"""
Command audit script: log shell commands, detect dangerous patterns,
and review the audit log for a project.
"""

import argparse
import hashlib
import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, Tuple

# Maximum entries per project log file
MAX_LOG_ENTRIES = 1000

# Storage directory for audit logs
LOG_DIR = Path.home() / ".codex" / "command-audit"

# Dangerous command patterns (regex, case-insensitive)
DANGEROUS_PATTERNS = [
    # Destructive file operations
    (r"rm\s+-[a-zA-Z]*r[a-zA-Z]*f|rm\s+-[a-zA-Z]*f[a-zA-Z]*r", "Recursive force delete"),
    (r"rm\s+-rf\s+/", "Recursive force delete from root"),
    (r"rm\s+-rf\s+\*", "Recursive force delete wildcard"),
    (r"rm\s+-rf\s+~", "Recursive force delete home directory"),
    # Git destructive operations
    (r"git\s+push\s+.*--force", "Git force push"),
    (r"git\s+push\s+-f\b", "Git force push (-f)"),
    (r"git\s+reset\s+--hard", "Git hard reset"),
    (r"git\s+clean\s+-[a-zA-Z]*f", "Git clean with force"),
    (r"git\s+checkout\s+--\s+\.", "Git checkout discard all"),
    (r"git\s+branch\s+-D", "Git branch force delete"),
    # Database destructive operations
    (r"DROP\s+(TABLE|DATABASE|SCHEMA)", "SQL DROP statement"),
    (r"TRUNCATE\s+TABLE", "SQL TRUNCATE TABLE"),
    (r"DELETE\s+FROM", "SQL DELETE FROM"),
    # Unsafe permission changes
    (r"chmod\s+777", "chmod 777 (world-writable)"),
    (r"chown\s+-R", "Recursive chown"),
    # Disk/device operations
    (r"dd\s+.*of=/dev/", "dd write to device"),
    (r"mkfs\.", "Filesystem format"),
    # Process killing
    (r"kill\s+-9\s+-1", "Kill all processes"),
    (r"killall", "Kill all by name"),
    # Environment-breaking operations
    (r"pip\s+install\s+--break-system-packages", "pip break system packages"),
    (r"npm\s+cache\s+clean\s+--force", "npm force cache clean"),
]


def get_project_id(repo_path: str) -> str:
    """Generate a stable identifier for a project based on its path."""
    resolved = str(Path(repo_path).resolve())
    return hashlib.sha256(resolved.encode()).hexdigest()[:16]


def get_log_path(repo_path: str) -> Path:
    """Return the JSONL log file path for a given project."""
    project_id = get_project_id(repo_path)
    project_name = Path(repo_path).resolve().name
    safe_name = re.sub(r"[^a-zA-Z0-9_-]", "_", project_name)[:50]
    return LOG_DIR / f"{safe_name}_{project_id}.jsonl"


def ensure_log_dir() -> None:
    """Create the log directory if it does not exist."""
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    try:
        os.chmod(LOG_DIR, 0o700)
    except OSError:
        pass


def trim_log(log_path: Path) -> None:
    """Trim the log file to MAX_LOG_ENTRIES, removing oldest entries."""
    if not log_path.is_file():
        return
    try:
        with open(log_path, "r", encoding="utf-8") as f:
            lines = f.readlines()
        if len(lines) > MAX_LOG_ENTRIES:
            lines = lines[-MAX_LOG_ENTRIES:]
            with open(log_path, "w", encoding="utf-8") as f:
                f.writelines(lines)
    except OSError:
        pass


def log_command(repo_path: str, command: str) -> None:
    """Log a command execution to the project audit log."""
    ensure_log_dir()
    log_path = get_log_path(repo_path)

    entry = {
        "command": command,
        "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "cwd": str(Path(repo_path).resolve()),
        "status": "executed",
    }

    # Check if the command is dangerous and annotate
    match = check_dangerous_pattern(command)
    if match:
        entry["status"] = "warned"
        entry["matched_pattern"] = match[0]
        entry["pattern_description"] = match[1]

    try:
        with open(log_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    except OSError as e:
        print(f"Error writing log: {e}", file=sys.stderr)
        sys.exit(1)

    trim_log(log_path)

    if entry["status"] == "warned":
        print(f"WARNING: Dangerous command detected - {match[1]}")
        print(f"  Command: {command}")
    else:
        print(f"Logged: {command}")


def check_dangerous_pattern(command: str) -> Optional[Tuple[str, str]]:
    """Check if a command matches any dangerous pattern.

    Returns (pattern, description) if matched, None otherwise.
    """
    for pattern, description in DANGEROUS_PATTERNS:
        if re.search(pattern, command, re.IGNORECASE):
            return (pattern, description)
    return None


def check_dangerous(command: str) -> None:
    """Check a command against dangerous patterns and report."""
    match = check_dangerous_pattern(command)
    if match:
        print(f"DANGEROUS: {match[1]}")
        print(f"  Pattern: {match[0]}")
        print(f"  Command: {command}")
        sys.exit(1)
    else:
        print(f"OK: No dangerous patterns detected in: {command}")


def show_log(repo_path: str) -> None:
    """Display the audit log for a project."""
    log_path = get_log_path(repo_path)
    if not log_path.is_file():
        print(f"No audit log found for: {repo_path}")
        return

    try:
        with open(log_path, "r", encoding="utf-8") as f:
            lines = f.readlines()
    except OSError as e:
        print(f"Error reading log: {e}", file=sys.stderr)
        sys.exit(1)

    if not lines:
        print(f"Audit log is empty for: {repo_path}")
        return

    print(f"=== Command Audit Log: {Path(repo_path).resolve().name} ===")
    print(f"Log file: {log_path}")
    print(f"Entries: {len(lines)}")
    print()

    for line in lines:
        line = line.strip()
        if not line:
            continue
        try:
            entry = json.loads(line)
            status = entry.get("status", "unknown")
            ts = entry.get("timestamp", "?")
            cmd = entry.get("command", "?")
            marker = "[WARN]" if status == "warned" else "[OK]  "
            print(f"  {marker} {ts}  {cmd}")
            if status == "warned" and "pattern_description" in entry:
                print(f"         Reason: {entry['pattern_description']}")
        except json.JSONDecodeError:
            continue

    print()
    print("=== End of Audit Log ===")


def show_summary(repo_path: str) -> None:
    """Show a session summary for a project."""
    log_path = get_log_path(repo_path)
    if not log_path.is_file():
        print(f"No audit log found for: {repo_path}")
        return

    total = 0
    warned = 0

    try:
        with open(log_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    entry = json.loads(line)
                    total += 1
                    if entry.get("status") == "warned":
                        warned += 1
                except json.JSONDecodeError:
                    continue
    except OSError as e:
        print(f"Error reading log: {e}", file=sys.stderr)
        sys.exit(1)

    print(f"=== Command Audit Summary: {Path(repo_path).resolve().name} ===")
    print(f"  Total commands logged: {total}")
    print(f"  Dangerous warnings:    {warned}")
    print(f"  Safe commands:         {total - warned}")
    if total > 0:
        pct = (warned / total) * 100
        print(f"  Warning rate:          {pct:.1f}%")
    print("=== End of Summary ===")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Audit shell commands: log, check, and review."
    )
    parser.add_argument(
        "--repo",
        type=str,
        required=True,
        help="Project root path.",
    )
    parser.add_argument(
        "--log-command",
        type=str,
        default=None,
        help="Log a command execution.",
    )
    parser.add_argument(
        "--check-dangerous",
        type=str,
        default=None,
        help="Check if a command matches dangerous patterns.",
    )
    parser.add_argument(
        "--show-log",
        action="store_true",
        default=False,
        help="Display the audit log for this project.",
    )
    parser.add_argument(
        "--summary",
        action="store_true",
        default=False,
        help="Show session summary (total commands, warned count).",
    )

    args = parser.parse_args()

    actions = sum([
        args.log_command is not None,
        args.check_dangerous is not None,
        args.show_log,
        args.summary,
    ])

    if actions == 0:
        parser.error("No action specified. Use --log-command, --check-dangerous, --show-log, or --summary.")
    if actions > 1:
        parser.error("Only one action can be specified at a time.")

    if args.log_command is not None:
        log_command(args.repo, args.log_command)
    elif args.check_dangerous is not None:
        check_dangerous(args.check_dangerous)
    elif args.show_log:
        show_log(args.repo)
    elif args.summary:
        show_summary(args.repo)

    sys.exit(0)


if __name__ == "__main__":
    main()
