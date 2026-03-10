---
name: context-loader
description: Use this skill when the user wants Codex to load project-specific context files from a curated config, especially at the start of work or before making architectural changes.
---

# Context Loader

## Overview

Use this skill to load a known set of important project files from `.context-loader.json`.
Prefer it when the repo already defines what context matters.

## Workflow

1. Run `scripts/load_context.py --project-root <path> --print-content` when the user wants the actual file contents.
2. Run `scripts/load_context.py --project-root <path> --paths-only` when you only need the candidate file list first.
3. Respect file size and total size limits.
4. If the config is missing, fall back to normal repo inspection instead of guessing.

## Config

See `references/config.md` for the file format.

## Resources

- Script: `scripts/load_context.py`
- Reference: `references/config.md`
