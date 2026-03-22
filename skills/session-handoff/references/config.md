# Session Handoff Configuration

## Storage Location

Handoff notes are stored in `~/.codex/session-handoff/`. The directory is created automatically on the first `generate` action.

Each note is saved as a separate JSON file named `<session_id>.json`.

## JSON Format

```json
{
  "session_id": "a1b2c3d4e5f6",
  "project_path": "/absolute/path/to/project",
  "project_key": "_absolute_path_to_project",
  "timestamp": "2026-03-22T12:00:00+00:00",
  "git_branch": "main",
  "git_status": "M src/app.py\n?? new_file.txt",
  "recent_commits": "abc1234 Fix login bug\ndef5678 Add user model"
}
```

### Fields

| Field | Description |
|---|---|
| `session_id` | Unique 12-character hex identifier for the session note. |
| `project_path` | Absolute, resolved path to the project root. |
| `project_key` | Filesystem-safe key derived from the project path; used to filter notes per project. |
| `timestamp` | ISO 8601 UTC timestamp of when the note was generated. |
| `git_branch` | Current branch at the time of generation. |
| `git_status` | Output of `git status --short` (uncommitted changes). |
| `recent_commits` | Last 10 commits from `git log --oneline -10`. |

## Cleanup Policy

Notes older than **30 days** are automatically deleted whenever any action (`generate`, `load`, `list`) is executed. This keeps the storage directory manageable without requiring manual maintenance.

## Limits

- The `list` action displays a maximum of **10** notes per project, sorted newest-first.
