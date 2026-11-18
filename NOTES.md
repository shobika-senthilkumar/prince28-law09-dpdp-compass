# Day 3 Notes — PostgreSQL Integration

## 1. Database

DPDP Compass now uses PostgreSQL through SQLAlchemy.

The database connection is configured using the `DATABASE_URL`
environment variable. The real `.env` file is not committed to GitHub.

## 2. Schema

The main database tables are:

- `documents`
- `pages`


Each document contains:

- `id`
- `external_id`
- `title`
- `source`
- `source_url`
- `doc_type`
- `year`
- `description`
- `licence`
- `published_on`
- `sha256`
- `metadata`
- `created_at`
- `updated_at`

The `external_id` column is unique and is used to identify each
DPDP Compass source record.

The `metadata` JSONB column stores filterable structured metadata such as:

- `source`
- `year`
- `document_type`

The `pages` table stores page-level source content using:

- `doc_id`
- `page_no`
- `text`

Each document can have multiple pages, and `(doc_id, page_no)` is unique.

## 3. Migration

Alembic is used for database migrations.

The migrations create the `documents` and `pages` tables and add the
required indexes.

Migration verification:

```text
uv run alembic upgrade head
uv run alembic downgrade -1
uv run alembic upgrade head
uv run alembic check
