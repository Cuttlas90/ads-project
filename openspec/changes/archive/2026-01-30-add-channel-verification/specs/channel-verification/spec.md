## ADDED Requirements
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
On successful permission checks, the system SHALL fetch Telegram channel data using two calls: one for channel info/subscribers and one for channel statistics. It SHALL attempt to populate `subscribers`, `avg_views`, `language_stats`, and `premium_stats` where available, and SHALL store a combined `raw_stats` JSON object that includes both responses.

#### Scenario: Stats fields missing
- **WHEN** Telegram omits optional stats fields
- **THEN** the snapshot is still stored with null parsed fields and the full raw payloads

### Requirement: Channel metadata refresh on verification
The system SHALL update `channels.telegram_channel_id`, `channels.username`, and `channels.title` from Telegram data (when available) and set `channels.is_verified = true` within the same transaction that stores the snapshot. Re-verifying an already verified channel SHALL append another snapshot and refresh metadata.

#### Scenario: Re-verification refreshes metadata
- **WHEN** a verified channel is verified again
- **THEN** a new snapshot is appended and channel metadata is refreshed

### Requirement: Channel verification endpoint
The system SHALL expose `POST /channels/{id}/verify` requiring authentication. It SHALL return HTTP 200 with updated channel data on success, HTTP 404 when the channel does not exist, and HTTP 403 when the caller lacks membership or bot permissions are insufficient.

#### Scenario: Verification success
- **WHEN** an authorized caller verifies a channel with valid bot permissions
- **THEN** the response is HTTP 200 and includes `is_verified = true`
