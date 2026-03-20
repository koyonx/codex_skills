---
name: workflow-replay
description: Use this skill when the user wants to record tool operations as reusable recipes, list saved recipes, replay a recipe, or delete recipes during Codex work.
---

# Workflow Replay

## Overview

Use this skill to record sequences of tool operations (file writes, edits, shell commands) as reusable recipes that can be replayed in new contexts.
Recipes are stored under `~/.codex/workflow-replay/`.

## Workflow

1. Run `scripts/workflow_replay.py --repo <path> --action record --step "description of step"` to record a single step to the active recording.
2. Run `scripts/workflow_replay.py --repo <path> --action save --name <recipe-name>` to save the current recording as a named recipe.
3. Run `scripts/workflow_replay.py --repo <path> --action list` to list all saved recipes.
4. Run `scripts/workflow_replay.py --repo <path> --action run --name <recipe-name>` to replay a saved recipe (prints steps to stdout for context injection).
5. Run `scripts/workflow_replay.py --repo <path> --action delete --name <recipe-name>` to delete a saved recipe.

## Resources

- Script: `scripts/workflow_replay.py`
