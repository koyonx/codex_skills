---
name: dead-code-detector
description: Use this skill when the user wants to detect dead references after renaming or removing functions, classes, or variables, by scanning the repository for remaining usages of deleted identifiers.
---

# Dead Code Detector

## Overview

Use this skill after editing source files to detect remaining references to identifiers that were removed or renamed.
It extracts defined names (functions, classes, variables) from old content, compares with new content, and searches the repository for stale references.
Supports 12+ programming languages.

## Workflow

1. Run `scripts/detect_dead_refs.py --repo <path> --files <file1> <file2>` after editing files.
2. Review the output listing removed identifiers and the files that still reference them.
3. Update or remove stale references in the reported files.
4. Re-run to confirm all dead references are cleared.

## Resources

- Script: `scripts/detect_dead_refs.py`
