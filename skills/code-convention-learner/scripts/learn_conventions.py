#!/usr/bin/env python3
"""Analyze code for coding conventions or display learned conventions."""

import argparse
import json
import os
import re
import sys
from pathlib import Path

LANG_MAP = {
    ".js": "javascript",
    ".jsx": "javascript",
    ".ts": "typescript",
    ".tsx": "typescript",
    ".py": "python",
    ".go": "go",
    ".rs": "rust",
    ".rb": "ruby",
    ".java": "java",
}

MAX_FILE_SIZE = 1_048_576  # 1 MB
MAX_FILES_PER_LANG = 100
MIN_LINES = 5

VALID_LANGS = {"javascript", "typescript", "python", "go", "rust", "ruby", "java"}


def project_name(repo_path: str) -> str:
    """Derive a safe project name from the repo path."""
    name = re.sub(r"[^a-zA-Z0-9/_.-]", "", repo_path).replace("/", "_").lstrip("_")
    return name or "default"


def analyze_file(file_path: Path) -> dict:
    """Analyze a single file for convention signals."""
    stats = {
        "indent_spaces": 0,
        "indent_tabs": 0,
        "indent_size_2": 0,
        "indent_size_4": 0,
        "single_quotes": 0,
        "double_quotes": 0,
        "semicolons": 0,
        "no_semicolons": 0,
        "camel_case": 0,
        "snake_case": 0,
        "trailing_comma": 0,
        "no_trailing_comma": 0,
    }

    try:
        content = file_path.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return stats

    lines = content.split("\n")

    for line in lines:
        # Indentation
        if line.startswith("  "):
            stats["indent_spaces"] += 1
            if re.match(r"^    [^ ]", line):
                stats["indent_size_4"] += 1
            elif re.match(r"^  [^ ]", line):
                stats["indent_size_2"] += 1
        elif line.startswith("\t"):
            stats["indent_tabs"] += 1

    ext = file_path.suffix
    lang = LANG_MAP.get(ext, "")

    # Quote analysis (JS/TS/Python)
    if lang in ("javascript", "typescript", "python"):
        stats["single_quotes"] = content.count("'")
        stats["double_quotes"] = content.count('"')

    # Semicolon analysis (JS/TS)
    if lang in ("javascript", "typescript"):
        stats["semicolons"] = len(re.findall(r";\s*$", content, re.MULTILINE))
        stats["no_semicolons"] = len(re.findall(r"[^;{}\s]\s*$", content, re.MULTILINE))

    # Naming convention analysis
    if lang in ("javascript", "typescript", "python", "ruby"):
        stats["camel_case"] = len(re.findall(r"\b[a-z][a-z0-9]*[A-Z][a-zA-Z0-9]*\b", content))
        stats["snake_case"] = len(re.findall(r"\b[a-z][a-z0-9]*_[a-z][a-z0-9_]*\b", content))

    # Trailing comma analysis (JS/TS)
    if lang in ("javascript", "typescript"):
        stats["trailing_comma"] = len(re.findall(r",\s*$", content, re.MULTILINE))
        stats["no_trailing_comma"] = len(re.findall(r"[^,]\s*[}\]]\s*$", content, re.MULTILINE))

    return stats


def learn(repo: Path, conv_file: Path) -> None:
    """Scan source files and learn conventions."""
    # Load existing data
    existing: dict = {}
    if conv_file.is_file() and not conv_file.is_symlink():
        try:
            existing = json.loads(conv_file.read_text(encoding="utf-8"))
            if not isinstance(existing, dict):
                existing = {}
        except (json.JSONDecodeError, OSError):
            existing = {}

    files_by_lang: dict[str, list[Path]] = {}

    # Walk the repo for source files
    for root, dirs, files in os.walk(str(repo)):
        # Skip hidden directories and common non-source directories
        dirs[:] = [d for d in dirs if not d.startswith(".") and d not in (
            "node_modules", "vendor", "__pycache__", ".git", "dist", "build", "target",
        )]

        for fname in files:
            fpath = Path(root) / fname
            ext = fpath.suffix
            lang = LANG_MAP.get(ext)
            if not lang:
                continue

            # Skip symlinks
            if fpath.is_symlink():
                continue

            # File size check
            try:
                size = fpath.stat().st_size
            except OSError:
                continue
            if size > MAX_FILE_SIZE or size == 0:
                continue

            # Line count check
            try:
                line_count = sum(1 for _ in open(fpath, encoding="utf-8", errors="ignore"))
            except OSError:
                continue
            if line_count < MIN_LINES:
                continue

            if lang not in files_by_lang:
                files_by_lang[lang] = []

            # Check per-language limit
            current_analyzed = existing.get(lang, {}).get("files_analyzed", 0)
            if current_analyzed + len(files_by_lang[lang]) >= MAX_FILES_PER_LANG:
                continue

            files_by_lang[lang].append(fpath)

    total_analyzed = 0

    for lang, file_list in files_by_lang.items():
        for fpath in file_list:
            stats = analyze_file(fpath)

            if lang not in existing:
                existing[lang] = {"files_analyzed": 0}

            existing[lang]["files_analyzed"] = existing[lang].get("files_analyzed", 0) + 1
            for key, val in stats.items():
                existing[lang][key] = existing[lang].get(key, 0) + val

            total_analyzed += 1

    # Write
    tmp = conv_file.with_suffix(".tmp")
    tmp.write_text(json.dumps(existing, indent=2, ensure_ascii=False), encoding="utf-8")
    tmp.rename(conv_file)

    lang_count = sum(1 for v in existing.values() if isinstance(v, dict) and v.get("files_analyzed", 0) >= 5)
    total_files = sum(v.get("files_analyzed", 0) for v in existing.values() if isinstance(v, dict))

    print(f"Scanned {total_analyzed} new files.")
    print(f"Total files analyzed: {total_files}")
    print(f"Languages with enough data (>=5 files): {lang_count}")


