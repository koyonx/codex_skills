# Command Audit Configuration Reference

## Storage Location

Audit logs are stored in `~/.codex/command-audit/` as JSONL files. Each project gets its own log file named `<project-name>_<hash>.jsonl`, where the hash is derived from the absolute project path.

The directory is created with `0700` permissions (owner-only access).

## Log Format

Each line in the JSONL file is a JSON object with the following fields:

| Field                 | Type   | Description                                   |
|-----------------------|--------|-----------------------------------------------|
| `command`             | string | The shell command that was executed            |
| `timestamp`           | string | UTC timestamp in ISO 8601 format              |
| `cwd`                 | string | Working directory at the time of execution     |
| `status`              | string | `executed` (safe) or `warned` (dangerous)      |
| `matched_pattern`     | string | Regex pattern that matched (warned entries only)|
| `pattern_description` | string | Human-readable description (warned entries only)|

## Log Rotation

- Maximum entries per log file: **1000**
- When the limit is exceeded, the oldest entries are trimmed and only the most recent 1000 entries are retained.
- Rotation is performed automatically after each write operation.

## Dangerous Patterns

The following patterns are checked (case-insensitive regex matching):

### File Operations
| Pattern | Description |
|---------|-------------|
| `rm -rf /` | Recursive force delete from root |
| `rm -rf *` | Recursive force delete wildcard |
| `rm -rf ~` | Recursive force delete home directory |

### Git Operations
| Pattern | Description |
|---------|-------------|
| `git push --force` | Force push to remote |
| `git push -f` | Force push to remote (short flag) |
| `git reset --hard` | Hard reset discarding changes |
| `git clean -f` | Force clean untracked files |
| `git checkout -- .` | Discard all working tree changes |
| `git branch -D` | Force delete a branch |

### Database Operations
| Pattern | Description |
|---------|-------------|
| `DROP TABLE/DATABASE/SCHEMA` | Drop database objects |
| `TRUNCATE TABLE` | Truncate table data |
| `DELETE FROM` | Delete rows from table |

### System Operations
| Pattern | Description |
|---------|-------------|
| `chmod 777` | Set world-writable permissions |
| `chown -R` | Recursive ownership change |
| `dd of=/dev/` | Direct write to device |
| `mkfs.` | Filesystem format |
| `kill -9 -1` | Kill all processes |
| `killall` | Kill all processes by name |

### Environment Operations
| Pattern | Description |
|---------|-------------|
| `pip install --break-system-packages` | Break system Python packages |
| `npm cache clean --force` | Force clean npm cache |
