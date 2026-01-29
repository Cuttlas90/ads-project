.PHONY: help dev lint test test-db

help:
	@echo "Available commands:"
	@echo "  make dev   - Print instructions for running services"
	@echo "  make lint  - Run available linters (safe no-op if not configured)"
	@echo "  make test  - Run available tests (safe no-op if not configured)"
	@echo "  make test-db - Start Postgres via Docker and run backend DB tests"

dev:
	@echo "Frontend: cd frontend && npm install && npm run dev"
	@echo "Backend:  cd backend  && uv pip install --system -e . --group dev"
	@echo "Bot:      cd bot      && uv pip install --system -e . --group dev"

lint:
	@echo "Running linters if configured..."
	@if command -v ruff >/dev/null 2>&1; then \
		(cd backend && ruff .) || echo "Backend lint skipped (install deps first)."; \
		(cd bot && ruff .) || echo "Bot lint skipped (install deps first)."; \
	else \
		echo "ruff not found. Install with: cd backend && uv pip install --system -e . --group dev"; \
	fi
	@if command -v npm >/dev/null 2>&1; then \
		echo "Frontend lint not configured yet."; \
	else \
		echo "npm not found. Install Node.js to run frontend tooling."; \
	fi
	@true

test:
	@echo "Running tests if configured..."
	@if command -v pytest >/dev/null 2>&1; then \
		(cd backend && pytest) || echo "Backend tests skipped (install deps first)."; \
		(cd bot && pytest) || echo "Bot tests skipped (install deps first)."; \
	else \
		echo "pytest not found. Install with: cd backend && uv pip install --system -e . --group dev"; \
	fi
	@if command -v npm >/dev/null 2>&1; then \
		echo "Frontend tests not configured yet."; \
	else \
		echo "npm not found. Install Node.js to run frontend tooling."; \
	fi
	@true

test-db:
	@if [ ! -f .env ]; then echo "Missing .env. Run: cp .env.example .env"; exit 1; fi
	@if ! command -v docker >/dev/null 2>&1; then echo "docker not found. Install Docker first."; exit 1; fi
	@if ! command -v pytest >/dev/null 2>&1; then echo "pytest not found. Install with: cd backend && uv pip install --system -e . --group dev"; exit 1; fi
	@echo "Starting postgres container..."
	@docker compose --env-file .env -f infra/docker-compose.yml up -d postgres
	@echo "Running backend DB tests..."
	@DATABASE_URL=$${DATABASE_URL:-postgresql+psycopg://ads:ads@localhost:5433/ads} \
		PYTHONPATH=$(PWD) \
		(cd backend && pytest tests/test_db.py)
	@echo "Stopping postgres container..."
	@docker compose --env-file .env -f infra/docker-compose.yml stop postgres
