# Error Memory Config

This skill has no config file. Settings are built into the scripts.

## Storage

Error databases are stored per project at `~/.codex/error-memory/<project-key>.json`.

The directory is created with `0700` permissions.

## Defaults

| Setting | Value | Description |
|---------|-------|-------------|
| Max entries | 200 | Oldest entries are pruned when the limit is exceeded |
| Max error text | 500 chars | Error messages and solutions are truncated |
| Default top | 10 | Number of entries shown by `show_errors.py --top` |

## CLI Options

```bash
# Record an error with its solution
scripts/record_error.py --repo <path> --error "<message>" --command "<cmd>" --solution "<fix>"

# Show top known errors (default 10)
scripts/show_errors.py --repo <path> --top 20
```

The `--top` flag on `show_errors.py` controls how many entries are displayed, sorted by resolved count (most frequent first).
