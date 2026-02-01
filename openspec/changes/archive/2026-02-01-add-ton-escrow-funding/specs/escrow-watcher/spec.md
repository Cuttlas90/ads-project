## ADDED Requirements
### Requirement: TonCenter chain adapter
The system SHALL provide a TonCenter V3 JSON-RPC adapter with a minimal interface to (a) list incoming transactions for a given address since a cursor and (b) fetch confirmation counts for a transaction hash. The adapter SHALL be configured via `TONCENTER_API` and optional `TONCENTER_KEY` and MUST NOT hardcode provider URLs.

#### Scenario: Adapter uses configured base URL
- **WHEN** the adapter performs a chain query
- **THEN** it uses the `TONCENTER_API` base URL and includes `TONCENTER_KEY` when provided

### Requirement: Escrow watcher job
The system SHALL run a Celery beat task every 60 seconds (default) to process escrows in `AWAITING_DEPOSIT` or `DEPOSIT_DETECTED`. For each escrow it SHALL:
- scan for new incoming transactions to the deposit address,
- record each new transaction in `escrow_events` with its hash, amount, and cursor fields,
- add the amounts of new transactions to `received_amount_ton`,
- update `deposit_tx_hash` to the most recent transaction hash, and
- update `deposit_confirmations` from the latest transaction confirmation count.
When `received_amount_ton >= expected_amount_ton` and confirmations meet the threshold, it SHALL transition escrow to `FUNDED` and transition the deal to `FUNDED` via the deal FSM as a system action. The watcher MUST be idempotent and MUST NOT double-count transactions across runs.

#### Scenario: Partial deposits reach funded
- **WHEN** multiple incoming transactions cumulatively reach the expected amount and confirmations meet the threshold
- **THEN** the escrow and deal transition to `FUNDED` exactly once
