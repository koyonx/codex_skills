#!/usr/bin/env python3

import argparse
import json
import os
import re
from pathlib import Path
from typing import Optional

MAX_FILE_SIZE = 2 * 1024 * 1024

# Extensions to skip (docs, binary, fonts, images)
SKIP_EXTENSIONS = {
    "md", "txt", "lock", "sum", "png", "jpg", "jpeg", "gif", "svg",
    "ico", "woff", "woff2", "ttf", "eot", "pdf",
}

# Test/mock filename patterns (prefix or suffix)
TEST_BASENAME_PATTERNS = re.compile(
    r"^test_.*|.*_test\.\w+$|.*\.test\.\w+$|.*\.spec\.\w+$|.*_spec\.\w+$"
    r"|.*\.mock\.\w+$|.*\.fake\.\w+$|.*\.stub\.\w+$"
    r"|.*\.example$|.*\.sample$|.*\.template$",
    re.IGNORECASE,
)

# Test/mock directory components
TEST_DIR_PARTS = {
    "test", "tests", "__tests__", "mocks", "__mocks__",
    "fixtures", "testdata",
}

# Secret detection patterns
SECRET_PATTERNS: list[tuple[str, re.Pattern, Optional[re.Pattern]]] = [
    (
        "AWS Access Key (AKIA...)",
        re.compile(r"AKIA[0-9A-Z]{16}"),
        None,
    ),
    (
        "GitHub Token (ghp_/gho_/ghu_/ghs_/ghr_)",
        re.compile(r"gh[pousr]_[A-Za-z0-9_]{36,}"),
        None,
    ),
    (
        "Private Key",
        re.compile(r"-----BEGIN (?:RSA |EC |DSA |OPENSSH )?PRIVATE KEY-----"),
        None,
    ),
    (
        "API Key/Secret assignment",
        re.compile(
            r"(?:api[_\-]?key|apikey|api[_\-]?secret)\s*[:=]\s*['\"][^'\"]{8,}",
            re.IGNORECASE,
        ),
        None,
    ),
    (
        "Secret/Token assignment",
        re.compile(
            r"(?:secret_key|private_key|access_token|auth_token)\s*[:=]\s*['\"][^'\"]{8,}",
            re.IGNORECASE,
        ),
        None,
    ),
    (
        "Password assignment",
        re.compile(
            r"(?:password|passwd|pwd)\s*[:=]\s*['\"][^'\"]{8,}",
            re.IGNORECASE,
        ),
        # Exclude placeholders / env references
        re.compile(
            r"(?:password|passwd|pwd)\s*[:=]\s*['\"]"
            r"(?:your_|change_me|placeholder|example|xxx|\$\{|process\.env|os\.environ)",
            re.IGNORECASE,
        ),
    ),
    (
        "Authorization token (Basic/Bearer)",
        re.compile(r"(?:basic|bearer)\s+[A-Za-z0-9+/=]{20,}", re.IGNORECASE),
        None,
    ),
    (
        "Long hex string (potential secret)",
        re.compile(r"['\"][0-9a-fA-F]{40,}['\"]"),
        # Exclude commit hash / checksum references
        re.compile(
            r"(?:commit|sha|hash|checksum|fingerprint)\s*[:=]?\s*['\"][0-9a-fA-F]{40,}",
            re.IGNORECASE,
        ),
    ),
]


def project_key(repo: Path) -> str:
    return str(repo.resolve()).replace("/", "_").lstrip("_")


def should_skip(path: Path) -> bool:
    """Return True if the file should be excluded from scanning."""
    ext = path.suffix.lstrip(".")
    if ext.lower() in SKIP_EXTENSIONS:
        return True

    if TEST_BASENAME_PATTERNS.match(path.name):
        return True

    parts = set(path.parts)
    if parts & TEST_DIR_PARTS:
        return True

    return False


def scan_file(path: Path) -> list[dict]:
    if not path.is_file() or path.stat().st_size > MAX_FILE_SIZE:
        return []
    if should_skip(path):
        return []

    try:
        content = path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return []

    findings: list[dict] = []
    for line_no, line in enumerate(content.splitlines(), start=1):
        for label, pattern, exclude_pattern in SECRET_PATTERNS:
            if not pattern.search(line):
                continue
            if exclude_pattern and exclude_pattern.search(line):
                continue
            findings.append(
                {
                    "file": str(path),
                    "line": line_no,
                    "type": label,
                    "snippet": line.strip()[:120],
                }
            )
            break  # one finding per line is enough

    return findings


def iter_files(repo: Path, explicit_files: Optional[list[str]]) -> list[Path]:
    if explicit_files:
        return [Path(f).resolve() for f in explicit_files]
    return [p for p in repo.rglob("*") if p.is_file()]


def main() -> int:
    parser = argparse.ArgumentParser(description="Scan files for hardcoded secrets.")
    parser.add_argument("--repo", default=".")
    parser.add_argument("--files", nargs="*")
    args = parser.parse_args()

    repo = Path(args.repo).resolve()
    if not repo.is_dir():
        print(f"Repo not found: {repo}")
        return 1

    results: list[dict] = []
    for path in iter_files(repo, args.files):
        try:
            resolved = path.resolve()
        except OSError:
            continue
        if not str(resolved).startswith(str(repo)):
            continue
        results.extend(scan_file(resolved))

    output_dir = Path(
        os.environ.get(
            "SECRET_SCANNER_HOME",
            str(Path.home() / ".codex" / "secret-scanner"),
        )
    )
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / f"{project_key(repo)}.json"
    output_path.write_text(
        json.dumps(results, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )

    if results:
        print(f"WARNING: {len(results)} potential secret(s) detected.")
        for finding in results:
            print(f"  {finding['file']}:{finding['line']} - {finding['type']}")
        print(f"\nFull report: {output_path}")
        return 1
    else:
        print("No secrets detected.")
        print(f"Report: {output_path}")
        return 0


if __name__ == "__main__":
    raise SystemExit(main())
