#!/usr/bin/env python3
"""Analyze import/dependency graphs to find files affected by changes."""

import argparse
import re
import subprocess
import sys
from pathlib import Path

MAX_IMPACT_FILES = 10
MAX_OUTPUT_LINES = 40


def sanitize_output(text: str) -> str:
    """Remove control characters and HTML tags."""
    text = re.sub(r"<[^>]+>", "", text)
    text = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]", "", text)
    return text


def sanitize_path(text: str) -> str:
    """Keep only safe path characters."""
    return re.sub(r"[^a-zA-Z0-9_./-]", "", text)[:200]


def validate_path(file_path: str, cwd: str) -> str | None:
    """Validate file path is under cwd and exists."""
    if not file_path or not cwd:
        return None
    try:
        resolved = Path(file_path).resolve()
        resolved_cwd = Path(cwd).resolve()
        if not resolved.is_relative_to(resolved_cwd):
            return None
        if not resolved.is_file():
            return None
        return str(resolved)
    except (OSError, ValueError):
        return None


def get_module_name(file_path: str, cwd: str) -> str:
    """Derive the module/import path from a file path."""
    try:
        rel = Path(file_path).resolve().relative_to(Path(cwd).resolve())
    except ValueError:
        return ""
    return str(rel.with_suffix(""))


def extract_exports(file_path: str) -> list[str]:
    """Extract exported names from a source file."""
    exports = []
    try:
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read(100_000)
    except OSError:
        return exports

    suffix = Path(file_path).suffix

    if suffix in (".ts", ".tsx", ".js", ".jsx", ".mjs"):
        patterns = [
            r'export\s+(?:default\s+)?(?:function|class|const|let|var|type|interface|enum)\s+(\w+)',
            r'export\s*\{\s*([^}]+)\}',
        ]
        for pattern in patterns:
            for match in re.finditer(pattern, content):
                if "{" in match.group(0):
                    names = match.group(1).split(",")
                    for name in names:
                        name = name.strip().split(" as ")[0].strip()
                        if name:
                            exports.append(name)
                else:
                    exports.append(match.group(1))

    elif suffix == ".py":
        for match in re.finditer(r'^(?:class|def)\s+(\w+)', content, re.MULTILINE):
            exports.append(match.group(1))
        all_match = re.search(r'__all__\s*=\s*\[([^\]]+)\]', content)
        if all_match:
            for name in re.findall(r'["\'](\w+)["\']', all_match.group(1)):
                exports.append(name)

    elif suffix == ".go":
        for match in re.finditer(r'^(?:func|type|var|const)\s+([A-Z]\w*)', content, re.MULTILINE):
            exports.append(match.group(1))

    elif suffix in (".java", ".kt"):
        for match in re.finditer(r'public\s+(?:class|interface|enum)\s+(\w+)', content):
            exports.append(match.group(1))

    elif suffix == ".rs":
        for match in re.finditer(r'pub\s+(?:fn|struct|enum|trait|type|const|static|mod)\s+(\w+)', content):
            exports.append(match.group(1))

    elif suffix == ".rb":
        for match in re.finditer(r'^(?:class|module|def)\s+(\w+)', content, re.MULTILINE):
            exports.append(match.group(1))

    # Deduplicate and validate
    valid = []
    seen = set()
    for name in exports:
        if re.fullmatch(r'[a-zA-Z_][a-zA-Z0-9_]*', name) and name not in seen:
            valid.append(name)
            seen.add(name)
    return valid[:20]


def find_importers(file_path: str, exports: list[str], cwd: str) -> list[str]:
    """Find files that import the changed file."""
    importers = set()
    module_name = get_module_name(file_path, cwd)
    stem = Path(file_path).stem

    search_terms = [stem]
    if module_name:
        search_terms.append(module_name.replace("/", "."))
        search_terms.append(module_name.replace("/", "::"))
        search_terms.append(module_name)

    for export_name in exports[:5]:
        if len(export_name) > 3:
            search_terms.append(export_name)

    # Deduplicate
    search_terms = list(dict.fromkeys(search_terms))

    include_flags = []
    for ext in ("py", "ts", "tsx", "js", "jsx", "go", "rs", "java", "rb", "kt"):
        include_flags.extend(["--include", f"*.{ext}"])

    for term in search_terms:
        try:
            result = subprocess.run(
                ["grep", "-Frl"] + include_flags + ["--", term],
                cwd=cwd,
                capture_output=True,
                text=True,
                timeout=10,
            )
            if result.returncode == 0:
                for line in result.stdout.strip().split("\n"):
                    line = line.strip()
                    if not line:
                        continue
                    full = str((Path(cwd) / line).resolve())
                    resolved_target = str(Path(file_path).resolve())
                    if full != resolved_target and ".." not in line:
                        importers.add(line)
        except (subprocess.TimeoutExpired, OSError):
            continue

    return sorted(importers)[:MAX_IMPACT_FILES]


