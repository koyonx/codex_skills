# Git Conflict Resolver Config

This skill has no config file. It operates purely on git state.

## Usage

```bash
scripts/detect_conflicts.py --repo <path>
```

The script:

1. Runs `git diff --name-only --diff-filter=U` to find conflicted files
2. Counts `<<<<<<<` markers in each file
3. Reports the current branch and merge head (if in a merge)
4. Saves the report as JSON

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `GIT_CONFLICT_RESOLVER_HOME` | `~/.codex/git-conflict-resolver` | Directory for report storage |

## Limits

- Maximum 20 conflicted files reported per scan
