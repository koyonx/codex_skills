---
name: file-complexity-guard
description: Use this skill when the user wants to check file complexity metrics, find overly long functions, detect deep nesting, or identify files that should be split into smaller modules.
---

# File Complexity Guard

## Overview

File Complexity Guard analyzes source files in a project to surface complexity warnings. It checks file length, function/method length, and nesting depth against configurable thresholds. The goal is to catch files that have grown unwieldy before they become a maintenance burden.

## Workflow

1. Determine which files to analyze. By default the skill checks files modified according to `git diff --name-only`. When specific paths are provided via `--files`, those are used instead.
2. For each file, run three checks:
   - **File line count** -- flag files that exceed the line threshold.
   - **Function / method length** -- use language-aware patterns to locate function boundaries and measure their length.
   - **Nesting depth** -- use indentation analysis to detect deeply nested blocks.
3. Skip files that are tests (`test_*`, `*_test.*`, `*.test.*`, `*.spec.*`), configuration files, or files larger than 2 MB.
4. Print a per-file report listing every threshold violation along with the measured value and the threshold.

## Thresholds

| Metric | Default | Environment Variable |
|---|---|---|
| File line count | 300 | `COMPLEXITY_MAX_LINES` |
| Function / method length (lines) | 50 | `COMPLEXITY_MAX_FUNC_LINES` |
| Nesting depth | 5 | `COMPLEXITY_MAX_NESTING` |

All thresholds can also be overridden via CLI flags (`--max-lines`, `--max-func-lines`, `--max-nesting`).

## Resources

- `scripts/check_complexity.py` -- main analysis script.
- `references/config.md` -- full configuration reference.
- `agents/openai.yaml` -- agent interface definition.
