## ADDED Requirements
### Requirement: Telegram permissions are authoritative
The system SHALL treat Telegram permissions as the source of truth for sensitive channel actions. `channel_members` records SHALL be treated as internal intent only and SHALL NOT grant access when Telegram indicates the user is no longer an admin or lacks required rights. Authorization failures due to Telegram permissions SHALL block the action without mutating database state.

#### Scenario: Manager revoked in Telegram
- **WHEN** a user is listed as a `manager` in `channel_members` but Telegram reports they are not an admin
- **THEN** the sensitive action is blocked and the membership row remains unchanged

### Requirement: Channel access revalidation helper
The backend SHALL provide `revalidate_channel_access` in `backend/app/services/manager_revalidate.py` with the signature:

```python
async def revalidate_channel_access(
    *,
    telegram_client: TelegramClientService,
    channel,
    telegram_user_id: int,
    required_rights: set[str],
) -> None:
    ...
```

It SHALL call `check_user_permissions` from `backend/app/telegram/permissions.py` to verify the user is an admin and has all `required_rights`. If the check fails, it SHALL raise a domain-level error that includes the channel id, `telegram_user_id`, and missing permissions. It SHALL not access or mutate the database.

#### Scenario: Admin with required rights
- **WHEN** the Telegram permission check returns `ok=True`
- **THEN** `revalidate_channel_access` returns without raising

#### Scenario: Missing rights
- **WHEN** the Telegram permission check returns `ok=False` with missing permissions
- **THEN** `revalidate_channel_access` raises a domain error containing the channel id, `telegram_user_id`, and missing permissions
