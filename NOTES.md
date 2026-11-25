**# Day 3 Notes ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬ÃƒÂ¢Ã¢â€šÂ¬Ã‚Â PostgreSQL Integration**

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

**# Day 4 Notes ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬ÃƒÂ¢Ã¢â€šÂ¬Ã‚Â Docker, Tests and Coverage**

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
ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â€šÂ¬Ã‚ÂÃƒâ€¦Ã¢â‚¬Å“ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â€šÂ¬Ã‚ÂÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â€šÂ¬Ã‚ÂÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬ conftest.py
ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â€šÂ¬Ã‚ÂÃƒâ€¦Ã¢â‚¬Å“ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â€šÂ¬Ã‚ÂÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â€šÂ¬Ã‚ÂÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬ test_api.py
ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â€šÂ¬Ã‚ÂÃƒâ€¦Ã¢â‚¬Å“ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â€šÂ¬Ã‚ÂÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â€šÂ¬Ã‚ÂÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬ test_db_integration.py
ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â€šÂ¬Ã‚ÂÃƒâ€¦Ã¢â‚¬Å“ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â€šÂ¬Ã‚ÂÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â€šÂ¬Ã‚ÂÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬ integration/
ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â€šÂ¬Ã‚ÂÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡   ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â€šÂ¬Ã‚ÂÃƒâ€¦Ã¢â‚¬Å“ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â€šÂ¬Ã‚ÂÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â€šÂ¬Ã‚ÂÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬ conftest.py
ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â€šÂ¬Ã‚ÂÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡   ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â€šÂ¬Ã‚ÂÃƒÂ¢Ã¢â€šÂ¬Ã‚ÂÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â€šÂ¬Ã‚ÂÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â€šÂ¬Ã‚ÂÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬ test_api_integration.py
ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â€šÂ¬Ã‚ÂÃƒÂ¢Ã¢â€šÂ¬Ã‚ÂÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â€šÂ¬Ã‚ÂÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â€šÂ¬Ã‚ÂÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬ unit/
    ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â€šÂ¬Ã‚ÂÃƒâ€¦Ã¢â‚¬Å“ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â€šÂ¬Ã‚ÂÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â€šÂ¬Ã‚ÂÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬ conftest.py
    ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â€šÂ¬Ã‚ÂÃƒâ€¦Ã¢â‚¬Å“ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â€šÂ¬Ã‚ÂÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â€šÂ¬Ã‚ÂÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬ test_health.py
    ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â€šÂ¬Ã‚ÂÃƒâ€¦Ã¢â‚¬Å“ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â€šÂ¬Ã‚ÂÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â€šÂ¬Ã‚ÂÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬ test_loader.py
    ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â€šÂ¬Ã‚ÂÃƒÂ¢Ã¢â€šÂ¬Ã‚ÂÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â€šÂ¬Ã‚ÂÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â€šÂ¬Ã‚ÂÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬ test_repository.py
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
- Stretch: Docker image history showed the largest application layer is 94.5 MB from COPY --chown=app:app /app/.venv /app/.venv, because it contains the installed runtime Python dependencies.

## D05 - CI/CD and going live

