## MODIFIED Requirements

### Requirement: TONConnect payload builder and endpoint
The system SHALL provide a `build_tonconnect_transaction(deal_id, from_user)` helper and expose `POST /deals/{id}/escrow/tonconnect-tx` requiring authentication. It SHALL allow only the advertiser to call it, SHALL require the deal to be in `CREATIVE_APPROVED` state, SHALL use the escrow deposit address, SHALL set the amount to `deal.price_ton`, and SHALL include a `validUntil` timestamp ~10 minutes in the future.

#### Scenario: TONConnect payload created for advertiser
- **WHEN** an advertiser requests the TONConnect payload for a creative-approved deal
- **THEN** the response includes the deposit address, the deal price amount, and a validUntil timestamp
