## Why

Escrow funding for TON deals is stalling in production-like testing because generated deposit addresses are not consistently wallet-valid for the active network, and funding detection/worker execution gaps leave deals stuck in `CREATIVE_APPROVED`. We need a hardening pass now so escrow funding, auto-posting, and payout/refund can complete reliably end to end.

## What Changes

- Make per-deal escrow addresses network-correct and wallet-compatible (including testnet-safe user-friendly encoding) while storing a canonical form for chain matching.
- Add deterministic address normalization in watcher logic so incoming transfers are matched regardless of raw/friendly or bounce/non-bounce representation.
- Enforce funding timeout at effective start time (`scheduled_at`, fallback to negotiated `start_at`) for unfunded deals, closing the deal and refunding partial deposits when present.
- Move payout/refund transfer source from global wallet subwallet `0` to the deterministic per-deal escrow subwallet.
- Align posting behavior and FSM expectations with funded-first progression (`CREATIVE_APPROVED -> FUNDED -> SCHEDULED -> POSTED`) and require operational readiness of Celery worker/beat and TON settings.
- Extend `GET /health` to report missing required environment configuration (without exposing secret values), including TON worker-critical settings.

## Capabilities

### New Capabilities
- None.

### Modified Capabilities
- `ton-integration`: tighten address encoding, source-wallet selection, and settlement amount rules.
- `escrow-management`: persist canonical escrow address/subwallet metadata and timeout outcomes.
- `escrow-watcher`: normalize chain/account addresses and enforce funding timeout/refund triggers.
- `deal-posting`: enforce funded-first scheduling semantics and skip unfunded approved deals.
- `deal-management`: extend transition table for system timeout closure from `CREATIVE_APPROVED`.
- `backend-skeleton`: expand `/health` contract to surface readiness and missing configuration keys.

## Impact

- Affected code: `backend/app/services/ton/*`, `backend/app/worker/ton_watch.py`, `backend/app/worker/deal_posting.py`, `backend/app/services/deal_fsm.py`, `backend/app/api/routes/deals.py`, `backend/app/api/routes/health.py`, `backend/app/settings.py`, shared SQLModel/Alembic migration files.
- Affected runtime: Docker/Celery operations must run both worker and beat processes with TON env configured (`TONCENTER_API`, key when required).
- Affected behavior: escrow deposits become wallet/network-safe, funding timeout uses effective start time, release/refund funds originate from the deal escrow wallet path, and `/health` exposes missing config keys by subsystem.
