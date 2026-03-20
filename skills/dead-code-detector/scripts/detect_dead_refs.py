#!/usr/bin/env python3

import argparse
import json
import os
import re
import subprocess
from pathlib import Path
from typing import Optional

MAX_FILE_SIZE = 2 * 1024 * 1024

# Supported source extensions
SOURCE_EXTENSIONS = {
    "py", "js", "ts", "jsx", "tsx", "go", "rs", "rb",
    "java", "php", "c", "cpp", "h", "hpp", "cs", "swift", "kt",
}

# Language-specific definition patterns
DEFINITION_PATTERNS: list[re.Pattern] = [
    # Python: def foo, class Foo
    re.compile(r"(?:def|class)\s+([a-zA-Z_][a-zA-Z0-9_]*)"),
    # JS/TS: function foo, const foo, let foo, var foo, class Foo
    re.compile(r"(?:function|const|let|var|class)\s+([a-zA-Z_][a-zA-Z0-9_]*)"),
    # Go: func Foo, type Foo
    re.compile(r"(?:func|type)\s+([a-zA-Z_][a-zA-Z0-9_]*)"),
    # Rust: fn foo, struct Foo, enum Foo, trait Foo, impl Foo
    re.compile(r"(?:fn|struct|enum|trait|impl)\s+([a-zA-Z_][a-zA-Z0-9_]*)"),
    # Ruby: module Foo
    re.compile(r"(?:module)\s+([a-zA-Z_][a-zA-Z0-9_]*)"),
    # Java/C#/Swift/Kotlin: class/interface/struct
    re.compile(r"(?:interface|protocol|object)\s+([a-zA-Z_][a-zA-Z0-9_]*)"),
    # PHP: function foo, class Foo
    re.compile(r"(?:function)\s+([a-zA-Z_][a-zA-Z0-9_]*)"),
]

# Names too generic to report
IGNORED_NAMES = {
    "if", "else", "for", "while", "do", "in", "of", "to", "or", "and",
    "not", "is", "as", "at", "by", "on", "up", "it", "no", "so", "go",
    "self", "this", "true", "false", "None", "null", "undefined",
    "return", "break", "continue", "pass", "import", "from", "with",
    "i", "j", "k", "x", "y", "z", "n", "v", "e", "f", "s", "t", "_",
    "new", "get", "set", "put", "run", "add", "map", "key", "val",
}


def project_key(repo: Path) -> str:
    return str(repo.resolve()).replace("/", "_").lstrip("_")


def extract_names(text: str) -> set[str]:
    """Extract function/class/variable names from source text."""
    names: set[str] = set()
    for pattern in DEFINITION_PATTERNS:
        for match in pattern.finditer(text):
            name = match.group(1)
            if len(name) >= 2 and name not in IGNORED_NAMES:
                names.add(name)
    return names


def find_references(repo: Path, name: str, exclude_file: Path) -> list[str]:
    """Search repo for files referencing the given name (excluding the source file)."""
    include_args: list[str] = []
    for ext in SOURCE_EXTENSIONS:
        include_args.extend(["--include", f"*.{ext}"])

    try:
        result = subprocess.run(
            ["grep", "-Frl", *include_args, "--", name, str(repo)],
            capture_output=True,
            text=True,
            timeout=15,
        )
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return []

    if result.returncode != 0:
        return []

    files: list[str] = []
    exclude_str = str(exclude_file.resolve())
    for line in result.stdout.strip().splitlines():
        line = line.strip()
        if line and line != exclude_str:
            files.append(line)
        if len(files) >= 10:
            break
    return files


def analyze_file(repo: Path, filepath: Path) -> list[dict]:
    """Analyze a single file for dead references by comparing git diff."""
    resolved = filepath.resolve()
    if not resolved.is_file():
        return []
    if not str(resolved).startswith(str(repo)):
        return []

    ext = resolved.suffix.lstrip(".")
    if ext not in SOURCE_EXTENSIONS:
        return []

    # Get current file content
    try:
        current = resolved.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return []

    current_names = extract_names(current)

    # Get previous version via git
    env = os.environ.copy()
    env["GIT_CONFIG_NOSYSTEM"] = "1"
    env["GIT_TERMINAL_PROMPT"] = "0"

    try:
        rel_path = resolved.relative_to(repo)
    except ValueError:
        return []

    try:
        result = subprocess.run(
            ["git", "-C", str(repo), "show", f"HEAD:{rel_path}"],
            capture_output=True,
            text=True,
            timeout=15,
            env=env,
        )
        if result.returncode != 0:
            return []
        previous = result.stdout
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return []

    previous_names = extract_names(previous)

    # Names in previous but not in current = removed/renamed
    removed = previous_names - current_names

    if not removed:
        return []

    findings: list[dict] = []
    for name in sorted(removed):
        ref_files = find_references(repo, name, resolved)
        if ref_files:
            findings.append(
                {
                    "identifier": name,
                    "source_file": str(rel_path),
                    "referencing_files": ref_files,
                    "reference_count": len(ref_files),
                }
            )

    return findings


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Detect dead references after removing or renaming identifiers."
    )
    parser.add_argument("--repo", default=".")
    parser.add_argument("--files", nargs="*", required=True,
                        help="Files that were recently edited")
    args = parser.parse_args()

    repo = Path(args.repo).resolve()
    if not repo.is_dir():
        print(f"Repo not found: {repo}")
        return 1

    all_findings: list[dict] = []
    for file_arg in args.files:
        filepath = Path(file_arg)
        if not filepath.is_absolute():
            filepath = repo / filepath
        all_findings.extend(analyze_file(repo, filepath))

    # Save report
    output_dir = Path(
        os.environ.get(
            "DEAD_CODE_DETECTOR_HOME",
            str(Path.home() / ".codex" / "dead-code-detector"),
        )
    )
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / f"{project_key(repo)}.json"
    output_path.write_text(
        json.dumps(all_findings, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )

    if not all_findings:
        print("No dead references detected.")
        print(f"Report: {output_path}")
        return 0

    total_refs = sum(f["reference_count"] for f in all_findings)
    print(f"=== dead-code-detector: Potential Dead References ===")
    for finding in all_findings:
        print(
            f"  {finding['identifier']}: "
            f"{finding['reference_count']} file(s) still reference this "
            f"(removed from {finding['source_file']})"
        )
    print(f"\nTotal files with potential dead references: {total_refs}")
    print(f"Full report: {output_path}")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
