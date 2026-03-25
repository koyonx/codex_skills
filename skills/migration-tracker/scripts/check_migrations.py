#!/usr/bin/env python3

import argparse
import json
import os
import re
import subprocess
from pathlib import Path
from typing import Optional

MAX_FILE_SIZE = 2 * 1024 * 1024

# Migration directories to look for
MIGRATION_DIRS = [
    "migrations",
    "db/migrate",
    "alembic/versions",
    "prisma/migrations",
]

MIGRATION_FILE_EXTENSIONS = {".py", ".rb", ".sql", ".ts", ".js"}

# Framework detection rules: (framework_name, file_pattern_check, content_pattern)
FRAMEWORK_RULES: list[tuple[str, "callable", re.Pattern]] = []


def project_key(repo: Path) -> str:
    return str(repo.resolve()).replace("/", "_").lstrip("_")


def run_git(repo: Path, *args: str) -> str:
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


def detect_model_file(filepath: Path, repo: Path) -> Optional[str]:
    """Check if a file is a model/schema file. Returns framework name or None."""
    resolved = filepath.resolve()
    if not resolved.is_file() or resolved.is_symlink():
        return None
    if resolved.stat().st_size > MAX_FILE_SIZE:
        return None

    rel = str(filepath)
    basename = filepath.name
    ext = filepath.suffix.lower()

    try:
        content = resolved.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return None

    # Check if it's a migration file itself
    for mig_dir in MIGRATION_DIRS:
        if f"/{mig_dir}/" in rel or rel.startswith(f"{mig_dir}/"):
            return None

    # Django models
    if basename == "models.py" or "/models/" in rel:
        if re.search(r"class\s+\w+\(.*Model\)", content):
            return "Django"

    # SQLAlchemy / Alembic
    if ext == ".py":
        if re.search(
            r"(?:Column|relationship|ForeignKey|Table|Base\.metadata"
            r"|declarative_base|mapped_column)",
            content,
        ):
            return "SQLAlchemy/Alembic"

    # Rails ActiveRecord
    if ext == ".rb" and ("/models/" in rel or "/app/models/" in rel):
        if re.search(
            r"class\s+\w+\s*<\s*(?:ApplicationRecord|ActiveRecord::Base)",
            content,
        ):
            return "Rails"

    # Prisma
    if basename == "schema.prisma":
        return "Prisma"

    # TypeORM
    if ext == ".ts":
        if re.search(r"@Entity\(\)|@Column\(\)|@PrimaryGeneratedColumn", content):
            return "TypeORM"

    # Sequelize
    if ext in (".js", ".ts"):
        if re.search(r"sequelize\.define|Model\.init|DataTypes\.", content):
            return "Sequelize"

    # GORM (Go)
    if ext == ".go":
        if re.search(r'gorm\.Model|gorm:"', content):
            return "GORM"

    return None


def show_status(repo: Path) -> dict:
    """Show migration status: directories, file counts, uncommitted migrations."""
    status: dict = {
        "migration_dirs": {},
        "total_migration_files": 0,
        "uncommitted_migrations": 0,
        "prisma_schema_found": False,
    }

    for mig_dir in MIGRATION_DIRS:
        full_dir = repo / mig_dir
        if full_dir.is_dir() and not full_dir.is_symlink():
            count = sum(
                1
                for f in full_dir.rglob("*")
                if f.is_file()
                and f.suffix in MIGRATION_FILE_EXTENSIONS
                and not f.name.startswith("__")
            )
            if count > 0:
                status["migration_dirs"][mig_dir] = count
                status["total_migration_files"] += count

    prisma_schema = repo / "prisma" / "schema.prisma"
    if prisma_schema.is_file() and not prisma_schema.is_symlink():
        status["prisma_schema_found"] = True

    # Check for uncommitted migration files via git
    git_status = run_git(repo, "status", "--short")
    if git_status:
        for line in git_status.splitlines():
            for mig_dir in MIGRATION_DIRS:
                if mig_dir + "/" in line:
                    status["uncommitted_migrations"] += 1
                    break

    return status


def scan_for_model_changes(repo: Path) -> list[dict]:
    """Scan git-modified files for model/schema changes."""
    # Get recently modified files (staged + unstaged)
    modified: set[str] = set()

    diff_output = run_git(repo, "diff", "--name-only")
    if diff_output:
        modified.update(diff_output.splitlines())

    cached_output = run_git(repo, "diff", "--cached", "--name-only")
    if cached_output:
        modified.update(cached_output.splitlines())

    findings: list[dict] = []
    for rel_path in sorted(modified):
        rel_path = rel_path.strip()
        if not rel_path:
            continue
        filepath = repo / rel_path
        framework = detect_model_file(filepath, repo)
        if framework:
            findings.append(
                {
                    "file": rel_path,
                    "framework": framework,
                }
            )

    return findings


# Migration command hints per framework
MIGRATION_COMMANDS = {
    "Django": "python manage.py makemigrations",
    "SQLAlchemy/Alembic": "alembic revision --autogenerate -m 'description'",
    "Rails": "rails generate migration MigrationName",
    "Prisma": "npx prisma migrate dev --name description",
    "TypeORM": "npx typeorm migration:generate -n MigrationName",
    "Sequelize": "npx sequelize-cli migration:generate --name migration-name",
    "GORM": "# GORM: use AutoMigrate or create manual migration",
}


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Detect model/schema changes and check migration status."
    )
    parser.add_argument("--repo", default=".")
    parser.add_argument(
        "--status",
        action="store_true",
        help="Show migration status instead of scanning for changes",
    )
    args = parser.parse_args()

    repo = Path(args.repo).resolve()
    if not repo.is_dir():
        print(f"Repo not found: {repo}")
        return 1

    output_dir = Path(
        os.environ.get(
            "MIGRATION_TRACKER_HOME",
            str(Path.home() / ".codex" / "migration-tracker"),
        )
    )
    output_dir.mkdir(parents=True, exist_ok=True)

    if args.status:
        status = show_status(repo)
        output_path = output_dir / f"{project_key(repo)}_status.json"
        output_path.write_text(
            json.dumps(status, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )

        print("=== migration-tracker: Migration Status ===")
        if status["migration_dirs"]:
            for dir_name, count in status["migration_dirs"].items():
                print(f"  {dir_name}: {count} migration file(s)")
        else:
            print("  No migration directories found.")
        print(f"Total migration files: {status['total_migration_files']}")
        if status["prisma_schema_found"]:
            print("Prisma schema: found")
        if status["uncommitted_migrations"] > 0:
            print(
                f"WARNING: {status['uncommitted_migrations']} uncommitted "
                f"migration file(s)"
            )
        print(f"Report: {output_path}")
        return 0

    # Scan for model changes
    findings = scan_for_model_changes(repo)

    report = {
        "model_changes": findings,
    }
    output_path = output_dir / f"{project_key(repo)}.json"
    output_path.write_text(
        json.dumps(report, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )

    if not findings:
        print("No model/schema changes detected in modified files.")
        print(f"Report: {output_path}")
        return 0

    print("=== migration-tracker: Model Changes Detected ===")
    frameworks_seen: set[str] = set()
    for finding in findings:
        fw = finding["framework"]
        frameworks_seen.add(fw)
        print(f"  {finding['file']} ({fw})")

    print()
    print("If database schema was changed, create a migration:")
    for fw in sorted(frameworks_seen):
        cmd = MIGRATION_COMMANDS.get(fw, "")
        if cmd:
            print(f"  {fw}: {cmd}")

    print(f"\nFull report: {output_path}")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
