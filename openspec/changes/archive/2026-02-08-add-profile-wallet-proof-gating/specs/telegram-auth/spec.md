## MODIFIED Requirements

### Requirement: Auth verification endpoint
The backend SHALL expose a protected `/auth/me` route that returns basic user information for verification/testing, including `preferred_role` (nullable), `ton_wallet_address` (nullable), and `has_wallet` (boolean derived from wallet presence).

#### Scenario: Authenticated request with wallet set
- **WHEN** a request with valid initData calls `/auth/me` for a user with a stored wallet
- **THEN** the response includes user identifiers, `preferred_role`, `ton_wallet_address`, and `has_wallet = true`

#### Scenario: Authenticated request without wallet
- **WHEN** a request with valid initData calls `/auth/me` for a user without a stored wallet
- **THEN** the response includes user identifiers, `preferred_role`, `ton_wallet_address = null`, and `has_wallet = false`
