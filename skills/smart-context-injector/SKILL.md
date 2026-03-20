---
name: smart-context-injector
description: Use this skill when the user wants to analyze a prompt for file references and identifiers, find related source and test files, and surface recent git changes for better context.
---

# Smart Context Injector

## Overview

Use this skill to automatically enrich a user prompt with related context: referenced files, identifier definitions, corresponding test files, and recent git changes.
Output is printed to stdout for context injection.

## Workflow

1. Run `scripts/enrich_context.py --repo <path> --prompt "user prompt text"` to analyze a prompt and print related context.
2. Run `scripts/enrich_context.py --repo <path> --files <file1> <file2> ...` to find test files and recent changes for explicit file paths.
3. Review the stdout output which lists related files, test files, and recent git history.

## Resources

- Script: `scripts/enrich_context.py`
