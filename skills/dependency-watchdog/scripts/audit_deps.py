#!/usr/bin/env python3

import argparse
import json
import os
import shutil
import subprocess
from pathlib import Path

TIMEOUT = 30  # seconds

# Dependency file -> (audit_type, display_name)
DEP_FILE_MAP: dict[str, tuple[str, str]] = {
    "package.json": ("npm", "npm"),
    "package-lock.json": ("npm", "npm"),
    "yarn.lock": ("npm", "npm"),
    "pnpm-lock.yaml": ("npm", "npm"),
    "requirements.txt": ("pip", "pip"),
    "requirements-dev.txt": ("pip", "pip"),
    "Pipfile": ("pip", "pip"),
    "Pipfile.lock": ("pip", "pip"),
    "pyproject.toml": ("pip", "pip"),
    "go.mod": ("go", "Go"),
    "go.sum": ("go", "Go"),
    "Gemfile": ("ruby", "Bundler"),
    "Gemfile.lock": ("ruby", "Bundler"),
    "Cargo.toml": ("rust", "Cargo"),
    "Cargo.lock": ("rust", "Cargo"),
    "composer.json": ("php", "Composer"),
    "composer.lock": ("php", "Composer"),
}


def project_key(repo: Path) -> str:
    return str(repo.resolve()).replace("/", "_").lstrip("_")


def detect_dep_files(repo: Path) -> dict[str, list[str]]:
    """Detect dependency files grouped by audit type."""
    found: dict[str, list[str]] = {}
    for filename, (audit_type, _) in DEP_FILE_MAP.items():
        dep_path = repo / filename
        if dep_path.is_file() and not dep_path.is_symlink():
            found.setdefault(audit_type, []).append(filename)
    return found


def run_audit(audit_type: str, repo: Path) -> dict:
    """Run the appropriate audit command and return results."""
    result: dict = {"type": audit_type, "status": "skipped", "summary": ""}

    if audit_type == "npm":
        if not shutil.which("npm"):
            result["summary"] = "npm not found in PATH"
            return result
        try:
            proc = subprocess.run(
                ["npm", "audit", "--json"],
                cwd=str(repo), capture_output=True, text=True, timeout=TIMEOUT,
            )
            result["status"] = "completed"
            try:
                data = json.loads(proc.stdout)
                meta = data.get("metadata", {})
                vulns = meta.get("vulnerabilities", {})
                if vulns:
                    result["summary"] = (
                        f"Total: {vulns.get('total', 0)}, "
                        f"Critical: {vulns.get('critical', 0)}, "
                        f"High: {vulns.get('high', 0)}, "
                        f"Moderate: {vulns.get('moderate', 0)}"
                    )
                elif "vulnerabilities" in data:
                    result["summary"] = f"Vulnerabilities found: {len(data['vulnerabilities'])}"
                else:
                    result["summary"] = "No vulnerability data available"
            except (json.JSONDecodeError, KeyError):
                result["summary"] = f"Audit completed (exit: {proc.returncode})"
        except subprocess.TimeoutExpired:
            result["status"] = "timeout"
            result["summary"] = "Audit timed out after 30s"

    elif audit_type == "pip":
        if shutil.which("pip-audit"):
            try:
                proc = subprocess.run(
                    ["pip-audit", "--format", "json"],
                    cwd=str(repo), capture_output=True, text=True, timeout=TIMEOUT,
                )
                result["status"] = "completed"
                try:
                    data = json.loads(proc.stdout)
                    result["summary"] = f"Vulnerabilities found: {len(data)}"
                except (json.JSONDecodeError, TypeError):
                    result["summary"] = f"Audit completed (exit: {proc.returncode})"
            except subprocess.TimeoutExpired:
                result["status"] = "timeout"
                result["summary"] = "Audit timed out after 30s"
        else:
            result["summary"] = "pip-audit not installed. Run: pip install pip-audit"

    elif audit_type == "go":
        if shutil.which("govulncheck"):
            try:
                proc = subprocess.run(
                    ["govulncheck", "./..."],
                    cwd=str(repo), capture_output=True, text=True, timeout=TIMEOUT,
                )
                result["status"] = "completed"
                vuln_count = proc.stdout.count("Vulnerability")
                result["summary"] = f"Vulnerabilities found: {vuln_count}"
            except subprocess.TimeoutExpired:
                result["status"] = "timeout"
                result["summary"] = "Audit timed out after 30s"
        elif shutil.which("go"):
            result["summary"] = "govulncheck not installed. Run: go install golang.org/x/vuln/cmd/govulncheck@latest"
        else:
            result["summary"] = "go not found in PATH"

    elif audit_type == "ruby":
        if shutil.which("bundler-audit"):
            try:
                proc = subprocess.run(
                    ["bundler-audit", "check"],
                    cwd=str(repo), capture_output=True, text=True, timeout=TIMEOUT,
                )
                result["status"] = "completed"
                vuln_count = proc.stdout.count("CVE-")
                result["summary"] = f"Vulnerabilities found: {vuln_count}"
            except subprocess.TimeoutExpired:
                result["status"] = "timeout"
                result["summary"] = "Audit timed out after 30s"
        else:
            result["summary"] = "bundler-audit not installed. Run: gem install bundler-audit"

    elif audit_type == "rust":
        if shutil.which("cargo-audit"):
            try:
                proc = subprocess.run(
                    ["cargo", "audit", "--json"],
                    cwd=str(repo), capture_output=True, text=True, timeout=TIMEOUT,
                )
                result["status"] = "completed"
                try:
                    data = json.loads(proc.stdout)
                    vuln_count = data.get("vulnerabilities", {}).get("found", 0)
                    result["summary"] = f"Vulnerabilities found: {vuln_count}"
                except (json.JSONDecodeError, KeyError):
                    result["summary"] = f"Audit completed (exit: {proc.returncode})"
            except subprocess.TimeoutExpired:
                result["status"] = "timeout"
                result["summary"] = "Audit timed out after 30s"
        else:
            result["summary"] = "cargo-audit not installed. Run: cargo install cargo-audit"

    elif audit_type == "php":
        if shutil.which("composer"):
            try:
                proc = subprocess.run(
                    ["composer", "audit", "--format=json"],
                    cwd=str(repo), capture_output=True, text=True, timeout=TIMEOUT,
                )
                result["status"] = "completed"
                try:
                    data = json.loads(proc.stdout)
                    advisories = data.get("advisories", {})
                    result["summary"] = f"Vulnerabilities found: {len(advisories)}"
                except (json.JSONDecodeError, KeyError):
                    result["summary"] = f"Audit completed (exit: {proc.returncode})"
            except subprocess.TimeoutExpired:
                result["status"] = "timeout"
                result["summary"] = "Audit timed out after 30s"
        else:
            result["summary"] = "composer not found in PATH"

    return result


