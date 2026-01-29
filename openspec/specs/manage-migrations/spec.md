# manage-migrations Specification

## Purpose
TBD - created by archiving change add-backend-db-migrations. Update Purpose after archive.
## Requirements
### Requirement: Alembic configuration
The backend service SHALL include Alembic configuration under `backend/alembic/` with `backend/alembic.ini`, and Alembic SHALL load the `DATABASE_URL` setting and SQLModel metadata from the shared database base module (e.g., `shared.db.base`) as its `target_metadata`.

#### Scenario: Alembic environment wiring
- **WHEN** Alembic runs in online or offline mode
- **THEN** it uses `DATABASE_URL` for the engine configuration and SQLModel metadata for autogeneration

### Requirement: Initial users migration
The backend service SHALL include an initial Alembic migration that creates the `users` table defined in the database model, including `id`, `telegram_user_id`, profile fields, `created_at`, and `last_login_at`, and enforces uniqueness for `telegram_user_id`.

#### Scenario: Apply initial migration
- **WHEN** the initial migration is applied to an empty database
- **THEN** the `users` table exists with the columns defined in the model and uniqueness on `telegram_user_id`

