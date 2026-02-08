# telegram-auth Specification

## Purpose
TBD - created by archiving change add-telegram-miniapp-auth. Update Purpose after archive.
## Requirements
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
The backend SHALL expose a protected `/auth/me` route that returns basic user information for verification/testing, including `preferred_role` (nullable), `ton_wallet_address` (nullable), and `has_wallet` (boolean derived from wallet presence).

#### Scenario: Authenticated request with wallet set
- **WHEN** a request with valid initData calls `/auth/me` for a user with a stored wallet
- **THEN** the response includes user identifiers, `preferred_role`, `ton_wallet_address`, and `has_wallet = true`

#### Scenario: Authenticated request without wallet
- **WHEN** a request with valid initData calls `/auth/me` for a user without a stored wallet
- **THEN** the response includes user identifiers, `preferred_role`, `ton_wallet_address = null`, and `has_wallet = false`

### Requirement: User role preference endpoint
The backend SHALL expose `PUT /users/me/preferences` requiring authentication. It SHALL accept `preferred_role` with allowed values `owner` or `advertiser`, persist the value on the user record, and return the updated preference.

#### Scenario: User sets role preference
- **WHEN** an authenticated user sets `preferred_role = owner`
- **THEN** the response is HTTP 200 and includes `preferred_role = owner`

