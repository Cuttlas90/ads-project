# manage-migrations Specification

## MODIFIED Requirements
### Requirement: Initial users migration
The backend service SHALL include an initial Alembic migration that creates the `users` table defined in the database model, including `id`, `telegram_user_id`, profile fields, `created_at`, and `last_login_at`, and enforces uniqueness for `telegram_user_id`.

#### Scenario: Apply initial migration
- **WHEN** the initial migration is applied to an empty database
- **THEN** the `users` table exists with the columns defined in the model and uniqueness on `telegram_user_id`
