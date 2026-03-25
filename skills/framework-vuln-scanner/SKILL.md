---
name: framework-vuln-scanner
description: Use this skill when the user wants to check runtime and framework versions for EOL status or known vulnerabilities, covering Node.js, Python, Ruby, Go, and popular web frameworks.
---

# Framework Vuln Scanner

## Overview

Use this skill to detect runtime and framework versions in a project and flag those that are end-of-life or have known security concerns. Checks system runtimes and parses dependency files for framework versions.

## Workflow

1. Run `scripts/check_versions.py --repo <path>` to scan for runtime and framework versions.
2. Review the output for EOL warnings and upgrade recommendations.
3. Plan upgrades for any flagged versions, starting with the most critical.

## Resources

- Script: `scripts/check_versions.py`
