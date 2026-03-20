#!/usr/bin/env python3
"""Find and run tests related to given source files."""

import argparse
import os
import re
import subprocess
import sys
from pathlib import Path

TIMEOUT_SECONDS = 30


def sanitize_display(text: str) -> str:
    """Remove control characters and HTML tags from display text."""
    text = re.sub(r"<[^>]+>", "", text)
    text = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]", "", text)
    return text


def is_test_file(basename: str, file_path: str) -> bool:
    """Return True if the file itself is a test file."""
    test_patterns = ("test_", "_test.", ".test.", ".spec.", "_spec.")
    if any(basename.startswith(p) or p in basename for p in test_patterns):
        return True
    test_dirs = ("test/", "tests/", "__tests__/", "spec/")
    for td in test_dirs:
        if td in file_path:
            return True
    return False


def find_test_file(name: str, ext: str, src_dir: Path, repo: Path) -> Path | None:
    """Locate the test file for a given source file."""
    candidates = []

    if ext == ".py":
        candidates = [
            repo / "tests" / f"test_{name}.py",
            repo / "test" / f"test_{name}.py",
            src_dir / f"test_{name}.py",
            src_dir / f"{name}_test.py",
        ]
    elif ext in (".js", ".jsx"):
        candidates = [
            src_dir / f"{name}.test.js",
            src_dir / f"{name}.spec.js",
            src_dir / "__tests__" / f"{name}.test.js",
            repo / "test" / f"{name}.test.js",
        ]
    elif ext in (".ts", ".tsx"):
        candidates = [
            src_dir / f"{name}.test.ts",
            src_dir / f"{name}.test.tsx",
            src_dir / f"{name}.spec.ts",
            src_dir / "__tests__" / f"{name}.test.ts",
            repo / "test" / f"{name}.test.ts",
        ]
    elif ext == ".go":
        candidates = [
            src_dir / f"{name}_test.go",
        ]
    elif ext == ".rb":
        try:
            rel_dir = src_dir.relative_to(repo)
        except ValueError:
            rel_dir = Path(".")
        candidates = [
            repo / "spec" / f"{name}_spec.rb",
            repo / "spec" / rel_dir / f"{name}_spec.rb",
            repo / "test" / f"test_{name}.rb",
        ]

    for c in candidates:
        if c.is_file():
            resolved = c.resolve()
            if str(resolved).startswith(str(repo.resolve())):
                return resolved
    return None


def get_test_runner(ext: str, test_file: Path, src_file: Path, repo: Path) -> tuple[str, list[str]] | None:
    """Determine the test runner and arguments."""
    try:
        rel_test = str(test_file.relative_to(repo.resolve()))
    except ValueError:
        rel_test = str(test_file)

    if ext == ".py":
        if subprocess.run(["which", "pytest"], capture_output=True).returncode == 0:
            return "pytest", [rel_test, "-x", "--tb=short", "-q"]
        return "python", ["-m", "pytest", rel_test, "-x", "--tb=short", "-q"]

    elif ext in (".js", ".jsx"):
        if (repo / "package.json").is_file():
            return "npx", ["jest", rel_test, "--no-coverage"]

    elif ext in (".ts", ".tsx"):
        if (repo / "package.json").is_file():
            try:
                pkg = (repo / "package.json").read_text(encoding="utf-8")
                if '"vitest"' in pkg:
                    return "npx", ["vitest", "run", rel_test]
            except OSError:
                pass
            return "npx", ["jest", rel_test, "--no-coverage"]

    elif ext == ".go":
        try:
            pkg_dir = str(src_file.parent.relative_to(repo.resolve()))
        except ValueError:
            pkg_dir = "."
        return "go", ["test", f"./{pkg_dir}/...", "-v", "-count=1", "-run", "."]

    elif ext == ".rs":
        # For Rust, check for #[cfg(test)] in the source file
        try:
            content = src_file.read_text(encoding="utf-8", errors="ignore")
            if "#[cfg(test)]" in content:
                return "cargo", ["test", "--lib"]
        except OSError:
            pass

    elif ext == ".rb":
        gemfile = repo / "Gemfile"
        if gemfile.is_file():
            try:
                gf_content = gemfile.read_text(encoding="utf-8", errors="ignore")
                if "rspec" in gf_content:
                    return "bundle", ["exec", "rspec", rel_test]
            except OSError:
                pass
        return "ruby", ["-Itest", rel_test]

    return None


