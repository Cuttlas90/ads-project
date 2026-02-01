## Context
The system currently supports deal creation, escrow funding detection, and basic bot messaging. The escrow lifecycle stops at `FUNDED`, and no automated posting, verification, or settlement exists. This change introduces the end-to-end workflow from creative approval through auto-posting, integrity verification, and TON release/refund.

## Goals / Non-Goals
- Goals:
  - Auto-post approved creatives at scheduled time via Telegram Bot API.
  - Verify posts via Telethon for deletion/edit detection and hold-time window.
  - Release or refund TON with fee handling and record transaction hashes.
  - Persist wallet addresses for payouts.
- Non-Goals:
  - Disputes, manual overrides, KYC/geo restrictions.
  - Frontend UI beyond a wallet address API.
  - Multi-post campaigns per deal.

## Decisions
- **Scheduling source**: `scheduled_at` is a first-class column on `deals`.
- **FSM progression**: auto-posting uses `CREATIVE_APPROVED → SCHEDULED → POSTED`; verification uses `POSTED → VERIFIED`; settlement uses `VERIFIED → RELEASED` or `POSTED → REFUNDED` when tampered.
- **Verification transport**: Telethon is used to fetch message content and detect deletion/edits.
- **Message content hash**: a deterministic hash is computed over all fields used to send the post (text, media reference, media type, posting params that affect rendering).
- **Verification window**: a per-deal `verification_window_hours` is stored on the deal; values are derived from ad type parameters. Default is 24 hours when not provided.
- **Wallet addresses**: payout addresses are stored on the user record via a dedicated API endpoint.
- **TON payouts**: outbound transfers use the existing TonCenter/tonutils stack, signed by the hot wallet mnemonic.
- **Refund fee policy**: refund returns the full deal amount minus a fixed network fee (default 0.02 TON) in addition to the platform fee handling.

## Risks / Trade-offs
- Using a single `scheduled_at` on `deals` limits multi-post use cases; we accept this for MVP simplicity.
- Telethon message fetch requires proper bot permissions and may fail on channels without required rights; failures must be retried and logged without blocking the worker.
- Outbound TON transfers introduce operational risk; idempotency and transaction logging are mandatory to prevent double payments.

## Migration Plan
- Add new columns to `deals`, `deal_escrows`, and `users` via Alembic migrations.
- Backfill existing rows with nulls/defaults where needed.
- Deploy workers and APIs behind the new specs.

## Open Questions
- None (inputs provided by requester).
