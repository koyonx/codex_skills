# Change Impact Analyzer Config

This skill has no config file. Import patterns and supported languages are built into the script.

## Supported Languages

Python, TypeScript, JavaScript (including JSX/TSX/MJS), Go, Rust, Java, Kotlin, Ruby, PHP, C, C++, C#, Swift.

## How Imports Are Traced

The script finds affected files by:

1. Extracting exported names from the changed file (functions, classes, types, etc.)
2. Searching the repo for files that reference the module name or exported identifiers via `grep -Frl`
3. Locating corresponding test files
4. Locating `.d.ts` type definition files (TypeScript/JavaScript)

## Export Extraction Patterns

| Language | Patterns |
|----------|----------|
| JS/TS | `export function/class/const/type/interface/enum`, `export { ... }` |
| Python | `class`/`def` definitions, `__all__` |
| Go | Capitalized `func`/`type`/`var`/`const` |
| Java/Kotlin | `public class/interface/enum` |
| Rust | `pub fn/struct/enum/trait/type/const/static/mod` |
| Ruby | `class`/`module`/`def` |

## Defaults

| Setting | Value | Description |
|---------|-------|-------------|
| Max impact files | 10 | Maximum number of affected files reported per changed file |
| Max output lines | 40 | Output is truncated after this many lines |
| State directory | `~/.codex/change-impact-analyzer/` | Directory for state storage |
