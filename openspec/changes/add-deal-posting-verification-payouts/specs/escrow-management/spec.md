## MODIFIED Requirements
### Requirement: Escrow persistence
The system SHALL persist escrows in a `deal_escrows` table with fields `id`, `deal_id` (FK to `deals.id`, unique), `state` (required, indexed), `deposit_address` (nullable, unique), `expected_amount_ton` (nullable decimal), `received_amount_ton` (nullable decimal), `deposit_tx_hash` (nullable string, indexed), `deposit_confirmations` (int default 0), `fee_percent` (required decimal), `release_tx_hash` (nullable string), `refund_tx_hash` (nullable string), `released_amount_ton` (nullable decimal), `refunded_amount_ton` (nullable decimal), `released_at` (nullable timestamp), `refunded_at` (nullable timestamp), `created_at`, and `updated_at`. It SHALL set `expected_amount_ton = deal.price_ton` at escrow creation, set `fee_percent` as a snapshot from settings, and enforce one escrow per deal.

#### Scenario: Release metadata stored
- **WHEN** a verified deal is released
- **THEN** the escrow stores `release_tx_hash`, `released_amount_ton`, and `released_at`

#### Scenario: Refund metadata stored
- **WHEN** a tampered deal is refunded
- **THEN** the escrow stores `refund_tx_hash`, `refunded_amount_ton`, and `refunded_at`
