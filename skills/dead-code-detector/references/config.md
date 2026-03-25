# Dead Code Detector Config

This skill has no config file. Supported extensions and ignored names are built into the script.

## Supported Extensions

`py`, `js`, `ts`, `jsx`, `tsx`, `go`, `rs`, `rb`, `java`, `php`, `c`, `cpp`, `h`, `hpp`, `cs`, `swift`, `kt`

## How It Works

1. Reads the current version of the edited file and extracts defined names (functions, classes, variables)
2. Reads the previous version from `git show HEAD:<file>`
3. Computes removed identifiers (names in previous but not in current)
4. Searches the repo for files that still reference the removed names

## Ignored Names

Short or generic names are excluded from detection (e.g., `self`, `this`, `true`, `false`, `None`, `return`, `import`, single-letter variables, and common short identifiers like `get`, `set`, `run`, `add`).

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `DEAD_CODE_DETECTOR_HOME` | `~/.codex/dead-code-detector` | Directory for report storage |

## Limits

- Max file size: 2 MB
- Max 10 referencing files reported per identifier
- Reference search timeout: 15 seconds per identifier
