## Context
This change introduces a local development stack that runs multiple services (database, cache, API, worker, frontend, optional bot) via Docker Compose. It also relaxes existing skeleton constraints to allow minimal entrypoints for service health and container startup.

## Goals / Non-Goals
- Goals:
  - Provide a single `docker compose` entrypoint for local dev.
  - Keep service containers dev-friendly (bind mounts, reload).
  - Ensure backend health endpoint returns structured JSON.
- Non-Goals:
  - Production deployment patterns.
  - Business logic, migrations, or domain models.

## Decisions
- Decision: Use `infra/docker-compose.yml` as the canonical dev stack entrypoint.
  - Why: Keeps infra isolated and matches repository structure conventions.
- Decision: Use `postgres:16-alpine` and `redis:7-alpine` images.
  - Why: Matches requested versions and lightweight images.
- Decision: Reuse backend image for worker (Celery) and run uvicorn with reload for API.
  - Why: Minimizes duplication while preserving dev ergonomics.
- Decision: Include the bot service under a compose profile (`bot`) with a minimal `bot/app/main.py` entrypoint.
  - Why: Keeps optional service available without blocking default `docker compose up`.
- Decision: Use a uv-based install flow in Dockerfiles while keeping `pyproject.toml` as the source of dependency metadata.
  - Why: Aligns with requested tooling while preserving Poetry-managed metadata.

## Risks / Trade-offs
- Bind mounts + reload can increase container start time → acceptable for dev.
- Adding minimal entrypoints modifies skeleton specs → handled via spec deltas.

## Migration Plan
- No data migrations. Existing dev setup remains unchanged; new compose stack is additive.

## Open Questions
- None (resolved in request).
