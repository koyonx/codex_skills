---
name: test-auto-runner
description: Use this skill when the user wants to find and run tests related to specific source files that were changed.
---

# Test Auto Runner

## Overview

Use this skill after editing source files to automatically discover and execute the corresponding test files.
It supports multiple languages and test frameworks with a 30-second timeout.

## Workflow

1. Run `scripts/run_tests.py --repo <path> --files <file1> <file2> ...` with the repository root and the changed source files.
2. The script detects the language from file extensions and locates test files using naming conventions.
3. Tests are executed with the appropriate runner (pytest, Jest, go test, cargo test, RSpec/Minitest).
4. Review the output: PASS, FAIL, or TIMEOUT results are reported per file.

## Supported Languages

| Language   | Test Runner         | Test File Patterns                                    |
|------------|---------------------|-------------------------------------------------------|
| Python     | pytest              | `test_<name>.py`, `<name>_test.py`                   |
| JavaScript | Jest                | `<name>.test.js`, `<name>.spec.js`, `__tests__/`     |
| TypeScript | Jest / Vitest       | `<name>.test.ts`, `<name>.spec.ts`, `__tests__/`     |
| Go         | go test             | `<name>_test.go`                                      |
| Rust       | cargo test          | `#[cfg(test)]` in same file                           |
| Ruby       | RSpec / Minitest    | `spec/<name>_spec.rb`, `test/test_<name>.rb`         |

## Resources

- Script: `scripts/run_tests.py`
