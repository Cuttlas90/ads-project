# Change: Add Telegram client wrappers for MTProto + Bot API

## Why
Both backend and bot will need a minimal, reusable Telegram integration layer before any channel stats, messaging, or posting logic can be built. Centralizing credentials and exposing thin wrappers keeps future features consistent and CI-safe without duplicating code.

## What Changes
- Add a shared Telegram integration module in `shared/telegram/` that wraps Telethon (MTProto) with explicit connect/disconnect lifecycle methods and a configurable session name
- Add a shared Telegram Bot API wrapper with a single sendMessage call
- Centralize Telegram credentials, a TELEGRAM_ENABLED feature flag, and TELEGRAM_SESSION_NAME in both backend and bot settings using the same pydantic-settings pattern
- Add mocked unit tests for both wrappers in backend and bot to keep CI free of real Telegram calls
- Update the bot-skeleton spec to allow the bot settings scaffold

## Impact
- Affected specs: new `telegram-integration` capability; modified `bot-skeleton`
- Affected code: `shared/telegram/*`, `backend/app/settings.py`, `bot/app/settings.py`, `backend/pyproject.toml`, `bot/pyproject.toml`, `backend/tests/telegram/*`, `bot/tests/telegram/*`, `.env.example`
