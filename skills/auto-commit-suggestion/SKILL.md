---
name: auto-commit-suggestion
description: Use this skill when the user wants to know whether a git workspace is ready for a commit, asks for a threshold-based change summary, or wants help deciding when to checkpoint work in Codex.
---

# Auto Commit Suggestion

## Overview

Use this skill to evaluate commit readiness in the current git repository.
It is a manual Codex skill, not an automatic hook.

## Workflow

1. Run `scripts/check_commit_threshold.sh` from the repo root or pass `--repo`.
2. Review the changed-file count, staged count, and top changed paths.
3. If the threshold is exceeded, suggest a checkpoint commit and explain why.
4. If the user wants to commit, help prepare a message but do not commit unless asked.

## Thresholds

- Default threshold is `5`.
- Override with `--threshold <n>` or `AUTO_COMMIT_THRESHOLD=<n>`.
- Treat many untracked files or many staged files as stronger commit signals.

## Resources

- Script: `scripts/check_commit_threshold.sh`
