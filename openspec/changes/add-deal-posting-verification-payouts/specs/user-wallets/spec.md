## ADDED Requirements
### Requirement: User wallet address storage
The system SHALL persist a `ton_wallet_address` on the user record to support payouts and refunds. The address MUST be required before release or refund transfers are attempted.

#### Scenario: Wallet address stored
- **WHEN** a user submits a TON wallet address
- **THEN** it is stored on the user record

### Requirement: Wallet address API
The system SHALL expose `PUT /users/me/wallet` requiring authentication to store or update the caller's `ton_wallet_address`. It SHALL validate the address is non-empty and return the updated user payload.

#### Scenario: Authenticated user updates wallet
- **WHEN** an authenticated user submits a new wallet address
- **THEN** the address is updated and returned in the response
