# telegram-permissions Specification

## ADDED Requirements
### Requirement: Required bot permissions set
The backend SHALL define a single `REQUIRED_BOT_RIGHTS` constant in `backend/app/telegram/permissions.py` containing exactly `post_messages`, `edit_messages`, `delete_messages`, and `view_statistics` using Telethon field names. It SHALL be importable by other modules.

#### Scenario: Required rights are importable
- **WHEN** a caller imports `REQUIRED_BOT_RIGHTS`
- **THEN** the set contains exactly `post_messages`, `edit_messages`, `delete_messages`, and `view_statistics`

### Requirement: Permission check result structure
Permission checks SHALL return a structured result object with `ok: bool`, `is_admin: bool`, `missing_permissions: list[str]`, and `present_permissions: list[str]`.

#### Scenario: Structured result returned
- **WHEN** a permission check is performed and some rights are missing
- **THEN** the result includes `ok=False`, `is_admin` reflecting admin status, and lists the missing and present permissions

### Requirement: Bot permission check
The system SHALL provide `check_bot_permissions(client, channel)` in `backend/app/telegram/permissions.py` to verify the system bot is an admin and has all required rights. It SHALL accept a channel id, channel username, or `InputChannel`, and SHALL return a structured result without raising on failure.

#### Scenario: Bot admin with full rights
- **WHEN** the bot is an admin and has all required rights
- **THEN** the result returns `ok=True` with an empty `missing_permissions`

#### Scenario: Bot not admin
- **WHEN** the bot is not an admin
- **THEN** the result returns `ok=False` and `missing_permissions` includes all required rights

### Requirement: User permission check
The system SHALL provide `check_user_permissions(client, channel, telegram_user_id, required_rights)` in `backend/app/telegram/permissions.py` to verify a user is an admin and has the requested rights. It SHALL accept a channel id, channel username, or `InputChannel`, SHALL use Telegram as the source of truth, and SHALL return a structured result without raising on failure.

#### Scenario: User missing required rights
- **WHEN** the user is an admin but lacks some required rights
- **THEN** the result returns `ok=False` and lists the missing rights

### Requirement: Domain permission enforcement helper
The system SHALL provide `ensure_permissions(result, *, context)` in `backend/app/domain/permissions.py` that raises a domain-level error when `result.ok` is false and includes the provided context and missing permissions. It SHALL not raise when `result.ok` is true.

#### Scenario: Permission denied raises
- **WHEN** `ensure_permissions` is called with `ok=False`
- **THEN** a domain-level permission error is raised with the context and missing permissions
