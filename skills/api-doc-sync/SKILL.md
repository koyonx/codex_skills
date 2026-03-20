---
name: api-doc-sync
description: Use this skill when the user wants to scan a repository for API route definitions and verify that API documentation (openapi.yaml, swagger.json, etc.) exists and is up to date.
---

# API Doc Sync

## Overview

Use this skill to detect API endpoint definitions across multiple frameworks and check whether corresponding API documentation files exist in the project.

## Workflow

1. Run `scripts/check_api_docs.py --repo <path>` to scan the repository for API route definitions.
2. Review the output for detected endpoints and documentation status.
3. If documentation is missing, create an `openapi.yaml` or `swagger.json` in the project root.
4. If documentation exists but endpoints have changed, update the spec to reflect current routes.

## Resources

- Script: `scripts/check_api_docs.py`
