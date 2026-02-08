## MODIFIED Requirements

### Requirement: Telegram stats fetching and raw payload storage
On successful permission checks, the system SHALL perform a Telethon preflight before channel stats RPC calls. The preflight MUST include a successful Telethon transport connection and an authorized Telethon session check. Only after preflight success SHALL the system fetch Telegram channel data using two calls: one for channel info/subscribers and one for channel statistics. It SHALL attempt to populate `subscribers`, `avg_views`, `language_stats`, and `premium_stats` where available, and SHALL store a combined `raw_stats` JSON object that includes both responses.

#### Scenario: Stats fields missing
- **WHEN** Telegram omits optional stats fields
- **THEN** the snapshot is still stored with null parsed fields and the full raw payloads

#### Scenario: Telethon preflight fails
- **WHEN** Telethon connection fails or the Telethon session is not authorized
- **THEN** verification stops before Telegram stats RPC calls and no new snapshot is stored

### Requirement: Channel verification endpoint
The system SHALL expose `POST /channels/{id}/verify` requiring authentication. It SHALL return HTTP 200 with updated channel data on success, HTTP 404 when the channel does not exist, HTTP 403 when the caller lacks membership or bot permissions are insufficient, and HTTP 502 when Telegram upstream dependencies required for verification are unavailable or fail.

#### Scenario: Verification success
- **WHEN** an authorized caller verifies a channel with valid bot permissions and Telethon preflight succeeds
- **THEN** the response is HTTP 200 and includes `is_verified = true`

#### Scenario: Upstream verification dependency failure
- **WHEN** bot permission checks succeed but Telethon preflight or stats RPC calls fail
- **THEN** the response is HTTP 502 with a controlled verification error detail

## ADDED Requirements

### Requirement: Failure path persistence guardrails
The system SHALL preserve channel verification persistence integrity across Telegram failure paths. If verification fails after request admission but before completion, it MUST NOT set `channels.is_verified = true` and MUST NOT append a `channel_stats_snapshots` row.

#### Scenario: No partial persistence on failure
- **WHEN** a verification request fails due to Telethon connection, authorization, or Telegram stats errors
- **THEN** channel verification state and snapshot history remain unchanged
