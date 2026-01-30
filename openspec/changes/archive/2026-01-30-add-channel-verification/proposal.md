# Change: Add channel verification with Telegram stats snapshots

## Why
Channel verification is required before enabling Telegram interactions, and we need an audit trail of initial channel statistics. This change adds a verified gate backed by Telegram permissions and captures a raw stats snapshot for future refreshes.

## What Changes
- Add a channel stats snapshot table that stores parsed stats and the full raw Telegram payload.
- Add a channel verification service that checks owner/manager access, validates bot permissions, fetches stats, updates channel metadata, and persists a snapshot in a single transaction.
- Add `POST /channels/{id}/verify` to trigger verification and return the updated channel.
- Add mocked Telethon tests for permission failure, success snapshot creation, and authorization denial.

## Impact
- Affected specs: new `channel-verification` capability.
- Affected code: `shared/db/models/*`, `backend/app/models/*`, `backend/app/services/*`, `backend/app/api/routes/channels.py`, Alembic migrations, backend tests.
