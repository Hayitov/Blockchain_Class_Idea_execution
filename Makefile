.PHONY: help db-create db-drop migrate seed-map seed-dev api web test health install

# Defaults — override on command line if your local Postgres uses different creds:
#   make db-create PG_SUPERUSER=postgres
PG_SUPERUSER ?= $(USER)
DB_NAME      ?= cs423_grading
DB_USER      ?= cs423
DB_PASSWORD  ?= cs423

help:
	@echo "Targets:"
	@echo "  install     Install backend (pip) and frontend (npm) deps"
	@echo "  db-create   Create the cs423 role and cs423_grading database (idempotent)"
	@echo "  db-drop     Drop the database (DESTRUCTIVE — local only)"
	@echo "  migrate     Run alembic upgrade head"
	@echo "  seed-map    Fetch OZ Ethernaut gamedata and seed assignments.config_json"
	@echo "  seed-dev    Insert sample students (dev only)"
	@echo "  api         Run FastAPI on :8000 with reload"
	@echo "  web         Run Vite dev server on :5173"
	@echo "  health      curl /api/health (smoke test)"
	@echo "  test        Run backend pytest"

install:
	cd backend && python -m venv .venv && . .venv/bin/activate && pip install -e .
	cd frontend && npm install

db-create:
	@psql -U $(PG_SUPERUSER) -d postgres -tAc "SELECT 1 FROM pg_roles WHERE rolname='$(DB_USER)'" | grep -q 1 \
	  || psql -U $(PG_SUPERUSER) -d postgres -c "CREATE ROLE $(DB_USER) LOGIN PASSWORD '$(DB_PASSWORD)';"
	@psql -U $(PG_SUPERUSER) -d postgres -tAc "SELECT 1 FROM pg_database WHERE datname='$(DB_NAME)'" | grep -q 1 \
	  || psql -U $(PG_SUPERUSER) -d postgres -c "CREATE DATABASE $(DB_NAME) OWNER $(DB_USER);"
	@echo "DB ready: $(DB_NAME) owned by $(DB_USER)"

db-drop:
	psql -U $(PG_SUPERUSER) -d postgres -c "DROP DATABASE IF EXISTS $(DB_NAME);"

migrate:
	cd backend && . .venv/bin/activate && alembic upgrade head

seed-map:
	cd backend && . .venv/bin/activate && python -m scripts.seed_ethernaut_map

seed-dev:
	cd backend && . .venv/bin/activate && python -m scripts.seed_dev_data

api:
	cd backend && . .venv/bin/activate && uvicorn app.main:app --reload --host 127.0.0.1 --port 8000

web:
	cd frontend && npm run dev

health:
	curl -s http://localhost:8000/api/health | python -m json.tool

test:
	cd backend && . .venv/bin/activate && pytest -q
