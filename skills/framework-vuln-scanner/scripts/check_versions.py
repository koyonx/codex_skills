#!/usr/bin/env python3

import argparse
import json
import os
import re
import shutil
import subprocess
from pathlib import Path


def project_key(repo: Path) -> str:
    return str(repo.resolve()).replace("/", "_").lstrip("_")


def get_version_output(cmd: list[str]) -> str:
    """Run a command and return stdout, or empty string on failure."""
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
        return proc.stdout.strip()
    except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
        return ""


def extract_version_numbers(text: str) -> str:
    """Extract the first version-like string from text."""
    match = re.search(r"(\d+\.\d+(?:\.\d+)?)", text)
    return match.group(1) if match else ""


def parse_major_minor(version: str) -> tuple[int, int]:
    """Parse major.minor from a version string. Returns (-1, -1) on failure."""
    parts = version.split(".")
    try:
        major = int(parts[0])
        minor = int(parts[1]) if len(parts) > 1 else 0
        return major, minor
    except (ValueError, IndexError):
        return -1, -1


def read_json_file(path: Path) -> dict:
    """Safely read a JSON file."""
    if not path.is_file() or path.is_symlink():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8", errors="replace"))
    except (json.JSONDecodeError, OSError):
        return {}


def extract_pkg_version(pkg_data: dict, package: str) -> str:
    """Extract a package version from package.json dependencies."""
    version = pkg_data.get("dependencies", {}).get(package, "")
    if not version:
        version = pkg_data.get("devDependencies", {}).get(package, "")
    # Strip version prefixes like ^, ~, >=
    return re.sub(r"^[^0-9]*", "", version)


def extract_requirements_version(req_file: Path, package: str) -> str:
    """Extract a package version from requirements.txt."""
    if not req_file.is_file() or req_file.is_symlink():
        return ""
    try:
        for line in req_file.read_text(encoding="utf-8", errors="replace").splitlines():
            if re.match(rf"^{re.escape(package)}[=><~!]", line, re.IGNORECASE):
                match = re.search(r"(\d+\.\d+(?:\.\d+)?)", line)
                if match:
                    return match.group(1)
    except OSError:
        pass
    return ""


def extract_gemfile_version(gemfile: Path, gem_name: str) -> str:
    """Extract a gem version from Gemfile."""
    if not gemfile.is_file() or gemfile.is_symlink():
        return ""
    try:
        for line in gemfile.read_text(encoding="utf-8", errors="replace").splitlines():
            if re.search(rf"""gem\s+['"]{re.escape(gem_name)}['"]""", line):
                match = re.search(r"(\d+\.\d+(?:\.\d+)?)", line)
                if match:
                    return match.group(1)
    except OSError:
        pass
    return ""


def check_runtimes() -> tuple[list[dict], list[dict]]:
    """Check system runtime versions."""
    info: list[dict] = []
    warnings: list[dict] = []

    # Node.js
    if shutil.which("node"):
        raw = get_version_output(["node", "--version"])
        ver = extract_version_numbers(raw)
        if ver:
            major, _ = parse_major_minor(ver)
            if major >= 0:
                info.append({"name": "Node.js", "version": ver})
                if major % 2 != 0:
                    warnings.append({
                        "name": "Node.js", "version": ver,
                        "message": f"Node.js v{ver}: Odd version (non-LTS). Consider using an LTS version.",
                    })
                if major <= 18:
                    warnings.append({
                        "name": "Node.js", "version": ver,
                        "message": f"Node.js v{ver}: EOL or nearing EOL. Upgrade to a supported LTS version.",
                    })

    # Python
    if shutil.which("python3"):
        raw = get_version_output(["python3", "--version"])
        ver = extract_version_numbers(raw)
        if ver:
            major, minor = parse_major_minor(ver)
            if major >= 0:
                info.append({"name": "Python", "version": ver})
                if major < 3:
                    warnings.append({
                        "name": "Python", "version": ver,
                        "message": f"Python {ver}: Python 2 is EOL. Upgrade to Python 3.",
                    })
                elif major == 3 and minor <= 9:
                    warnings.append({
                        "name": "Python", "version": ver,
                        "message": f"Python {ver}: EOL or nearing EOL. Upgrade to Python 3.10+.",
                    })

    # Ruby
    if shutil.which("ruby"):
        raw = get_version_output(["ruby", "--version"])
        ver = extract_version_numbers(raw)
        if ver:
            major, minor = parse_major_minor(ver)
            if major >= 0:
                info.append({"name": "Ruby", "version": ver})
                if major < 3 or (major == 3 and minor <= 0):
                    warnings.append({
                        "name": "Ruby", "version": ver,
                        "message": f"Ruby {ver}: EOL. Upgrade to Ruby 3.1+.",
                    })

    # Go
    if shutil.which("go"):
        raw = get_version_output(["go", "version"])
        ver = extract_version_numbers(raw)
        if ver:
            _, minor = parse_major_minor(ver)
            if minor >= 0:
                info.append({"name": "Go", "version": ver})
                if minor <= 21:
                    warnings.append({
                        "name": "Go", "version": ver,
                        "message": f"Go {ver}: No longer supported. Upgrade to latest.",
                    })

    return info, warnings


