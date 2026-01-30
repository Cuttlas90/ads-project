# Change: Add channel manager CRUD and Telegram revalidation helper

## Why
Channel owners need to manage internal managers, and sensitive operations must be blocked whenever Telegram permissions drift from database intent. Introducing manager CRUD plus a reusable revalidation helper preserves separation of concerns while keeping Telegram as the source of truth.

## What Changes
- Add manager CRUD endpoints under `/channels/{channel_id}/managers` (POST/DELETE/GET) using `telegram_user_id` and no Telegram API calls.
- Add `revalidate_channel_access` to centralize Telegram admin/right checks and raise explicit domain errors on mismatches.
- Document that `channel_members` is non-authoritative and Telegram permissions always gate sensitive actions.
- Add unit tests for the revalidation helper and API tests for manager CRUD.

## Impact
- Affected specs: `channel-registry` (manager CRUD), new `channel-access-revalidation`.
- Affected code: `backend/app/api/routes/channel_managers.py`, `backend/app/api/router.py`, `backend/app/services/manager_revalidate.py`, `backend/app/domain/permissions.py`, `backend/app/schemas/*`, backend tests.
