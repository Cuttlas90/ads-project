# Change: Add shared PostgreSQL integration and Alembic migrations

## Why
The backend and bot need a shared database layer and migration tooling so future models can be added safely and consistently across services.

## What Changes
- Add a shared SQLModel-based database module (in `shared/`) with engine, session factory, Base/metadata access, and a `get_db` helper.
- Update backend and bot to import the shared database module.
- Add Alembic configuration under `backend/alembic/` wired to the application settings and SQLModel metadata.
- Add an initial migration for a minimal `users` table based on the Telegram User object.
- Verify local dev stack configuration (PYTHONPATH and volume mounts) so shared imports work in backend and bot containers.
- Add tests that validate the DB session lifecycle and that Alembic detects SQLModel metadata (using the local Docker Postgres).

## Impact
- Affected specs: `access-database`, `manage-migrations`, `local-dev-stack`
- Affected code: `shared/`, `backend/app/api/deps.py`, `backend/alembic/`, `backend/pyproject.toml`, `bot/pyproject.toml`, `infra/docker-compose.yml`, `backend/Dockerfile`, `bot/Dockerfile`, `backend/tests/`, `bot/tests/`
