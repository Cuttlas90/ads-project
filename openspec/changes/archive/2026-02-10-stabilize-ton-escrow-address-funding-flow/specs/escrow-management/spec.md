## MODIFIED Requirements

### Requirement: Escrow persistence
The system SHALL persist escrows in a `deal_escrows` table with fields `id`, `deal_id` (FK to `deals.id`, unique), `state` (required, indexed), `deposit_address` (wallet-facing friendly form, nullable), `deposit_address_raw` (canonical raw form, nullable, indexed), `subwallet_id` (required int), `escrow_network` (nullable string), `expected_amount_ton` (nullable decimal), `received_amount_ton` (nullable decimal), `deposit_tx_hash` (nullable string, indexed), `deposit_confirmations` (int default 0), `fee_percent` (required decimal), `release_tx_hash` (nullable string), `refund_tx_hash` (nullable string), `released_amount_ton` (nullable decimal), `refunded_amount_ton` (nullable decimal), `released_at` (nullable timestamp), `refunded_at` (nullable timestamp), `created_at`, and `updated_at`. It SHALL set `expected_amount_ton = deal.price_ton` at escrow creation, set `fee_percent` as a snapshot from settings, derive and persist `subwallet_id` from deal id, persist `escrow_network` when available from active TON configuration, and enforce one escrow per deal.

#### Scenario: Escrow created for creative-approved deal
- **WHEN** an advertiser initializes escrow for a `CREATIVE_APPROVED` deal
- **THEN** one escrow row is created with `expected_amount_ton = deal.price_ton`, `fee_percent` populated, and `state = CREATED`

#### Scenario: Release metadata stored
- **WHEN** a verified deal is released
- **THEN** the escrow stores `release_tx_hash`, `released_amount_ton`, and `released_at`

#### Scenario: Refund metadata stored
- **WHEN** a refunded deal executes payout back to advertiser
- **THEN** the escrow stores `refund_tx_hash`, `refunded_amount_ton`, and `refunded_at`

### Requirement: Escrow event persistence
The system SHALL persist escrow events in an `escrow_events` table with fields `id`, `escrow_id` (FK to `deal_escrows.id`, indexed), `actor_user_id` (FK to `users.id`, nullable), `from_state` (nullable string), `to_state` (required string), `event_type` (required string), `payload` (nullable JSON), and `created_at`. It SHALL be append-only. For `tx_seen` events, payload SHALL include canonical `tx_hash` and `lt` cursor metadata. The system SHALL enforce idempotency for observed chain transactions using uniqueness semantics for `tx_seen` by escrow and transaction identity, and watcher cursor progression SHALL be based on the highest persisted `lt`.

#### Scenario: Escrow transition event stored
- **WHEN** an escrow state transition occurs
- **THEN** an `escrow_events` row is stored with the `from_state`, `to_state`, and event payload

#### Scenario: Duplicate tx observation is ignored
- **WHEN** the watcher sees a transaction hash/lt already persisted for the same escrow
- **THEN** no duplicate `tx_seen` amount is counted and no duplicate transaction event is recorded

### Requirement: Escrow init endpoint
The system SHALL expose `POST /deals/{id}/escrow/init` requiring authentication. It SHALL allow only the deal advertiser to call it and SHALL require the deal to be in `CREATIVE_APPROVED` state. It SHALL create the escrow row if missing, ensure both `deposit_address` and `deposit_address_raw` exist, transition the escrow to `AWAITING_DEPOSIT`, and return the wallet-facing deposit address, fee percent, and confirmation threshold. The endpoint SHALL be idempotent.

#### Scenario: Escrow init is idempotent
- **WHEN** the advertiser calls escrow init twice for the same creative-approved deal
- **THEN** the same escrow id, subwallet id, and deposit addresses are returned and no duplicate escrow is created

## ADDED Requirements

### Requirement: Funding timeout outcome persistence
The system SHALL enforce funding timeout at effective start time for escrows that are still not funded. Effective start time SHALL resolve to `deal.scheduled_at`; when `scheduled_at` is null it SHALL fallback to the latest negotiated `start_at`. Timeout processing SHALL persist explicit reason payloads in escrow/deal events. If no funds were received, timeout closure SHALL persist zero-refund outcome without transfer hash. If partial funds were received, timeout closure SHALL persist advertiser refund metadata (`refund_tx_hash`, `refunded_amount_ton`, `refunded_at`) after transfer.

#### Scenario: Timeout with no received funds
- **WHEN** `scheduled_at` is reached and escrow received amount is zero
- **THEN** timeout closure is persisted with reason metadata and no refund transfer hash

#### Scenario: Timeout with partial received funds
- **WHEN** `scheduled_at` is reached and escrow received amount is greater than zero but below expected
- **THEN** timeout closure is persisted and advertiser refund transfer metadata is stored

#### Scenario: Timeout uses start_at fallback
- **WHEN** `scheduled_at` is null and latest negotiated `start_at` is in the past while escrow is not fully funded
- **THEN** timeout closure behavior executes using that fallback start time
