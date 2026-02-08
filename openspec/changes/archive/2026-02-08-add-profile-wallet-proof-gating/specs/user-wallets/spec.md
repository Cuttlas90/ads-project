## MODIFIED Requirements

### Requirement: User wallet address storage
The system SHALL persist a `ton_wallet_address` on the user record only after successful TonConnect proof verification bound to the authenticated user. The address MUST be updateable, and each update MUST require a fresh proof. The address MUST be required before release or refund transfers are attempted.

#### Scenario: Wallet address stored after valid proof
- **WHEN** an authenticated user completes wallet proof verification successfully
- **THEN** the verified wallet address is stored on that user record

#### Scenario: Wallet address update requires re-proof
- **WHEN** an authenticated user with an existing wallet submits a different wallet
- **THEN** the system requires a new valid proof before replacing the stored wallet address

### Requirement: Wallet address API
The system SHALL expose an authenticated challenge/verify wallet API flow. It SHALL provide `POST /users/me/wallet/challenge` to issue a one-time challenge bound to the caller with a 5-minute expiration, and `POST /users/me/wallet/verify` to verify TonConnect proof and persist the wallet. Proof verification MUST validate challenge binding, expiration, single-use semantics, and app-domain binding before updating the wallet, and it SHALL return the updated user wallet payload on success.

#### Scenario: Challenge issued for authenticated user
- **WHEN** an authenticated user requests `POST /users/me/wallet/challenge`
- **THEN** the system returns a one-time challenge with 5-minute expiry bound to that user

#### Scenario: Valid proof stores wallet
- **WHEN** an authenticated user submits `POST /users/me/wallet/verify` with a valid TonConnect proof for an unexpired challenge
- **THEN** the wallet is stored and the response returns the updated wallet payload

#### Scenario: Replayed challenge is rejected
- **WHEN** an authenticated user reuses an already-consumed challenge in `POST /users/me/wallet/verify`
- **THEN** the system rejects the request and does not update wallet data

#### Scenario: Expired challenge is rejected
- **WHEN** an authenticated user submits proof for a challenge older than 5 minutes
- **THEN** the system rejects the request and does not update wallet data