- Live URL: https://dpdp-compass.onrender.com
- CI run for PR #10: https://github.com/shobika-senthilkumar/prince28-law09-dpdp-compass/actions/runs/45345476577
- First automatic deployment (CD #8): https://github.com/shobika-senthilkumar/prince28-law09-dpdp-compass/actions/runs/45345986371
- Merge: 12:39:16 PM IST; smoke test passed: 12:41:18 PM IST; lead time: 2 minutes 2 seconds.

### Smoke test output

```text
ok /health -> 200, version 35e3c9b1b05936714b57910997d1d84e58e9a63d
ok /ready -> 200, database true, records_count 20
ok /v1/documents?limit=1 -> 200
Smoke test passed
```

### Monitoring

- UptimeRobot monitors /health every 5 minutes.
- Email alerts enabled.
- HEAD request support added to /health.
- Verified HEAD /health returns HTTP 200.
- UptimeRobot monitor recovered and shows UP.

### Secrets

- DATABASE_URL: GitHub Actions secret and Render environment variable.
- RENDER_DEPLOY_HOOK: GitHub Actions secret only.
- UptimeRobot monitor-specific key used for the README badge; value not recorded.

### First-request performance

- An always-on deployment or warm-up strategy can help reduce cold-start latency.


## D05 - CI/CD and going live

- Live URL: https://dpdp-compass.onrender.com
- CI run for PR #10: https://github.com/shobika-senthilkumar/prince28-law09-dpdp-compass/actions/runs/45345476577
- First automatic deployment (CD #8): https://github.com/shobika-senthilkumar/prince28-law09-dpdp-compass/actions/runs/45345986371
- Merge: 12:39:16 PM IST; smoke test passed: 12:41:18 PM IST; lead time: 2 minutes 2 seconds.

### Smoke test output

```text
ok /health -> 200, version 35e3c9b1b05936714b57910997d1d84e58e9a63d
ok /ready -> 200, database true, records_count 20
ok /v1/documents?limit=1 -> 200
Smoke test passed
```

### Monitoring

- UptimeRobot monitors /health every 5 minutes.
- Email alerts enabled.
- HEAD request support added to /health.
- Verified HEAD /health returns HTTP 200.
- UptimeRobot monitor recovered and shows UP.

### Secrets

- DATABASE_URL: GitHub Actions secret and Render environment variable.
- RENDER_DEPLOY_HOOK: GitHub Actions secret only.
- UptimeRobot monitor-specific key used for the README badge; value not recorded.

### First-request performance

- An always-on deployment or warm-up strategy can help reduce cold-start latency.

### Rollback drill

- Status: Completed; rollback and roll-forward were both manually verified through /health.
- The original PR #1 merge SHA 8f929d83c6182ed56174152bd47646379cb74594 had no published GHCR image. Render rejected that deployment request with HTTP 400, so it was not used as the rollback target.
- Rollback target: 2bc6bebccc611fb5a7022787916fa66d69d3d70a (published image). CD run #14: https://github.com/shobika-senthilkumar/prince28-law09-dpdp-compass/actions/runs/45367461647
- Rollback workflow started: 15:10:42 IST, 24 November 2026. The automatic smoke test initially saw the previous live SHA; a later direct /health check confirmed 2bc6bebccc611fb5a7022787916fa66d69d3d70a.
- Roll-forward target: 58654368e81a355000d373a2a11dbebad3375c9e (current main). CD run #15: https://github.com/shobika-senthilkumar/prince28-law09-dpdp-compass/actions/runs/45368417988
- Roll-forward workflow started: 15:16:47 IST, 24 November 2026. The automatic smoke test initially saw the previous live SHA; a later direct /health check confirmed 58654368e81a355000d373a2a11dbebad3375c9e.
- Exact times of the later manual verification requests were not captured, so rollout durations are not claimed.
- The database schema remained at the latest migrated revision. Manual workflow_dispatch skips the migration step, so this drill changed the application image without downgrading the database schema.

### D05 stretch tasks

#### 1. Human approval gate

- Enabled required reviewers for the GitHub production environment.
- Configured shobika-senthilkumar as a reviewer with self-review permitted.
- CD #17 for the older commit did not complete successfully; the latest CD #18 completed successfully after the production review gate.
- CD #18: https://github.com/shobika-senthilkumar/prince28-law09-dpdp-compass/actions/runs/45575052254
- Why this gate is useful: production changes involving student personal data, authentication, or database migrations benefit from a final human review. For low-risk documentation changes, the added delay may not be worthwhile.

#### 2. Dependabot

- Added .github/dependabot.yml for the github-actions ecosystem.
- Update interval: weekly.
- Merged in PR #14: https://github.com/shobika-senthilkumar/prince28-law09-dpdp-compass/pull/14

#### 3. Pre-commit in CI

- Added the Run pre-commit step to the lint and test job in .github/workflows/ci.yml.
- Command: uv run pre-commit run --all-files
- Merged in PR #15: https://github.com/shobika-senthilkumar/prince28-law09-dpdp-compass/pull/15
- Main CI run #40 passed, including the pre-commit step and build image job.
- CI run: https://github.com/shobika-senthilkumar/prince28-law09-dpdp-compass/actions/runs/45574849144

#### 4. Lead-time measurement

Merge-to-smoke-test-passed times for the first three automatic CD runs (24 November 2026, IST):

| PR / CD run | Merge time | Smoke test passed | Lead time |
| --- | --- | --- | --- |
| PR #10 / CD #8 | 12:39:16.000 | 12:41:18.797 | 2m 02.797s |
| PR #11 / CD #9 | 13:59:53.000 | 14:02:21.042 | 2m 28.042s |
| PR #12 / CD #10 | 14:56:52.000 | 14:58:32.378 | 1m 40.378s |

- Average merge-to-smoke-test-passed time: 2m 03.739s.
- The slowest observed step was Smoke test the live URL, which took about 18.9 seconds in CD #8 while Render was switching versions.
- CD #8: https://github.com/shobika-senthilkumar/prince28-law09-dpdp-compass/actions/runs/45345986371
- CD #9: https://github.com/shobika-senthilkumar/prince28-law09-dpdp-compass/actions/runs/45356955141
- CD #10: https://github.com/shobika-senthilkumar/prince28-law09-dpdp-compass/actions/runs/45365500063
- Measurement caveat: CD #9 and CD #10 smoke tests passed while /health still reported the previous deployed SHA. Subsequent direct /health checks confirmed the intended versions. Therefore, these figures measure merge-to-smoke-test completion, not exact time until the new SHA first became live.

#### Final stretch deployment verification

- Latest main commit: c66247f16ec4a4e89dae987267b3785aca86ec95.
- CD #18 completed successfully: https://github.com/shobika-senthilkumar/prince28-law09-dpdp-compass/actions/runs/45575052254
- Final manual /health verification returned version c66247f16ec4a4e89dae987267b3785aca86ec95.
- /ready returned 200 with database true and 20 records; the documents endpoint returned 200.

# Day 6 Notes â€” Corpus Fetch & Capacity

## Licence / terms checks
- Reviewed the source register in `data/sources.csv`.
- Official MeitY legal documents are government-hosted Gazette material; no blanket full-text reuse permission was verified.
- India Code content is government-hosted; no explicit full-text reuse permission was verified.
- PIB material may be reproduced with prominent attribution under PIB policy, subject to its stated exclusions.
- MeitY overview material is official government information; no blanket reuse licence was verified.
- Downloader does not bypass robots.txt, HTTP 403 restrictions, or access controls.

## Robots / access findings
- Automated requests to the official MeitY/PIB source URLs returned HTTP 403.
- Per the Build Lab guidance, the downloader does not attempt to bypass the block.
- Required documents were collected manually from the official sources and registered using `register_manual.py`.

## Kill / resume verification
- Run 1: interrupted with Ctrl+C; process ended with `KeyboardInterrupt`.
- Run 2: resumed and completed the test download successfully.
- Run 3: completed with `downloaded=0 skipped=1`.
- Verified that no `.part` files remained after interruption.
- The resume test used a controlled local slow HTTP test file so interruption and resume behavior could be verified reliably.

## Current corpus
- 5 official PDF documents downloaded and registered.
- DPDP Act 2023
- DPDP Rules 2025 â€” G.S.R. 846(E)
- Commencement notification â€” G.S.R. 843(E)
- Data Protection Board establishment â€” G.S.R. 844(E)
- Data Protection Board members â€” G.S.R. 845(E)

## Capacity measurements
- Current PDF count: 5
- Current PDF pages: 68
- Extracted characters: 191,402
- Estimated tokens: 47,851
- Estimated embedding storage: 280.38 MiB
- 1,000-page estimate: 2,814,735 characters
- 1,000-page estimate: 703,684 tokens
- 1,000-page embedding estimate: 4.03 GiB

## Problem and solution
Problem: official source URLs returned HTTP 403 during automated collection, preventing the downloader from retrieving the corpus directly.

Solution: follow the Build Lab's compliant fallback path by manually downloading the official documents and registering them with the manifest, while keeping the automated downloader capable of robots checks, retries, atomic `.part` handling, resumable execution, and successful-download skipping.

## Known gap
- MeitY FAQs are still a collection gap and must be added before claiming the full start target is complete.

### Stretch 4 — Crawl Statistics
- Files and size per source: MeitY — 5 files, 7.79 MB; total — 5 files, 7.79 MB.
- Slowest site: unavailable because the manifest does not currently record download duration.
- Documents needing more than one attempt: 0.
