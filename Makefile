APP_DEBUG ?= true

.PHONY: help install dev test lint format fix check \
	postgres-up migrate revision migration-current \
	docker-up docker-down docker-ps docker-logs airflow-errors \
	clickhouse-init

help:
	@echo "Available commands:"
	@echo "  make install                         Install dependencies"
	@echo "  make dev                             Run API locally"
	@echo "  make test                            Run tests"
	@echo "  make lint                            Run Ruff linter"
	@echo "  make format                          Format code"
	@echo "  make fix                             Auto-fix lint issues and format code"
	@echo "  make check                           Run lint and tests"
	@echo "  make postgres-up                     Start backend PostgreSQL"
	@echo "  make migrate                         Apply database migrations"
	@echo "  make revision MESSAGE=\"description\" Create Alembic migration"
	@echo "  make migration-current               Show current Alembic revision"
	@echo "  make docker-up                       Start Docker stack"
	@echo "  make docker-down                     Stop Docker stack"
	@echo "  make docker-ps                       Show Docker services"
	@echo "  make docker-logs                     Follow Docker logs"
	@echo "  make airflow-errors                  Show DAG import errors"
	@echo "  make clickhouse-init                 Create ClickHouse tables"

install:
	uv sync --dev

dev:
	env DEBUG=$(APP_DEBUG) uv run uvicorn app.main:app --reload

test:
	uv run pytest

lint:
	uv run ruff check app dags

format:
	uv run ruff format app dags

fix:
	uv run ruff format app dags
	uv run ruff check --fix app dags

check: lint test

postgres-up:
	docker compose up -d postgres

migrate: postgres-up
	env DEBUG=$(APP_DEBUG) uv run alembic upgrade head

revision: postgres-up
	@test -n "$(MESSAGE)" || (echo 'MESSAGE is required. Example: make revision MESSAGE="add reports table"' && exit 1)
	env DEBUG=$(APP_DEBUG) uv run alembic revision --autogenerate -m "$(MESSAGE)"

migration-current: postgres-up
	env DEBUG=$(APP_DEBUG) uv run alembic current

docker-up:
	docker compose up -d

docker-down:
	docker compose down

docker-ps:
	docker compose ps

docker-logs:
	docker compose logs -f

airflow-errors:
	docker compose exec airflow-scheduler airflow dags list-import-errors

clickhouse-init:
	env DEBUG=$(APP_DEBUG) uv run python -m scripts.create_clickhouse_tables