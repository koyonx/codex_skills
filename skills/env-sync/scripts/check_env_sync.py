#!/usr/bin/env python3

import argparse
import json
import os
import re
from pathlib import Path

KEY_RE = re.compile(r"^([A-Za-z_][A-Za-z0-9_]*)=")

ENV_FILES = [".env", ".env.local", ".env.development", ".env.production", ".env.staging", ".env.test"]
EXAMPLE_FILES = [".env.example", ".env.sample", ".env.template"]


def project_key(repo: Path) -> str:
    return str(repo.resolve()).replace("/", "_").lstrip("_")


def extract_keys(file_path: Path) -> set[str]:
    """Extract environment variable key names only (never values) for privacy."""
    if not file_path.is_file() or file_path.is_symlink():
        return set()
    keys: set[str] = set()
    try:
        for line in file_path.read_text(encoding="utf-8", errors="replace").splitlines():
            match = KEY_RE.match(line)
            if match:
                keys.add(match.group(1))
    except OSError:
        pass
    return keys


def check_gitignore(repo: Path) -> dict:
    """Check if .env is covered by .gitignore."""
    gitignore_path = repo / ".gitignore"
    result = {"gitignore_exists": False, "env_covered": False}

    if not gitignore_path.is_file():
        return result

    result["gitignore_exists"] = True
    try:
        content = gitignore_path.read_text(encoding="utf-8", errors="replace")
        for line in content.splitlines():
            stripped = line.strip()
            if stripped in (".env", ".env.*", ".env*"):
                result["env_covered"] = True
                break
            if re.match(r"^\s*\.env\s*$", stripped) or re.match(r"^\s*\.env\.\*\s*$", stripped):
                result["env_covered"] = True
                break
    except OSError:
        pass

    return result


def scan_env_files(repo: Path) -> dict:
    """Scan for .env and .env.example files and compare keys."""
    results: dict = {
        "repo": str(repo),
        "env_files_found": [],
        "example_files_found": [],
        "comparisons": [],
        "gitignore": {},
        "warnings": [],
    }

    # Find env files
    for env_name in ENV_FILES:
        env_path = repo / env_name
        if env_path.is_file() and not env_path.is_symlink():
            results["env_files_found"].append(env_name)

    # Find example files
    for ex_name in EXAMPLE_FILES:
        ex_path = repo / ex_name
        if ex_path.is_file() and not ex_path.is_symlink():
            results["example_files_found"].append(ex_name)

    # Check .gitignore
    results["gitignore"] = check_gitignore(repo)

    if results["env_files_found"] and not results["gitignore"]["env_covered"]:
        if not results["gitignore"]["gitignore_exists"]:
            results["warnings"].append("No .gitignore found. .env files should be gitignored.")
        else:
            results["warnings"].append(".env may not be in .gitignore. Ensure secrets are not committed.")

    # Compare env vs example
    if not results["example_files_found"]:
        if results["env_files_found"]:
            results["warnings"].append(
                "No .env.example found. Consider creating one to document required environment variables."
            )
        return results

    # Use the first example file found
    example_path = repo / results["example_files_found"][0]
    example_keys = extract_keys(example_path)

    for env_name in results["env_files_found"]:
        env_path = repo / env_name
        env_keys = extract_keys(env_path)

        new_keys = sorted(env_keys - example_keys)
        missing_keys = sorted(example_keys - env_keys)

        comparison = {
            "env_file": env_name,
            "example_file": results["example_files_found"][0],
            "env_key_count": len(env_keys),
            "example_key_count": len(example_keys),
            "new_in_env": new_keys[:20],  # limit output
            "missing_from_example": missing_keys[:20],
            "in_sync": len(new_keys) == 0 and len(missing_keys) == 0,
        }
        results["comparisons"].append(comparison)

        if new_keys:
            results["warnings"].append(
                f"{env_name}: {len(new_keys)} key(s) not in {results['example_files_found'][0]}"
            )
        if missing_keys:
            results["warnings"].append(
                f"{env_name}: {len(missing_keys)} key(s) missing from {results['example_files_found'][0]}"
            )

    return results


def main() -> int:
    parser = argparse.ArgumentParser(description="Compare .env vs .env.example keys.")
    parser.add_argument("--repo", default=".", help="Path to the repository root")
    args = parser.parse_args()

    repo = Path(args.repo).resolve()
    if not repo.is_dir():
        print(f"Repo not found: {repo}")
        return 1

    results = scan_env_files(repo)

    # Persist results
    output_dir = Path(os.environ.get("ENV_SYNC_HOME", str(Path.home() / ".codex" / "env-sync")))
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / f"{project_key(repo)}.json"
    output_path.write_text(json.dumps(results, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    # Print summary
    print("=== env-sync: Environment Sync Check ===")
    print(f"Repository: {repo}")

    if not results["env_files_found"] and not results["example_files_found"]:
        print("No .env or .env.example files found.")
        print(f"\nResults saved to: {output_path}")
        print("=== End of env-sync ===")
        return 0

    if results["env_files_found"]:
        print(f"Env files: {', '.join(results['env_files_found'])}")
    if results["example_files_found"]:
        print(f"Example files: {', '.join(results['example_files_found'])}")

    # Gitignore status
    gi = results["gitignore"]
    if gi["gitignore_exists"]:
        if gi["env_covered"]:
            print(".gitignore: .env is covered")
        else:
            print("WARNING: .env may not be covered by .gitignore")
    else:
        print("WARNING: No .gitignore found")

    # Comparisons
    for comp in results["comparisons"]:
        print(f"\n--- {comp['env_file']} vs {comp['example_file']} ---")
        if comp["in_sync"]:
            print("  In sync.")
        else:
            if comp["new_in_env"]:
                print(f"  New keys not in example ({len(comp['new_in_env'])}):")
                for key in comp["new_in_env"]:
                    print(f"    - {key}")
            if comp["missing_from_example"]:
                print(f"  Missing keys from example ({len(comp['missing_from_example'])}):")
                for key in comp["missing_from_example"]:
                    print(f"    - {key}")

    # Warnings
    if results["warnings"]:
        print("\nWarnings:")
        for warning in results["warnings"]:
            print(f"  - {warning}")

    print(f"\nResults saved to: {output_path}")
    print("=== End of env-sync ===")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
