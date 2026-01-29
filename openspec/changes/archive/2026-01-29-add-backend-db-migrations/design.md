## Context
The backend and bot skeletons include minimal entrypoints but no shared database integration or migration tooling. The project stack calls for PostgreSQL, SQLAlchemy/SQLModel, and Alembic, and both services need access to the same database layer.

## Goals / Non-Goals
- Goals:
  - Provide a minimal SQLModel-based DB layer in a root-level `shared/` module (engine, session factory, Base/metadata, `get_db`).
  - Ensure both backend and bot can import the shared module in local dev and Docker.
  - Wire Alembic to the application settings and shared SQLModel metadata.
  - Include a minimal `users` table migration to validate wiring.
  - Add tests that exercise DB session lifecycle and metadata detection.
- Non-Goals:
  - Async database engine or async sessions.
  - Domain/business models beyond the placeholder `users` table.
  - Repository/service abstractions or advanced session scoping.

## Decisions
- Use SQLModel for the model base and metadata (`SQLModel.metadata`) while keeping a standard SQLAlchemy engine and `sessionmaker`.
- Place the DB module and models in `shared/` so backend and bot import the same definitions.
- Read `DATABASE_URL` from the environment inside the shared DB module to avoid coupling to a service-specific settings module; the backend settings already mirror the same environment variable.
- Provide a `get_db` dependency that yields a session and always closes it.
- Keep Alembic configuration under `backend/alembic/` with `alembic.ini` at `backend/alembic.ini` and `env.py` importing SQLModel metadata from the shared base module.
- Ensure Docker Compose mounts the `shared/` directory into backend, worker, and bot containers and sets `PYTHONPATH` accordingly.

## Alternatives considered
- Pure SQLAlchemy declarative base instead of SQLModel: rejected to align with the project stack and modern typing ergonomics.
- Async engine/session: deferred for MVP simplicity.
- Skipping the initial migration: rejected because a concrete migration is needed to validate Alembic wiring.

## Risks / Trade-offs
- Tests require a running Postgres container; mitigate by documenting the dependency and scoping tests to integration-only fixtures.
- Alembic autogenerate may require explicit imports of model modules; mitigate by ensuring the shared base module imports the model package.
- Shared module imports may fail without consistent PYTHONPATH; mitigate by codifying container environment variables and volume mounts.

## Migration Plan
1. Add SQLModel + Alembic dependencies in backend and bot where needed.
2. Create the `shared/` DB module and placeholder `users` model.
3. Update backend/bot imports and dev stack configuration for shared module access.
4. Scaffold Alembic configuration and create the initial migration.
5. Add tests and validate against local Docker Postgres.

## Open Questions
- None.
