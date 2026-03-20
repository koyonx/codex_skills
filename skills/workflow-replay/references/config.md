# Workflow Replay Config

This skill has no config file. Settings are built into the script.

## Storage

| Path | Contents |
|------|----------|
| `~/.codex/workflow-replay/recording/` | Active recordings (JSONL per project) |
| `~/.codex/workflow-replay/recipes/` | Saved recipes (JSON per recipe) |

The data directory is created with `0700` permissions.

## Defaults

| Setting | Value | Description |
|---------|-------|-------------|
| Max steps per recording | 500 | Recording stops accepting new steps at this limit |
| Max step description length | 500 chars | Step descriptions are truncated |
| Max steps replayed | 100 | Only the first 100 steps are printed during `run` |

## Recipe Format

Saved recipes are JSON files named `<recipe-name>.json`:

```json
{
  "name": "setup-api",
  "created_at": "2025-01-15T10:30:00Z",
  "source_project": "/path/to/repo",
  "step_count": 5,
  "steps": [
    { "description": "Create routes file", "timestamp": "..." },
    { "description": "Add middleware", "timestamp": "..." }
  ]
}
```

Recipe names may only contain alphanumeric characters, hyphens, and underscores.
