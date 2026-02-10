## MODIFIED Requirements

### Requirement: TON settings
The backend SHALL define TON settings: `TON_ENABLED` (default true), `TON_NETWORK` (default `testnet` when `ENV=dev`, `mainnet` otherwise), `TON_CONFIRMATIONS_REQUIRED` (default 3), `TON_FEE_PERCENT`, `TON_HOT_WALLET_MNEMONIC`, `TONCENTER_API`, `TONCENTER_KEY` (optional), and `TONCONNECT_MANIFEST_URL`. All TON features SHALL fail fast with a clear error if `TON_ENABLED` is false or required values are missing.

#### Scenario: TON disabled
- **WHEN** `TON_ENABLED` is false and a TON service is invoked
- **THEN** the call fails with a controlled error before any network request

#### Scenario: Missing TonCenter API blocks chain operations
- **WHEN** `TON_ENABLED` is true and `TONCENTER_API` is missing when watcher or transfer services execute
- **THEN** the operation fails with a controlled configuration error before scanning or sending any transaction

#### Scenario: Missing mnemonic blocks wallet operations
- **WHEN** `TON_ENABLED` is true and `TON_HOT_WALLET_MNEMONIC` is missing when address derivation or transfer is requested
- **THEN** the operation fails with a controlled configuration error naming the missing setting

### Requirement: Deterministic per-deal address derivation
The system SHALL provide deterministic per-deal escrow wallet derivation based on `generate_deal_deposit_address(deal_id)` using `subwallet_id = hash(deal_id) mod 2^31` from `TON_HOT_WALLET_MNEMONIC`. The derivation SHALL NOT persist per-deal private keys. The system SHALL persist both a wallet-facing friendly deposit address and a canonical raw deposit address for each escrow. The friendly address SHALL be encoded for the configured network (`test-only` flag on testnet) and SHALL use non-bounce encoding for deposit funding UX.

#### Scenario: Deterministic derivation matches on repeat
- **WHEN** deposit address derivation is executed multiple times for the same deal id and network
- **THEN** the same subwallet id, friendly address, and canonical raw address are produced

#### Scenario: Testnet escrow address is test-only encoded
- **WHEN** `TON_NETWORK` is `testnet` and escrow address is generated
- **THEN** the emitted friendly address is test-only encoded and accepted by testnet wallets

### Requirement: TONConnect payload builder and endpoint
The system SHALL provide a `build_tonconnect_transaction(deal_id, from_user)` helper and expose `POST /deals/{id}/escrow/tonconnect-tx` requiring authentication. It SHALL allow only the advertiser to call it, SHALL require the deal to be in `CREATIVE_APPROVED` state, SHALL use the escrow's wallet-facing deposit address, SHALL set the amount to `deal.price_ton`, and SHALL include a `validUntil` timestamp ~10 minutes in the future.

#### Scenario: TONConnect payload created for advertiser
- **WHEN** an advertiser requests the TONConnect payload for a creative-approved deal
- **THEN** the response includes the escrow wallet-facing deposit address, the deal price amount, and a validUntil timestamp

### Requirement: TON payout and refund service
The system SHALL provide a TON transfer service that sends funds from the deal-derived escrow subwallet (not a hardcoded global subwallet) to a target address using the TonCenter/tonutils stack. The service SHALL support release (owner payout), verification refund, and timeout refund flows, and SHALL return the transaction hash for each transfer. It SHALL fail fast if TON is disabled or required values are missing.

#### Scenario: TON release transfer uses deal escrow subwallet
- **WHEN** the system releases funds for a verified deal
- **THEN** it sends a transfer from that deal's deterministic escrow subwallet to the channel owner's wallet and returns the transaction hash

#### Scenario: TON timeout refund uses deal escrow subwallet
- **WHEN** a deal is closed by funding timeout with partial funds received
- **THEN** the system sends advertiser refund from that deal's deterministic escrow subwallet and returns the transaction hash

### Requirement: Fee and refund calculation
The system SHALL compute settlement principal as `min(received_amount_ton, expected_amount_ton)` from escrow before applying release/refund math. It SHALL compute platform fee percentage from `TON_FEE_PERCENT` and subtract it from principal at release time. Refunds SHALL return principal minus a fixed network fee amount (`TON_REFUND_NETWORK_FEE`, default 0.02 TON), MUST NOT apply the platform fee, and MUST always deduct the refund network fee (no waiver for small principals). If the post-fee refund amount is zero or negative, the system SHALL record a zero refund outcome and MUST NOT send an on-chain transfer.

#### Scenario: Fee deducted on release
- **WHEN** a deal has escrow principal 10 TON and fee percent is 5%
- **THEN** the release payout amount is 9.5 TON

#### Scenario: Partial timeout refund subtracts only network fee
- **WHEN** escrow principal is 0.5 TON and refund network fee is 0.02 TON
- **THEN** the refund amount is 0.48 TON

#### Scenario: Very small partial refund still deducts fee
- **WHEN** escrow principal is 0.01 TON and refund network fee is 0.02 TON
- **THEN** the system records a zero refund outcome and does not send a refund transfer
