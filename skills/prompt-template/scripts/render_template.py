#!/usr/bin/env python3

import argparse
from pathlib import Path

SKILL_ROOT = Path(__file__).resolve().parent.parent
BUILTIN_DIR = SKILL_ROOT / "assets" / "templates"
USER_DIR = Path.home() / ".codex" / "prompt-templates"


def available_templates() -> dict[str, Path]:
    templates: dict[str, Path] = {}
    for directory in (BUILTIN_DIR, USER_DIR):
        if not directory.is_dir():
            continue
        for path in sorted(directory.glob("*.md")):
            templates[path.stem] = path
    return templates


def main() -> int:
    parser = argparse.ArgumentParser(description="Render a built-in or user prompt template.")
    parser.add_argument("name", nargs="?")
    parser.add_argument("--list", action="store_true")
    args = parser.parse_args()

    templates = available_templates()
    if args.list:
        for name in sorted(templates):
            print(name)
        return 0

    if not args.name:
        parser.error("template name is required unless --list is used")

    template_path = templates.get(args.name)
    if template_path is None:
        print(f"Template not found: {args.name}")
        return 1

    print(template_path.read_text(encoding="utf-8"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
