#!/usr/bin/env python3
"""File Complexity Guard -- check source files for complexity violations."""

import argparse
import os
import re
import subprocess
import sys

# ---------------------------------------------------------------------------
# Defaults
# ---------------------------------------------------------------------------

DEFAULT_MAX_LINES = 300
DEFAULT_MAX_FUNC_LINES = 50
DEFAULT_MAX_NESTING = 5
MAX_FILE_SIZE = 2 * 1024 * 1024  # 2 MB

# Extensions we consider source code (mapped to language for function patterns)
LANG_MAP = {
    ".py": "python",
    ".js": "javascript",
    ".jsx": "javascript",
    ".ts": "typescript",
    ".tsx": "typescript",
    ".go": "go",
    ".rs": "rust",
    ".rb": "ruby",
    ".java": "java",
    ".php": "php",
    ".c": "c",
    ".h": "c",
    ".cpp": "cpp",
    ".hpp": "cpp",
    ".cs": "csharp",
    ".swift": "swift",
    ".kt": "kotlin",
}

CONFIG_EXTENSIONS = {
    ".json", ".yaml", ".yml", ".toml", ".ini", ".cfg", ".xml",
    ".lock", ".env", ".properties",
}

CONFIG_FILENAMES = {
    "Makefile", "Dockerfile", "Vagrantfile", "Procfile",
    "docker-compose.yml", "docker-compose.yaml",
    ".gitignore", ".dockerignore", ".editorconfig",
}

# ---------------------------------------------------------------------------
# Function-definition patterns (per language)
# ---------------------------------------------------------------------------

FUNC_PATTERNS = {
    "python": re.compile(
        r"^[ \t]*(async\s+)?def\s+\w+", re.MULTILINE
    ),
    "javascript": re.compile(
        r"^[ \t]*(export\s+)?(default\s+)?(async\s+)?function[\s*]+\w+|"
        r"^[ \t]*(const|let|var)\s+\w+\s*=\s*(async\s+)?\(|"
        r"^[ \t]*\w+\s*\([^)]*\)\s*\{",
        re.MULTILINE,
    ),
    "typescript": re.compile(
        r"^[ \t]*(export\s+)?(default\s+)?(async\s+)?function[\s*]+\w+|"
        r"^[ \t]*(const|let|var)\s+\w+\s*=\s*(async\s+)?\(|"
        r"^[ \t]*(public|private|protected|static|async|override)?\s*\w+\s*\([^)]*\)\s*[:{]",
        re.MULTILINE,
    ),
    "go": re.compile(
        r"^func\s+(\(\s*\w+\s+\*?\w+\s*\)\s*)?\w+", re.MULTILINE
    ),
    "rust": re.compile(
        r"^[ \t]*(pub\s+)?(async\s+)?fn\s+\w+", re.MULTILINE
    ),
    "ruby": re.compile(
        r"^[ \t]*def\s+\w+", re.MULTILINE
    ),
    "java": re.compile(
        r"^[ \t]*(public|private|protected|static|final|abstract|synchronized|native)[\s\w<>\[\],]*\s+\w+\s*\(",
        re.MULTILINE,
    ),
    "php": re.compile(
        r"^[ \t]*(public|private|protected|static)?\s*function\s+\w+", re.MULTILINE
    ),
    "c": re.compile(
        r"^[a-zA-Z_][\w\s\*]+\w+\s*\([^;]*\)\s*\{", re.MULTILINE
    ),
    "cpp": re.compile(
        r"^[ \t]*(virtual\s+|static\s+|inline\s+)*[\w:<>\*&\s]+\w+\s*\([^;]*\)\s*(const\s*)?\{",
        re.MULTILINE,
    ),
    "csharp": re.compile(
        r"^[ \t]*(public|private|protected|internal|static|async|override|virtual|abstract)[\s\w<>\[\]]*\s+\w+\s*\(",
        re.MULTILINE,
    ),
    "swift": re.compile(
        r"^[ \t]*(public|private|internal|open|fileprivate|static|class|override|mutating)?\s*func\s+\w+",
        re.MULTILINE,
    ),
    "kotlin": re.compile(
        r"^[ \t]*(public|private|protected|internal|open|override|suspend)?\s*fun\s+\w+",
        re.MULTILINE,
    ),
}

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def is_test_file(filename: str) -> bool:
    base = os.path.basename(filename)
    if base.startswith("test_"):
        return True
    name_no_ext, _ = os.path.splitext(base)
    if name_no_ext.endswith("_test"):
        return True
    # *.test.* or *.spec.*
    parts = base.split(".")
    if len(parts) >= 3:
        if parts[-2] in ("test", "spec"):
            return True
    return False