def show(conv_file: Path) -> None:
    """Display learned conventions."""
    if not conv_file.is_file() or conv_file.is_symlink():
        print("No conventions learned yet. Run with --learn first.")
        sys.exit(0)

    try:
        data = json.loads(conv_file.read_text(encoding="utf-8"))
        if not isinstance(data, dict):
            data = {}
    except (json.JSONDecodeError, OSError):
        print("Error reading conventions file.", file=sys.stderr)
        sys.exit(1)

    has_output = False

    print("=== code-convention-learner: Project Conventions ===")

    for lang in sorted(data.keys()):
        if lang not in VALID_LANGS:
            continue
        info = data[lang]
        if not isinstance(info, dict):
            continue
        if info.get("files_analyzed", 0) < 5:
            continue

        has_output = True
        print(f"\n  {lang.upper()}:")

        # Indentation
        sp = info.get("indent_spaces", 0)
        tb = info.get("indent_tabs", 0)
        total_indent = sp + tb
        if total_indent > 0:
            if sp > tb:
                s2 = info.get("indent_size_2", 0)
                s4 = info.get("indent_size_4", 0)
                pct = sp * 100 // total_indent
                if (s2 + s4) > 0:
                    if s2 > s4:
                        print(f"    Indentation: 2 spaces ({pct}%)")
                    else:
                        print(f"    Indentation: 4 spaces ({pct}%)")
                else:
                    print(f"    Indentation: spaces ({pct}%)")
            else:
                pct = tb * 100 // total_indent
                print(f"    Indentation: tabs ({pct}%)")

        # Quotes
        sq = info.get("single_quotes", 0)
        dq = info.get("double_quotes", 0)
        total_q = sq + dq
        if total_q > 10:
            if sq > dq:
                print(f"    Quotes: single ({sq * 100 // total_q}%)")
            else:
                print(f"    Quotes: double ({dq * 100 // total_q}%)")

        # Semicolons
        sc = info.get("semicolons", 0)
        nsc = info.get("no_semicolons", 0)
        total_sc = sc + nsc
        if total_sc > 10:
            if sc > nsc:
                print(f"    Semicolons: yes ({sc * 100 // total_sc}%)")
            else:
                print(f"    Semicolons: no ({nsc * 100 // total_sc}%)")

        # Naming
        cc = info.get("camel_case", 0)
        snk = info.get("snake_case", 0)
        total_n = cc + snk
        if total_n > 10:
            if cc > snk:
                print(f"    Naming: camelCase ({cc * 100 // total_n}%)")
            else:
                print(f"    Naming: snake_case ({snk * 100 // total_n}%)")

        # Trailing commas
        tc = info.get("trailing_comma", 0)
        ntc = info.get("no_trailing_comma", 0)
        total_tc = tc + ntc
        if total_tc > 10:
            if tc > ntc:
                print(f"    Trailing commas: yes ({tc * 100 // total_tc}%)")
            else:
                print(f"    Trailing commas: no ({ntc * 100 // total_tc}%)")

        print(f"    Files analyzed: {info.get('files_analyzed', 0)}")

    if not has_output:
        print("  No languages with enough data yet (need >= 5 files per language).")

    print("\n=== End of code-convention-learner ===")


def main() -> None:
    parser = argparse.ArgumentParser(description="Learn or show project coding conventions")
    parser.add_argument("--repo", required=True, help="Repository root path")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--learn", action="store_true", help="Scan files and learn conventions")
    group.add_argument("--show", action="store_true", help="Display learned conventions")
    args = parser.parse_args()

    repo = Path(args.repo).resolve()
    if not repo.is_dir():
        print(f"Error: repository path does not exist: {args.repo}", file=sys.stderr)
        sys.exit(1)

    data_dir = Path.home() / ".codex" / "code-convention-learner"
    data_dir.mkdir(parents=True, exist_ok=True)
    os.chmod(str(data_dir), 0o700)

    proj = project_name(str(repo))
    conv_file = data_dir / f"{proj}.json"

    if args.learn:
        learn(repo, conv_file)
    elif args.show:
        show(conv_file)

    sys.exit(0)


if __name__ == "__main__":
    main()
