# escrow-management Specification

## Purpose
TBD - created by archiving change add-ton-escrow-funding. Update Purpose after archive.
## Requirements
### Requirement: Escrow persistence
The system SHALL persist escrows in a `deal_escrows` table with fields `id`, `deal_id` (FK to `deals.id`, unique), `state` (required, indexed), `deposit_address` (nullable, unique), `expected_amount_ton` (nullable decimal), `received_amount_ton` (nullable decimal), `deposit_tx_hash` (nullable string, indexed), `deposit_confirmations` (int default 0), `fee_percent` (required decimal), `release_tx_hash` (nullable string), `refund_tx_hash` (nullable string), `released_amount_ton` (nullable decimal), `refunded_amount_ton` (nullable decimal), `released_at` (nullable timestamp), `refunded_at` (nullable timestamp), `created_at`, and `updated_at`. It SHALL set `expected_amount_ton = deal.price_ton` at escrow creation, set `fee_percent` as a snapshot from settings, and enforce one escrow per deal.

#### Scenario: Escrow created for accepted deal
- **WHEN** an advertiser initializes escrow for an `ACCEPTED` deal
- **THEN** one escrow row is created with `expected_amount_ton = deal.price_ton`, `fee_percent` populated, and `state = CREATED`

#### Scenario: Release metadata stored
- **WHEN** a verified deal is released
- **THEN** the escrow stores `release_tx_hash`, `released_amount_ton`, and `released_at`

#### Scenario: Refund metadata stored
- **WHEN** a tampered deal is refunded
- **THEN** the escrow stores `refund_tx_hash`, `refunded_amount_ton`, and `refunded_at`

### Requirement: Escrow event persistence
The system SHALL persist escrow events in an `escrow_events` table with fields `id`, `escrow_id` (FK to `deal_escrows.id`, indexed), `actor_user_id` (FK to `users.id`, nullable), `from_state` (nullable string), `to_state` (required string), `event_type` (required string), `payload` (nullable JSON), and `created_at`. It SHALL be append-only.

#### Scenario: Escrow transition event stored
- **WHEN** an escrow state transition occurs
- **THEN** an `escrow_events` row is stored with the `from_state`, `to_state`, and event payload

### Requirement: Escrow FSM and transition helper
The system SHALL define an EscrowState enum with the values `CREATED`, `AWAITING_DEPOSIT`, `DEPOSIT_DETECTED`, `FUNDED`, and `FAILED`, and a transition table listing allowed `from_state` -> `to_state` pairs. It SHALL expose `apply_escrow_transition(escrow, to_state, actor_user_id, event_type, payload)` as the only allowed way to mutate `deal_escrows.state`, and each successful transition SHALL write an `escrow_events` row.

#### Scenario: Invalid escrow transition rejected
- **WHEN** a transition not in the escrow transition table is requested
- **THEN** the transition is rejected and no state or event change occurs

### Requirement: Escrow init endpoint
The system SHALL expose `POST /deals/{id}/escrow/init` requiring authentication. It SHALL allow only the deal advertiser to call it and SHALL require the deal to be in `ACCEPTED` state. It SHALL create the escrow row if missing, ensure a deposit address exists, transition the escrow to `AWAITING_DEPOSIT`, and return the deposit address, fee percent, and confirmation threshold. The endpoint SHALL be idempotent.

#### Scenario: Escrow init is idempotent
- **WHEN** the advertiser calls escrow init twice for the same accepted deal
- **THEN** the same escrow and deposit address are returned and no duplicate escrow is created
