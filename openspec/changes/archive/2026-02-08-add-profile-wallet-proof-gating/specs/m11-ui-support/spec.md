## ADDED Requirements

### Requirement: Profile wallet connection UX
The Profile UI SHALL include a wallet section that allows authenticated users to connect or update their TON wallet using the backend TonConnect proof flow. Wallet setup SHALL be optional for both owner and advertiser roles and SHALL NOT block role selection or role switching on Profile.

#### Scenario: User can skip wallet during role selection
- **WHEN** a user with no wallet opens Profile and selects a role
- **THEN** role selection succeeds without requiring wallet connection

#### Scenario: User connects wallet from Profile
- **WHEN** a user completes the Profile wallet proof flow successfully
- **THEN** the UI reflects wallet-connected status for that user

## MODIFIED Requirements

### Requirement: Funding flow uses TONConnect
The funding screen SHALL check wallet readiness from authenticated user data before funding actions. If the advertiser wallet is missing (`has_wallet = false`), the screen SHALL hard-block funding actions, SHALL show an in-page modal with one-click navigation to `/profile` including a return target (`next`) to the same funding route, and SHALL NOT call `POST /deals/{id}/escrow/init` or `POST /deals/{id}/escrow/tonconnect-tx`. When wallet readiness is true, the funding screen SHALL use TONConnect UI to submit the payload from `POST /deals/{id}/escrow/tonconnect-tx` and SHALL poll `GET /deals/{id}/escrow` until the escrow state is `FUNDED` or `FAILED`.

#### Scenario: Missing wallet blocks funding actions
- **WHEN** an advertiser opens funding for a deal with `has_wallet = false`
- **THEN** funding actions are blocked and an in-page modal prompts navigation to Profile

#### Scenario: Profile jump preserves funding return path
- **WHEN** the advertiser confirms the modal action from funding
- **THEN** the app navigates to Profile with a `next` target for the same funding route

#### Scenario: Funding flow success after wallet setup
- **WHEN** the advertiser returns from Profile with `has_wallet = true` and submits the TONConnect transaction
- **THEN** the UI calls escrow init/payload endpoints and polls escrow status until it reaches `FUNDED` or `FAILED`
