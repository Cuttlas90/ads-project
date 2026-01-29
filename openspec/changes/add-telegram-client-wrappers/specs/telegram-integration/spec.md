# telegram-integration Specification

## ADDED Requirements
### Requirement: Telegram integration settings
The backend and bot services SHALL define `TELEGRAM_ENABLED` (default `true`), `TELEGRAM_BOT_TOKEN`, `TELEGRAM_API_ID`, `TELEGRAM_API_HASH`, and `TELEGRAM_SESSION_NAME` (default `"tgads_backend"`) in settings. Telegram service methods SHALL fail fast with a clear configuration error when `TELEGRAM_ENABLED` is false or required credentials are missing.

#### Scenario: Telegram disabled
- **WHEN** `TELEGRAM_ENABLED` is false and a Telegram service method is called
- **THEN** the call fails with a controlled error and no network request is made

#### Scenario: Missing credentials
- **WHEN** `TELEGRAM_ENABLED` is true but required Telegram credentials are missing
- **THEN** the call fails with a controlled error before any network request is attempted

### Requirement: Telethon client wrapper
The system SHALL provide `shared/telegram/telethon_client.py` with a `TelegramClientService` that wraps Telethon's `TelegramClient` using `TELEGRAM_API_ID`, `TELEGRAM_API_HASH`, and `TELEGRAM_SESSION_NAME` (default `"tgads_backend"`). It SHALL expose explicit async `connect()` and `disconnect()` methods and MUST NOT auto-connect at import time. It SHALL NOT expose business operations beyond connection lifecycle management.

#### Scenario: Explicit connect lifecycle
- **WHEN** a caller instantiates `TelegramClientService`, calls `connect()`, then `disconnect()`
- **THEN** the underlying client connects and disconnects exactly once and no auto-connection occurs at import time

### Requirement: Bot API wrapper
The system SHALL provide `shared/telegram/bot_api.py` with a `BotApiService` that constructs the Bot API base URL from `TELEGRAM_BOT_TOKEN` and exposes `send_message(chat_id, text, reply_markup=None, disable_web_page_preview=True)` to call `sendMessage`. It SHALL return the parsed JSON response on success and raise a clear error on non-200 responses. It SHALL NOT implement retries, polling, or webhook handling.

#### Scenario: SendMessage success
- **WHEN** `send_message` is called with a chat_id and text
- **THEN** it issues an HTTP POST to the Bot API `sendMessage` endpoint with the provided payload and returns the parsed JSON response

#### Scenario: Bot API error
- **WHEN** the Bot API responds with a non-200 status
- **THEN** `send_message` raises a controlled error that includes response details

### Requirement: Telegram package exports
The system SHALL expose `TelegramClientService` and `BotApiService` from `shared/telegram/__init__.py`.

#### Scenario: Import convenience
- **WHEN** a caller imports from `app.telegram`
- **THEN** `TelegramClientService` and `BotApiService` are available for use
