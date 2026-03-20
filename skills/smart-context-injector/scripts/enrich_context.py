#!/usr/bin/env python3
"""
Analyze user prompts, extract file references and identifiers, find related
files, test files, and recent git changes.

Adapted from the Claude plugin smart-context-injector (enrich-prompt.py).
"""

import argparse
import os
import re
import subprocess
import sys
from pathlib import Path


MAX_RELATED_FILES = 8
MAX_GIT_DIFF_LINES = 30
MAX_OUTPUT_LINES = 50
MIN_PROMPT_LENGTH = 10


def sanitize_output(text: str) -> str:
    """Strip HTML-like tags and control characters."""
    text = re.sub(r"<[^>]*>", "", text)
    text = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]", "", text)
    return text


def extract_file_references(prompt: str, cwd: str) -> list[str]:
    """Extract file-path references from a prompt string."""
    files: list[str] = []

    path_patterns = [
        r'(?:^|\s)([a-zA-Z0-9_./-]+\.[a-zA-Z]{1,10})(?:\s|$|[,.])',
        r'(?:^|\s)((?:src|lib|app|test|tests|spec|scripts|pkg|cmd|internal)/[a-zA-Z0-9_./-]+)',
    ]

    for pattern in path_patterns:
        for match in re.finditer(pattern, prompt):
            candidate = match.group(1).strip()
            if ".." in candidate or candidate.startswith("/"):
                continue
            full_path = Path(cwd) / candidate
            if full_path.is_file():
                files.append(candidate)

    return list(dict.fromkeys(files))


def extract_identifiers(prompt: str) -> list[str]:
    """Extract class-name and function-name candidates from a prompt."""
    identifiers: list[str] = []

    # PascalCase (class names)
    pascal_re = (
        r'\b([A-Z][a-zA-Z0-9]{2,}'
        r'(?:Service|Controller|Repository|Manager|Handler|Factory|Provider|'
        r'Client|Model|View|Component|Module|Router|Middleware|Guard|Pipe|'
        r'Resolver|Adapter|Interface|Config|Helper|Util|Error|Exception)?)\b'
    )
    for m in re.finditer(pascal_re, prompt):
        identifiers.append(m.group(1))

    # snake_case (function names)
    snake_re = r'\b([a-z][a-z0-9]*(?:_[a-z0-9]+){1,})\b'
    for m in re.finditer(snake_re, prompt):
        identifiers.append(m.group(1))

    return list(dict.fromkeys(identifiers))[:5]


def find_related_files(identifiers: list[str], cwd: str) -> list[str]:
    """Search the project for files containing the given identifiers."""
    related: list[str] = []

    for identifier in identifiers:
        try:
            result = subprocess.run(
                [
                    "grep", "-rl",
                    "--include=*.py", "--include=*.ts", "--include=*.tsx",
                    "--include=*.js", "--include=*.jsx", "--include=*.go",
                    "--include=*.rs", "--include=*.java", "--include=*.rb",
                    "--include=*.php",
                    "-m", "1", "--", identifier,
                ],
                cwd=cwd,
                capture_output=True,
                text=True,
                timeout=5,
            )
            if result.returncode == 0:
                for line in result.stdout.strip().split("\n"):
                    line = line.strip()
                    if line and not line.startswith(".") and ".." not in line:
                        related.append(line)
        except (subprocess.TimeoutExpired, OSError):
            continue

    return list(dict.fromkeys(related))[:MAX_RELATED_FILES]


