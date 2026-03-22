---
name: session-handoff
description: Use this skill when the user wants to generate handoff notes for session continuity, load previous session context, or transfer work state between Codex sessions.
---

# Session Handoff

## Overview

Session Handoff enables seamless context transfer between Codex sessions. At the end of a session, it generates structured handoff notes capturing current work state including git branch, uncommitted changes, and recent commit history. When starting a new session, these notes can be loaded to restore full context and resume work without losing momentum.

## Workflow

1. **Generate** -- Run `session_handoff.py --repo <path> --action generate` to capture the current session state. The script records the git branch, working tree status, and recent commits into a timestamped JSON file stored in `~/.codex/session-handoff/`.

2. **Load** -- Run `session_handoff.py --repo <path> --action load --latest` (or `--session-id <id>`) at the start of a new session to restore previous context. The loaded note is printed as structured output for the agent to consume.

3. **List** -- Run `session_handoff.py --repo <path> --action list` to display available handoff notes for the current project. Up to 10 notes are shown, sorted by most recent first.

4. **Auto-cleanup** -- Notes older than 30 days are automatically removed during any action to keep storage tidy.

## Resources

- `scripts/session_handoff.py` -- Main script for generate / load / list operations.
- `references/config.md` -- Storage location, JSON format, and cleanup policy documentation.
- `agents/openai.yaml` -- Agent interface definition.
