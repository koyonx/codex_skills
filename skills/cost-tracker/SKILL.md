---
name: cost-tracker
description: Use this skill when the user wants to inspect Codex token usage or session counts for a workspace, summarize recent Codex sessions, or compare usage across recent threads.
---

# Cost Tracker

## Overview

Use this skill to summarize real Codex session usage from `~/.codex/sessions` and `~/.codex/state_5.sqlite`.
It is useful for answering questions like "how much did this project use?" or "which recent sessions were expensive?"

## Workflow

1. Run `scripts/summarize_sessions.py --project-root <path>` for project totals.
2. Add `--since-days` or `--limit` for narrower slices.
3. Use the output to answer with session counts, input/output totals, and cache usage.
4. If no Codex session data exists for the target path, say so explicitly.

## Resources

- Script: `scripts/summarize_sessions.py`