def is_config_file(filename: str) -> bool:
    base = os.path.basename(filename)
    if base in CONFIG_FILENAMES:
        return True
    _, ext = os.path.splitext(base)
    return ext in CONFIG_EXTENSIONS


def get_git_modified_files(repo: str):
    """Return list of files modified according to git (staged + unstaged + untracked)."""
    try:
        result = subprocess.run(
            ["git", "diff", "--name-only", "HEAD"],
            capture_output=True, text=True, cwd=repo,
        )
        files = [f.strip() for f in result.stdout.splitlines() if f.strip()]
        # Also include untracked files
        result2 = subprocess.run(
            ["git", "ls-files", "--others", "--exclude-standard"],
            capture_output=True, text=True, cwd=repo,
        )
        files += [f.strip() for f in result2.stdout.splitlines() if f.strip()]
        return list(set(files))
    except Exception:
        return []


def measure_functions(source: str, lang: str):
    """Yield (func_name, start_line, length) for each function detected."""
    pattern = FUNC_PATTERNS.get(lang)
    if pattern is None:
        return

    lines = source.splitlines()
    func_starts = []
    for match in pattern.finditer(source):
        lineno = source[:match.start()].count("\n")
        # Extract a readable name from the match
        text = match.group().strip()
        func_starts.append((lineno, text))

    for idx, (start, name) in enumerate(func_starts):
        if idx + 1 < len(func_starts):
            end = func_starts[idx + 1][0]
        else:
            end = len(lines)
        length = end - start
        yield name, start + 1, length


def measure_max_nesting(source: str, lang: str) -> int:
    """Estimate maximum nesting depth using indentation analysis."""
    lines = source.splitlines()
    max_depth = 0

    # For brace-based languages, count braces
    brace_languages = {
        "javascript", "typescript", "go", "rust", "java", "php",
        "c", "cpp", "csharp", "swift", "kotlin",
    }

    if lang in brace_languages:
        depth = 0
        for line in lines:
            stripped = line.strip()
            if not stripped or stripped.startswith("//") or stripped.startswith("/*"):
                continue
            depth += stripped.count("{") - stripped.count("}")
            if depth > max_depth:
                max_depth = depth
    elif lang == "python":
        # Use indentation (spaces/tabs)
        for line in lines:
            stripped = line.lstrip()
            if not stripped or stripped.startswith("#"):
                continue
            indent = len(line) - len(stripped)
            # Estimate depth: assume 4-space indent, fall back to tab=1
            if "\t" in line[:indent]:
                depth = line[:indent].count("\t")
            else:
                depth = indent // 4
            if depth > max_depth:
                max_depth = depth
    elif lang == "ruby":
        depth = 0
        block_open = re.compile(r"\b(def|class|module|do|if|unless|while|until|for|case|begin)\b")
        block_close = re.compile(r"\bend\b")
        for line in lines:
            stripped = line.strip()
            if not stripped or stripped.startswith("#"):
                continue
            opens = len(block_open.findall(stripped))
            closes = len(block_close.findall(stripped))
            depth += opens - closes
            if depth > max_depth:
                max_depth = depth
    else:
        # Fallback: indentation-based
        for line in lines:
            stripped = line.lstrip()
            if not stripped:
                continue
            indent = len(line) - len(stripped)
            depth = indent // 4
            if depth > max_depth:
                max_depth = depth

    return max_depth


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def check_file(filepath: str, max_lines: int, max_func_lines: int, max_nesting: int):
    """Check a single file and return list of warning strings."""
    warnings = []

    # Skip large files
    try:
        size = os.path.getsize(filepath)
    except OSError:
        return warnings
    if size > MAX_FILE_SIZE:
        return warnings

    _, ext = os.path.splitext(filepath)
    lang = LANG_MAP.get(ext)
    if lang is None:
        return warnings

    try:
        with open(filepath, "r", encoding="utf-8", errors="replace") as fh:
            source = fh.read()
    except OSError:
        return warnings

    lines = source.splitlines()
    line_count = len(lines)

    # 1. File line count
    if line_count > max_lines:
        warnings.append(
            f"  [lines] {line_count} lines (threshold: {max_lines})"
        )

    # 2. Function / method length
    for func_name, start_line, length in measure_functions(source, lang):
        if length > max_func_lines:
            short_name = func_name[:80].replace("\n", " ")
            warnings.append(
                f"  [func-length] line {start_line}: {length} lines -- {short_name} (threshold: {max_func_lines})"
            )

    # 3. Nesting depth
    depth = measure_max_nesting(source, lang)
    if depth > max_nesting:
        warnings.append(
            f"  [nesting] max depth {depth} (threshold: {max_nesting})"
        )

    return warnings


