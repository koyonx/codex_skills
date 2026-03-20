# API Doc Sync Config

This skill has no config file. Behavior is controlled by built-in defaults.

## Supported Frameworks

Route detection patterns are built in for these file extensions:

| Extension | Frameworks |
|-----------|------------|
| `.py` | FastAPI, Flask, Django |
| `.js` | Express, Nest.js, Next.js |
| `.ts` | Express, Nest.js, Next.js |
| `.go` | Gin, Echo, net/http |
| `.rb` | Rails |
| `.java` | Spring |
| `.php` | Laravel |

## Documentation Files Checked

The script looks for these files in the project root:

- `openapi.yaml` / `openapi.yml` / `openapi.json`
- `swagger.yaml` / `swagger.yml` / `swagger.json`
- `api-spec.yaml` / `api-spec.yml`
- `docs/api` / `doc/api`

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `API_DOC_SYNC_HOME` | `~/.codex/api-doc-sync` | Directory for scan result storage |

## Limits

- Max file size: 2 MB (files larger than this are skipped)
