## ADDED Requirements
### Requirement: TON settings
The backend SHALL define TON settings: `TON_ENABLED` (default true), `TON_NETWORK` (default `testnet` when `ENV=dev`, `mainnet` otherwise), `TON_CONFIRMATIONS_REQUIRED` (default 3), `TON_FEE_PERCENT`, `TON_HOT_WALLET_MNEMONIC`, `TONCENTER_API`, `TONCENTER_KEY` (optional), and `TONCONNECT_MANIFEST_URL`. All TON features SHALL fail fast with a clear error if `TON_ENABLED` is false or required values are missing.

#### Scenario: TON disabled
- **WHEN** `TON_ENABLED` is false and a TON service is invoked
- **THEN** the call fails with a controlled error before any network request

### Requirement: Deterministic per-deal address derivation
The system SHALL provide `generate_deal_deposit_address(deal_id)` that derives a Tonkeeper-valid W5 address deterministically from `TON_HOT_WALLET_MNEMONIC`. The derivation SHALL compute `subwallet_id = hash(deal_id) mod 2^31`, SHALL NOT persist per-deal private keys, and SHALL store the resulting address on the escrow record.

#### Scenario: Deterministic address matches on repeat
- **WHEN** `generate_deal_deposit_address` is called multiple times for the same deal id
- **THEN** the same deposit address is returned

### Requirement: TONConnect payload builder and endpoint
The system SHALL provide a `build_tonconnect_transaction(deal_id, from_user)` helper and expose `POST /deals/{id}/escrow/tonconnect-tx` requiring authentication. It SHALL allow only the advertiser to call it, SHALL use the escrow deposit address, SHALL set the amount to `deal.price_ton`, and SHALL include a `validUntil` timestamp ~10 minutes in the future.

#### Scenario: TONConnect payload created for advertiser
- **WHEN** an advertiser requests the TONConnect payload for an accepted deal
- **THEN** the response includes the deposit address, the deal price amount, and a validUntil timestamp
