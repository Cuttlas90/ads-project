## MODIFIED Requirements

### Requirement: Deal persistence
The system SHALL persist deals in a `deals` table with fields `id`, `source_type` (enum: `listing`, `campaign`), `advertiser_id` (FK to `users.id`), `channel_id` (FK to `channels.id`), `channel_owner_id` (FK to `users.id`), `listing_id` (FK to `listings.id`, nullable), `listing_format_id` (FK to `listing_formats.id`, nullable), `campaign_id` (FK to `campaign_requests.id`, nullable), `campaign_application_id` (FK to `campaign_applications.id`, nullable), `price_ton` (required decimal), `ad_type` (required string), `placement_type` (nullable enum: `post` or `story`), `exclusive_hours` (nullable int), `retention_hours` (nullable int), `creative_text` (required text), `creative_media_type` (required string: `image` or `video`), `creative_media_ref` (required string), `posting_params` (nullable JSON), `scheduled_at` (nullable timestamp), `verification_window_hours` (nullable int), `posted_at` (nullable timestamp), `posted_message_id` (nullable string), `posted_content_hash` (nullable string), `verified_at` (nullable timestamp), `state` (DealState), `created_at`, and `updated_at`. It SHALL default `state = DRAFT`. It SHALL enforce that exactly one source is set: listing fields for `source_type = listing`, campaign fields for `source_type = campaign`. It SHALL enforce unique `campaign_application_id` and unique `campaign_id` to allow only one accepted application per campaign. It SHALL index `advertiser_id`, `channel_id`, and `state`.

#### Scenario: Listing-sourced deal stores structured terms
- **WHEN** a deal is created from a listing format
- **THEN** the row persists `placement_type`, `exclusive_hours`, and `retention_hours` copied from the listing format

#### Scenario: Scheduled posting metadata stored
- **WHEN** a deal is scheduled after creative approval
- **THEN** `scheduled_at` and `verification_window_hours` are stored on the deal

#### Scenario: Posted metadata stored
- **WHEN** a post is published via the bot
- **THEN** `posted_at`, `posted_message_id`, and `posted_content_hash` are stored on the deal

### Requirement: Create deal from listing selection
The system SHALL expose `POST /listings/{listing_id}/deals` requiring authentication. It SHALL require `listing_format_id`, `creative_text`, `creative_media_type`, `creative_media_ref`, and optional `posting_params`. It SHALL validate the listing exists, is active, and the format belongs to the listing. It SHALL create a deal in `DRAFT` with `source_type = listing`, `price_ton`, `ad_type`, `placement_type`, `exclusive_hours`, and `retention_hours` copied from the listing format, and ignore any client-provided values for these listing-derived fields.

#### Scenario: Listing selection creates draft deal with locked structured terms
- **WHEN** an advertiser submits a valid listing format and creative payload
- **THEN** the response is HTTP 201 with a deal in `DRAFT` and listing-derived terms locked to the selected format

### Requirement: Update deal draft proposal
The system SHALL expose `PATCH /deals/{id}` requiring authentication. It SHALL allow updates only when the deal state is `DRAFT` or `NEGOTIATION`. It SHALL enforce role-based field edits as follows:
- For `source_type = listing`: both parties MAY edit `creative_text`, `creative_media_type`, `creative_media_ref`, and `posting_params`; `price_ton`, `ad_type`, `placement_type`, `exclusive_hours`, and `retention_hours` SHALL remain locked.
- For `source_type = campaign`: the advertiser MAY edit `price_ton`, `ad_type`, `creative_*`, and `posting_params`; the channel owner MAY edit only `creative_*` and `posting_params`.
Each update SHALL write a `deal_events` row with `event_type = proposal` and the changed fields in `payload`. If the deal is in `DRAFT`, the update SHALL transition it to `NEGOTIATION` via `apply_transition()`.

#### Scenario: Listing-sourced structured terms cannot be edited
- **WHEN** either participant attempts to update `placement_type`, `exclusive_hours`, or `retention_hours` on a listing-sourced deal in `DRAFT` or `NEGOTIATION`
- **THEN** the request is rejected and the deal remains unchanged
