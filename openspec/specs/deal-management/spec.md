# deal-management Specification

## Purpose
TBD - created by archiving change add-deal-fsm. Update Purpose after archive.
## Requirements
### Requirement: Deal persistence
The system SHALL persist deals in a `deals` table with fields `id`, `source_type` (enum: `listing`, `campaign`), `advertiser_id` (FK to `users.id`), `channel_id` (FK to `channels.id`), `channel_owner_id` (FK to `users.id`), `listing_id` (FK to `listings.id`, nullable), `listing_format_id` (FK to `listing_formats.id`, nullable), `campaign_id` (FK to `campaign_requests.id`, nullable), `campaign_application_id` (FK to `campaign_applications.id`, nullable), `price_ton` (required decimal), `ad_type` (required string), `creative_text` (required text), `creative_media_type` (required string: `image` or `video`), `creative_media_ref` (required string), `posting_params` (nullable JSON), `scheduled_at` (nullable timestamp), `verification_window_hours` (nullable int), `posted_at` (nullable timestamp), `posted_message_id` (nullable string), `posted_content_hash` (nullable string), `verified_at` (nullable timestamp), `state` (DealState), `created_at`, and `updated_at`. It SHALL default `state = DRAFT`. It SHALL enforce that exactly one source is set: listing fields for `source_type = listing`, campaign fields for `source_type = campaign`. It SHALL enforce unique `campaign_application_id` and unique `campaign_id` to allow only one accepted application per campaign. It SHALL index `advertiser_id`, `channel_id`, and `state`.

#### Scenario: Listing-sourced deal stored
- **WHEN** a deal is created from a listing format
- **THEN** the row persists with `source_type = listing`, listing fields set, campaign fields null, and `state = DRAFT`

#### Scenario: Scheduled posting metadata stored
- **WHEN** a deal is scheduled after creative approval
- **THEN** `scheduled_at` and `verification_window_hours` are stored on the deal

#### Scenario: Posted metadata stored
- **WHEN** a post is published via the bot
- **THEN** `posted_at`, `posted_message_id`, and `posted_content_hash` are stored on the deal

### Requirement: Deal event persistence
The system SHALL persist deal events in a `deal_events` table with fields `id`, `deal_id` (FK to `deals.id`), `actor_id` (FK to `users.id`, nullable for system actions), `event_type` (required string), `from_state` (nullable DealState), `to_state` (nullable DealState), `payload` (nullable JSON), and `created_at`. It SHALL index `deal_id` and `created_at`.

#### Scenario: Transition event stored
- **WHEN** a deal state transition occurs
- **THEN** a `deal_events` row is stored with `event_type = transition` and populated `from_state`/`to_state`

### Requirement: DealState enum and transition table
The system SHALL define a DealState enum with the canonical values `DRAFT`, `NEGOTIATION`, `REJECTED`, `ACCEPTED`, `CREATIVE_SUBMITTED`, `CREATIVE_CHANGES_REQUESTED`, `CREATIVE_APPROVED`, `FUNDED`, `SCHEDULED`, `POSTED`, `VERIFIED`, `RELEASED`, and `REFUNDED`. It SHALL define a transition table that lists allowed actions, allowed actor roles (`advertiser`, `channel_owner`, `system`), and allowed `from_state` → `to_state` pairs. The transition table SHALL include explicit creative actions: owner submits creative (`ACCEPTED` → `CREATIVE_SUBMITTED`), advertiser approves (`CREATIVE_SUBMITTED` → `CREATIVE_APPROVED`), advertiser requests edits (`CREATIVE_SUBMITTED` → `CREATIVE_CHANGES_REQUESTED`), owner resubmits (`CREATIVE_CHANGES_REQUESTED` → `CREATIVE_SUBMITTED`), and system funding (`CREATIVE_APPROVED` → `FUNDED`) when escrow funding is confirmed. The transition table SHALL include system-only actions that move a deal from `FUNDED` to `SCHEDULED`, from `SCHEDULED` to `POSTED`, from `POSTED` to `VERIFIED`, from `VERIFIED` to `RELEASED`, and from `POSTED` to `REFUNDED` when verification fails. The transition table SHALL be treated as authoritative and SHALL reject any unspecified transition.

