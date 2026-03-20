---
name: secret-scanner
description: Use this skill when the user wants to scan files or a repository for hardcoded secrets such as API keys, tokens, passwords, or private keys before committing or deploying.
---

# Secret Scanner

## Overview

Use this skill to scan source files for accidentally hardcoded secrets.
It detects AWS keys, GitHub tokens, private keys, API key assignments, password assignments, Bearer/Basic auth tokens, and suspicious long hex strings.
Documentation and test/mock files are automatically skipped.

## Workflow

1. Run `scripts/scan_secrets.py --repo <path>` to scan the entire repository.
2. Run `scripts/scan_secrets.py --repo <path> --files <file1> <file2>` to scan specific files.
3. Review the JSON output for detected secrets and their locations.
4. Replace hardcoded secrets with environment variables or a secrets manager.

## Resources

- Script: `scripts/scan_secrets.py`
