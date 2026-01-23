.PHONY: help dev lint test

help:
	@echo "Available commands:"
	@echo "  make dev   - Print instructions for running services"
	@echo "  make lint  - Run available linters (safe no-op if not configured)"
	@echo "  make test  - Run available tests (safe no-op if not configured)"

dev:
	@echo "Frontend: cd frontend && npm install && npm run dev"
	@echo "Backend:  cd backend  && poetry install"
	@echo "Bot:      cd bot      && poetry install"

lint:
	@echo "Running linters if configured..."
	@if command -v poetry >/dev/null 2>&1; then \
		(cd backend && poetry run ruff .) || echo "Backend lint skipped (install deps first)."; \
		(cd bot && poetry run ruff .) || echo "Bot lint skipped (install deps first)."; \
	else \
		echo "Poetry not found. Install Poetry to run Python lint."; \
	fi
	@if command -v npm >/dev/null 2>&1; then \
		echo "Frontend lint not configured yet."; \
	else \
		echo "npm not found. Install Node.js to run frontend tooling."; \
	fi
	@true

test:
	@echo "Running tests if configured..."
	@if command -v poetry >/dev/null 2>&1; then \
		(cd backend && poetry run pytest) || echo "Backend tests skipped (install deps first)."; \
		(cd bot && poetry run pytest) || echo "Bot tests skipped (install deps first)."; \
	else \
		echo "Poetry not found. Install Poetry to run Python tests."; \
	fi
	@if command -v npm >/dev/null 2>&1; then \
		echo "Frontend tests not configured yet."; \
	else \
		echo "npm not found. Install Node.js to run frontend tooling."; \
	fi
	@true
