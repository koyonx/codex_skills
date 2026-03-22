# Configuration Reference

## Thresholds

| Metric | CLI Flag | Environment Variable | Default |
|---|---|---|---|
| File line count | `--max-lines` | `COMPLEXITY_MAX_LINES` | 300 |
| Function / method length | `--max-func-lines` | `COMPLEXITY_MAX_FUNC_LINES` | 50 |
| Nesting depth | `--max-nesting` | `COMPLEXITY_MAX_NESTING` | 5 |

CLI flags take precedence over environment variables. Environment variables take precedence over built-in defaults.

## Supported Languages

The function-length check recognises function/method definitions in the following languages:

| Extension(s) | Language |
|---|---|
| `.py` | Python |
| `.js`, `.jsx` | JavaScript |
| `.ts`, `.tsx` | TypeScript |
| `.go` | Go |
| `.rs` | Rust |
| `.rb` | Ruby |
| `.java` | Java |
| `.php` | PHP |
| `.c`, `.h` | C |
| `.cpp`, `.hpp` | C++ |
| `.cs` | C# |
| `.swift` | Swift |
| `.kt` | Kotlin |

## Skipped Files

The following files are automatically excluded from analysis:

- **Test files** -- filenames matching `test_*`, `*_test.*`, `*.test.*`, or `*.spec.*`.
- **Configuration files** -- common config filenames and extensions (e.g., `*.json`, `*.yaml`, `*.yml`, `*.toml`, `*.ini`, `*.cfg`, `*.xml`, `Makefile`, `Dockerfile`).
- **Large files** -- any file exceeding 2 MB in size.

## Usage Examples

```bash
# Check git-modified files with default thresholds
python3 scripts/check_complexity.py --repo /path/to/project

# Check specific files with custom thresholds
python3 scripts/check_complexity.py --repo /path/to/project \
  --files src/main.py src/utils.py \
  --max-lines 200 --max-func-lines 30 --max-nesting 4

# Override via environment variables
export COMPLEXITY_MAX_LINES=500
export COMPLEXITY_MAX_FUNC_LINES=80
python3 scripts/check_complexity.py --repo /path/to/project
```
