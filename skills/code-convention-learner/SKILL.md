---
name: code-convention-learner
description: Use this skill when the user wants to analyze a project's coding conventions or see what style patterns have been learned from the codebase.
---

# Code Convention Learner

## Overview

Use this skill to scan source files and learn coding conventions such as indentation style, quote preference, semicolon usage, naming conventions, and trailing commas.
Conventions are stored per project and per language.

## Workflow

1. **Learn conventions**: Run `scripts/learn_conventions.py --repo <path> --learn` to scan source files and record style patterns.
2. **Show conventions**: Run `scripts/learn_conventions.py --repo <path> --show` to display the learned conventions for each language.
3. Supports: JavaScript, TypeScript, Python, Go, Rust, Ruby, Java.
4. Convention data is stored per project under `~/.codex/code-convention-learner/`.
5. Analysis is limited to 100 files per language and files under 1 MB.

## Resources

- Script: `scripts/learn_conventions.py`
