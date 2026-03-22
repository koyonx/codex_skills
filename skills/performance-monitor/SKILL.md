---
name: performance-monitor
description: Use this skill when the user wants to track command execution times, detect performance anomalies, review build time trends, or identify slow commands in a project.
---

# Performance Monitor

## Overview

The Performance Monitor skill tracks and analyzes command execution times across projects. It records build, test, and compilation durations, detects performance anomalies, and surfaces trends to help developers identify slow commands and regressions.

## Workflow

1. **Record**: After a command finishes, record its name, duration, and exit code against the current project.
2. **Analyze Trends**: Query historical execution data to see how build/test times have changed over time.
3. **Detect Anomalies**: Automatically flag commands whose duration exceeds 2x the rolling average for that command in the project.
4. **Report**: Present summaries, trend charts (text-based), and anomaly alerts to the user.

## Tracked Commands

The following command patterns are automatically recognized:

- **Node.js**: `npm run build`, `npm test`, `yarn build`, `yarn test`, `pnpm build`, `pnpm test`
- **C/C++**: `make`, `cmake --build`
- **Rust**: `cargo build`, `cargo test`
- **Go**: `go build`, `go test`
- **Python**: `pytest`
- **JavaScript Testing**: `jest`, `vitest`
- **JVM**: `gradle`, `gradlew`, `mvn`

## Resources

- **Storage**: `~/.codex/performance-monitor/<project-hash>.jsonl`
- **Configuration**: See `references/config.md` for thresholds, limits, and tracked patterns.
- **Script**: `scripts/track_performance.py` — CLI entry point for recording and querying data.