def check_frameworks(repo: Path) -> tuple[list[dict], list[dict]]:
    """Check framework versions from dependency files."""
    info: list[dict] = []
    warnings: list[dict] = []

    # package.json frameworks
    pkg_json = repo / "package.json"
    pkg_data = read_json_file(pkg_json)

    if pkg_data:
        # React
        ver = extract_pkg_version(pkg_data, "react")
        if ver:
            major, _ = parse_major_minor(ver)
            if major >= 0:
                info.append({"name": "React", "version": ver})
                if major <= 16:
                    warnings.append({
                        "name": "React", "version": ver,
                        "message": f"React {ver}: Consider upgrading to React 18+.",
                    })

        # Next.js
        ver = extract_pkg_version(pkg_data, "next")
        if ver:
            major, _ = parse_major_minor(ver)
            if major >= 0:
                info.append({"name": "Next.js", "version": ver})
                if major <= 13:
                    warnings.append({
                        "name": "Next.js", "version": ver,
                        "message": f"Next.js {ver}: Consider upgrading to Next.js 14+.",
                    })

        # Express
        ver = extract_pkg_version(pkg_data, "express")
        if ver:
            major, _ = parse_major_minor(ver)
            if major >= 0:
                info.append({"name": "Express", "version": ver})
                if major <= 3:
                    warnings.append({
                        "name": "Express", "version": ver,
                        "message": f"Express {ver}: EOL. Upgrade to Express 4+.",
                    })

        # Vue.js
        ver = extract_pkg_version(pkg_data, "vue")
        if ver:
            major, _ = parse_major_minor(ver)
            if major >= 0:
                info.append({"name": "Vue.js", "version": ver})
                if major <= 2:
                    warnings.append({
                        "name": "Vue.js", "version": ver,
                        "message": f"Vue.js {ver}: Vue 2 is EOL (Dec 2023). Upgrade to Vue 3.",
                    })

        # Angular
        ver = extract_pkg_version(pkg_data, "@angular/core")
        if ver:
            major, _ = parse_major_minor(ver)
            if major >= 0:
                info.append({"name": "Angular", "version": ver})
                if major <= 15:
                    warnings.append({
                        "name": "Angular", "version": ver,
                        "message": f"Angular {ver}: No longer supported. Upgrade to Angular 16+.",
                    })

    # Python frameworks from requirements.txt
    req_file = repo / "requirements.txt"

    # Django
    ver = extract_requirements_version(req_file, "django")
    if not ver:
        ver = extract_requirements_version(req_file, "Django")
    if ver:
        major, _ = parse_major_minor(ver)
        if major >= 0:
            info.append({"name": "Django", "version": ver})
            if major <= 3:
                warnings.append({
                    "name": "Django", "version": ver,
                    "message": f"Django {ver}: Consider upgrading to Django 4.2+ (LTS).",
                })

    # Flask
    ver = extract_requirements_version(req_file, "flask")
    if not ver:
        ver = extract_requirements_version(req_file, "Flask")
    if ver:
        major, _ = parse_major_minor(ver)
        if major >= 0:
            info.append({"name": "Flask", "version": ver})
            if major <= 1:
                warnings.append({
                    "name": "Flask", "version": ver,
                    "message": f"Flask {ver}: Consider upgrading to Flask 2+.",
                })

    # Ruby frameworks from Gemfile
    gemfile = repo / "Gemfile"
    ver = extract_gemfile_version(gemfile, "rails")
    if ver:
        major, _ = parse_major_minor(ver)
        if major >= 0:
            info.append({"name": "Rails", "version": ver})
            if major <= 5:
                warnings.append({
                    "name": "Rails", "version": ver,
                    "message": f"Rails {ver}: EOL. Upgrade to Rails 7+.",
                })
            elif major == 6:
                warnings.append({
                    "name": "Rails", "version": ver,
                    "message": f"Rails {ver}: Nearing EOL. Consider upgrading to Rails 7+.",
                })

    return info, warnings


def main() -> int:
    parser = argparse.ArgumentParser(description="Check runtime and framework versions for EOL or vulnerabilities.")
    parser.add_argument("--repo", default=".", help="Path to the repository root")
    args = parser.parse_args()

    repo = Path(args.repo).resolve()
    if not repo.is_dir():
        print(f"Repo not found: {repo}")
        return 1

    runtime_info, runtime_warnings = check_runtimes()
    framework_info, framework_warnings = check_frameworks(repo)

    all_info = runtime_info + framework_info
    all_warnings = runtime_warnings + framework_warnings

    if not all_info and not all_warnings:
        print("No runtimes or frameworks detected.")
        return 0

    # Persist results
    output_dir = Path(os.environ.get("FVS_HOME", str(Path.home() / ".codex" / "framework-vuln-scanner")))
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / f"{project_key(repo)}.json"

    output_data = {
        "repo": str(repo),
        "detected": all_info,
        "warnings": all_warnings,
    }
    output_path.write_text(json.dumps(output_data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    # Print summary
    print("=== framework-vuln-scanner: Version Check ===")
    print(f"Repository: {repo}")

    if all_info:
        print("\nDetected versions:")
        for item in all_info:
            print(f"  {item['name']}: {item['version']}")

    if all_warnings:
        print("\nWARNINGS:")
        for w in all_warnings:
            print(f"  - {w['message']}")
        print(f"\nTotal warnings: {len(all_warnings)}")
    else:
        print("\nNo version warnings.")

    print(f"\nResults saved to: {output_path}")
    print("=== End of framework-vuln-scanner ===")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
