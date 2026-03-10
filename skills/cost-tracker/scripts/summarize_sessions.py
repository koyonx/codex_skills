#!/usr/bin/env python3

import argparse
import json
import sqlite3
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Optional

CODEX_HOME = Path.home() / ".codex"
STATE_DB = CODEX_HOME / "state_5.sqlite"


def load_threads(project_root: Optional[Path], since_days: Optional[int], limit: Optional[int]) -> list[dict]:
    connection = sqlite3.connect(STATE_DB)
    connection.row_factory = sqlite3.Row
    query = """
        SELECT id, rollout_path, cwd, title, created_at, updated_at, tokens_used
        FROM threads
        WHERE archived = 0
        ORDER BY updated_at DESC
    """
    rows = [dict(row) for row in connection.execute(query)]
    connection.close()

    if project_root is not None:
        root_str = str(project_root.resolve())
        rows = [row for row in rows if row["cwd"] == root_str or row["cwd"].startswith(root_str + "/")]

    if since_days is not None:
        cutoff = datetime.now(timezone.utc) - timedelta(days=since_days)
        rows = [row for row in rows if datetime.fromtimestamp(row["updated_at"], timezone.utc) >= cutoff]

    if limit is not None:
        rows = rows[:limit]

    return rows


def parse_rollout(path: Path) -> dict:
    usage = {
        "input_tokens": 0,
        "cached_input_tokens": 0,
        "output_tokens": 0,
        "reasoning_output_tokens": 0,
        "total_tokens": 0,
    }
    if not path.is_file():
        return usage

    with open(path, "r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            try:
                event = json.loads(line)
            except json.JSONDecodeError:
                continue
            payload = event.get("payload", {})
            if event.get("type") != "event_msg" or payload.get("type") != "token_count":
                continue
            total_usage = payload.get("info", {}).get("total_token_usage", {})
            if total_usage:
                usage = {
                    "input_tokens": int(total_usage.get("input_tokens", 0)),
                    "cached_input_tokens": int(total_usage.get("cached_input_tokens", 0)),
                    "output_tokens": int(total_usage.get("output_tokens", 0)),
                    "reasoning_output_tokens": int(total_usage.get("reasoning_output_tokens", 0)),
                    "total_tokens": int(total_usage.get("total_tokens", 0)),
                }
    return usage


def main() -> int:
    parser = argparse.ArgumentParser(description="Summarize Codex session usage.")
    parser.add_argument("--project-root", default=None)
    parser.add_argument("--since-days", type=int, default=None)
    parser.add_argument("--limit", type=int, default=20)
    args = parser.parse_args()

    if not STATE_DB.is_file():
        print(f"Missing Codex state database: {STATE_DB}")
        return 1

    project_root = Path(args.project_root).resolve() if args.project_root else None
    rows = load_threads(project_root, args.since_days, args.limit)
    if not rows:
        print("No matching Codex sessions found.")
        return 0

    totals = {
        "input_tokens": 0,
        "cached_input_tokens": 0,
        "output_tokens": 0,
        "reasoning_output_tokens": 0,
        "total_tokens": 0,
    }

    print(f"Sessions: {len(rows)}")
    if project_root:
        print(f"Project root: {project_root}")
    print("")

    for row in rows:
        rollout_path = Path(row["rollout_path"])
        usage = parse_rollout(rollout_path)
        for key in totals:
            totals[key] += usage[key]
        updated_at = datetime.fromtimestamp(row["updated_at"], timezone.utc).astimezone().strftime("%Y-%m-%d %H:%M")
        print(f"- {row['id']} | {updated_at} | total={usage['total_tokens']} | input={usage['input_tokens']} | cached={usage['cached_input_tokens']} | output={usage['output_tokens']} | cwd={row['cwd']}")

    print("")
    print("Totals:")
    print(f"  input_tokens={totals['input_tokens']}")
    print(f"  cached_input_tokens={totals['cached_input_tokens']}")
    print(f"  output_tokens={totals['output_tokens']}")
    print(f"  reasoning_output_tokens={totals['reasoning_output_tokens']}")
    print(f"  total_tokens={totals['total_tokens']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
