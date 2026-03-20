---
name: change-impact-analyzer
description: Use this skill when the user wants to understand the impact of file changes by analyzing import and dependency graphs to find affected files.
---

# Change Impact Analyzer

## Overview

Use this skill after editing source files to discover which other files depend on the changed files.
It analyzes import statements and dependency graphs across multiple languages.

## Workflow

1. Run `scripts/analyze_impact.py --repo <path> --files <file1> <file2> ...` with the repository root and the changed files.
2. The script extracts exports from each changed file.
3. It searches for other files that import or reference those exports.
4. It also locates related test files and type definitions.
5. Review the impact report to decide which files need attention.

## Supported Languages

Python, JavaScript, TypeScript, Go, Rust, Ruby, Java, Kotlin.

## Resources

- Script: `scripts/analyze_impact.py`