def find_test_file(file_path: str, cwd: str) -> str | None:
    """Find the corresponding test file."""
    stem = Path(file_path).stem
    suffix = Path(file_path).suffix

    test_candidates = [
        f"test_{stem}{suffix}",
        f"{stem}_test{suffix}",
        f"{stem}.test{suffix}",
        f"{stem}.spec{suffix}",
    ]

    test_dirs = ["test", "tests", "spec", "__tests__", "."]
    try:
        parent = str(Path(file_path).resolve().relative_to(Path(cwd).resolve()).parent)
    except ValueError:
        parent = "."

    for td in test_dirs:
        for candidate in test_candidates:
            for search_dir in [Path(cwd) / td, Path(cwd) / parent / td, Path(cwd) / parent]:
                path = search_dir / candidate
                if path.is_file():
                    try:
                        return str(path.relative_to(Path(cwd)))
                    except ValueError:
                        pass

    return None


def find_type_definitions(file_path: str, cwd: str) -> str | None:
    """Find corresponding type definition file (.d.ts)."""
    suffix = Path(file_path).suffix
    if suffix in (".ts", ".tsx", ".js", ".jsx"):
        dts = Path(file_path).with_suffix(".d.ts")
        if dts.is_file():
            try:
                return str(dts.relative_to(Path(cwd)))
            except ValueError:
                pass
    return None


def process_file(file_path: str, cwd: str) -> list[str]:
    """Analyze impact for a single changed file."""
    resolved = validate_path(file_path, cwd)
    if not resolved:
        return []

    suffix = Path(resolved).suffix
    code_extensions = {
        ".py", ".ts", ".tsx", ".js", ".jsx", ".mjs",
        ".go", ".rs", ".java", ".kt", ".rb", ".php",
        ".c", ".cpp", ".h", ".hpp", ".cs", ".swift",
    }
    if suffix not in code_extensions:
        return []

    exports = extract_exports(resolved)
    importers = find_importers(resolved, exports, cwd)
    test_file = find_test_file(resolved, cwd)
    type_def = find_type_definitions(resolved, cwd)

    if not importers and not test_file and not type_def:
        return []

    output = []
    try:
        rel_path = sanitize_output(str(Path(resolved).relative_to(Path(cwd).resolve())))
    except ValueError:
        rel_path = sanitize_output(Path(resolved).name)

    output.append(f"Changed: {rel_path}")

    if importers:
        output.append(f"Affected files ({len(importers)}):")
        for imp in importers:
            output.append(f"  - {sanitize_path(imp)}")
        output.append("Consider reviewing these files for breaking changes.")

    if test_file:
        output.append(f"Test file: {sanitize_output(test_file)}")
        output.append("Consider running tests to verify changes.")

    if type_def:
        output.append(f"Type definition: {sanitize_output(type_def)}")
        output.append("Type definitions may need updating.")

    return output


def main() -> None:
    parser = argparse.ArgumentParser(description="Analyze change impact via import graphs")
    parser.add_argument("--repo", required=True, help="Repository root path")
    parser.add_argument("--files", nargs="+", required=True, help="Changed files to analyze")
    args = parser.parse_args()

    cwd = str(Path(args.repo).resolve())
    if not Path(cwd).is_dir():
        print(f"Error: repository path does not exist: {args.repo}", file=sys.stderr)
        sys.exit(1)

    # Store state directory
    state_dir = Path.home() / ".codex" / "change-impact-analyzer"
    state_dir.mkdir(parents=True, exist_ok=True)

    all_output: list[str] = []

    for file_path in args.files:
        p = Path(file_path)
        if not p.is_absolute():
            p = Path(cwd) / p
        result = process_file(str(p), cwd)
        all_output.extend(result)

    if not all_output:
        print("No impact detected for the given files.")
        sys.exit(0)

    print("=== change-impact-analyzer ===")
    for line in all_output[:MAX_OUTPUT_LINES]:
        print(line)
    print("=== End of change-impact-analyzer ===")

    # Summary to stderr
    impact_count = sum(1 for l in all_output if l.startswith("  - "))
    print(f"\n=== change-impact-analyzer: {impact_count} related file(s) ===", file=sys.stderr)

    sys.exit(0)


if __name__ == "__main__":
    main()
