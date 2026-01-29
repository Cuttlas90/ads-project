## 1. Implementation
## 1. Implementation
- [x] 1.1 Add Telegram settings fields (including `TELEGRAM_SESSION_NAME`) and TELEGRAM_ENABLED gating in `backend/app/settings.py` and create `bot/app/settings.py` using the same pydantic-settings pattern with the same fields (required before services).
- [x] 1.2 Add `shared/telegram/telethon_client.py` with `TelegramClientService` connect/disconnect (depends on 1.1).
- [x] 1.3 Add `shared/telegram/bot_api.py` with `BotApiService.send_message` using sync `httpx` (depends on 1.1).
- [x] 1.4 Add `shared/telegram/__init__.py` exports for both services.
- [x] 1.5 Add `telethon` to `backend/pyproject.toml` and add `telethon` + `httpx` + `pydantic-settings` to `bot/pyproject.toml` runtime dependencies.
- [x] 1.6 Update `.env.example` to include `TELEGRAM_ENABLED` and `TELEGRAM_SESSION_NAME` alongside existing Telegram placeholders.
- [x] 1.7 Add backend unit tests for `TelegramClientService` with a mocked Telethon client (depends on 1.2).
- [x] 1.8 Add backend unit tests for `BotApiService` with mocked HTTP responses (depends on 1.3).
- [x] 1.9 Add backend unit tests for disabled/missing-credentials behavior to ensure no network calls.
- [x] 1.10 Add bot unit tests for shared Telegram wrappers and settings gating (depends on 1.1–1.4).

## 2. Validation
- [x] 2.1 Run `pytest` for backend tests (or at least the Telegram-related subset).
