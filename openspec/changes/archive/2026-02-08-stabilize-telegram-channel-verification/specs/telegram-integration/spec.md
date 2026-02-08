## MODIFIED Requirements

### Requirement: Telegram integration settings
The backend and bot services SHALL define `TELEGRAM_ENABLED` (default `true`), `TELEGRAM_BOT_TOKEN`, `TELEGRAM_API_ID`, `TELEGRAM_API_HASH`, `TELEGRAM_SESSION_NAME` (default `"tgads_backend"`), and `TELEGRAM_MEDIA_CHANNEL_ID`. They SHALL additionally support optional MTProto proxy configuration via `TELEGRAM_MTPROXY_HOST`, `TELEGRAM_MTPROXY_PORT`, and `TELEGRAM_MTPROXY_SECRET`. MTProxy fields MUST be treated as an all-or-none group: when any MTProxy field is set, all three MUST be present and valid. Telegram service methods SHALL fail fast with a clear configuration error when `TELEGRAM_ENABLED` is false or required credentials are missing.

#### Scenario: Telegram disabled
- **WHEN** `TELEGRAM_ENABLED` is false and a Telegram service method is called
- **THEN** the call fails with a controlled error and no network request is made

#### Scenario: Missing credentials
- **WHEN** `TELEGRAM_ENABLED` is true but required Telegram credentials are missing
- **THEN** the call fails with a controlled error before any network request is attempted

#### Scenario: Incomplete MTProxy configuration
- **WHEN** one or two MTProxy fields are set but the full MTProxy tuple is incomplete
- **THEN** Telethon client creation fails with a controlled configuration error that names the missing field(s)

### Requirement: Telethon client wrapper
The system SHALL provide `shared/telegram/telethon_client.py` with a `TelegramClientService` that wraps Telethon's `TelegramClient` using `TELEGRAM_API_ID`, `TELEGRAM_API_HASH`, and `TELEGRAM_SESSION_NAME` (default `"tgads_backend"`). It SHALL expose explicit async `connect()` and `disconnect()` methods and MUST NOT auto-connect at import time. When a complete MTProxy tuple is configured, it SHALL initialize Telethon with an MTProxy-capable connection mode using the configured proxy tuple; otherwise it SHALL use the default direct MTProto connection mode. It SHALL NOT expose business operations beyond connection lifecycle management.

#### Scenario: Explicit connect lifecycle
- **WHEN** a caller instantiates `TelegramClientService`, calls `connect()`, then `disconnect()`
- **THEN** the underlying client connects and disconnects exactly once and no auto-connection occurs at import time

#### Scenario: MTProxy transport selected
- **WHEN** MTProxy settings are fully configured
- **THEN** the Telethon wrapper initializes the client with MTProxy transport and proxy tuple settings

## ADDED Requirements

### Requirement: Telethon authorization status helper
The Telegram integration layer SHALL provide an explicit way for backend services to determine whether the current Telethon session is authorized before issuing stats-dependent business operations.

#### Scenario: Unauthorized session reported
- **WHEN** backend verification checks Telethon authorization status and the session is not authorized
- **THEN** the integration layer reports unauthorized state so the caller can fail with a controlled verification error
