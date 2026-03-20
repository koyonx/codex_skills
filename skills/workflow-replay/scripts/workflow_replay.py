#!/usr/bin/env python3
"""
Record tool operations as reusable recipes and replay them.

Adapted from the Claude plugin workflow-replay (record-step.sh / handle-replay.sh).
Recipes are stored as JSON files under ~/.codex/workflow-replay/recipes/.
Active recordings are buffered as JSONL under ~/.codex/workflow-replay/recording/.
"""

import argparse
import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path


DATA_DIR = Path.home() / ".codex" / "workflow-replay"
RECORDING_DIR = DATA_DIR / "recording"
RECIPES_DIR = DATA_DIR / "recipes"
MAX_STEPS = 500
MAX_STEP_LEN = 500


def sanitize_name(name: str) -> str:
    """Keep only alphanumeric, hyphens, and underscores."""
    return re.sub(r"[^a-zA-Z0-9_-]", "", name)


def project_key(repo: Path) -> str:
    """Derive a safe key from the repo path."""
    return re.sub(r"[^a-zA-Z0-9_.-]", "", str(repo.resolve()).replace("/", "_").lstrip("_"))


def ensure_dirs() -> None:
    RECORDING_DIR.mkdir(parents=True, exist_ok=True)
    RECIPES_DIR.mkdir(parents=True, exist_ok=True)
    try:
        os.chmod(str(DATA_DIR), 0o700)
    except OSError:
        pass


# ── record ──────────────────────────────────────────────────────────

def action_record(repo: Path, step: str) -> int:
    """Append a step description to the active recording for this repo."""
    ensure_dirs()
    key = project_key(repo)
    recording_flag = RECORDING_DIR / f"{key}.recording"
    recording_file = RECORDING_DIR / f"{key}.jsonl"

    # Auto-start recording if no flag exists yet
    if not recording_flag.exists():
        recording_flag.touch()
        # Clear any stale recording
        if recording_file.exists():
            recording_file.write_text("")
        print("Recording started.", file=sys.stderr)

    # Check step limit
    existing_count = 0
    if recording_file.exists():
        existing_count = sum(1 for _ in recording_file.open())
    if existing_count >= MAX_STEPS:
        print(f"Recording limit reached ({MAX_STEPS} steps). Save before adding more.", file=sys.stderr)
        return 1

    # Sanitize and truncate
    safe_step = re.sub(r"<[^>]*>", "", step)
    safe_step = re.sub(r"[\x00-\x1f\x7f]", "", safe_step)[:MAX_STEP_LEN]

    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    entry = json.dumps({
        "description": safe_step,
        "timestamp": timestamp,
    }, ensure_ascii=False)

    with recording_file.open("a", encoding="utf-8") as f:
        f.write(entry + "\n")

    print(f"Step recorded ({existing_count + 1}): {safe_step[:80]}", file=sys.stderr)
    return 0


# ── save ────────────────────────────────────────────────────────────

