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

### Requirement: Add channel manager endpoint
The system SHALL expose `POST /channels/{channel_id}/managers` requiring authentication. It SHALL accept `telegram_user_id` (integer) and ignore other payload fields. It SHALL require the caller to be the channel owner and SHALL create a `channel_members` row with role `manager` for the target user. It SHALL NOT call Telegram APIs.

It SHALL return HTTP 201 with the created manager record (`telegram_user_id`, `role`) on success; HTTP 403 when the caller is not the owner; HTTP 404 when the channel or target user does not exist; and HTTP 409 when the target user is already a manager or the owner attempts to add themselves.

#### Scenario: Owner adds manager
- **WHEN** a channel owner posts a valid `telegram_user_id`
- **THEN** a manager membership row is created and HTTP 201 is returned

#### Scenario: Duplicate manager returns conflict
- **WHEN** a channel owner adds a user who is already a manager
- **THEN** the response is HTTP 409

#### Scenario: Non-owner denied
- **WHEN** a non-owner attempts to add a manager
- **THEN** the response is HTTP 403

#### Scenario: Target user missing
- **WHEN** the `telegram_user_id` does not exist in the users table
- **THEN** the response is HTTP 404

### Requirement: Remove channel manager endpoint
The system SHALL expose `DELETE /channels/{channel_id}/managers/{telegram_user_id}` requiring authentication. It SHALL require the caller to be the channel owner and SHALL remove the `channel_members` row with role `manager` for the target user. It SHALL return HTTP 204 on success and SHALL NOT call Telegram APIs.

It SHALL return HTTP 403 when the caller is not the owner; HTTP 404 when the channel does not exist or the user is not a manager; and HTTP 409 when the owner attempts to remove themselves.

#### Scenario: Owner removes manager
- **WHEN** a channel owner removes an existing manager
- **THEN** the manager membership row is deleted and HTTP 204 is returned

#### Scenario: Remove non-existent manager
- **WHEN** a channel owner removes a user who is not a manager
- **THEN** the response is HTTP 404

### Requirement: List channel managers endpoint
The system SHALL expose `GET /channels/{channel_id}/managers` requiring authentication. It SHALL allow callers who are channel owners or managers. It SHALL return HTTP 200 with a list of managers, each entry including `telegram_user_id` and `role`. It SHALL return HTTP 403 for non-members and HTTP 404 when the channel does not exist. It SHALL NOT call Telegram APIs.

#### Scenario: Manager lists managers
- **WHEN** a channel manager requests the manager list
- **THEN** the response is HTTP 200 and includes manager entries with `telegram_user_id` and `role`

