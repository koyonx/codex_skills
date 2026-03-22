---
name: command-audit
description: Use this skill when the user wants to audit shell commands executed during a session, review dangerous command patterns, or check the command execution log for a project.
---

# Command Audit

## Overview

The command-audit skill logs all shell commands executed during a coding session and warns on dangerous operations. It maintains a per-project audit trail stored as JSONL files, enabling post-session review and analysis.

Dangerous operations detected include:

- Destructive file operations (`rm -rf /`, `rm -rf *`, `rm -rf ~`)
- Destructive git commands (`git push --force`, `git push -f`, `git reset --hard`, `git clean -f`, `git checkout -- .`, `git branch -D`)
- Database destruction (`DROP TABLE`, `DROP DATABASE`, `DROP SCHEMA`, `TRUNCATE TABLE`, `DELETE FROM`)
- Unsafe permission changes (`chmod 777`, `chown -R`)
- Disk/device operations (`dd of=/dev/`, `mkfs.`)
- Process killing (`kill -9 -1`, `killall`)
- Environment-breaking installs (`pip install --break-system-packages`, `npm cache clean --force`)

## Workflow

1. **Log a command**: Each shell command executed in the session is recorded with a timestamp, working directory, and project path.
2. **Check for dangerous patterns**: Before or after execution, a command can be checked against the known dangerous patterns list. Matches are flagged with a warning status.
3. **Review the audit log**: At any time, the full audit log for a project can be displayed, showing all commands and their statuses.
4. **Generate a summary**: A session summary shows the total number of commands executed and how many triggered danger warnings.
5. **Automatic log rotation**: Logs are capped at 1000 entries per project. When the limit is exceeded, the oldest entries are automatically trimmed.

## Resources

- `scripts/audit_commands.py` - Main audit script for logging, checking, and reviewing commands.
- `references/config.md` - Configuration reference for dangerous patterns, storage location, and log rotation.
- `agents/openai.yaml` - OpenAI Codex agent interface definition.
