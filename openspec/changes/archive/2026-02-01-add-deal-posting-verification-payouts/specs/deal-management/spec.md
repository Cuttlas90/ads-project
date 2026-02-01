## MODIFIED Requirements
### Requirement: Deal persistence
The system SHALL persist deals in a `deals` table with fields `id`, `source_type` (enum: `listing`, `campaign`), `advertiser_id` (FK to `users.id`), `channel_id` (FK to `channels.id`), `channel_owner_id` (FK to `users.id`), `listing_id` (FK to `listings.id`, nullable), `listing_format_id` (FK to `listing_formats.id`, nullable), `campaign_id` (FK to `campaign_requests.id`, nullable), `campaign_application_id` (FK to `campaign_applications.id`, nullable), `price_ton` (required decimal), `ad_type` (required string), `creative_text` (required text), `creative_media_type` (required string: `image` or `video`), `creative_media_ref` (required string), `posting_params` (nullable JSON), `scheduled_at` (nullable timestamp), `verification_window_hours` (nullable int), `posted_at` (nullable timestamp), `posted_message_id` (nullable string), `posted_content_hash` (nullable string), `verified_at` (nullable timestamp), `state` (DealState), `created_at`, and `updated_at`. It SHALL default `state = DRAFT`. It SHALL enforce that exactly one source is set: listing fields for `source_type = listing`, campaign fields for `source_type = campaign`. It SHALL enforce unique `campaign_application_id` and unique `campaign_id` to allow only one accepted application per campaign. It SHALL index `advertiser_id`, `channel_id`, and `state`.

#### Scenario: Scheduled posting metadata stored
- **WHEN** a deal is scheduled after creative approval
- **THEN** `scheduled_at` and `verification_window_hours` are stored on the deal

#### Scenario: Posted metadata stored
- **WHEN** a post is published via the bot
- **THEN** `posted_at`, `posted_message_id`, and `posted_content_hash` are stored on the deal

## MODIFIED Requirements
### Requirement: DealState enum and transition table
The system SHALL define a DealState enum with the canonical values `DRAFT`, `NEGOTIATION`, `REJECTED`, `ACCEPTED`, `FUNDED`, `CREATIVE_SUBMITTED`, `CREATIVE_APPROVED`, `SCHEDULED`, `POSTED`, `VERIFIED`, `RELEASED`, and `REFUNDED`. It SHALL define a transition table that lists allowed actions, allowed actor roles (`advertiser`, `channel_owner`, `system`), and allowed `from_state` → `to_state` pairs. The transition table SHALL include system-only actions that move a deal from `ACCEPTED` to `FUNDED`, from `CREATIVE_APPROVED` to `SCHEDULED`, from `SCHEDULED` to `POSTED`, from `POSTED` to `VERIFIED`, from `VERIFIED` to `RELEASED`, and from `POSTED` to `REFUNDED` when verification fails. The transition table SHALL be treated as authoritative and SHALL reject any unspecified transition.

#### Scenario: System schedules approved creative
- **WHEN** the system applies the schedule action to a `CREATIVE_APPROVED` deal
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
