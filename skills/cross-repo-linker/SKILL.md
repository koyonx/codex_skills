---
name: cross-repo-linker
description: Use this skill when the user wants to link, unlink, list, or check cross-repository dependencies between related projects.
---

# Cross Repo Linker

## Overview

Use this skill to manage relationships between multiple repositories.
It tracks linked repos, detects shared dependencies, and checks status across linked projects.

## Workflow

1. **Link a repo**: Run `scripts/manage_links.py --repo <path> --action link --target <target-path>`.
2. **Unlink a repo**: Run `scripts/manage_links.py --repo <path> --action unlink --target <name>`.
3. **List linked repos**: Run `scripts/manage_links.py --repo <path> --action list`.
4. **Check status**: Run `scripts/manage_links.py --repo <path> --action check` to see uncommitted changes and branch info across all linked repos.
5. Links are stored in `~/.codex/cross-repo-linker/links.json`, limited to 10 entries.

## Resources

- Script: `scripts/manage_links.py`
