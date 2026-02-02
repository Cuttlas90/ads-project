## MODIFIED Requirements

### Requirement: DealState enum and transition table
The system SHALL define a DealState enum with the canonical values `DRAFT`, `NEGOTIATION`, `REJECTED`, `ACCEPTED`, `CREATIVE_SUBMITTED`, `CREATIVE_CHANGES_REQUESTED`, `CREATIVE_APPROVED`, `FUNDED`, `SCHEDULED`, `POSTED`, `VERIFIED`, `RELEASED`, and `REFUNDED`. It SHALL define a transition table that lists allowed actions, allowed actor roles (`advertiser`, `channel_owner`, `system`), and allowed `from_state` → `to_state` pairs. The transition table SHALL include explicit creative actions: owner submits creative (`ACCEPTED` → `CREATIVE_SUBMITTED`), advertiser approves (`CREATIVE_SUBMITTED` → `CREATIVE_APPROVED`), advertiser requests edits (`CREATIVE_SUBMITTED` → `CREATIVE_CHANGES_REQUESTED`), owner resubmits (`CREATIVE_CHANGES_REQUESTED` → `CREATIVE_SUBMITTED`), and system funding (`CREATIVE_APPROVED` → `FUNDED`) when escrow funding is confirmed. The transition table SHALL be treated as authoritative and SHALL reject any unspecified transition.

#### Scenario: Invalid transition rejected
- **WHEN** an action requests a `from_state` → `to_state` pair that is not in the transition table
- **THEN** the transition is rejected with a validation error

#### Scenario: System funds approved deal
- **WHEN** the system applies the funding action to a `CREATIVE_APPROVED` deal
- **THEN** the deal transitions to `FUNDED`

## ADDED Requirements

### Requirement: Deal inbox endpoint
The system SHALL expose `GET /deals` requiring authentication. It SHALL accept optional `role` (`owner` or `advertiser`), optional `state`, `page` (default 1), and `page_size` (default 20). It SHALL return only deals visible to the caller in a paginated list and include `id`, `state`, `channel_id`, `channel_username`, `channel_title`, `advertiser_id`, `price_ton`, `ad_type`, and `updated_at` for each item.

#### Scenario: State-filtered inbox
- **WHEN** an owner calls `/deals?role=owner&state=CREATIVE_SUBMITTED`
- **THEN** the response includes only their deals in `CREATIVE_SUBMITTED`

### Requirement: Deal detail endpoint
The system SHALL expose `GET /deals/{id}` requiring authentication for deal participants only. It SHALL return the deal summary plus participant display fields `channel_username`, `channel_title`, `advertiser_username`, `advertiser_first_name`, and `advertiser_last_name` when available.

#### Scenario: Participant views deal detail
- **WHEN** a deal participant calls `/deals/{id}`
- **THEN** the response includes the deal summary and participant display fields

### Requirement: Deal timeline endpoint
The system SHALL expose `GET /deals/{id}/events` requiring authentication for deal participants only. It SHALL return a single chronological list of deal and escrow events with fields `event_type`, `from_state`, `to_state`, `payload`, `created_at`, and `actor_id` (nullable). It SHALL support cursor pagination using `cursor` and `limit`, returning `next_cursor` when more events are available.

#### Scenario: Timeline uses cursor pagination
- **WHEN** a participant requests `/deals/{id}/events?limit=20` and a `next_cursor` is returned
- **THEN** a subsequent request with `cursor=next_cursor` returns the next page of events

### Requirement: Submit creative endpoint
The system SHALL expose `POST /deals/{id}/creative/submit` requiring authentication for the channel owner. It SHALL require `creative_text`, `creative_media_type`, and `creative_media_ref`, update the deal creative fields, and transition the deal to `CREATIVE_SUBMITTED` when the current state is `ACCEPTED` or `CREATIVE_CHANGES_REQUESTED`.

#### Scenario: Owner submits creative
- **WHEN** the channel owner submits creative for an `ACCEPTED` deal
- **THEN** the deal transitions to `CREATIVE_SUBMITTED` and creative fields are stored

### Requirement: Approve creative endpoint
The system SHALL expose `POST /deals/{id}/creative/approve` requiring authentication for the advertiser. It SHALL allow approval only when the deal state is `CREATIVE_SUBMITTED` and SHALL transition the deal to `CREATIVE_APPROVED`.

#### Scenario: Advertiser approves creative
- **WHEN** the advertiser approves a `CREATIVE_SUBMITTED` deal
- **THEN** the deal transitions to `CREATIVE_APPROVED`

### Requirement: Request creative edits endpoint
The system SHALL expose `POST /deals/{id}/creative/request-edits` requiring authentication for the advertiser. It SHALL allow requests only when the deal state is `CREATIVE_SUBMITTED` and SHALL transition the deal to `CREATIVE_CHANGES_REQUESTED`.

#### Scenario: Advertiser requests edits
- **WHEN** the advertiser requests edits for a `CREATIVE_SUBMITTED` deal
- **THEN** the deal transitions to `CREATIVE_CHANGES_REQUESTED`
