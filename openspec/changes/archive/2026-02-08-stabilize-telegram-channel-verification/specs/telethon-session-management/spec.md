## ADDED Requirements

### Requirement: Telethon service session lifecycle states
The system SHALL model the backend Telethon service account session with explicit lifecycle states: `unauthorized`, `authorizing`, `authorized`, and `revoked`. State transitions MUST be deterministic and driven by observable Telegram authentication outcomes.

#### Scenario: Successful authorization transition
- **WHEN** an authorization flow completes with valid phone login, OTP code, and required 2FA password
- **THEN** the session state transitions `unauthorized -> authorizing -> authorized`

#### Scenario: Revoked session detected
- **WHEN** a previously authorized session is no longer accepted by Telegram
- **THEN** the session state transitions `authorized -> revoked` and the system marks the session as not ready for stats operations

### Requirement: Verification readiness contract
The system SHALL expose a Telethon readiness contract for stats-dependent operations. A verification flow that requires Telethon stats MUST proceed only when the session state is `authorized`; it MUST fail fast with a controlled verification error for all other states.

#### Scenario: Ready session permits stats flow
- **WHEN** channel verification starts and the Telethon session state is `authorized`
- **THEN** the flow continues to Telegram stats RPC calls

#### Scenario: Unready session blocks stats flow
- **WHEN** channel verification starts and the Telethon session state is `unauthorized`, `authorizing`, or `revoked`
- **THEN** the flow stops before stats RPC calls and returns a controlled failure describing remediation

### Requirement: Session persistence and continuity
The system SHALL persist an authorized Telethon session across backend restarts using a configured durable session source, and it MUST support explicit session replacement without requiring source-code changes.

#### Scenario: Restart retains authorized state
- **WHEN** the backend restarts after a successful Telethon authorization
- **THEN** the service restores the persisted session and resumes in `authorized` state

#### Scenario: Session replacement updates active credentials
- **WHEN** operators replace the persisted Telethon session with a new authorized session
- **THEN** subsequent verification requests use the new session and no mixed-session state is observed
