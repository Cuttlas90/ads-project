## MODIFIED Requirements

### Requirement: DealState enum and transition table
The system SHALL define a DealState enum with the canonical values `DRAFT`, `NEGOTIATION`, `REJECTED`, `ACCEPTED`, `CREATIVE_SUBMITTED`, `CREATIVE_CHANGES_REQUESTED`, `CREATIVE_APPROVED`, `FUNDED`, `SCHEDULED`, `POSTED`, `VERIFIED`, `RELEASED`, and `REFUNDED`. It SHALL define a transition table that lists allowed actions, allowed actor roles (`advertiser`, `channel_owner`, `system`), and allowed `from_state` -> `to_state` pairs. The transition table SHALL include explicit negotiation actions: participant proposes (`DRAFT`/`NEGOTIATION` -> `NEGOTIATION`), counterparty approves latest proposal (`DRAFT`/`NEGOTIATION` -> `CREATIVE_APPROVED`), and counterparty rejects latest proposal (`DRAFT`/`NEGOTIATION` -> `REJECTED`). The transition table SHALL include system-only actions that move a deal from `CREATIVE_APPROVED` to `FUNDED`, from `FUNDED` to `SCHEDULED`, from `SCHEDULED` to `POSTED`, from `POSTED` to `VERIFIED`, from `VERIFIED` to `RELEASED`, from `POSTED` to `REFUNDED` when verification fails, and from `CREATIVE_APPROVED` to `REFUNDED` when funding timeout is reached at effective start time (`scheduled_at` or fallback `start_at`). The transition table SHALL be treated as authoritative and SHALL reject any unspecified transition.

#### Scenario: Invalid transition rejected
- **WHEN** an action requests a `from_state` -> `to_state` pair that is not in the transition table
- **THEN** the transition is rejected with a validation error

#### Scenario: Counterparty approval finalizes negotiation
- **WHEN** the non-proposing party approves the latest proposal on a deal in `DRAFT` or `NEGOTIATION`
- **THEN** the deal transitions directly to `CREATIVE_APPROVED`

#### Scenario: System funds approved deal
- **WHEN** the system applies the funding action to a `CREATIVE_APPROVED` deal
- **THEN** the deal transitions to `FUNDED`

#### Scenario: System schedules funded deal
- **WHEN** the system applies the schedule action to a `FUNDED` deal
- **THEN** the deal transitions to `SCHEDULED`

#### Scenario: System posts scheduled deal
- **WHEN** the system applies the post action to a `SCHEDULED` deal
- **THEN** the deal transitions to `POSTED`

#### Scenario: System verifies a posted deal
- **WHEN** the system applies the verify action to a `POSTED` deal
- **THEN** the deal transitions to `VERIFIED`

#### Scenario: System refunds a tampered deal
- **WHEN** the system applies the refund action to a `POSTED` deal that fails verification
- **THEN** the deal transitions to `REFUNDED`

#### Scenario: System closes unfunded approved deal at start time
- **WHEN** the system applies funding-timeout closure to a `CREATIVE_APPROVED` deal whose effective start time (`scheduled_at` or fallback `start_at`) has passed without full funding
- **THEN** the deal transitions to `REFUNDED`