def main():
    parser = argparse.ArgumentParser(
        description="File Complexity Guard -- check files for complexity violations."
    )
    parser.add_argument(
        "--repo", required=True,
        help="Path to the project root directory.",
    )
    parser.add_argument(
        "--files", nargs="*", default=None,
        help="Specific files to check. Defaults to git-modified files.",
    )
    parser.add_argument(
        "--max-lines", type=int,
        default=int(os.environ.get("COMPLEXITY_MAX_LINES", DEFAULT_MAX_LINES)),
        help=f"File line threshold (default: {DEFAULT_MAX_LINES}, env: COMPLEXITY_MAX_LINES).",
    )
    parser.add_argument(
        "--max-func-lines", type=int,
        default=int(os.environ.get("COMPLEXITY_MAX_FUNC_LINES", DEFAULT_MAX_FUNC_LINES)),
        help=f"Function length threshold (default: {DEFAULT_MAX_FUNC_LINES}, env: COMPLEXITY_MAX_FUNC_LINES).",
    )
    parser.add_argument(
        "--max-nesting", type=int,
        default=int(os.environ.get("COMPLEXITY_MAX_NESTING", DEFAULT_MAX_NESTING)),
        help=f"Nesting depth threshold (default: {DEFAULT_MAX_NESTING}, env: COMPLEXITY_MAX_NESTING).",
    )

    args = parser.parse_args()
    repo = os.path.abspath(args.repo)

    if not os.path.isdir(repo):
        print(f"Error: repo path does not exist: {repo}", file=sys.stderr)
        sys.exit(1)

    # Determine files to check
    if args.files:
        files = []
        for f in args.files:
            path = f if os.path.isabs(f) else os.path.join(repo, f)
            if os.path.isfile(path):
                files.append(path)
    else:
        rel_files = get_git_modified_files(repo)
        files = [os.path.join(repo, f) for f in rel_files if os.path.isfile(os.path.join(repo, f))]

    # Filter out test and config files
    files = [
        f for f in files
        if not is_test_file(f) and not is_config_file(f)
    ]

    if not files:
        print("No files to check.")
        sys.exit(0)

    total_warnings = 0
    for filepath in sorted(files):
        warnings = check_file(
            filepath, args.max_lines, args.max_func_lines, args.max_nesting,
        )
        if warnings:
            rel = os.path.relpath(filepath, repo)
            print(f"{rel}:")
            for w in warnings:
                print(w)
            print()
            total_warnings += len(warnings)

    if total_warnings:
        print(f"Total: {total_warnings} warning(s) in {len(files)} file(s) checked.")
        sys.exit(1)
    else:
        print(f"No complexity warnings. {len(files)} file(s) checked.")
        sys.exit(0)


if __name__ == "__main__":
    main()
