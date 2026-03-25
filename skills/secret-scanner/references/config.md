# Secret Scanner Config

This skill has no config file. Detection patterns and skip rules are built into the script.

## Secret Patterns Detected

- AWS Access Keys (`AKIA...`)
- GitHub Tokens (`ghp_`, `gho_`, `ghu_`, `ghs_`, `ghr_`)
- Private Keys (PEM format)
- API key/secret assignments in source code
- Secret/token/access_token assignments
- Password assignments (excludes placeholders like `your_`, `change_me`, `${}`)
- Bearer/Basic authorization tokens
- Long hex strings (40+ chars, excludes commit hash references)

## Auto-Skipped Files

Extensions skipped: `.md`, `.txt`, `.lock`, `.sum`, `.png`, `.jpg`, `.jpeg`, `.gif`, `.svg`, `.ico`, `.woff`, `.woff2`, `.ttf`, `.eot`, `.pdf`

Directories skipped: `test`, `tests`, `__tests__`, `mocks`, `__mocks__`, `fixtures`, `testdata`

File name patterns skipped: `test_*`, `*_test.*`, `*.test.*`, `*.spec.*`, `*_spec.*`, `*.mock.*`, `*.fake.*`, `*.stub.*`, `*.example`, `*.sample`, `*.template`

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `SECRET_SCANNER_HOME` | `~/.codex/secret-scanner` | Directory for scan result storage |

## Limits

- Max file size: 2 MB
