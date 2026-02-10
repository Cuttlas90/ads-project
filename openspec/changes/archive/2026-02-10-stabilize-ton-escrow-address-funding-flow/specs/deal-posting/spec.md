## MODIFIED Requirements

### Requirement: Auto-post scheduling
The system SHALL schedule auto-posting only after escrow funding has been confirmed. The scheduler SHALL select only deals in `FUNDED` or `SCHEDULED` with `scheduled_at <= now`, and SHALL transition `FUNDED -> SCHEDULED` before attempting to publish. Scheduling MUST be idempotent and MUST NOT schedule or post a deal more than once.

#### Scenario: Eligible funded deal is scheduled
- **WHEN** a deal is `FUNDED` and `scheduled_at` is in the past
- **THEN** the system transitions the deal to `SCHEDULED` exactly once

#### Scenario: Unfunded approved deal is skipped
- **WHEN** a deal is `CREATIVE_APPROVED` and `scheduled_at` is in the past but funding is incomplete
- **THEN** the scheduler does not transition or post the deal
