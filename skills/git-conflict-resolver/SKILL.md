---
name: git-conflict-resolver
description: Use this skill when the user wants to detect unresolved merge conflicts in a repository, list conflicted files with conflict counts, or get branch and merge context after a merge or rebase.
---

# Git Conflict Resolver

## Overview

Use this skill to detect unresolved merge conflicts in a git repository.
It lists conflicted files with the number of conflict markers in each, shows the current branch, and provides merge context when available.

## Workflow

1. Run `scripts/detect_conflicts.py --repo <path>` to scan for unresolved merge conflicts.
2. Review the output listing conflicted files and conflict counts.
3. Use the file list to read and resolve each conflict.
4. Re-run after resolution to confirm all conflicts are cleared.

## Resources

- Script: `scripts/detect_conflicts.py`
