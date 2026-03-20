---
name: dependency-watchdog
description: Use this skill when the user wants to check project dependencies for known vulnerabilities across npm, pip, go, bundler, cargo, and composer ecosystems.
---

# Dependency Watchdog

## Overview

Use this skill to audit project dependencies for known vulnerabilities. It detects dependency files, identifies the package manager, and runs the appropriate audit command.

## Workflow

1. Run `scripts/audit_deps.py --repo <path>` to detect dependency files and summarize status.
2. Run `scripts/audit_deps.py --repo <path> --audit` to execute a full vulnerability audit using available tools.
3. Review the output for vulnerability counts and severity levels.
4. Address critical and high-severity vulnerabilities first.

## Resources

- Script: `scripts/audit_deps.py`
