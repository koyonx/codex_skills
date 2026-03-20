# Framework Vuln Scanner Config

This skill has no config file. Version thresholds for EOL/upgrade warnings are built into the script.

## Runtime Version Thresholds

| Runtime | Warning Condition |
|---------|-------------------|
| Node.js | Odd-numbered (non-LTS) or <= 18 |
| Python | 2.x (EOL) or 3.x where minor <= 9 |
| Ruby | < 3.1 |
| Go | Minor version <= 21 |

## Framework Version Thresholds

| Framework | Source File | Warning Condition |
|-----------|------------|-------------------|
| React | `package.json` | <= 16 |
| Next.js | `package.json` | <= 13 |
| Express | `package.json` | <= 3 |
| Vue.js | `package.json` | <= 2 |
| Angular | `package.json` (`@angular/core`) | <= 15 |
| Django | `requirements.txt` | <= 3 |
| Flask | `requirements.txt` | <= 1 |
| Rails | `Gemfile` | <= 5 (EOL), 6 (nearing EOL) |

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `FVS_HOME` | `~/.codex/framework-vuln-scanner` | Directory for scan result storage |
