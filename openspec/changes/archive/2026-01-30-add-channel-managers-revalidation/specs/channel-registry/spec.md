## ADDED Requirements
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
