# Change: Telegram Mini App authentication (initData)

## Why
The MVP needs a single, secure authentication mechanism aligned with Telegram Mini App initData validation to establish user identity and persist users in Postgres.

## What Changes
- Add server-side Telegram Mini App initData verification using the bot token.
- Add `get_current_user` FastAPI dependency that validates initData, loads or creates users, and updates `last_login_at`.
- Update the shared users schema to use an internal primary key and `telegram_user_id` as the external identity.
- Replace the existing initial users migration to match the updated schema (fresh database assumption).
- Add a protected `/auth/me` route for verification/testing.
- Add unit and API tests for verification logic and user persistence.

## Impact
- Affected specs: `access-database`, `manage-migrations`, new `telegram-auth` capability.
- Affected code: `backend/app/auth/telegram_initdata.py`, `backend/app/models/user.py`, `backend/app/api/deps.py`, `backend/app/api/routes/auth.py`, `backend/app/api/router.py`, `shared/db/models/users.py`, `backend/alembic/versions/9c2b06f1d0d7_create_users_table.py`, and tests under `backend/tests/`.
