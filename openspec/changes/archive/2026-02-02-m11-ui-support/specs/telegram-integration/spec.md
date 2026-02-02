## MODIFIED Requirements

### Requirement: Telegram integration settings
The backend and bot services SHALL define `TELEGRAM_ENABLED` (default `true`), `TELEGRAM_BOT_TOKEN`, `TELEGRAM_API_ID`, `TELEGRAM_API_HASH`, `TELEGRAM_SESSION_NAME` (default `"tgads_backend"`), and `TELEGRAM_MEDIA_CHANNEL_ID`. Telegram service methods SHALL fail fast with a clear configuration error when `TELEGRAM_ENABLED` is false or required credentials are missing.

#### Scenario: Telegram disabled
- **WHEN** `TELEGRAM_ENABLED` is false and a Telegram service method is called
- **THEN** the call fails with a controlled error and no network request is made

#### Scenario: Missing credentials
- **WHEN** `TELEGRAM_ENABLED` is true but required Telegram credentials are missing
- **THEN** the call fails with a controlled error before any network request is attempted

## ADDED Requirements

### Requirement: Bot API media upload helper
The system SHALL provide a Bot API helper that uploads `image` or `video` media to `TELEGRAM_MEDIA_CHANNEL_ID` and returns the resulting Telegram `file_id` and media type. It SHALL raise a controlled error on non-200 responses.

#### Scenario: Media upload returns file id
- **WHEN** media is uploaded to the Telegram Bot API
- **THEN** the response includes the Telegram `file_id` for the uploaded media
