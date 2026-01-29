# channel-registry Specification

## Purpose
TBD - created by archiving change add-channel-registry. Update Purpose after archive.
## Requirements
### Requirement: Channel persistence
The system SHALL persist channels with fields `id`, `telegram_channel_id` (nullable), `username` (nullable), `title` (nullable), `is_verified` (default false), `created_at`, and `updated_at`. Channel submission SHALL be based on `username`, and no Telegram API calls SHALL occur during submission.

#### Scenario: Store unverified channel by username
- **WHEN** an authenticated user submits a valid channel username
- **THEN** a channel record is created with `is_verified = false` and `telegram_channel_id = null`

### Requirement: Channel username normalization and validation
The system SHALL trim whitespace, remove a leading `@`, and lowercase the username before validation and storage. It SHALL reject usernames that contain URL/path components (for example `t.me/`) or that do not match `[a-z0-9_]{5,32}`, returning HTTP 400.

#### Scenario: Normalize and accept valid username
- **WHEN** a request submits `"  @Example_Channel  "`
- **THEN** the stored username is `"example_channel"`

#### Scenario: Reject invalid username
- **WHEN** a request submits `"t.me/Example"` or `"ab"`
- **THEN** the request is rejected with HTTP 400

### Requirement: Channel membership roles and constraints
The system SHALL persist channel members with roles `owner` or `manager` and SHALL treat role semantics as internal only. It SHALL enforce one member per `(channel_id, user_id)` and exactly one `owner` per `channel_id` using a database-level constraint.

#### Scenario: Enforce single owner per channel
- **WHEN** a second `owner` membership is created for the same channel
- **THEN** the database constraint prevents the insert

### Requirement: Submit channel endpoint
The system SHALL expose `POST /channels` requiring authentication. It SHALL accept a `username`, normalize and validate it, create the channel with `is_verified = false`, and create a channel member record assigning the caller the `owner` role. It SHALL return HTTP 201 with the channel data and the caller role, return HTTP 409 on duplicate username, and return HTTP 400 on invalid username.

#### Scenario: Submit channel success
- **WHEN** an authenticated user submits a valid username
- **THEN** the response is HTTP 201 with `is_verified = false` and role `owner`

#### Scenario: Duplicate username
- **WHEN** an authenticated user submits a username that already exists
- **THEN** the response is HTTP 409

### Requirement: List channels endpoint
The system SHALL expose `GET /channels` requiring authentication and SHALL return channels where the caller is an `owner` or `manager`. Each list entry SHALL include channel `id`, `username`, `title`, `is_verified`, and the caller's role.

#### Scenario: List owned and managed channels
- **WHEN** an authenticated user requests `/channels`
- **THEN** the response includes only channels they own or manage with the required fields

#### Scenario: Unauthenticated access
- **WHEN** a request without valid authentication calls `/channels`
- **THEN** the response is HTTP 401

