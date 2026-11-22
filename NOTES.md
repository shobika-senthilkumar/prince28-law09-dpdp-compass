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

The `external_id` column is unique and is used to identify each DPDP Compass source record.

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

The migrations create the `documents` and `pages` tables and add the required indexes.

Migration verification:

```text
uv run alembic upgrade head
uv run alembic downgrade -1
uv run alembic upgrade head
uv run alembic check

## 4. Index / EXPLAIN verification

The `documents.metadata` JSONB field is indexed with the GIN index
`ix_documents_metadata_gin` using `jsonb_path_ops`.

The EXPLAIN verification was run with:

uv run python scripts/explain.py

The query:

SELECT id
FROM documents
WHERE metadata @> '{"source": "India Code"}'::jsonb;

produced:

Bitmap Heap Scan on documents  (cost=12.76..16.77 rows=1 width=4)
  Recheck Cond: (metadata @> '{"source": "India Code"}'::jsonb)
  ->  Bitmap Index Scan on ix_documents_metadata_gin  (cost=0.00..12.76 rows=1 width=0)
        Index Cond: (metadata @> '{"source": "India Code"}'::jsonb)

This confirms that PostgreSQL uses `ix_documents_metadata_gin`
for the JSONB containment filter.
