#!/usr/bin/env python3

import argparse
import json
import os
import re
from pathlib import Path

MAX_FILE_SIZE = 2 * 1024 * 1024  # 2MB

# Route detection patterns per file extension
ROUTE_PATTERNS: dict[str, list[re.Pattern]] = {
    "py": [
        # FastAPI: @app.get("/path"), @router.post("/path")
        # Flask: @app.route("/path"), @blueprint.route("/path")
        re.compile(r"@(app|router|blueprint)\.(get|post|put|delete|patch|route)\s*\("),
        # Django: path("url", view)
        re.compile(r"^\s*path\s*\("),
    ],
    "js": [
        # Express: app.get("/path"), router.post("/path")
        re.compile(r"(app|router)\.(get|post|put|delete|patch|all|use)\s*\("),
        # Nest.js: @Get("/path"), @Post("/path")
        re.compile(r"@(Get|Post|Put|Delete|Patch)\s*\("),
        # Next.js: export async function GET
        re.compile(r"export\s+(async\s+)?function\s+(GET|POST|PUT|DELETE|PATCH)"),
    ],
    "ts": [],  # filled below
    "go": [
        # Gin: r.GET("/path"), Echo: e.GET("/path")
        # net/http: http.HandleFunc("/path")
        re.compile(r"\.(GET|POST|PUT|DELETE|PATCH|Handle|HandleFunc)\s*\("),
    ],
    "rb": [
        # Rails: get "/path", post "/path", resources :foo
        re.compile(r"^\s*(get|post|put|patch|delete|resources|resource|namespace)\s"),
    ],
    "java": [
        # Spring: @GetMapping, @PostMapping, @RequestMapping
        re.compile(r"@(Get|Post|Put|Delete|Patch|Request)Mapping"),
    ],
    "php": [
        # Laravel: Route::get, Route::post
        re.compile(r"Route::(get|post|put|delete|patch|any|match)\s*\("),
    ],
}
# TypeScript shares JavaScript patterns
ROUTE_PATTERNS["ts"] = ROUTE_PATTERNS["js"]

# Documentation file patterns to look for
DOC_PATTERNS = [
    "openapi.yaml",
    "openapi.yml",
    "openapi.json",
    "swagger.yaml",
    "swagger.yml",
    "swagger.json",
    "api-spec.yaml",
    "api-spec.yml",
    "docs/api",
    "doc/api",
]

SUPPORTED_EXTENSIONS = set(ROUTE_PATTERNS.keys())


def project_key(repo: Path) -> str:
    return str(repo.resolve()).replace("/", "_").lstrip("_")


def count_routes(file_path: Path, ext: str) -> int:
    """Count API route definitions in a file."""
    if not file_path.is_file() or file_path.is_symlink():
        return 0
    try:
        size = file_path.stat().st_size
    except OSError:
        return 0
    if size > MAX_FILE_SIZE or size == 0:
        return 0

    patterns = ROUTE_PATTERNS.get(ext, [])
    if not patterns:
        return 0

    try:
        content = file_path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return 0

    count = 0
    for line in content.splitlines():
        for pattern in patterns:
            if pattern.search(line):
                count += 1
                break  # one match per line is enough
    return count


def find_doc_files(repo: Path) -> list[str]:
    """Find existing API documentation files."""
    found = []
    for doc_pattern in DOC_PATTERNS:
        doc_path = repo / doc_pattern
        if doc_path.exists() and not doc_path.is_symlink():
            found.append(doc_pattern)
    return found


def scan_repo(repo: Path) -> dict:
    """Scan the repository for API routes and documentation."""
    route_files: list[dict] = []

    for file_path in repo.rglob("*"):
        if not file_path.is_file() or file_path.is_symlink():
            continue
        # Skip hidden directories and common non-source dirs
        parts = file_path.relative_to(repo).parts
        if any(p.startswith(".") or p in ("node_modules", "vendor", "__pycache__", "venv", ".venv") for p in parts):
            continue

        ext = file_path.suffix.lstrip(".")
        if ext not in SUPPORTED_EXTENSIONS:
            continue

        route_count = count_routes(file_path, ext)
        if route_count > 0:
            rel_path = str(file_path.relative_to(repo))
            route_files.append({"file": rel_path, "endpoints": route_count})

    doc_files = find_doc_files(repo)
    total_endpoints = sum(f["endpoints"] for f in route_files)

    return {
        "repo": str(repo),
        "total_endpoints": total_endpoints,
        "route_files": route_files,
        "doc_files": doc_files,
        "docs_found": len(doc_files) > 0,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Scan a repo for API routes and check documentation status.")
    parser.add_argument("--repo", default=".", help="Path to the repository root")
    args = parser.parse_args()

    repo = Path(args.repo).resolve()
    if not repo.is_dir():
        print(f"Repo not found: {repo}")
        return 1

    result = scan_repo(repo)

    # Persist results
    output_dir = Path(os.environ.get("API_DOC_SYNC_HOME", str(Path.home() / ".codex" / "api-doc-sync")))
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / f"{project_key(repo)}.json"
    output_path.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    # Print summary
    print(f"=== api-doc-sync: Scan Results ===")
    print(f"Repository: {repo}")
    print(f"Total endpoints detected: {result['total_endpoints']}")
    print(f"Files with routes: {len(result['route_files'])}")

    if result["route_files"]:
        print("\nRoute files:")
        for rf in result["route_files"]:
            print(f"  {rf['file']}: {rf['endpoints']} endpoint(s)")

    if result["docs_found"]:
        print(f"\nAPI docs found: {', '.join(result['doc_files'])}")
        print("Reminder: Verify documentation reflects current endpoints.")
    else:
        print("\nWARNING: No API documentation found (openapi.yaml/swagger.json etc.)")
        print("Consider creating API documentation for this project.")

    print(f"\nResults saved to: {output_path}")
    print(f"=== End of api-doc-sync ===")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
