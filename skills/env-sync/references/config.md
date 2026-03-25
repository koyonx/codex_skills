# Env Sync Config

This skill has no config file. File paths are detected automatically in the project root.

## Files Scanned

Env files checked:

- `.env`, `.env.local`, `.env.development`, `.env.production`, `.env.staging`, `.env.test`

Example/template files checked:

- `.env.example`, `.env.sample`, `.env.template`

The first example file found is used as the reference for key comparison.

## What It Checks

1. Compares key names (never values) between `.env` and `.env.example`
2. Reports keys present in `.env` but missing from the example file
3. Reports keys in the example file but missing from `.env`
4. Verifies `.env` is listed in `.gitignore`

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `ENV_SYNC_HOME` | `~/.codex/env-sync` | Directory for result storage |
