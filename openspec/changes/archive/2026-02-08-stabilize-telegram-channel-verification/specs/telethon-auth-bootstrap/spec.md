## ADDED Requirements

### Requirement: Controlled Telethon authorization entrypoint
The system SHALL provide a controlled operator-only bootstrap entrypoint to authorize the Telethon service account without manual ad-hoc runtime shell steps. The entrypoint MUST require explicit operator initiation and MUST NOT run automatically during normal request handling.

#### Scenario: Operator initiates bootstrap
- **WHEN** an authorized operator triggers Telethon bootstrap
- **THEN** the system starts an interactive authorization flow in `authorizing` state and does not process channel verification within that flow

### Requirement: Interactive Telegram auth flow handling
The bootstrap flow SHALL support Telegram phone login with OTP and optional 2FA password. The flow MUST terminate in `authorized` only after all required factors succeed, otherwise it MUST return to `unauthorized` and report failure.

#### Scenario: OTP and 2FA success
- **WHEN** Telegram requires OTP and 2FA and the operator provides both correctly
- **THEN** bootstrap succeeds and transitions to `authorized`

#### Scenario: Invalid authentication factor
- **WHEN** OTP or 2FA input is invalid
- **THEN** bootstrap fails without creating an authorized session and the state remains `unauthorized`

### Requirement: Secure session material handling
The bootstrap flow SHALL persist authorized Telethon session material only to approved backend session storage, and it MUST NOT expose OTP values, 2FA passwords, or raw session secrets in API responses or standard logs.

#### Scenario: Successful bootstrap persistence
- **WHEN** bootstrap completes successfully
- **THEN** session material is written to the configured secure session store and is reusable by backend verification services

#### Scenario: Sensitive data redaction
- **WHEN** bootstrap logs operational events
- **THEN** logs include status metadata only and exclude OTP, 2FA password, and raw session secret contents
