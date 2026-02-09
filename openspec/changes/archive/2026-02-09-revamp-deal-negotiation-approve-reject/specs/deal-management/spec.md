## ADDED Requirements

### Requirement: Reject deal proposal endpoint
The system SHALL expose `POST /deals/{id}/reject` requiring authentication. It SHALL allow rejection only when the deal state is `DRAFT` or `NEGOTIATION`, and only by the counterparty to the most recent proposal. It SHALL finalize the deal in `REJECTED` using `apply_transition()`. After rejection, the system SHALL block further proposal actions (`PATCH /deals/{id}`, `POST /deals/{id}/accept`, and `POST /deals/{id}/reject`) and SHALL treat negotiation as closed.

#### Scenario: Counterparty rejects proposal and closes negotiation
- **WHEN** the non-proposing party rejects a deal proposal
- **THEN** the deal transitions to `REJECTED` and later proposal actions are rejected

## MODIFIED Requirements

### Requirement: DealState enum and transition table
The system SHALL define a DealState enum with the canonical values `DRAFT`, `NEGOTIATION`, `REJECTED`, `ACCEPTED`, `CREATIVE_SUBMITTED`, `CREATIVE_CHANGES_REQUESTED`, `CREATIVE_APPROVED`, `FUNDED`, `SCHEDULED`, `POSTED`, `VERIFIED`, `RELEASED`, and `REFUNDED`. It SHALL define a transition table that lists allowed actions, allowed actor roles (`advertiser`, `channel_owner`, `system`), and allowed `from_state` → `to_state` pairs. The transition table SHALL include explicit negotiation actions: participant proposes (`DRAFT`/`NEGOTIATION` → `NEGOTIATION`), counterparty approves latest proposal (`DRAFT`/`NEGOTIATION` → `CREATIVE_APPROVED`), and counterparty rejects latest proposal (`DRAFT`/`NEGOTIATION` → `REJECTED`). The transition table SHALL include system-only actions that move a deal from `CREATIVE_APPROVED` to `FUNDED`, from `FUNDED` to `SCHEDULED`, from `SCHEDULED` to `POSTED`, from `POSTED` to `VERIFIED`, from `VERIFIED` to `RELEASED`, and from `POSTED` to `REFUNDED` when verification fails. The transition table SHALL be treated as authoritative and SHALL reject any unspecified transition.

#### Scenario: Invalid transition rejected
- **WHEN** an action requests a `from_state` → `to_state` pair that is not in the transition table
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

### Requirement: Update deal draft proposal
The system SHALL expose `PATCH /deals/{id}` requiring authentication. It SHALL allow updates only when the deal state is `DRAFT` or `NEGOTIATION`. It SHALL enforce role-based field edits as follows:
- For `source_type = listing`: both parties MAY edit `creative_text`, `creative_media_type`, `creative_media_ref`, `posting_params`, and `start_at`; `price_ton`, `ad_type`, `placement_type`, `exclusive_hours`, and `retention_hours` SHALL remain locked.
- For `source_type = campaign`: the advertiser MAY edit `price_ton`, `ad_type`, `creative_*`, `posting_params`, and `start_at`; the channel owner MAY edit `creative_*`, `posting_params`, and `start_at`.
Each update SHALL write a `deal_events` row with `event_type = proposal` and a full proposal snapshot in `payload` (including `price_ton`, `ad_type`, `placement_type`, `exclusive_hours`, `retention_hours`, `creative_text`, `creative_media_type`, `creative_media_ref`, `start_at`, and `posting_params`) rather than changed fields only. If `start_at` is updated, the system SHALL persist it as `scheduled_at`. If the deal is in `DRAFT`, the update SHALL transition it to `NEGOTIATION` via `apply_transition()`.

#### Scenario: Start time is negotiable in draft and negotiation
- **WHEN** either deal participant updates `start_at` on a deal in `DRAFT` or `NEGOTIATION`
- **THEN** the deal proposal is updated with new `scheduled_at` and proposal payload stores the full proposal snapshot

### Requirement: Accept deal proposal
The system SHALL expose `POST /deals/{id}/accept` requiring authentication. It SHALL allow approval only when the deal state is `DRAFT` or `NEGOTIATION`, and only by the counterparty to the most recent proposal. It SHALL finalize the deal in `CREATIVE_APPROVED` using `apply_transition()` and SHALL block further proposal edits after approval.

#### Scenario: Counterparty approves proposal
- **WHEN** the non-proposing party approves a deal proposal
- **THEN** the deal transitions to `CREATIVE_APPROVED` and subsequent proposal edits are rejected

### Requirement: Deal timeline endpoint
The system SHALL expose `GET /deals/{id}/events` requiring authentication for deal participants only. It SHALL return a single reverse-chronological list (newest first) of deal and escrow events with fields `event_type`, `from_state`, `to_state`, `payload`, `created_at`, and `actor_id` (nullable). It SHALL support cursor pagination using `cursor` and `limit`, returning `next_cursor` when older events are available.

#### Scenario: Timeline uses cursor pagination for older events
- **WHEN** a participant requests `/deals/{id}/events?limit=20` and a `next_cursor` is returned
- **THEN** a subsequent request with `cursor=next_cursor` returns the next page of older events in reverse-chronological order