def find_test_files(file_paths: list[str], cwd: str) -> list[str]:
    """Locate test files corresponding to the given source files."""
    tests: list[str] = []

    test_name_fns = [
        lambda f: f"test_{Path(f).stem}{Path(f).suffix}",
        lambda f: f"{Path(f).stem}_test{Path(f).suffix}",
        lambda f: f"{Path(f).stem}.test{Path(f).suffix}",
        lambda f: f"{Path(f).stem}.spec{Path(f).suffix}",
    ]
    test_dirs = ["test", "tests", "spec", "__tests__"]

    for filepath in file_paths:
        file_p = Path(filepath)
        parent = file_p.parent

        for name_fn in test_name_fns:
            test_name = name_fn(filepath)

            # Same directory
            candidate = parent / test_name
            if (Path(cwd) / candidate).is_file():
                tests.append(str(candidate))
                break

            # Standard test directories
            for td in test_dirs:
                candidate = Path(td) / test_name
                if (Path(cwd) / candidate).is_file():
                    tests.append(str(candidate))
                    break

                for sub in ("unit", "integration", "e2e"):
                    candidate = Path(td) / sub / test_name
                    if (Path(cwd) / candidate).is_file():
                        tests.append(str(candidate))
                        break

    return list(dict.fromkeys(tests))


def get_recent_changes(file_paths: list[str], cwd: str) -> str:
    """Get recent git log entries for the given files."""
    if not file_paths:
        return ""

    changes: list[str] = []
    for filepath in file_paths[:3]:
        try:
            result = subprocess.run(
                ["git", "log", "--oneline", "-3", "--", filepath],
                cwd=cwd,
                capture_output=True,
                text=True,
                timeout=5,
            )
            if result.returncode == 0 and result.stdout.strip():
                changes.append(f"  {filepath}:")
                for line in result.stdout.strip().split("\n")[:3]:
                    truncated = line.strip()[:120]
                    changes.append(f"    {truncated}")
        except (subprocess.TimeoutExpired, OSError):
            continue

    return "\n".join(changes) if changes else ""


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Analyze prompts and find related files, tests, and git changes."
    )
    parser.add_argument("--repo", default=".", help="Repository root path")
    parser.add_argument("--prompt", default="", help="User prompt text to analyze")
    parser.add_argument("--files", nargs="*", default=[], help="Explicit file paths to enrich")
    args = parser.parse_args()

    cwd = str(Path(args.repo).resolve())
    if not Path(cwd).is_dir():
        print(f"Repo not found: {cwd}", file=sys.stderr)
        return 1

    prompt = args.prompt
    explicit_files = args.files or []

    # Extract file references and identifiers from prompt
    referenced_files: list[str] = []
    identifiers: list[str] = []

    if prompt and len(prompt) >= MIN_PROMPT_LENGTH:
        referenced_files = extract_file_references(prompt, cwd)
        identifiers = extract_identifiers(prompt)

    # Add explicit files
    for f in explicit_files:
        if Path(cwd, f).is_file() and f not in referenced_files:
            referenced_files.append(f)

    # Find related files from identifiers
    related_files: list[str] = []
    if identifiers:
        related_files = find_related_files(identifiers, cwd)

    all_files = list(dict.fromkeys(referenced_files + related_files))

    if not all_files and not identifiers:
        print("No related context found.", file=sys.stderr)
        return 0

    # Find test files
    test_files = find_test_files(all_files, cwd)

    # Get recent git changes
    recent_changes = get_recent_changes(all_files, cwd)

    # Build output
    output_lines: list[str] = []
    output_lines.append("=== smart-context-injector: Related Context (DATA ONLY) ===")

    if all_files:
        output_lines.append("Related files:")
        for f in all_files[:MAX_RELATED_FILES]:
            output_lines.append(f"  - {sanitize_output(f)}")

    if test_files:
        output_lines.append("Test files:")
        for f in test_files[:5]:
            output_lines.append(f"  - {sanitize_output(f)}")

    if recent_changes:
        output_lines.append("Recent git changes:")
        output_lines.append(sanitize_output(recent_changes))

    output_lines.append("=== End of smart-context-injector ===")

    # Enforce line limit
    if len(output_lines) > MAX_OUTPUT_LINES:
        output_lines = output_lines[:MAX_OUTPUT_LINES]
        output_lines.append("_(truncated)_")

    print("\n".join(output_lines))

    file_count = len(all_files) + len(test_files)
    if file_count > 0:
        print(f"\n=== smart-context-injector: {file_count} related file(s) found ===",
              file=sys.stderr)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