def run_test(runner: str, args: list[str], repo: Path) -> tuple[str, str, int]:
    """Execute a test command with timeout."""
    try:
        result = subprocess.run(
            [runner] + args,
            cwd=str(repo),
            capture_output=True,
            text=True,
            timeout=TIMEOUT_SECONDS,
        )
        return result.stdout, result.stderr, result.returncode
    except subprocess.TimeoutExpired:
        return "", "", 124
    except OSError as e:
        return "", str(e), 1


def process_file(file_path: str, repo: Path) -> None:
    """Process a single source file: find and run its tests."""
    src = Path(file_path).resolve()
    repo_resolved = repo.resolve()

    if not str(src).startswith(str(repo_resolved)):
        return
    if not src.is_file():
        return

    basename = src.name
    ext = src.suffix
    name = src.stem

    # Only process source code files
    valid_extensions = {".py", ".js", ".ts", ".jsx", ".tsx", ".go", ".rs", ".rb"}
    if ext not in valid_extensions:
        return

    # Validate name contains only safe characters
    if not re.fullmatch(r"[a-zA-Z0-9_-]+", name):
        return

    # Skip test files themselves
    if is_test_file(basename, file_path):
        return

    src_dir = src.parent

    # Special case: Rust with inline tests
    if ext == ".rs":
        runner_info = get_test_runner(ext, src, src, repo)
        if runner_info:
            runner, args = runner_info
            try:
                rel_src = str(src.relative_to(repo_resolved))
            except ValueError:
                rel_src = basename
            safe_src = sanitize_display(rel_src)
            print(f"=== test-auto-runner: Running tests ===")
            print(f"Source: {safe_src}")
            print(f"Test:   (inline #[cfg(test)])")
            stdout, stderr, exit_code = run_test(runner, args, repo)
            _print_result(exit_code, stdout + stderr, safe_src, "(inline)")
        return

    test_file = find_test_file(name, ext, src_dir, repo)
    if test_file is None:
        return

    runner_info = get_test_runner(ext, test_file, src, repo)
    if runner_info is None:
        return

    runner, args = runner_info

    try:
        rel_src = str(src.relative_to(repo_resolved))
        rel_test = str(test_file.relative_to(repo_resolved))
    except ValueError:
        rel_src = basename
        rel_test = str(test_file)

    safe_src = sanitize_display(rel_src)
    safe_test = sanitize_display(rel_test)

    print(f"=== test-auto-runner: Running tests ===")
    print(f"Source: {safe_src}")
    print(f"Test:   {safe_test}")

    stdout, stderr, exit_code = run_test(runner, args, repo)
    _print_result(exit_code, stdout + stderr, safe_src, safe_test)


def _print_result(exit_code: int, output: str, safe_src: str, safe_test: str) -> None:
    """Print formatted test results."""
    if exit_code == 124:
        result = f"TIMEOUT ({TIMEOUT_SECONDS}s)"
    elif exit_code == 0:
        result = "PASS"
    else:
        result = f"FAIL (exit code: {exit_code})"

    # Sanitize output
    safe_output = sanitize_display(output)
    lines = safe_output.split("\n")[:30]
    safe_output = "\n".join(lines)[:3000]

    print(f"Result: {result}")
    print()
    print(safe_output)
    print(f"=== End of test-auto-runner ===")
    print()


def main() -> None:
    parser = argparse.ArgumentParser(description="Find and run tests for source files")
    parser.add_argument("--repo", required=True, help="Repository root path")
    parser.add_argument("--files", nargs="+", required=True, help="Source files to find tests for")
    args = parser.parse_args()

    repo = Path(args.repo).resolve()
    if not repo.is_dir():
        print(f"Error: repository path does not exist: {args.repo}", file=sys.stderr)
        sys.exit(1)

    # Store state directory
    state_dir = Path.home() / ".codex" / "test-auto-runner"
    state_dir.mkdir(parents=True, exist_ok=True)

    for file_path in args.files:
        # Resolve relative paths against repo
        p = Path(file_path)
        if not p.is_absolute():
            p = repo / p
        process_file(str(p), repo)

    sys.exit(0)


if __name__ == "__main__":
    main()
