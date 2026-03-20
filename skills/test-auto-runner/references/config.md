# Test Auto Runner Config

This skill has no config file. Test runner selection is auto-detected from file extensions and project files.

## Test Runner Selection

| Extension | Runner | Condition |
|-----------|--------|-----------|
| `.py` | `pytest` | `pytest` in PATH, otherwise `python -m pytest` |
| `.js`, `.jsx` | `npx jest` | `package.json` exists |
| `.ts`, `.tsx` | `npx vitest` | `"vitest"` in `package.json` |
| `.ts`, `.tsx` | `npx jest` | Fallback when vitest not found |
| `.go` | `go test` | Always |
| `.rs` | `cargo test` | `#[cfg(test)]` found in source |
| `.rb` | `bundle exec rspec` | `"rspec"` in `Gemfile` |
| `.rb` | `ruby -Itest` | Fallback |

## Test File Discovery

| Language | Test File Patterns |
|----------|-------------------|
| Python | `test_<name>.py`, `<name>_test.py` in `tests/`, `test/`, or same dir |
| JS/JSX | `<name>.test.js`, `<name>.spec.js`, `__tests__/<name>.test.js` |
| TS/TSX | `<name>.test.ts`, `<name>.test.tsx`, `<name>.spec.ts` |
| Go | `<name>_test.go` in same directory |
| Ruby | `spec/<name>_spec.rb`, `test/test_<name>.rb` |
| Rust | Inline `#[cfg(test)]` in same file |

## Defaults

| Setting | Value |
|---------|-------|
| Timeout | 30 seconds per test run |
| State directory | `~/.codex/test-auto-runner/` |
