## Context
We need a minimal channel persistence layer and ownership mapping before any Telegram permission checks or stats collection. This change must stay focused on storage and basic APIs.

## Goals / Non-Goals
- Goals:
  - Persist channels with normalized usernames and unverified state.
  - Persist channel members with explicit owner/manager roles.
  - Provide minimal authenticated APIs to submit and list channels.
- Non-Goals:
  - Telegram API calls, permission checks, bot admin verification.
  - Stats fetching, deal logic, pricing, or background jobs.

## Decisions
- Normalize usernames by trimming whitespace, stripping leading '@', lowercasing, then validating against `[a-z0-9_]{5,32}` and rejecting URL/path-like inputs (e.g., `t.me/`).
- Store the normalized lowercase username to enforce case-insensitive uniqueness via a unique index.
- Enforce ownership at the database level using a partial unique index on `channel_members(channel_id)` where `role = 'owner'`.
- Use SQLModel tables in `shared/db/models` and re-export in `backend/app/models` so Alembic metadata stays centralized.
- Keep roles as internal strings (`owner`, `manager`), with semantics validated later via Telegram checks.

## Risks / Trade-offs
- Partial unique indexes are Postgres-specific; SQLite used in tests may not enforce the single-owner constraint.

## Migration Plan
- Add a migration that creates `channels` and `channel_members`, plus required indexes and FKs.
- Rollback by dropping the new tables and indexes.

## Open Questions
- None.
