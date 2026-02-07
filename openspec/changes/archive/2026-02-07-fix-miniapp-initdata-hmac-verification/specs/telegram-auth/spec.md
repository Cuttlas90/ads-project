## MODIFIED Requirements

### Requirement: Telegram Mini App initData verification
The backend SHALL validate Telegram Mini App `initData` signatures using the bot token per Telegram Mini App documentation. It SHALL compute the data-check-string by removing the `hash` key, sorting remaining `key=value` pairs alphabetically, and joining with `\n`. It SHALL derive the HMAC secret key as `HMAC_SHA256(key="WebAppData", msg=bot_token)` and then compare an HMAC-SHA256 of the data-check-string against the provided `hash`. It SHALL reject `initData` with missing or invalid hash values, missing `auth_date`, or `auth_date` older than 24 hours.

The backend SHALL NOT accept Telegram Login Widget signature derivation (`sha256(bot_token)` secret key) for Mini App authentication endpoints.

#### Scenario: Valid Mini App initData
- **WHEN** a request provides `initData` with a correct Mini App hash and `auth_date` within 24 hours
- **THEN** verification succeeds and returns the parsed `initData` payload

#### Scenario: Login Widget signature model rejected
- **WHEN** a request provides `initData` whose hash was generated with Login Widget derivation (`sha256(bot_token)` secret key)
- **THEN** verification fails with an authentication error

#### Scenario: Invalid or expired initData
- **WHEN** a request provides `initData` with a missing or invalid hash, missing `auth_date`, or an `auth_date` older than 24 hours
- **THEN** verification fails with an authentication error
