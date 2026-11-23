**# Day 3 Notes — PostgreSQL Integration**

**## 1. Database**

DPDP Compass now uses PostgreSQL through SQLAlchemy.

The database connection is configured using the \`DATABASE_URL\`
environment variable. The real \`.env\` file is not committed to GitHub.

**## 2. Schema**

The main database tables are:

\- \`documents\`
\- \`pages\`

Each document contains:

\- \`id\`
\- \`external_id\`
\- \`title\`
\- \`source\`
\- \`source_url\`
\- \`doc_type\`
\- \`year\`
\- \`description\`
\- \`licence\`
\- \`published_on\`
\- \`sha256\`
\- \`metadata\`
\- \`created_at\`
\- \`updated_at\`

The \`external_id\` column is unique and is used to identify each DPDP Compass source record.

The \`metadata\` JSONB column stores filterable structured metadata such as:

\- \`source\`
\- \`year\`
\- \`document_type\`

The \`pages\` table stores page-level source content using:

\- \`doc_id\`
\- \`page_no\`
\- \`text\`

Each document can have multiple pages, and \`(doc_id, page_no)\` is unique.

**## 3. Migration**

Alembic is used for database migrations.

The migrations create the \`documents\` and \`pages\` tables and add the required indexes.

Migration verification:

\`\`\`text
uv run alembic upgrade head
uv run alembic downgrade -1
uv run alembic upgrade head
uv run alembic check

\## 4. Index / EXPLAIN verification

The \`documents.metadata\` JSONB field is indexed with the GIN index
\`ix_documents_metadata_gin\` using \`jsonb_path_ops\`.

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

This confirms that PostgreSQL uses \`ix_documents_metadata_gin\`
for the JSONB containment filter.

\## 3. Loader verification

Second run:

\`\`\`text
records=20 inserted=0 updated=0 unchanged=20
\`\`\`

D03 stretch -- --prune verification:

\`\`\`text
records=19 inserted=0 updated=0 unchanged=19 deleted=1
\`\`\`

Normal --prune run with no stale records:

\`\`\`text
records=20 inserted=0 updated=0 unchanged=20 deleted=0
\`\`\`

**# Day 4 Notes — Docker, Tests and Coverage**

**## 1. Tests**

Unit tests:

\`\`\`text
uv run pytest tests/unit --cov --cov-report=term-missing

25 passed in 0.72s
TOTAL 282 stmts, 55 miss, 40 branch, 8 partial, 79%

## 2. Combined Test Suite

\`\`\`text
uv run pytest --cov --cov-report=term-missing

38 passed in 22.28s
TOTAL 282 stmts, 38 miss, 40 branch, 8 partial, 85%
\`\`\`

Combined coverage: **85%**

## 3. Coverage Summary

Unit-only coverage: **79%**

Combined coverage: **85%**

Main uncovered areas in the combined coverage report:

- \`src/dpdpcompass/api/middleware.py\`
- \`src/dpdpcompass/api/routes/documents.py\`
- \`src/dpdpcompass/db/loader.py\`
- \`src/dpdpcompass/db/repository.py\`
- \`src/dpdpcompass/db/session.py\`
- \`src/dpdpcompass/store.py\`

## 4. Test Structure

The repository contains separate unit and integration test suites.

\`\`\`text
tests/
├── conftest.py
├── test_api.py
├── test_db_integration.py
├── integration/
│   ├── conftest.py
│   └── test_api_integration.py
└── unit/
    ├── conftest.py
    ├── test_health.py
    ├── test_loader.py
    └── test_repository.py
\`\`\`

## 5. Integration Tests

The integration test suite currently runs successfully in the configured environment.

The current integration tests cover:

- \`/health\`
- \`/ready\`
- \`/ready\` when the database is not sufficiently populated
- \`/ready\` when a database error occurs
- \`/v1/documents/stats\`

The current integration fixture does not yet implement a completely fresh database for every test run.

## 6. Docker

The following Day 4 Docker files are present:

- \`Dockerfile\`
- \`.dockerignore\`
- \`docker-compose.yml\`
- \`Makefile\`

The Docker Compose configuration contains:

- \`db\`
- \`redis\`
- \`migrate\`
- \`api\`

The database and Redis services include healthchecks.

The API service depends on the database, Redis, and successful completion of the migration service.

Docker runtime verification could not be performed locally because Docker Desktop is not available in the development environment.

Therefore, the following Docker runtime evidence has not been locally verified:

- Docker image size
- Container user verification
- \`docker compose up --build\`
- \`docker compose ps -a\`
- Migration container logs
- \`/ready\` behavior with the database stopped
- \`/ready\` recovery after the database is restarted

## 7. Coverage Command

The project coverage task was also verified with:

\`\`\`text
uv run poe cov
\`\`\`

Result:

\`\`\`text
38 passed in 22.28s
TOTAL 282 stmts, 38 miss, 40 branch, 8 partial, 85%
\`\`\`

## 8. Docker Runtime Status

Docker runtime testing remains pending because Docker Desktop is not available locally.

The Dockerfile, Docker Compose configuration, \`.dockerignore\`, Makefile, unit tests, integration tests, and coverage tasks are present in the repository.
