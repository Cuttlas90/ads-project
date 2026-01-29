## 1. Implementation
- [x] 1.1 Add `backend/app/auth/telegram_initdata.py` with initData parsing, signature verification, and 24-hour `auth_date` validation.
- [x] 1.2 Add `backend/app/models/user.py` as a re-export alias of the shared User model.
- [x] 1.3 Update `shared/db/models/users.py` to the new schema (internal `id`, unique `telegram_user_id`, optional profile fields, `last_login_at`).
- [x] 1.4 Replace the existing initial users Alembic migration (`backend/alembic/versions/9c2b06f1d0d7_create_users_table.py`) to match the updated schema.
- [x] 1.5 Add `TELEGRAM_BOT_TOKEN` to backend settings usage (read from environment; `.env.example` already includes it).
- [x] 1.6 Extend `backend/app/api/deps.py` with `get_current_user` that reads initData from header/query, verifies it, extracts the user from initData, and loads/creates users while updating `last_login_at`.
- [x] 1.7 Add `/auth/me` route (e.g., `backend/app/api/routes/auth.py`) protected by `Depends(get_current_user)` and wire it into `backend/app/api/router.py`.

## 2. Tests
- [x] 2.1 Unit tests for initData verification: valid payload, invalid hash, missing hash, missing `auth_date`, and expired `auth_date` (>24h).
- [x] 2.2 API tests for `/auth/me`: 401 on missing/invalid initData; 200 with valid initData; user row created on first call; `last_login_at` updates on subsequent calls.
- [x] 2.3 API test ensures `telegram_user_id` is derived from initData even if a conflicting query parameter is provided.
- [x] 2.4 Schema test verifying `users` table columns include `telegram_user_id` unique/indexed and `last_login_at`.

## 3. Validation
- [x] 3.1 Run backend tests covering auth and DB behavior.
- [x] 3.2 Run Alembic migration validation if applicable.
