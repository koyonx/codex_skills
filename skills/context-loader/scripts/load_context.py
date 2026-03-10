#!/usr/bin/env python3

import argparse
import glob
import json
import sys
from pathlib import Path

MAX_FILE_SIZE = 5 * 1024 * 1024
MAX_TOTAL_SIZE = 20 * 1024 * 1024
CONFIG_FILENAME = ".context-loader.json"


def validate_path(file_path: Path, project_root: Path) -> bool:
    try:
        resolved = file_path.resolve()
        return resolved.is_relative_to(project_root.resolve())
    except (OSError, ValueError):
        return False


def load_config(project_root: Path) -> dict:
    config_path = project_root / CONFIG_FILENAME
    with open(config_path, "r", encoding="utf-8") as handle:
        config = json.load(handle)
    if not isinstance(config, dict):
        raise ValueError("Config root must be a JSON object.")
    return config


def resolve_files(config: dict, project_root: Path) -> list[Path]:
    files: list[Path] = []
    seen: set[str] = set()

    for file_entry in config.get("files", []):
        if not isinstance(file_entry, str):
            continue
        candidate = project_root / file_entry
        if validate_path(candidate, project_root):
            resolved = candidate.resolve()
            if resolved.is_file() and str(resolved) not in seen:
                seen.add(str(resolved))
                files.append(resolved)

    for pattern in config.get("globs", []):
        if not isinstance(pattern, str):
            continue
        if ".." in pattern or pattern.startswith("/") or pattern.startswith("~"):
            continue
        for match in sorted(glob.glob(str(project_root / pattern), recursive=True)):
            resolved = Path(match).resolve()
            if resolved.is_file() and validate_path(resolved, project_root) and str(resolved) not in seen:
                seen.add(str(resolved))
                files.append(resolved)

    return files


def print_paths(files: list[Path], project_root: Path) -> int:
    for file_path in files:
        try:
            rel_path = file_path.relative_to(project_root.resolve())
        except ValueError:
            rel_path = file_path
        print(rel_path)
    return 0


def print_contents(files: list[Path], project_root: Path) -> int:
    total_size = 0
    loaded = 0
    for file_path in files:
        file_size = file_path.stat().st_size
        if file_size > MAX_FILE_SIZE:
            print(f"Skipping oversized file: {file_path}", file=sys.stderr)
            continue
        if total_size + file_size > MAX_TOTAL_SIZE:
            print("Stopping at total size limit.", file=sys.stderr)
            break
        rel_path = file_path.relative_to(project_root.resolve())
        print(f"===== {rel_path} =====")
        print(file_path.read_text(encoding="utf-8", errors="replace"))
        print("")
        total_size += file_size
        loaded += 1
    print(f"Loaded {loaded} file(s), {total_size} bytes total.", file=sys.stderr)
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Load files listed by .context-loader.json")
    parser.add_argument("--project-root", default=".")
    parser.add_argument("--paths-only", action="store_true")
    parser.add_argument("--print-content", action="store_true")
    args = parser.parse_args()

    project_root = Path(args.project_root).resolve()
    if not project_root.is_dir():
        print(f"Project root not found: {project_root}", file=sys.stderr)
        return 1

    config_path = project_root / CONFIG_FILENAME
    if not config_path.is_file():
        print(f"Missing config: {config_path}", file=sys.stderr)
        return 1

    config = load_config(project_root)
    files = resolve_files(config, project_root)
    if not files:
        print("No files matched.", file=sys.stderr)
        return 0

    if args.paths_only or not args.print_content:
        return print_paths(files, project_root)
    return print_contents(files, project_root)


if __name__ == "__main__":
    raise SystemExit(main())
