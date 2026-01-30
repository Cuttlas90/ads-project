## Context
Verification is the first time the system actively interacts with Telegram for a channel. We must ensure the system bot has admin rights, update channel metadata from Telegram as the source of truth, and persist an immutable stats snapshot (including raw payloads) for future audits.

## Goals / Non-Goals
- Goals:
  - Verify channels only when the system bot has required rights.
  - Store an append-only stats snapshot with parsed fields and raw Telegram payloads.
  - Update channel metadata (telegram_channel_id, username, title) from Telegram on verification.
  - Keep verification transactional with no partial updates.
- Non-Goals:
  - Background refresh jobs or periodic stats updates.
  - Pricing, listing, or deal logic.
  - Bot posting or escrow-related flows.

## Decisions
- Decision: Use two Telethon calls during verification: one for channel info/subscribers and one for statistics.
  - Rationale: `GetFullChannel` provides subscriber count and metadata; `GetStatistics` provides avg views and breakdowns. Verification should use the minimal set of calls needed to extract required stats.
- Decision: Store `raw_stats` as a combined object with distinct keys for each Telethon response (e.g., `{"full_channel": ..., "statistics": ...}`).
  - Rationale: Preserves raw Telegram source data while avoiding ambiguity about payload origin.
- Decision: Re-verifying an already verified channel will still append a new snapshot and refresh channel metadata.
  - Rationale: Future re-verification scenarios require new snapshots without special-casing the verified state.
- Decision: Wrap permission checks, stats fetch, snapshot creation, and channel updates in a single database transaction.
  - Rationale: Ensures no partial updates when Telegram calls fail or permissions are insufficient.

## Risks / Trade-offs
- Risk: Telethon response objects may not be JSON-serializable as-is.
  - Mitigation: Convert Telethon objects to plain dicts before persistence (e.g., `to_dict()` or an equivalent encoder) and store only JSON-serializable data.
- Risk: Verification may be slower due to two Telegram calls.
  - Mitigation: Keep calls minimal and avoid additional data processing in this flow.

## Migration Plan
- Add the `channel_stats_snapshots` table via Alembic.
- Deploy backend changes behind the new verification endpoint.
- No backfill required; snapshots begin at first verification.

## Open Questions
- None. (Requirements confirmed: re-verification allowed, two Telethon calls, combined raw stats object, update channel metadata.)
