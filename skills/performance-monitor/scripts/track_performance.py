#!/usr/bin/env python3
"""Performance Monitor — track command execution times and detect anomalies."""

import argparse
import hashlib
import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

STORAGE_DIR = Path.home() / ".codex" / "performance-monitor"
MAX_ENTRIES = 1000

TRACKED_PATTERNS = [
    r"\bnpm\s+run\s+build\b",
    r"\bnpm\s+test\b",
    r"\byarn\s+build\b",
    r"\byarn\s+test\b",
    r"\bpnpm\s+build\b",
    r"\bpnpm\s+test\b",
    r"\bmake\b",
    r"\bcmake\s+--build\b",
    r"\bcargo\s+build\b",
    r"\bcargo\s+test\b",
    r"\bgo\s+build\b",
    r"\bgo\s+test\b",
    r"\bpytest\b",
    r"\bjest\b",
    r"\bvitest\b",
    r"\bgradle\b",
    r"\bgradlew\b",
    r"\bmvn\b",
]

ANOMALY_THRESHOLD = 2.0
MIN_SAMPLES_FOR_ANOMALY = 3


def project_file(repo: str) -> Path:
    """Return the JSONL file path for a given project root."""
    h = hashlib.sha256(os.path.abspath(repo).encode()).hexdigest()
    return STORAGE_DIR / f"{h}.jsonl"


def ensure_storage():
    STORAGE_DIR.mkdir(parents=True, exist_ok=True)


def is_tracked_command(cmd: str) -> bool:
    """Check whether a command matches any tracked pattern."""
    for pattern in TRACKED_PATTERNS:
        if re.search(pattern, cmd):
            return True
    return False


def load_entries(filepath: Path) -> list[dict]:
    """Load all JSONL entries from a file."""
    if not filepath.exists():
        return []
    entries = []
    with open(filepath, "r") as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    entries.append(json.loads(line))
                except json.JSONDecodeError:
                    continue
    return entries


def save_entries(filepath: Path, entries: list[dict]):
    """Write entries back to JSONL, trimming to MAX_ENTRIES."""
    if len(entries) > MAX_ENTRIES:
        entries = entries[-MAX_ENTRIES:]
    with open(filepath, "w") as f:
        for entry in entries:
            f.write(json.dumps(entry) + "\n")


def record(repo: str, command: str, duration_ms: int, exit_code: int):
    """Record a command execution."""
    ensure_storage()

    if not is_tracked_command(command):
        print(f"Warning: '{command}' does not match a known tracked command pattern.")
        print("Recording anyway.")

    filepath = project_file(repo)
    entries = load_entries(filepath)

    entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "command": command,
        "duration_ms": duration_ms,
        "exit_code": exit_code,
        "project": os.path.abspath(repo),
    }
    entries.append(entry)
    save_entries(filepath, entries)

    print(f"Recorded: {command} — {duration_ms}ms (exit {exit_code})")

    # Inline anomaly check
    same_cmd = [e for e in entries[:-1] if e["command"] == command]
    if len(same_cmd) >= MIN_SAMPLES_FOR_ANOMALY:
        avg = sum(e["duration_ms"] for e in same_cmd) / len(same_cmd)
        if duration_ms > avg * ANOMALY_THRESHOLD:
            print(
                f"⚠ ANOMALY: {duration_ms}ms is {duration_ms / avg:.1f}x the "
                f"average ({avg:.0f}ms) for '{command}'."
            )


def trends(repo: str):
    """Show build time trends for a project."""
    filepath = project_file(repo)
    entries = load_entries(filepath)

    if not entries:
        print("No performance data recorded for this project.")
        return

    # Group by command
    by_command: dict[str, list[dict]] = {}
    for e in entries:
        by_command.setdefault(e["command"], []).append(e)

    print(f"Performance trends for: {os.path.abspath(repo)}")
    print(f"Total records: {len(entries)}")
    print("=" * 60)

    for cmd in sorted(by_command.keys()):
        runs = by_command[cmd]
        durations = [r["duration_ms"] for r in runs]
        avg = sum(durations) / len(durations)
        min_d = min(durations)
        max_d = max(durations)
        latest = durations[-1]
        failures = sum(1 for r in runs if r["exit_code"] != 0)

        print(f"\n  {cmd}")
        print(f"    Runs: {len(runs)}  |  Failures: {failures}")
        print(f"    Avg: {avg:.0f}ms  |  Min: {min_d}ms  |  Max: {max_d}ms")
        print(f"    Latest: {latest}ms", end="")

        if len(durations) >= 2:
            prev_avg = sum(durations[:-1]) / len(durations[:-1])
            if prev_avg > 0:
                change = ((latest - prev_avg) / prev_avg) * 100
                direction = "+" if change >= 0 else ""
                print(f"  ({direction}{change:.1f}% vs avg)")
            else:
                print()
        else:
            print()

    print()


def anomalies(repo: str):
    """Detect anomalous execution times for a project."""
    filepath = project_file(repo)
    entries = load_entries(filepath)

    if not entries:
        print("No performance data recorded for this project.")
        return

    by_command: dict[str, list[dict]] = {}
    for e in entries:
        by_command.setdefault(e["command"], []).append(e)

    found = False
    print(f"Anomaly report for: {os.path.abspath(repo)}")
    print(f"Threshold: {ANOMALY_THRESHOLD}x average duration")
    print("=" * 60)

    for cmd in sorted(by_command.keys()):
        runs = by_command[cmd]
        if len(runs) < MIN_SAMPLES_FOR_ANOMALY + 1:
            continue

        for i in range(MIN_SAMPLES_FOR_ANOMALY, len(runs)):
            prior = runs[:i]
            avg = sum(e["duration_ms"] for e in prior) / len(prior)
            current = runs[i]
            if avg > 0 and current["duration_ms"] > avg * ANOMALY_THRESHOLD:
                ratio = current["duration_ms"] / avg
                print(
                    f"\n  [{current['timestamp']}] {cmd}"
                    f"\n    Duration: {current['duration_ms']}ms "
                    f"({ratio:.1f}x avg of {avg:.0f}ms)"
                )
                found = True

    if not found:
        print("\nNo anomalies detected.")
    print()


def main():
    parser = argparse.ArgumentParser(
        description="Track command execution times and detect performance anomalies."
    )
    parser.add_argument(
        "--repo",
        required=True,
        help="Absolute path to the project root directory.",
    )
    parser.add_argument(
        "--record",
        action="store_true",
        help="Record a command execution.",
    )
    parser.add_argument(
        "--command",
        help="The command that was executed (used with --record).",
    )
    parser.add_argument(
        "--duration-ms",
        type=int,
        help="Execution duration in milliseconds (used with --record).",
    )
    parser.add_argument(
        "--exit-code",
        type=int,
        default=0,
        help="Exit code of the command (used with --record, default 0).",
    )
    parser.add_argument(
        "--trends",
        action="store_true",
        help="Show build time trends for the project.",
    )
    parser.add_argument(
        "--anomalies",
        action="store_true",
        help="Detect anomalous execution times.",
    )

    args = parser.parse_args()

    if args.record:
        if not args.command:
            parser.error("--command is required with --record")
        if args.duration_ms is None:
            parser.error("--duration-ms is required with --record")
        record(args.repo, args.command, args.duration_ms, args.exit_code)
    elif args.trends:
        trends(args.repo)
    elif args.anomalies:
        anomalies(args.repo)
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
