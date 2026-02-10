## MODIFIED Requirements

### Requirement: TonCenter chain adapter
The system SHALL provide a TonCenter V3 JSON-RPC adapter with a minimal interface to (a) list incoming transactions for a given address since a cursor and (b) fetch confirmation counts for a transaction hash. The adapter SHALL be configured via `TONCENTER_API` and optional `TONCENTER_KEY` and MUST NOT hardcode provider URLs. The adapter SHALL normalize account and destination addresses to canonical raw format before matching transactions.

#### Scenario: Adapter uses configured base URL
- **WHEN** the adapter performs a chain query
- **THEN** it uses the `TONCENTER_API` base URL and includes `TONCENTER_KEY` when provided

#### Scenario: Adapter matches friendly and raw address variants
- **WHEN** incoming transaction destination is represented in a different friendly/raw form than stored escrow address
- **THEN** normalization maps both to the same canonical raw address and matching succeeds

### Requirement: Escrow watcher job
The system SHALL run a Celery beat task every 60 seconds (default) to process escrows in `AWAITING_DEPOSIT` or `DEPOSIT_DETECTED`. For each escrow it SHALL:
- resolve effective start time from `deal.scheduled_at`, falling back to latest negotiated `start_at` when `scheduled_at` is null,
- enforce funding timeout when effective start time is known, `effective_start_at <= now`, and escrow is not funded,
- scan for new incoming transactions to the escrow canonical address,
- record each new transaction in `escrow_events` with its hash, amount, and cursor fields,
- add the amounts of new transactions to `received_amount_ton`,
- update `deposit_tx_hash` to the most recent transaction hash, and
- update `deposit_confirmations` from the latest transaction confirmation count.
When `received_amount_ton >= expected_amount_ton` and confirmations meet the threshold, it SHALL transition escrow to `FUNDED` and transition the deal to `FUNDED` via the deal FSM as a system action. When timeout is reached before full funding, it SHALL transition escrow to `FAILED`, transition the deal from `CREATIVE_APPROVED` to `REFUNDED`, and trigger advertiser refund flow when partial funds exist. The watcher MUST be idempotent and MUST NOT double-count transactions or duplicate timeout/refund side effects across runs, including reruns over the same transaction cursor window.

#### Scenario: Partial deposits reach funded
- **WHEN** multiple incoming transactions cumulatively reach the expected amount and confirmations meet the threshold
- **THEN** the escrow and deal transition to `FUNDED` exactly once

#### Scenario: Timeout without funding closes deal
- **WHEN** a creative-approved deal reaches `scheduled_at` and escrow has zero received amount
- **THEN** escrow transitions to `FAILED` and deal transitions to `REFUNDED` without refund transfer

#### Scenario: Timeout with partial funding triggers refund
- **WHEN** a creative-approved deal reaches `scheduled_at` and escrow has partial received amount
- **THEN** escrow transitions to `FAILED`, deal transitions to `REFUNDED`, and partial advertiser refund is initiated exactly once

#### Scenario: Timeout uses start_at fallback when scheduled_at is null
- **WHEN** a creative-approved deal has null `scheduled_at`, fallback `start_at` in the past, and escrow is unfunded
- **THEN** watcher executes timeout closure using fallback start time rules