#### Scenario: Invalid transition rejected
- **WHEN** an action requests a `from_state` → `to_state` pair that is not in the transition table
- **THEN** the transition is rejected with a validation error

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

### Requirement: apply_transition function
The system SHALL expose a single `apply_transition(deal, action, actor_id, actor_role, payload=None)` function as the only allowed way to mutate `deals.state`. It SHALL validate the transition using the transition table, enforce actor role constraints, write a `deal_events` row for every transition, and update `updated_at` atomically. Direct state mutation outside `apply_transition()` SHALL be treated as invalid behavior.

#### Scenario: State change writes audit trail
- **WHEN** a valid transition is applied via `apply_transition`
- **THEN** the deal state changes and a `deal_events` row is written in the same transaction

### Requirement: Create deal from listing selection
The system SHALL expose `POST /listings/{listing_id}/deals` requiring authentication. It SHALL require `listing_format_id`, `creative_text`, `creative_media_type`, `creative_media_ref`, and optional `posting_params`. It SHALL validate the listing exists, is active, and the format belongs to the listing. It SHALL create a deal in `DRAFT` with `source_type = listing`, `price_ton` and `ad_type` copied from the listing format, and ignore any client-provided price or ad type fields.

#### Scenario: Listing selection creates draft deal
- **WHEN** an advertiser submits a valid listing format and creative payload
- **THEN** the response is HTTP 201 with a deal in `DRAFT` and `price_ton`/`ad_type` locked to the listing format

### Requirement: Create deal from campaign application acceptance
The system SHALL expose `POST /campaigns/{campaign_id}/applications/{application_id}/accept` requiring authentication. It SHALL allow only the campaign `advertiser_id` to call it. It SHALL validate the application exists, belongs to the campaign, and is in `submitted` status. It SHALL require `price_ton`, `ad_type`, `creative_text`, `creative_media_type`, `creative_media_ref`, and optional `posting_params`. It SHALL create a deal in `DRAFT` with `source_type = campaign`, set `campaign_id` and `campaign_application_id`, set `channel_id` and `channel_owner_id` from the application, and set the application status to `accepted`. It SHALL return HTTP 409 if a deal already exists for the campaign or application.

#### Scenario: Advertiser accepts application and creates deal
- **WHEN** the advertiser accepts a submitted campaign application with deal terms
- **THEN** the application becomes `accepted` and a `DRAFT` deal is created

### Requirement: Update deal draft proposal
The system SHALL expose `PATCH /deals/{id}` requiring authentication. It SHALL allow updates only when the deal state is `DRAFT` or `NEGOTIATION`. It SHALL enforce role-based field edits as follows:
- For `source_type = listing`: both parties MAY edit `creative_text`, `creative_media_type`, `creative_media_ref`, and `posting_params`; `price_ton` and `ad_type` SHALL remain locked.
- For `source_type = campaign`: the advertiser MAY edit `price_ton`, `ad_type`, `creative_*`, and `posting_params`; the channel owner MAY edit only `creative_*` and `posting_params`.
Each update SHALL write a `deal_events` row with `event_type = proposal` and the changed fields in `payload`. If the deal is in `DRAFT`, the update SHALL transition it to `NEGOTIATION` via `apply_transition()`.

#### Scenario: Channel owner counters a campaign deal
- **WHEN** a channel owner updates the creative fields on a campaign-sourced deal in `DRAFT`
- **THEN** the deal moves to `NEGOTIATION` and a proposal event is logged

### Requirement: Accept deal proposal
The system SHALL expose `POST /deals/{id}/accept` requiring authentication. It SHALL allow acceptance only when the deal state is `DRAFT` or `NEGOTIATION`, and only by the counterparty to the most recent proposal. It SHALL finalize the deal in `ACCEPTED` using `apply_transition()` and SHALL block further edits after acceptance.

#### Scenario: Counterparty accepts proposal
- **WHEN** the non-proposing party accepts a deal proposal
- **THEN** the deal transitions to `ACCEPTED` and subsequent edits are rejected

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
