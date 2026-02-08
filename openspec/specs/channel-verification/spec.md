# channel-verification Specification

## Purpose
TBD - created by archiving change add-channel-verification. Update Purpose after archive.
## Requirements
### Requirement: Channel stats snapshot persistence
The system SHALL persist channel stats snapshots in a `channel_stats_snapshots` table with fields `id`, `channel_id` (FK to `channels.id`), `subscribers` (nullable), `avg_views` (nullable), `language_stats` (JSON, nullable), `premium_stats` (JSON, nullable), `raw_stats` (JSON, nullable), and `created_at`. Snapshots SHALL be append-only and never updated.

#### Scenario: Snapshot stored on verification
- **WHEN** a channel is successfully verified
- **THEN** exactly one new snapshot row is created for that verification

### Requirement: Channel verification authorization
The system SHALL allow channel verification only for callers who are recorded as `owner` or `manager` members of the channel. Unauthorized callers SHALL receive HTTP 403.

#### Scenario: Non-member denied
- **WHEN** a user who is not an owner or manager attempts verification
- **THEN** the request returns HTTP 403

### Requirement: Bot permission gate
The system SHALL reuse `check_bot_permissions` from `backend/app/telegram/permissions.py` to validate the system bot’s admin rights on the channel. If the permission check fails, verification SHALL not mark the channel as verified and SHALL not store a snapshot.

#### Scenario: Missing bot rights
- **WHEN** the bot lacks required admin permissions
- **THEN** verification fails and no snapshot is stored

### Requirement: Telegram stats fetching and raw payload storage
On successful permission checks, the system SHALL perform a Telethon preflight before channel stats RPC calls. The preflight MUST include a successful Telethon transport connection and an authorized Telethon session check. Only after preflight success SHALL the system fetch Telegram channel data using `channels.getFullChannel`, `stats.getBroadcastStats`, and a best-effort `premium.getBoostsStatus` call. Verification SHALL attempt to populate `subscribers`, `avg_views`, `language_stats`, and `premium_stats` where available, and SHALL store a combined `raw_stats` JSON object that includes `full_channel`, `statistics`, and `boosts_status` payloads.

Premium ratio derivation in `premium_stats` SHALL prefer `statistics.premium_graph` when parseable, and SHALL fall back to `boosts_status.premium_audience.part/total` when premium graph data is absent. Failure of `premium.getBoostsStatus` SHALL NOT fail channel verification when other verification steps succeed.

#### Scenario: Boosts fallback derives premium ratio
- **WHEN** broadcast stats omit parseable premium graph data and boosts status contains premium audience counts
- **THEN** verification stores snapshot `premium_stats` with premium ratio derived from `part / total`

#### Scenario: Boosts fetch failure does not block verification
- **WHEN** `premium.getBoostsStatus` fails but channel info and broadcast stats are fetched successfully
- **THEN** verification still succeeds, marks the channel verified, and stores a snapshot with available stats

#### Scenario: Telethon preflight fails
- **WHEN** Telethon connection fails or the Telethon session is not authorized
- **THEN** verification stops before Telegram stats RPC calls and no new snapshot is stored

### Requirement: Channel metadata refresh on verification
The system SHALL update `channels.telegram_channel_id`, `channels.username`, and `channels.title` from Telegram data (when available) and set `channels.is_verified = true` within the same transaction that stores the snapshot. Re-verifying an already verified channel SHALL append another snapshot and refresh metadata.

#### Scenario: Re-verification refreshes metadata
- **WHEN** a verified channel is verified again
- **THEN** a new snapshot is appended and channel metadata is refreshed

### Requirement: Channel verification endpoint
The system SHALL expose `POST /channels/{id}/verify` requiring authentication. It SHALL return HTTP 200 with updated channel data on success, HTTP 404 when the channel does not exist, HTTP 403 when the caller lacks membership or bot permissions are insufficient, and HTTP 502 when Telegram upstream dependencies required for verification are unavailable or fail.

#### Scenario: Verification success
- **WHEN** an authorized caller verifies a channel with valid bot permissions and Telethon preflight succeeds
- **THEN** the response is HTTP 200 and includes `is_verified = true`

#### Scenario: Upstream verification dependency failure
- **WHEN** bot permission checks succeed but Telethon preflight or stats RPC calls fail
- **THEN** the response is HTTP 502 with a controlled verification error detail

### Requirement: Failure path persistence guardrails
The system SHALL preserve channel verification persistence integrity across Telegram failure paths. If verification fails after request admission but before completion, it MUST NOT set `channels.is_verified = true` and MUST NOT append a `channel_stats_snapshots` row.

#### Scenario: No partial persistence on failure
- **WHEN** a verification request fails due to Telethon connection, authorization, or Telegram stats errors
- **THEN** channel verification state and snapshot history remain unchanged

