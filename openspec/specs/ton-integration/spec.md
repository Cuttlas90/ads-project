# ton-integration Specification

## Purpose
TBD - created by archiving change add-ton-escrow-funding. Update Purpose after archive.
## Requirements
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
The system SHALL provide a `build_tonconnect_transaction(deal_id, from_user)` helper and expose `POST /deals/{id}/escrow/tonconnect-tx` requiring authentication. It SHALL allow only the advertiser to call it, SHALL require the deal to be in `CREATIVE_APPROVED` state, SHALL use the escrow deposit address, SHALL set the amount to `deal.price_ton`, and SHALL include a `validUntil` timestamp ~10 minutes in the future.

#### Scenario: TONConnect payload created for advertiser
- **WHEN** an advertiser requests the TONConnect payload for a creative-approved deal
- **THEN** the response includes the deposit address, the deal price amount, and a validUntil timestamp

### Requirement: TON payout and refund service
The system SHALL provide a TON transfer service that sends funds from the hot wallet mnemonic to a target address using the TonCenter/tonutils stack. The service SHALL support release (owner payout) and refund (advertiser payout) and SHALL return the transaction hash for each transfer. It SHALL fail fast if TON is disabled or required settings are missing.

#### Scenario: TON release transfer
- **WHEN** the system releases funds for a verified deal
- **THEN** it sends a transfer to the channel owner's wallet and returns the transaction hash

### Requirement: Fee and refund calculation
The system SHALL compute a platform fee percentage from `TON_FEE_PERCENT` and subtract it from the deal amount at release time. Refunds SHALL return the full deal amount minus a fixed network fee amount (default 0.02 TON), and MUST NOT apply the platform fee.

#### Scenario: Fee deducted on release
- **WHEN** a deal with price 10 TON is released and fee percent is 5%
- **THEN** the payout amount is 9.5 TON

#### Scenario: Refund subtracts network fee
- **WHEN** a deal with price 10 TON is refunded with a 0.02 TON network fee
- **THEN** the refund amount is 9.98 TON
