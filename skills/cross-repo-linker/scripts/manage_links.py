#!/usr/bin/env python3
"""Manage cross-repository dependency links: link, unlink, list, check."""

import argparse
import json
import os
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

MAX_LINKS = 10


def sanitize_name(text: str) -> str:
    """Keep only safe characters for repo names."""
    return re.sub(r"[^a-zA-Z0-9_.-]", "", text)


def sanitize_path_str(text: str) -> str:
    """Keep only safe characters for paths."""
    return re.sub(r"[^a-zA-Z0-9_./-]", "", text)[:200]


def load_links(links_file: Path) -> list[dict]:
    """Load links from JSON file."""
    if not links_file.is_file() or links_file.is_symlink():
        return []
    try:
        data = json.loads(links_file.read_text(encoding="utf-8"))
        if isinstance(data, list):
            return data
    except (json.JSONDecodeError, OSError):
        pass
    return []


def save_links(links_file: Path, links: list[dict]) -> None:
    """Atomically save links to JSON file."""
    tmp = links_file.with_suffix(".tmp")
    tmp.write_text(json.dumps(links, indent=2, ensure_ascii=False), encoding="utf-8")
    tmp.rename(links_file)


def detect_shared_deps(repo: Path, target: Path) -> str:
    """Detect shared dependencies between two repos."""
    shared = []

    # npm
    repo_pkg = repo / "package.json"
    tgt_pkg = target / "package.json"
    if repo_pkg.is_file() and tgt_pkg.is_file():
        try:
            repo_data = json.loads(repo_pkg.read_text(encoding="utf-8"))
            tgt_data = json.loads(tgt_pkg.read_text(encoding="utf-8"))
            repo_deps = set()
            tgt_deps = set()
            for key in ("dependencies", "devDependencies"):
                repo_deps.update(repo_data.get(key, {}).keys())
                tgt_deps.update(tgt_data.get(key, {}).keys())
            common = repo_deps & tgt_deps
            if common:
                shared.append(f"npm:{len(common)}")
        except (json.JSONDecodeError, OSError):
            pass

    # pip
    repo_req = repo / "requirements.txt"
    tgt_req = target / "requirements.txt"
    if repo_req.is_file() and tgt_req.is_file():
        try:
            repo_pkgs = set()
            tgt_pkgs = set()
            for line in repo_req.read_text(encoding="utf-8").splitlines():
                m = re.match(r"^([a-zA-Z0-9_-]+)", line)
                if m:
                    repo_pkgs.add(m.group(1).lower())
            for line in tgt_req.read_text(encoding="utf-8").splitlines():
                m = re.match(r"^([a-zA-Z0-9_-]+)", line)
                if m:
                    tgt_pkgs.add(m.group(1).lower())
            common = repo_pkgs & tgt_pkgs
            if common:
                shared.append(f"pip:{len(common)}")
        except OSError:
            pass

    return ", ".join(shared)


def action_link(repo: Path, target_str: str, links_file: Path) -> None:
    """Link a target repository."""
    target = Path(target_str).resolve()

    if not target.is_dir():
        print(f"Error: path does not exist or is not a directory: {target_str}", file=sys.stderr)
        sys.exit(1)

    if not (target / ".git").is_dir():
        print(f"Error: target is not a git repository: {target_str}", file=sys.stderr)
        sys.exit(1)

    home = Path.home()
    if not str(target).startswith(str(home)):
        print("Error: only repositories under HOME can be linked.", file=sys.stderr)
        sys.exit(1)

    links = load_links(links_file)

    if len(links) >= MAX_LINKS:
        print(f"Error: max {MAX_LINKS} linked repos. Unlink some first.", file=sys.stderr)
        sys.exit(1)

    repo_name = sanitize_name(target.name)

    for link in links:
        if link.get("name") == repo_name:
            print(f"Error: repository '{repo_name}' is already linked.", file=sys.stderr)
            sys.exit(1)

    shared = detect_shared_deps(repo, target)
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    links.append({
        "name": repo_name,
        "path": str(target),
        "shared_deps": shared,
        "linked_at": timestamp,
    })

    save_links(links_file, links)

    print(f"Linked: {repo_name} ({target})")
    if shared:
        print(f"Shared dependencies: {shared}")


def action_unlink(target_name: str, links_file: Path) -> None:
    """Unlink a repository by name."""
    safe_name = sanitize_name(target_name)
    links = load_links(links_file)

    found = False
    new_links = []
    for link in links:
        if link.get("name") == safe_name:
            found = True
        else:
            new_links.append(link)

    if not found:
        print(f"Error: repository '{safe_name}' not found.", file=sys.stderr)
        sys.exit(1)

    save_links(links_file, new_links)
    print(f"Unlinked: {safe_name}")


