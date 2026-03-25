# Migration Tracker Config

This skill has no config file. ORM frameworks are auto-detected from file content and location.

## Supported Frameworks

| Framework | Detection Rule | Migration Command |
|-----------|---------------|-------------------|
| Django | `models.py` or `/models/` with `class Foo(Model)` | `python manage.py makemigrations` |
| SQLAlchemy/Alembic | `.py` files with `Column`, `relationship`, `mapped_column`, etc. | `alembic revision --autogenerate -m 'desc'` |
| Rails | `.rb` in `/models/` with `< ApplicationRecord` or `< ActiveRecord::Base` | `rails generate migration Name` |
| Prisma | `schema.prisma` | `npx prisma migrate dev --name desc` |
| TypeORM | `.ts` with `@Entity()`, `@Column()` | `npx typeorm migration:generate -n Name` |
| Sequelize | `.js`/`.ts` with `sequelize.define`, `DataTypes.` | `npx sequelize-cli migration:generate --name name` |
| GORM | `.go` with `gorm.Model` or `gorm:"` | Manual migration or `AutoMigrate` |

## Migration Directories Scanned

- `migrations`
- `db/migrate`
- `alembic/versions`
- `prisma/migrations`

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `MIGRATION_TRACKER_HOME` | `~/.codex/migration-tracker` | Directory for report storage |

## Limits

- Max file size: 2 MB
