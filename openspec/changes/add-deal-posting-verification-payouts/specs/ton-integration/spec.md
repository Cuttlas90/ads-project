## ADDED Requirements
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
