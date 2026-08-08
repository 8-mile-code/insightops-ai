.PHONY: help install dev test lint format fix check \
	postgres-up migrate revision migration-current \
	docker-up docker-down docker-ps docker-logs airflow-errors \
	clickhouse-init seed-demo format-check

help:
	@echo "Available commands:"
	@echo "  make install                         Install dependencies"
	@echo "  make dev                             Run API locally"
	@echo "  make test                            Run tests"
	@echo "  make lint                            Run Ruff linter"
	@echo "  make format                          Format code"
	@echo "  make format-check                    Check code formatting"
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
	@echo "  make seed-demo                       Seed demo data"

install:
	uv sync --dev

dev:
	uv run uvicorn app.main:app --reload

test:
	uv run pytest

lint:
	uv run ruff check .

format:
	uv run ruff format .

format-check:
	uv run ruff format --check .

fix:
	uv run ruff check --fix .
	uv run ruff format .

check: lint format-check test

postgres-up:
	docker compose up -d postgres

migrate: postgres-up
	uv run alembic upgrade head

revision: postgres-up
	@test -n "$(MESSAGE)" || (echo 'MESSAGE is required. Example: make revision MESSAGE="add reports table"' && exit 1)
	uv run alembic revision --autogenerate -m "$(MESSAGE)"

migration-current: postgres-up
	uv run alembic current

docker-up:
	docker compose up -d --build

docker-down:
	docker compose down

docker-ps:
	docker compose ps

docker-logs:
	docker compose logs -f

airflow-errors:
	docker compose exec airflow-scheduler airflow dags list-import-errors

clickhouse-init:
	uv run python -m scripts.create_clickhouse_tables

seed-demo:
	uv run python -m scripts.seed_demo_data
