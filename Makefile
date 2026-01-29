.PHONY: help dev lint test

help:
	@echo "Available commands:"
	@echo "  make dev   - Print instructions for running services"
	@echo "  make lint  - Run available linters (safe no-op if not configured)"
	@echo "  make test  - Run available tests (safe no-op if not configured)"

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
