## 1. Implementation
- [x] 1.1 Add `ChannelStatsSnapshot` model in `shared/db/models`, export via `shared/db/base.py`, and add a thin wrapper in `backend/app/models/`.
- [x] 1.2 Create Alembic migration for `channel_stats_snapshots` with FK to `channels.id` and required indexes.
- [x] 1.3 Define domain/service errors for channel verification outcomes (not found, not member, permission denied).
- [x] 1.4 Implement `verify_channel` orchestration service with permission check, stats fetch (two Telethon calls), snapshot persistence, channel metadata updates, and transaction handling.
- [x] 1.5 Add `POST /channels/{id}/verify` endpoint that maps service errors to HTTP 404/403 and returns the updated channel.
- [x] 1.6 Add tests with mocked Telethon and permission checks covering: permission denied, success snapshot creation, and non-owner/manager access.

## 2. Validation
- [x] 2.1 Run `openspec validate add-channel-verification --strict`.
- [x] 2.2 Run backend test suite (or targeted tests for channels/telegram verification).
