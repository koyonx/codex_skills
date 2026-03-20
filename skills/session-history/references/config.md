# Session History Config

This skill has no config file. Settings are built into the script.

## Storage

| Path | Contents |
|------|----------|
| `~/.codex/sessions/` | Source transcript files (JSONL/JSON, read-only) |
| `~/.codex/session-history/sessions/<project-key>/` | Saved Markdown session logs |

Session logs are saved as `<timestamp>_<session-id>.md`.

## Defaults

| Setting | Value | Description |
|---------|-------|-------------|
| Max transcript size | 100 MB | Transcripts larger than this are skipped |

## Actions

```bash
# Save the most recent session as Markdown
scripts/session_history.py --repo <path> --action save

# List saved sessions for a project
scripts/session_history.py --repo <path> --action list

# View a specific session log
scripts/session_history.py --repo <path> --action show --session-id <id>
```

The `--session-id` for `show` supports partial matching -- it searches for any saved file containing the given ID string.