def action_list(links_file: Path) -> None:
    """List all linked repositories."""
    links = load_links(links_file)

    if not links:
        print("No linked repositories. Use --action link --target <path> to add one.")
        return

    print(f"=== cross-repo-linker: {len(links)} linked repo(s) ===")
    for link in links:
        name = sanitize_name(link.get("name", ""))
        path = sanitize_path_str(link.get("path", ""))
        shared = link.get("shared_deps", "none") or "none"
        exists = "yes" if Path(path).is_dir() else "missing"
        print(f"  {name} -> {path} (exists: {exists}, shared: {shared})")
    print("=== End of cross-repo-linker ===")


def action_check(links_file: Path) -> None:
    """Check status of all linked repositories."""
    links = load_links(links_file)

    if not links:
        print("No linked repositories.")
        return

    print(f"=== cross-repo-linker: status of {len(links)} linked repo(s) ===")
    home = str(Path.home())

    for link in links:
        name = sanitize_name(link.get("name", ""))
        path = link.get("path", "")

        if not path or not Path(path).is_dir():
            print(f"  {name}: missing")
            continue

        resolved = str(Path(path).resolve())
        if not resolved.startswith(home):
            print(f"  {name}: skipped (not under HOME)")
            continue

        # Get branch
        try:
            branch_result = subprocess.run(
                ["git", "-C", resolved, "rev-parse", "--abbrev-ref", "HEAD"],
                capture_output=True, text=True, timeout=5,
                env={**os.environ, "GIT_TERMINAL_PROMPT": "0"},
            )
            branch = re.sub(r"[^a-zA-Z0-9_./-]", "", branch_result.stdout.strip()) or "?"
        except (subprocess.TimeoutExpired, OSError):
            branch = "?"

        # Get uncommitted changes count
        try:
            diff_result = subprocess.run(
                ["git", "-C", resolved, "diff", "--name-only", "HEAD"],
                capture_output=True, text=True, timeout=5,
                env={**os.environ, "GIT_TERMINAL_PROMPT": "0"},
            )
            changes = len([l for l in diff_result.stdout.strip().split("\n") if l.strip()])
        except (subprocess.TimeoutExpired, OSError):
            changes = 0

        # Get last commit
        try:
            log_result = subprocess.run(
                ["git", "-C", resolved, "log", "-1", "--format=%h %s"],
                capture_output=True, text=True, timeout=5,
                env={**os.environ, "GIT_TERMINAL_PROMPT": "0"},
            )
            last_commit = re.sub(r"[^a-zA-Z0-9 _.:-]", "", log_result.stdout.strip())[:60] or "?"
        except (subprocess.TimeoutExpired, OSError):
            last_commit = "?"

        print(f"  {name} ({branch}): {changes} uncommitted, last: {last_commit}")

    print("=== End of cross-repo-linker ===")


def main() -> None:
    parser = argparse.ArgumentParser(description="Manage cross-repo dependency links")
    parser.add_argument("--repo", required=True, help="Current repository root path")
    parser.add_argument("--action", required=True, choices=["link", "unlink", "list", "check"],
                        help="Action to perform")
    parser.add_argument("--target", default="", help="Target path (for link) or name (for unlink)")
    args = parser.parse_args()

    repo = Path(args.repo).resolve()
    if not repo.is_dir():
        print(f"Error: repository path does not exist: {args.repo}", file=sys.stderr)
        sys.exit(1)

    data_dir = Path.home() / ".codex" / "cross-repo-linker"
    data_dir.mkdir(parents=True, exist_ok=True)
    os.chmod(str(data_dir), 0o700)

    links_file = data_dir / "links.json"
    if not links_file.exists():
        links_file.write_text("[]", encoding="utf-8")

    if args.action == "link":
        if not args.target:
            print("Error: --target is required for link action.", file=sys.stderr)
            sys.exit(1)
        action_link(repo, args.target, links_file)
    elif args.action == "unlink":
        if not args.target:
            print("Error: --target is required for unlink action.", file=sys.stderr)
            sys.exit(1)
        action_unlink(args.target, links_file)
    elif args.action == "list":
        action_list(links_file)
    elif args.action == "check":
        action_check(links_file)

    sys.exit(0)


if __name__ == "__main__":
    main()
