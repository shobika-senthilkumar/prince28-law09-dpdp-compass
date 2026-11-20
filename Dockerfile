FROM python:3.12-slim AS builder

COPY --from=ghcr.io/astral-sh/uv:0.11.32 /uv /uvx /bin/

ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PYTHON_DOWNLOADS=0

WORKDIR /app

COPY pyproject.toml uv.lock ./

RUN uv sync --locked --no-install-project --no-dev

COPY . /app

RUN uv sync --locked --no-dev --no-editable


FROM python:3.12-slim

RUN groupadd --system app && \
    useradd --system --gid app --create-home app

WORKDIR /app

COPY --from=builder --chown=app:app /app/.venv /app/.venv
COPY --chown=app:app alembic.ini /app/
COPY --chown=app:app alembic /app/alembic
COPY --chown=app:app scripts /app/scripts
COPY --chown=app:app src /app/src
COPY --chown=app:app data /app/data

ARG GIT_SHA=dev

ENV PATH="/app/.venv/bin:$PATH" \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    GIT_SHA=${GIT_SHA}

USER app

EXPOSE 8000

CMD ["sh", "-c", "exec uvicorn dpdpcompass.api.main:create_app --factory --host 0.0.0.0 --port ${PORT:-8000}"]
