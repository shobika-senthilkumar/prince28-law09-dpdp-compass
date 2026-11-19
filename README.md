# DPDP Compass

Practical compliance guidance for Indian startups navigating the Digital Personal Data Protection Act 2023 and the DPDP Rules 2025.

## Who It Is For

Founder-developers of small and growing Indian startups handling personal data, especially teams that need practical compliance guidance without having a dedicated legal team.

## Core Features

- Compliance guidance for the DPDP Act 2023
- Guidance based on the final DPDP Rules 2025
- Effective-date awareness for phased commencement
- Compliance Clock for checking whether a duty is currently in force
- Source-backed answers with Act sections and Rule references
- Distinction between final Rules and earlier draft Rules
- Guidance for notices, consent, children's data, and personal data breaches

## Key Challenge

The DPDP framework has different commencement dates for different provisions. DPDP Compass must distinguish between:

- What is legally required
- When the requirement comes into force
- Whether a provision is from the final Rules or only from the earlier draft
- Which authoritative source supports the answer

## Success Criteria

- 100% correct in-force status across the 40 duty-date evaluation tests
- 90%+ correct Act section / Rule citations across the 40 citation questions
- Answers grounded in authoritative sources
- Clear distinction between final and draft requirements

## Project Structure

```text
src/dpdpcompass/
├── api/
├── core/
├── domain/
└── services/

docs/
data/
tests/
```

## Run locally in one command

### Using Docker Compose

```bash
docker compose up --build -d
```

The stack starts the PostgreSQL database, Redis, migrations/seed job, and FastAPI API.

### API

- API: `http://localhost:8000`
- Swagger UI: `http://localhost:8000/docs`
- Liveness: `http://localhost:8000/health`
- Readiness: `http://localhost:8000/ready`

### Development tasks

```bash
uv run poe dev
uv run poe test
uv run poe test-integration
uv run poe cov
uv run poe lint
uv run poe migrate
uv run poe seed
```

### Test coverage

The unit test suite runs without Docker. Integration tests require the PostgreSQL service from Docker Compose.

```bash
uv run poe test
uv run poe cov
```
