---
name: session-history
description: Use this skill when the user wants to save, list, or view Codex session history as readable Markdown transcripts.
---

# Session History

## Overview

Use this skill to save Codex session transcripts as human-readable Markdown files, list saved sessions for a project, or view a specific session log.
Sessions are stored under `~/.codex/session-history/`.

## Workflow

1. Run `scripts/session_history.py --repo <path> --action save` to save the current or most recent session transcript as Markdown.
2. Run `scripts/session_history.py --repo <path> --action list` to list all saved session logs for the project.
3. Run `scripts/session_history.py --repo <path> --action show --session-id <id>` to display a specific session log.

## Resources

- Script: `scripts/session_history.py`
