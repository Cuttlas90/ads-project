## MODIFIED Requirements

### Requirement: Escrow init endpoint
The system SHALL expose `POST /deals/{id}/escrow/init` requiring authentication. It SHALL allow only the deal advertiser to call it and SHALL require the deal to be in `CREATIVE_APPROVED` state. It SHALL create the escrow row if missing, ensure a deposit address exists, transition the escrow to `AWAITING_DEPOSIT`, and return the deposit address, fee percent, and confirmation threshold. The endpoint SHALL be idempotent.

#### Scenario: Escrow init is idempotent
- **WHEN** the advertiser calls escrow init twice for the same creative-approved deal
- **THEN** the same escrow and deposit address are returned and no duplicate escrow is created

## ADDED Requirements

### Requirement: Escrow status endpoint
The system SHALL expose `GET /deals/{id}/escrow` requiring authentication for deal participants. It SHALL return `state`, `deposit_address`, `expected_amount_ton`, `received_amount_ton`, and `deposit_confirmations`.

#### Scenario: Funding screen polls escrow
- **WHEN** the UI calls `/deals/{id}/escrow`
- **THEN** the response includes escrow state and confirmation data
