## 1. Escrow Address Model and TON Encoding

- [x] 1.1 Add escrow schema fields for `deposit_address_raw`, `subwallet_id`, and optional `escrow_network`, with Alembic migration/backfill.
- [x] 1.2 Update TON wallet derivation helpers to emit network-correct friendly addresses and canonical raw addresses from the same derived wallet.
- [x] 1.3 Update escrow init and TONConnect payload paths to use the new address contract and preserve idempotency.

## 2. Funding Detection and Timeout Closure

- [x] 2.1 Normalize TON addresses in chain scan matching so friendly/raw and bounce/non-bounce variants map to the same canonical account.
- [x] 2.2 Extend escrow watcher timeout logic to use effective start time (`scheduled_at`, fallback `start_at`) and persist timeout events.
- [x] 2.3 Add escrow event uniqueness and cursor semantics for `tx_seen` entries to guarantee watcher idempotency (no double-count).
- [x] 2.4 Implement timeout closure path that moves deal `CREATIVE_APPROVED -> REFUNDED` and executes advertiser refund when partial funds exist.

## 3. Payout/Refund Source Wallet Hardening

- [x] 3.1 Extend transfer service to support selecting source subwallet id instead of always using subwallet `0`.
- [x] 3.2 Update release/refund services to settle from escrow-linked subwallet, use escrowed amount basis, and always deduct refund network fee.
- [x] 3.3 Keep settlement idempotent by enforcing single-write transaction hash behavior for release/refund.

## 4. Posting and Worker Operations

- [x] 4.1 Keep posting scheduler funded-first (`FUNDED -> SCHEDULED -> POSTED`) and explicitly skip unfunded creative-approved deals.
- [x] 4.2 Ensure Celery worker task registration and beat schedule include escrow watch, posting, and verification tasks.
- [x] 4.3 Add runtime checks so TON-dependent workers fail fast with actionable logs when required settings are missing (`TONCENTER_API`, mnemonic, etc.).
- [x] 4.4 Extend `GET /health` to evaluate required env configuration and return missing-key diagnostics by subsystem (without exposing secret values).
- [x] 4.5 Update runbook/compose guidance for required TON/worker env and worker+beat startup verification.

## 5. Tests and Validation

- [x] 5.1 Add tests for address encoding variants and canonical normalization behavior.
- [x] 5.2 Add watcher tests for no-fund timeout and partial-fund timeout refund behavior.
- [x] 5.3 Add payout/refund tests that prove source subwallet selection and escrow-based amount calculations.
- [x] 5.4 Add posting tests verifying unfunded deals are never auto-posted.
- [x] 5.5 Run `openspec validate stabilize-ton-escrow-address-funding-flow --strict` and targeted backend tests for TON escrow/posting/verification flows.
- [x] 5.6 Add FSM-authority tests: reject unspecified transitions and assert workers mutate deal/escrow state only via FSM actions/helpers.
- [x] 5.7 Add `/health` readiness tests covering fully configured and missing-config degraded responses.
