# Code Convention Learner Config

This skill has no config file. Settings are built into the script.

## Supported Languages

`javascript` (`.js`, `.jsx`), `typescript` (`.ts`, `.tsx`), `python` (`.py`), `go` (`.go`), `rust` (`.rs`), `ruby` (`.rb`), `java` (`.java`)

## Conventions Detected

| Convention | Languages |
|------------|-----------|
| Indentation (spaces vs tabs, 2 vs 4) | All |
| Quote style (single vs double) | JavaScript, TypeScript, Python |
| Semicolons (yes vs no) | JavaScript, TypeScript |
| Naming (camelCase vs snake_case) | JavaScript, TypeScript, Python, Ruby |
| Trailing commas | JavaScript, TypeScript |

## Storage

Convention data is stored per project at `~/.codex/code-convention-learner/<project-key>.json`.

The directory is created with `0700` permissions.

## Defaults

| Setting | Value | Description |
|---------|-------|-------------|
| Max files per language | 100 | Analysis stops after this many files per language |
| Max file size | 1 MB | Files larger than this are skipped |
| Min lines | 5 | Files with fewer lines are skipped |
| Min files for reporting | 5 | A language needs at least 5 analyzed files to show conventions |

## Skipped Directories

`node_modules`, `vendor`, `__pycache__`, `.git`, `dist`, `build`, `target`, and any directory starting with `.`
