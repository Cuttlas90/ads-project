# local-dev-stack Specification

## Purpose
TBD - created by archiving change add-docker-compose-dev-stack. Update Purpose after archive.
## Requirements
### Requirement: Local Docker Compose stack
The repository SHALL include `infra/docker-compose.yml` defining services for postgres, redis, backend, worker, frontend, and an optional bot profile. The compose file SHALL expose ports 5432, 6379, 8000, and 5173; define a named volume `postgres_data` for Postgres; and wire healthchecks with `depends_on` conditions for backend and worker.

#### Scenario: Compose services wired
- **WHEN** a developer inspects `infra/docker-compose.yml`
- **THEN** all required services, ports, volume, and health-based dependencies are defined, and the bot service is gated behind a `bot` profile

### Requirement: Dev service Dockerfiles
The repository SHALL include `backend/Dockerfile` and `frontend/Dockerfile` to build dev-friendly images. If a bot service is defined in compose, the repository SHALL include `bot/Dockerfile` as well. The Python Dockerfiles SHALL install dependencies using uv while keeping `pyproject.toml` as the dependency source of truth.

#### Scenario: Dockerfiles present
- **WHEN** a developer inspects the repository
- **THEN** the required Dockerfiles exist and indicate uv-based dependency installation for Python services

### Requirement: Compose environment examples
The root `.env.example` SHALL include `POSTGRES_DB`, `POSTGRES_USER`, `POSTGRES_PASSWORD`, `DATABASE_URL`, `REDIS_URL`, and optional `BACKEND_PORT` values, plus commented placeholders for `TELEGRAM_*` and `TON_*` variables.

#### Scenario: Environment template expanded
- **WHEN** a developer opens `.env.example`
- **THEN** the compose-related variables and placeholders are listed

### Requirement: Shared module available in dev containers
The local Docker Compose stack SHALL mount the root `shared/` directory into backend, worker, and bot containers and set `PYTHONPATH` so those services can import the shared module.

#### Scenario: Shared imports in dev stack
- **WHEN** a developer starts the local dev stack
- **THEN** backend, worker, and bot can import the shared database module without manual path tweaks

