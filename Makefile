.PHONY: dev test test-integration cov lint up

dev:
	uv run uvicorn dpdpcompass.api.main:create_app --factory --reload

test:
	uv run pytest tests/unit

test-integration:
	uv run pytest tests/integration

cov:
	uv run pytest --cov

lint:
	uv run ruff check . && uv run ruff format --check .

up:
	docker compose up --build -d