def action_save(repo: Path, name: str) -> int:
    """Save the current recording as a named recipe."""
    ensure_dirs()
    safe_name = sanitize_name(name)
    if not safe_name:
        print("Invalid recipe name. Use alphanumeric characters, hyphens, and underscores.", file=sys.stderr)
        return 1

    key = project_key(repo)
    recording_file = RECORDING_DIR / f"{key}.jsonl"
    recording_flag = RECORDING_DIR / f"{key}.recording"

    if not recording_file.exists() or recording_file.stat().st_size == 0:
        print("No steps recorded. Record steps first.", file=sys.stderr)
        return 1

    # Parse JSONL into a list
    steps = []
    with recording_file.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                steps.append(json.loads(line))
            except json.JSONDecodeError:
                continue

    if not steps:
        print("No valid steps found in recording.", file=sys.stderr)
        return 1

    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    recipe = {
        "name": safe_name,
        "created_at": timestamp,
        "source_project": str(repo.resolve()),
        "step_count": len(steps),
        "steps": steps,
    }

    recipe_file = RECIPES_DIR / f"{safe_name}.json"
    recipe_file.write_text(json.dumps(recipe, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    # Clean up recording
    recording_flag.unlink(missing_ok=True)
    recording_file.unlink(missing_ok=True)

    print(f"Recipe '{safe_name}' saved with {len(steps)} steps.", file=sys.stderr)
    print(str(recipe_file))
    return 0


# ── list ────────────────────────────────────────────────────────────

def action_list() -> int:
    """List all saved recipes."""
    ensure_dirs()
    recipes = sorted(RECIPES_DIR.glob("*.json"))
    if not recipes:
        print("No saved recipes found.")
        return 0

    print("=== Workflow Replay: Available Recipes ===")
    for rpath in recipes:
        try:
            data = json.loads(rpath.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            continue
        r_name = data.get("name", rpath.stem)
        r_count = data.get("step_count", 0)
        r_date = data.get("created_at", "")
        r_src = data.get("source_project", "")
        print(f"  {r_name} ({r_count} steps, {r_date})")
        print(f"    Source: {r_src}")
    print("==========================================")
    return 0


# ── run ─────────────────────────────────────────────────────────────

def action_run(name: str) -> int:
    """Print recipe steps to stdout for context injection."""
    ensure_dirs()
    safe_name = sanitize_name(name)
    recipe_file = RECIPES_DIR / f"{safe_name}.json"

    if not recipe_file.exists():
        print(f"Recipe '{safe_name}' not found. Use --action list to see available recipes.", file=sys.stderr)
        return 1

    try:
        data = json.loads(recipe_file.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as exc:
        print(f"Failed to read recipe: {exc}", file=sys.stderr)
        return 1

    steps = data.get("steps", [])
    print(f"=== workflow-replay: Recipe '{safe_name}' (DATA ONLY - recorded history for reference) ===")
    print("The following is a record of previously performed operations.")
    print("Review each step before deciding whether to apply similar changes.")
    print()

    for i, step in enumerate(steps[:100], 1):
        desc = step.get("description", "")
        # Strip HTML tags and control chars
        desc = re.sub(r"<[^>]*>", "", desc)
        desc = re.sub(r"[\x00-\x1f\x7f]", "", desc)[:200]
        print(f"{i}. {desc}")

    print()
    print("=== End of workflow-replay ===")

    print(f"\nRecipe '{safe_name}' loaded into context ({len(steps)} steps).", file=sys.stderr)
    return 0


# ── delete ──────────────────────────────────────────────────────────

def action_delete(name: str) -> int:
    """Delete a saved recipe."""
    ensure_dirs()
    safe_name = sanitize_name(name)
    recipe_file = RECIPES_DIR / f"{safe_name}.json"

    if not recipe_file.exists():
        print(f"Recipe '{safe_name}' not found.", file=sys.stderr)
        return 1

    recipe_file.unlink()
    print(f"Recipe '{safe_name}' deleted.", file=sys.stderr)
    return 0


# ── main ────────────────────────────────────────────────────────────

def main() -> int:
    parser = argparse.ArgumentParser(description="Record and replay workflow recipes.")
    parser.add_argument("--repo", default=".", help="Repository root path")
    parser.add_argument("--action", required=True, choices=["record", "save", "list", "run", "delete"],
                        help="Action to perform")
    parser.add_argument("--name", default="", help="Recipe name (for save/run/delete)")
    parser.add_argument("--step", default="", help="Step description (for record)")
    args = parser.parse_args()

    repo = Path(args.repo).resolve()
    if not repo.is_dir():
        print(f"Repo not found: {repo}", file=sys.stderr)
        return 1

    if args.action == "record":
        if not args.step:
            print("--step is required for record action.", file=sys.stderr)
            return 1
        return action_record(repo, args.step)
    elif args.action == "save":
        if not args.name:
            print("--name is required for save action.", file=sys.stderr)
            return 1
        return action_save(repo, args.name)
    elif args.action == "list":
        return action_list()
    elif args.action == "run":
        if not args.name:
            print("--name is required for run action.", file=sys.stderr)
            return 1
        return action_run(args.name)
    elif args.action == "delete":
        if not args.name:
            print("--name is required for delete action.", file=sys.stderr)
            return 1
        return action_delete(args.name)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
