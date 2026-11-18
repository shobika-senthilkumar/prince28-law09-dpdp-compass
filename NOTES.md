@"
# Day 3 Notes — PostgreSQL Integration

## 1. Database

DPDP Compass now uses PostgreSQL through SQLAlchemy.

The database connection is configured using the `DATABASE_URL`
environment variable. The real `.env` file is not committed to GitHub.

## 2. Schema

The main database table is:

- `documents`

Each document contains:

- `id`
- `external_id`
- `title`
- `source`
- `source_url`
- `document_type`
- `year`
- `description`
- `metadata`
- `sha256`
- `created_at`
- `updated_at`

The `external_id` column is unique and is used to identify each
DPDP Compass source record.

The `metadata` JSONB column is reserved for future structured legal
metadata such as section/rule references, commencement dates, and
draft/final status.

## 3. Migration

Alembic is used for database migrations.

The initial migration creates the `documents` table and the SHA-256
index.

Migration applied successfully with:

```text
uv run alembic upgrade head
