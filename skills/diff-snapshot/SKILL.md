---
name: diff-snapshot
description: Use this skill when the user wants to snapshot files before risky edits, inspect diffs against saved snapshots, or restore a previous file state during Codex work.
---

# Diff Snapshot

## Overview

Use this skill for manual safety checkpoints before risky edits.
It creates restorable file snapshots under `~/.codex/diff-snapshots`.

## Workflow

1. Run `scripts/snapshot.sh <file...>` before making a risky edit.
2. After the edit, run `scripts/restore.sh diff <snapshot-file>` if you need to compare.
3. Run `scripts/restore.sh restore <snapshot-file>` only when the user explicitly wants rollback.
4. Prefer snapshotting specific files or `--changed` files in a git repo instead of the whole tree.

## Resources

- Script: `scripts/snapshot.sh`
- Script: `scripts/restore.sh`
