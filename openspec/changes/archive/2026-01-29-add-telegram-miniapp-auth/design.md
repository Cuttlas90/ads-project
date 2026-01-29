## Context
Telegram Mini Apps provide initData that includes user info and a signature. The backend must verify the signature using the bot token before trusting any user data. This will be the only authentication mechanism for the MVP.

## Goals / Non-Goals
- Goals:
  - Verify initData signatures server-side using Telegram's documented algorithm.
  - Persist authenticated users in Postgres with `telegram_user_id` as the external identity.
  - Expose a reusable `get_current_user` dependency for protected routes.
- Non-Goals:
  - JWTs, sessions, cookies, OAuth, or password-based auth.
  - Telegram Bot API calls during authentication.

## Decisions
- Keep the canonical User model in `shared/` and add `backend/app/models/user.py` as a re-export alias for backend usage.
- Replace the existing initial users migration to match the updated schema, treating this as a fresh database.
- Require `auth_date` in initData and reject payloads older than 24 hours.
- Extract `telegram_user_id` exclusively from verified initData; ignore any request parameters that attempt to supply user identity.
- Accept initData from `X-Telegram-Init-Data` header first, then `initData` query parameter as a fallback.

## Risks / Trade-offs
- Replacing the initial migration is not safe for an already-deployed database; this change assumes a fresh database.
- A 24-hour auth window balances replay risk with developer convenience; it is less strict than a short-lived window.

## Migration Plan
- Update the shared users model and replace the existing initial migration to match the new schema.
- Introduce auth verification and dependency wiring; add tests before enabling on routes.

## Open Questions
- None.
