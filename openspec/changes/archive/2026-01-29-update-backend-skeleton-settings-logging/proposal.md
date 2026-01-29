# Change: Update backend FastAPI skeleton structure

## Why
The backend currently exposes a single inline health endpoint with no settings, logging, or routing structure. This change establishes a minimal, production-style skeleton so future features can be added consistently while keeping the backend free of domain logic.

## What Changes
- Add a small app package layout with API router and health route modules.
- Add a dedicated deps module for dependency wiring (kept minimal for now).
- Introduce Pydantic Settings-based configuration with defaults aligned to the compose .env values.
- Centralize logging configuration and wire it into application startup.
- Update the /health response to return only {"status": "ok"} without database checks.
- Add minimal tests for health, settings, and logging configuration.

## Impact
- Affected specs: backend-skeleton (package layout, health endpoint, settings, logging, routing)
- Affected code: backend/app/*, backend/tests/*, backend/pyproject.toml
- Runtime: docker compose should continue to boot without changes
