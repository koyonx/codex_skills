---
name: migration-tracker
description: Use this skill when the user modifies model or schema files and needs a reminder to create database migrations, or when they want to check the current migration status of a project.
---

# Migration Tracker

## Overview

Use this skill to detect model/schema changes that may require a database migration and to check migration status.
Supports Django, SQLAlchemy/Alembic, Rails (ActiveRecord), Prisma, TypeORM, Sequelize, and GORM.

## Workflow

1. Run `scripts/check_migrations.py --repo <path>` to scan for model/schema changes that need migrations.
2. Run `scripts/check_migrations.py --repo <path> --status` to show the current migration status (file counts, uncommitted migrations).
3. Review the output and create the appropriate migration using your framework's CLI.
4. Re-run with `--status` to confirm the migration was created.

## Resources

- Script: `scripts/check_migrations.py`
