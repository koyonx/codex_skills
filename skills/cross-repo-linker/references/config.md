# Cross Repo Linker Config

This skill has no project-level config file. Links are stored globally at `~/.codex/cross-repo-linker/links.json`.

## Storage

The links file is a JSON array of linked repository entries:

```json
[
  {
    "name": "my-other-repo",
    "path": "/Users/you/projects/my-other-repo",
    "shared_deps": "npm:12, pip:3",
    "linked_at": "2025-01-15T10:30:00Z"
  }
]
```

The directory is created with `0700` permissions.

## Defaults

| Setting | Value | Description |
|---------|-------|-------------|
| Max links | 10 | Maximum number of linked repositories |

## Constraints

- Only repositories under `$HOME` can be linked
- Target must be a git repository (`.git` directory must exist)
- Repository names are derived from the directory name
- Duplicate names are not allowed

## Shared Dependency Detection

When linking, the script automatically detects shared dependencies by comparing:

- `package.json` (npm dependencies and devDependencies)
- `requirements.txt` (pip packages)
