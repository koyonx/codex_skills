---
name: branch-guard
description: Use this skill when the user wants to commit, push, create a branch, or verify whether the current branch is protected before making git changes in Codex.
---

# Branch Guard

## Overview

Use this skill before any commit or push workflow.
It checks whether the current branch is protected and can reject risky direct commits or pushes.

## Workflow

1. Run `scripts/check_branch.sh --command "<planned git command>"`.
2. If the current branch is protected, stop and create a feature branch first.
3. If the branch is safe, continue with the requested git workflow.
4. When branch policy is project-specific, read `.branch-guard.json` from the git root.

## Protected Branch Config

See `references/config.md` for the config file shape.

## Resources

- Script: `scripts/check_branch.sh`
- Reference: `references/config.md`
