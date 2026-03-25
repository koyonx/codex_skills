# Dependency Watchdog Config

This skill has no config file. Package managers are auto-detected from dependency files in the project root.

## Supported Package Managers

| Dependency Files | Audit Tool | Install Hint |
|------------------|------------|--------------|
| `package.json`, `package-lock.json`, `yarn.lock`, `pnpm-lock.yaml` | `npm audit` | (built-in) |
| `requirements.txt`, `Pipfile`, `pyproject.toml` | `pip-audit` | `pip install pip-audit` |
| `go.mod`, `go.sum` | `govulncheck` | `go install golang.org/x/vuln/cmd/govulncheck@latest` |
| `Gemfile`, `Gemfile.lock` | `bundler-audit` | `gem install bundler-audit` |
| `Cargo.toml`, `Cargo.lock` | `cargo audit` | `cargo install cargo-audit` |
| `composer.json`, `composer.lock` | `composer audit` | (built-in with Composer) |

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `DEP_WATCHDOG_HOME` | `~/.codex/dependency-watchdog` | Directory for audit result storage |

## Limits

- Audit command timeout: 30 seconds per package manager
