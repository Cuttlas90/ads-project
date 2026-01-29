# telegram-auth Specification

## ADDED Requirements
### Requirement: Telegram Mini App initData verification
The backend SHALL validate Telegram Mini App initData signatures using the bot token per Telegram's documented algorithm. It SHALL compute the data check string by removing the `hash` key, sorting remaining `key=value` pairs alphabetically, joining with `\n`, and comparing an HMAC-SHA256 (secret key = `sha256(bot_token)`) against the provided hash. It SHALL reject initData with missing or invalid hash values, missing `auth_date`, or `auth_date` older than 24 hours.

#### Scenario: Valid initData
- **WHEN** a request provides initData with a correct hash and `auth_date` within 24 hours
- **THEN** verification succeeds and returns the parsed initData payload

#### Scenario: Invalid initData
- **WHEN** a request provides initData with a missing/invalid hash or an `auth_date` older than 24 hours
- **THEN** verification fails with an authentication error

### Requirement: Telegram-only authentication
The backend SHALL authenticate users only via verified Telegram Mini App initData and SHALL NOT accept JWTs, sessions, cookies, OAuth, passwords, or user identifiers from request parameters.

#### Scenario: Non-Telegram auth rejected
- **WHEN** a request attempts to authenticate without valid initData
- **THEN** the request is treated as unauthenticated

### Requirement: get_current_user dependency
The backend SHALL provide a `get_current_user` FastAPI dependency that reads initData from the `X-Telegram-Init-Data` header, falling back to the `initData` query parameter, verifies it, extracts the Telegram user from initData, and returns the corresponding user record. It SHALL respond with HTTP 401 on missing or invalid initData and SHALL ignore any external user identity parameters.

#### Scenario: Missing or invalid initData
- **WHEN** a request calls a protected route without valid initData
- **THEN** the dependency returns HTTP 401

#### Scenario: Valid initData
- **WHEN** a request calls a protected route with valid initData
- **THEN** the dependency returns the authenticated user derived from initData

### Requirement: User provisioning and login tracking
The backend SHALL use `telegram_user_id` from verified initData to fetch or create a local user record and SHALL update `last_login_at` on each successful authentication.

#### Scenario: First login
- **WHEN** valid initData is received for a Telegram user not yet in the database
- **THEN** a new user record is created with `telegram_user_id` and profile fields from initData

#### Scenario: Subsequent login
- **WHEN** valid initData is received for a Telegram user that already exists
- **THEN** the existing user record is returned and `last_login_at` is updated

### Requirement: Auth verification endpoint
The backend SHALL expose a protected `/auth/me` route that returns basic user information for verification/testing.

#### Scenario: Authenticated request
- **WHEN** a request with valid initData calls `/auth/me`
- **THEN** the response includes the authenticated user's identifiers
