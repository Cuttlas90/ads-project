## Context

The current TON escrow flow derives a deterministic per-deal wallet address and exposes it via escrow init and TONConnect payloads. In live testing for `deal_id=5`, the deal stayed in `CREATIVE_APPROVED`, escrow stayed `AWAITING_DEPOSIT`, and `received_amount_ton` remained `0` despite a user-attempted transfer.

Observed runtime signals:
- Deal `5`: `CREATIVE_APPROVED`, `price_ton=0.50`, `scheduled_at` already passed.
- Escrow row: `AWAITING_DEPOSIT`, expected `0.500000000`, received `0.000000000`, only `address_generated` event.
- Generated deposit address is currently emitted as default `EQ...` format, while the environment is testnet-oriented.
- Backend container runtime was missing `TONCENTER_API`, and only backend/frontend/bot/postgres/redis were running (no worker/beat), preventing watcher/posting progression.

## Goals / Non-Goals

**Goals:**
- Ensure generated escrow deposit addresses are valid for the active TON network and accepted by advertiser wallets.
- Make transaction detection robust against TON address representation variants.
- Guarantee deterministic closure for unfunded deals at start time, including refund handling for partial deposits.
- Ensure release/refund transfers originate from the deal escrow wallet path, not the global sender wallet path.
- Keep the funded-first progression explicit and operationally runnable by Celery worker + beat.

**Non-Goals:**
- Redesigning the full deal lifecycle or introducing a brand-new deal terminal state.
- Introducing manual dispute resolution, manual operator payout workflows, or fiat/off-chain settlement.
- Reworking frontend UX beyond exposing accurate escrow state data already covered by existing APIs.

## Decisions

### 1) Address representation contract for escrow deposits
- Keep deterministic derivation: `subwallet_id = sha256(deal_id) mod 2^31`.
- Persist two address forms on escrow:
  - `deposit_address`: user-facing friendly address for wallets/TONConnect, encoded with network-correct flags.
  - `deposit_address_raw`: canonical raw `workchain:hash` form used for equality/matching.
- For `TON_NETWORK=testnet`, emit test-only friendly format; use non-bounce form for funding UX so wallets do not reject/bounce due representation mismatch.

Rationale: wallet UIs and chain APIs return multiple formats (`EQ/UQ/kQ/0Q` and raw). Persisting both avoids repeated lossy conversions and removes string-equality fragility.

Alternatives considered:
- Keep single stored friendly address and compare as-is: rejected because destination strings from chain providers frequently differ by encoding flags.

### 2) Funding timeout and closure behavior
- Funding deadline uses `effective_start_at`:
  - primary source: `deal.scheduled_at`
  - fallback source: latest negotiated `start_at` value when `scheduled_at` is null
- If no effective start time exists, timeout logic is skipped.
- If deadline is reached and escrow is not funded:
  - transition escrow to `FAILED` with reason `funding_timeout`.
  - transition deal from `CREATIVE_APPROVED` to `REFUNDED` as a system timeout closure.
- Timeout outcomes:
  - `received_amount_ton == 0`: no transfer, mark closure metadata.
  - `received_amount_ton > 0`: execute refund transfer to advertiser and persist refund metadata.
  - refund network fee is always deducted (no waiver), including very small partial deposits.

Rationale: this matches the required business rule (no funding by start time means the deal cannot proceed) while preserving an auditable terminal path.

Alternatives considered:
- Introduce a new `EXPIRED` deal state: rejected for now to avoid broad UI/API ripple for a case already representable as timeout refund closure.

### 3) Settlement source wallet and amount basis
- Extend TON transfer service to accept source subwallet id.
- Release/refund operations use the deal-derived subwallet id, not hardcoded subwallet `0`.
- Settlement amount basis is escrowed amount bounded by expected amount (`min(received_amount_ton, expected_amount_ton)`) before fee math.

Rationale: prevents treasury leakage from unrelated wallet balance and keeps settlements tied to escrowed funds.

Alternatives considered:
- Continue sending from subwallet `0`: rejected because it hides escrow funding failures and can pay from unrelated balance.

### 4) Watcher matching and operational guards
- TonCenter adapter normalizes both input addresses and transaction destination/source addresses to canonical raw before comparisons.
- TON-dependent workers fail fast with actionable logs when required TON settings are missing (`TONCENTER_API`, mnemonic, etc.).
- Watcher idempotency is enforced with persisted cursor semantics and `tx_seen` uniqueness keys to prevent double-counting.
- Deployment/runbook must explicitly include Celery worker and beat; otherwise funded/posting/verification automation cannot progress.

Rationale: the core issue is a combined data-format + operational readiness failure; both must be hardened.

Alternatives considered:
- Rely on silent retries/no-op when misconfigured: rejected because it creates invisible stuck states.

### 5) Posting sequencing remains funded-first
- Preserve canonical progression:
  - watcher: `CREATIVE_APPROVED -> FUNDED`
  - posting worker: `FUNDED -> SCHEDULED -> POSTED`
- Posting scheduler never posts unfunded deals, even if `scheduled_at` is in the past.

Rationale: prevents content publication without confirmed escrow funding.

### 6) Health endpoint readiness diagnostics
- `GET /health` remains lightweight and DB-independent but now reports configuration readiness by subsystem (`backend`, `ton`, `telegram`, `workers`).
- Health response includes missing env variable names only, never raw secret values.
- When required variables for an enabled subsystem are missing, health status is `degraded` with actionable `missing` arrays.

Rationale: this makes deployment/config issues visible immediately and reduces time spent debugging stuck workers and silent no-op flows.

## Risks / Trade-offs

- [Address migration drift] Existing escrows may contain only legacy friendly addresses -> Mitigation: backfill canonical raw values and normalize existing rows in migration/script.
- [Timeout state semantics] Using `REFUNDED` for zero-funded timeout can look semantically broad -> Mitigation: persist explicit event payload reason `funding_timeout_no_funds`.
- [Insufficient gas on subwallet] Deal subwallet may need gas/account activation behavior -> Mitigation: preflight balance/state checks and explicit transfer error logging with retry policy.
- [Operational regressions] Missing worker/beat still blocks automation -> Mitigation: add startup checks, health guidance, and deployment verification tasks.
- [Health data leakage risk] Reporting config diagnostics could expose sensitive values -> Mitigation: expose only variable names and readiness booleans; never return env values.

## Migration Plan

1. Add escrow columns for canonical/raw address and derived subwallet id (Alembic + SQLModel updates).
2. Backfill existing escrow rows:
   - derive subwallet id from deal id,
   - normalize stored friendly address to canonical raw,
   - re-encode user-facing friendly address for active network policy.
3. Update TON services (address generation, chain matching, transfer source selection) and watcher timeout logic.
4. Update FSM transition table for system timeout closure (`CREATIVE_APPROVED -> REFUNDED`).
5. Extend `/health` contract and implementation to return subsystem readiness + missing env keys (with value redaction guarantees).
6. Deploy backend + worker + beat together and restart containers so updated TON env values are loaded.
7. Verify with integration checks: init escrow -> fund -> watcher funded transition -> scheduled posting -> verification -> payout/refund.

Rollback strategy:
- Keep schema changes backward compatible (nullable new columns).
- Revert service logic to legacy address/transfer path while preserving new columns if emergency rollback is required.

## Open Questions

- None at this stage.
