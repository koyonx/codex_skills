---
name: error-memory
description: Use this skill when the user wants to record command errors with their solutions, or look up previously seen error patterns for the current project.
---

# Error Memory

## Overview

Use this skill to build a per-project database of error patterns and their solutions.
When an error is encountered, record it; when it recurs, the stored solution is surfaced instantly.

## Workflow

1. **Record an error**: Run `scripts/record_error.py --repo <path> --error "<message>" --command "<cmd>" --solution "<fix cmd>"`.
2. **Show known errors**: Run `scripts/show_errors.py --repo <path>` to display the top known error patterns and their fixes.
3. Error data is stored per project under `~/.codex/error-memory/`.
4. Entries are capped at 200 per project; oldest entries are pruned automatically.

## Resources

- Script: `scripts/record_error.py`
- Script: `scripts/show_errors.py`
