.PHONY: up down build logs test-api lint migrate

up:
	docker compose up -d

down:
	docker compose down

build:
	docker compose build

logs:
	docker compose logs -f

logs-api:
	docker compose logs -f api

logs-worker:
	docker compose logs -f worker

test-api:
	cd apps/api && pip install -e ".[dev]" -q && pytest tests/ -v

lint:
	cd apps/api && ruff check src/ tests/

migrate:
	cd apps/api && alembic upgrade head

migrate-new:
	cd apps/api && alembic revision --autogenerate -m "$(name)"

shell-db:
	docker compose exec postgres psql -U ankithis

shell-api:
	docker compose exec api bash

restart-api:
	docker compose restart api worker
