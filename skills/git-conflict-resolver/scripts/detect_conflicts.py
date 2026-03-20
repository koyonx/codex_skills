#!/usr/bin/env python3

import argparse
import json
import os
import re
import subprocess
from pathlib import Path


CONFLICT_MARKER_RE = re.compile(r"^<<<<<<<", re.MULTILINE)


def project_key(repo: Path) -> str:
    return str(repo.resolve()).replace("/", "_").lstrip("_")


def run_git(repo: Path, *args: str) -> str:
    """Run a git command and return stdout, or empty string on failure."""
    env = os.environ.copy()
    env["GIT_CONFIG_NOSYSTEM"] = "1"
    env["GIT_TERMINAL_PROMPT"] = "0"
    try:
        result = subprocess.run(
            ["git", "-C", str(repo), *args],
            capture_output=True,
            text=True,
            timeout=15,
            env=env,
        )
        return result.stdout.strip()
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return ""


def is_git_repo(repo: Path) -> bool:
    return bool(run_git(repo, "rev-parse", "--git-dir"))


def get_conflicted_files(repo: Path) -> list[str]:
    output = run_git(repo, "diff", "--name-only", "--diff-filter=U")
    if not output:
        return []
    return [f for f in output.splitlines()[:20] if f.strip()]


def count_conflicts(filepath: Path) -> int:
    if not filepath.is_file() or filepath.is_symlink():
        return 0
    try:
        content = filepath.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return 0
    return len(CONFLICT_MARKER_RE.findall(content))


def get_branch(repo: Path) -> str:
    branch = run_git(repo, "branch", "--show-current")
    return branch if branch else "unknown"


def get_merge_head(repo: Path) -> str:
    merge_head_path = repo / ".git" / "MERGE_HEAD"
    if not merge_head_path.is_file():
        return ""
    try:
        head = merge_head_path.read_text().strip()
    except OSError:
        return ""
    if re.match(r"^[0-9a-f]{40}$", head):
        return head
    return ""


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Detect unresolved merge conflicts in a git repository."
    )
    parser.add_argument("--repo", default=".")
    args = parser.parse_args()

    repo = Path(args.repo).resolve()
    if not repo.is_dir():
        print(f"Repo not found: {repo}")
        return 1

    if not is_git_repo(repo):
        print("Not a git repository.")
        return 1

    conflicted = get_conflicted_files(repo)
    if not conflicted:
        print("No merge conflicts detected.")
        return 0

    branch = get_branch(repo)
    merge_head = get_merge_head(repo)

    file_details: list[dict] = []
    for rel in conflicted:
        full_path = (repo / rel).resolve()
        # Ensure path stays within repo
        if not str(full_path).startswith(str(repo)):
            continue
        if full_path.is_symlink():
            continue
        conflicts = count_conflicts(full_path)
        file_details.append(
            {
                "file": rel,
                "conflicts": conflicts,
            }
        )

    report = {
        "branch": branch,
        "merge_head": merge_head[:8] if merge_head else None,
        "conflicted_file_count": len(file_details),
        "files": file_details,
    }

    # Save report
    output_dir = Path(
        os.environ.get(
            "GIT_CONFLICT_RESOLVER_HOME",
            str(Path.home() / ".codex" / "git-conflict-resolver"),
        )
    )
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / f"{project_key(repo)}.json"
    output_path.write_text(
        json.dumps(report, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )

    # Print summary
    print(f"=== git-conflict-resolver: Unresolved Merge Conflicts ===")
    print(f"Branch: {branch}")
    if merge_head:
        print(f"Merging from: {merge_head[:8]}")
    print()
    print(f"Conflicted files ({len(file_details)}):")
    for detail in file_details:
        print(f"  - {detail['file']} ({detail['conflicts']} conflict(s))")
    print()
    print("Use Read tool to examine conflicted files for resolution.")
    print(f"Full report: {output_path}")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
