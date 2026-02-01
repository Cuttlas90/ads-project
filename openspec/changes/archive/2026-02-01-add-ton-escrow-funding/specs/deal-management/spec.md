## MODIFIED Requirements
### Requirement: DealState enum and transition table
The system SHALL define a DealState enum with the canonical values `DRAFT`, `NEGOTIATION`, `REJECTED`, `ACCEPTED`, `FUNDED`, `CREATIVE_SUBMITTED`, `CREATIVE_APPROVED`, `SCHEDULED`, `POSTED`, `VERIFIED`, `RELEASED`, and `REFUNDED`. It SHALL define a transition table that lists allowed actions, allowed actor roles (`advertiser`, `channel_owner`, `system`), and allowed `from_state` → `to_state` pairs. The transition table SHALL include a system-only action that moves a deal from `ACCEPTED` to `FUNDED` when escrow funding is confirmed. The transition table SHALL be treated as authoritative and SHALL reject any unspecified transition.

#### Scenario: Invalid transition rejected
- **WHEN** an action requests a `from_state` → `to_state` pair that is not in the transition table
- **THEN** the transition is rejected with a validation error

#### Scenario: System funds accepted deal
- **WHEN** the system applies the funding action to an `ACCEPTED` deal
- **THEN** the deal transitions to `FUNDED`
