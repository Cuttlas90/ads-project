# access-database Specification

## Purpose
TBD - created by archiving change add-backend-db-migrations. Update Purpose after archive.
## Requirements
### Requirement: Shared database engine and session factory
The system SHALL provide a shared SQLModel-based database module under `shared/` that creates a SQLAlchemy engine using `DATABASE_URL` and exposes a `SessionLocal` factory configured with `autocommit=False` and `autoflush=False`. The backend and bot services SHALL import this shared module for database access.

#### Scenario: Engine and session configured
- **WHEN** the backend or bot imports the shared database session module
- **THEN** the engine is configured from `DATABASE_URL` and the session factory uses the required `autocommit` and `autoflush` settings

### Requirement: Database metadata registry
The shared database module SHALL expose SQLModel metadata from a shared base module so Alembic and future models can register against a single metadata registry.

#### Scenario: Metadata access
- **WHEN** Alembic loads the database base module
- **THEN** SQLModel metadata is available for autogeneration

### Requirement: Database session dependency
The shared database module SHALL expose a `get_db` helper that yields a database session and closes it after use, and the backend service SHALL use it as a FastAPI dependency.

#### Scenario: Session lifecycle
- **WHEN** a backend route dependency requests a database session
- **THEN** a session is yielded for the request and closed after the request completes

### Requirement: Placeholder users model
The shared database module SHALL define a minimal `users` table model based on the Telegram User object with the following columns:
- `id` (BigInteger, primary key, Telegram user ID)
- `first_name` (String, required)
- `last_name` (String, optional)
- `username` (String, optional)
- `language_code` (String, optional)
- `is_premium` (Boolean, default `False`)
- `created_at` (DateTime, server default `now()`)

#### Scenario: Users table definition
- **WHEN** SQLModel metadata is inspected
- **THEN** the `users` table includes the specified columns, types, and defaults