def main() -> int:
    parser = argparse.ArgumentParser(description="Check project dependencies for vulnerabilities.")
    parser.add_argument("--repo", default=".", help="Path to the repository root")
    parser.add_argument("--audit", action="store_true", help="Run full vulnerability audit")
    args = parser.parse_args()

    repo = Path(args.repo).resolve()
    if not repo.is_dir():
        print(f"Repo not found: {repo}")
        return 1

    dep_groups = detect_dep_files(repo)

    if not dep_groups:
        print("No dependency files found.")
        return 0

    print("=== dependency-watchdog: Dependency Check ===")
    print(f"Repository: {repo}")

    all_files = []
    for audit_type, files in dep_groups.items():
        display = DEP_FILE_MAP[files[0]][1]
        all_files.extend(files)
        print(f"  [{display}] {', '.join(files)}")

    audit_results: list[dict] = []

    if args.audit:
        print("\nRunning vulnerability audits...")
        for audit_type in dep_groups:
            audit_result = run_audit(audit_type, repo)
            audit_results.append(audit_result)
            display = DEP_FILE_MAP[dep_groups[audit_type][0]][1]
            print(f"\n  {display}: {audit_result['summary']}")
    else:
        print("\nRun with --audit to perform full vulnerability scan.")

    # Persist results
    output_dir = Path(os.environ.get("DEP_WATCHDOG_HOME", str(Path.home() / ".codex" / "dependency-watchdog")))
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / f"{project_key(repo)}.json"

    output_data = {
        "repo": str(repo),
        "dep_files": all_files,
        "audit_results": audit_results,
    }
    output_path.write_text(json.dumps(output_data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    print(f"\nResults saved to: {output_path}")
    print("=== End of dependency-watchdog ===")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
