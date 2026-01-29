## Context
The project needs MTProto access (Telethon) and Bot API access for future stats, messaging, and auto-posting workflows across both backend and bot services. Today we only verify Telegram Mini App initData. This change introduces a small, testable infrastructure layer with explicit lifecycle control and a feature flag to prevent unwanted network calls.

## Goals / Non-Goals
- Goals:
  - Provide thin, reusable wrappers for Telethon and the Bot API
  - Centralize Telegram credentials in settings
  - Keep CI safe with mocked tests and no automatic network calls
- Non-Goals:
  - Channel stats, permissions checks, posting, or updates handling
  - Retries, polling, webhooks, caching, or background connections

## Decisions
- Create `shared/telegram/` with `TelegramClientService` and `BotApiService`, plus package exports, so backend and bot share the same wrappers.
- Use a configurable Telethon session name via `TELEGRAM_SESSION_NAME` with default `"tgads_backend"`.
- Use sync `httpx` for the Bot API wrapper to align with existing dependencies.
- Add `TELEGRAM_ENABLED` (default true) and require credentials when enabled in both backend and bot settings.
- Implement `bot/app/settings.py` with the same pydantic-settings pattern as `backend/app/settings.py` (Settings class, env_file ".env", cached `get_settings()`).
- When `TELEGRAM_ENABLED` is false, service methods raise a clear, controlled error rather than silently no-oping.

## Risks / Trade-offs
- Telethon creates a local session file by default; this is acceptable for MVP but may require storage strategy later.
- Sync HTTP calls can block in busy endpoints; acceptable for now and can be upgraded to async if needed.
- Strict fail-fast gating may require test setup; mitigate with explicit test configuration and mocks.
- Shared wrappers mean dependency changes affect both services; mitigated by keeping the API minimal and stable.

## Migration Plan
- Add settings fields and update `.env.example` with `TELEGRAM_ENABLED`.
- Add wrappers and tests (all mocked).
- No runtime wiring yet; consumers will be added in later changes.

## Open Questions
- None.
