# Smart Context Injector Config

This skill has no config file. Settings are built into the script.

## How It Works

1. Extracts file path references from the user prompt (e.g., `src/utils/auth.ts`)
2. Extracts identifier names (PascalCase class names, snake_case function names)
3. Searches the repo for files containing those identifiers
4. Locates corresponding test files for all discovered files
5. Retrieves recent git log entries (last 3 commits) for discovered files

## Defaults

| Setting | Value | Description |
|---------|-------|-------------|
| Max related files | 8 | Maximum number of related files returned |
| Max git diff lines | 30 | Git diff output limit |
| Max output lines | 50 | Total output is truncated after this |
| Min prompt length | 10 | Prompts shorter than this are not analyzed |
| Max identifiers | 5 | Maximum identifiers extracted from a prompt |
| Git log depth | 3 | Commits shown per file |
| Files checked for git log | 3 | Only the first 3 files get git history |

## Supported File Extensions for Search

`.py`, `.ts`, `.tsx`, `.js`, `.jsx`, `.go`, `.rs`, `.java`, `.rb`, `.php`

## Test File Discovery

Test files are searched in `test/`, `tests/`, `spec/`, `__tests__/` (including `unit/`, `integration/`, `e2e/` subdirectories) using patterns: `test_<name>`, `<name>_test`, `<name>.test`, `<name>.spec`.
