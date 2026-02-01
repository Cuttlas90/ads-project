## ADDED Requirements
### Requirement: Funding notification via bot
When a deal transitions to `FUNDED` due to escrow confirmation, the system SHALL send a Telegram bot message to both the advertiser and channel owner stating “Funds for deal #<id> deposited”. It SHALL send the notification once per funding transition and SHALL avoid duplicate sends on watcher retries.

#### Scenario: Both parties notified on funding
- **WHEN** an escrow confirmation transitions a deal to `FUNDED`
- **THEN** the advertiser and channel owner each receive the funding notification message
