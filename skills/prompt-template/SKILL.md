---
name: prompt-template
description: Use this skill when the user wants to start from a reusable prompt template for review, refactoring, tests, or a custom template stored under ~/.codex/prompt-templates.
---

# Prompt Template

## Overview

Use this skill to fetch a reusable prompt body before starting work.
Built-in templates live in `assets/templates`, and user overrides live in `~/.codex/prompt-templates`.

## Workflow

1. Run `scripts/render_template.py --list` to see available templates.
2. Run `scripts/render_template.py <name>` to print the chosen template.
3. If a user template exists with the same name, prefer the user template over the built-in one.
4. After printing the template, continue the task using the rendered prompt content.

## Resources

- Script: `scripts/render_template.py`
- Assets: `assets/templates/`
