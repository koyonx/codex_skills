# Context Loader Config

Place `.context-loader.json` in the project root.

```json
{
  "files": [
    "AGENTS.md",
    "docs/architecture.md"
  ],
  "globs": [
    "src/**/*.proto",
    "docs/**/*.md"
  ]
}
```

- `files`: explicit project-relative paths
- `globs`: project-relative recursive glob patterns
- Absolute paths, `~`, and `..` are rejected
