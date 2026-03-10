---
name: todo-tracker
description: Use this skill when the user wants to scan a repository for TODO, FIXME, HACK, or XXX markers, prioritize unresolved items, or persist a lightweight backlog summary during Codex work.
---

# Todo Tracker

## Overview

Use this skill to scan the repo for TODO-style markers and summarize unresolved technical debt.
It can rescan the whole repository or only selected files.

## Workflow

1. Run `scripts/scan_todos.py --repo <path>` to scan the whole repo.
2. Run `scripts/scan_todos.py --repo <path> --files ...` when only a subset changed.
3. Review the generated JSON path.
4. Run `scripts/show_todos.py --repo <path>` to summarize totals and surface high-priority `FIXME` entries.

## Resources

- Script: `scripts/scan_todos.py`
- Script: `scripts/show_todos.py`
