---
name: env-sync
description: Use this skill when the user wants to compare .env files against .env.example to detect missing or extra environment variable keys, and verify .gitignore coverage.
---

# Env Sync

## Overview

Use this skill to ensure environment variable files stay in sync. It compares key names (never values) between `.env` and `.env.example`, detects missing or new keys, and checks that `.env` is listed in `.gitignore`.

## Workflow

1. Run `scripts/check_env_sync.py --repo <path>` to compare `.env` vs `.env.example` keys.
2. Review the output for missing or extra keys.
3. Add missing keys to the appropriate file.
4. Verify `.gitignore` includes `.env` to prevent secret leaks.

## Resources

- Script: `scripts/check_env_sync.py`
