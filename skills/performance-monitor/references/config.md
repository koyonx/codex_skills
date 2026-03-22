# Performance Monitor Configuration

## Storage

- **Base directory**: `~/.codex/performance-monitor/`
- **File format**: JSONL (one JSON object per line)
- **File naming**: Each project gets its own file, named by a SHA-256 hash of the absolute project root path (e.g., `a3f1b2c4...json`).

## Entry Format

Each JSONL entry contains the following fields:

| Field        | Type    | Description                          |
|------------- |-------- |--------------------------------------|
| `timestamp`  | string  | ISO-8601 UTC timestamp               |
| `command`    | string  | The command that was executed         |
| `duration_ms`| integer | Execution time in milliseconds       |
| `exit_code`  | integer | Process exit code                    |
| `project`    | string  | Absolute path to the project root    |

## Anomaly Detection

- **Threshold**: A command execution is flagged as anomalous if its duration exceeds **2x the rolling average** duration for that same command within the project.
- **Minimum samples**: At least 3 prior recordings of the same command are required before anomaly detection activates.

## Tracked Command Patterns

The following base commands are recognized and normalized:

| Pattern               | Category        |
|---------------------- |-----------------|
| `npm run build`       | Node.js build   |
| `npm test`            | Node.js test    |
| `yarn build`          | Node.js build   |
| `yarn test`           | Node.js test    |
| `pnpm build`          | Node.js build   |
| `pnpm test`           | Node.js test    |
| `make`                | C/C++ build     |
| `cmake --build`       | C/C++ build     |
| `cargo build`         | Rust build      |
| `cargo test`          | Rust test       |
| `go build`            | Go build        |
| `go test`             | Go test         |
| `pytest`              | Python test     |
| `jest`                | JS test         |
| `vitest`              | JS test         |
| `gradle`              | JVM build       |
| `gradlew`             | JVM build       |
| `mvn`                 | JVM build       |

## Entry Limits

- **Maximum entries per project**: 1000
- **Trimming strategy**: When the limit is reached, the oldest entries are removed to make room for new ones (FIFO).
