## MODIFIED Requirements

### Requirement: Deal persistence
The system SHALL persist deals in a `deals` table with fields `id`, `source_type` (enum: `listing`, `campaign`), `advertiser_id` (FK to `users.id`), `channel_id` (FK to `channels.id`), `channel_owner_id` (FK to `users.id`), `listing_id` (FK to `listings.id`, nullable), `listing_format_id` (FK to `listing_formats.id`, nullable), `campaign_id` (FK to `campaign_requests.id`, nullable), `campaign_application_id` (FK to `campaign_applications.id`, nullable), `price_ton` (required decimal), `ad_type` (required string), `placement_type` (nullable enum: `post` or `story`), `exclusive_hours` (nullable int), `retention_hours` (nullable int), `creative_text` (required text), `creative_media_type` (required string: `image` or `video`), `creative_media_ref` (required string), `posting_params` (nullable JSON), `scheduled_at` (nullable timestamp), `verification_window_hours` (nullable int), `posted_at` (nullable timestamp), `posted_message_id` (nullable string), `posted_content_hash` (nullable string), `verified_at` (nullable timestamp), `state` (DealState), `created_at`, and `updated_at`. It SHALL default `state = DRAFT`. It SHALL enforce that exactly one source is set: listing fields for `source_type = listing`, campaign fields for `source_type = campaign`. It SHALL enforce unique `campaign_application_id` so one application maps to at most one deal. It SHALL NOT enforce unique `campaign_id`, allowing multiple deals per campaign. It SHALL index `advertiser_id`, `channel_id`, and `state`.

#### Scenario: Multiple campaign deals allowed
- **WHEN** two different applications for the same campaign are accepted within campaign limits
- **THEN** two distinct deals with the same `campaign_id` and different `campaign_application_id` values are persisted

#### Scenario: Application-deal uniqueness preserved
- **WHEN** a second deal creation is attempted for the same `campaign_application_id`
- **THEN** the request is rejected with a conflict and no duplicate deal is created

### Requirement: Create deal from campaign application acceptance
The system SHALL expose `POST /campaigns/{campaign_id}/applications/{application_id}/accept` requiring authentication. It SHALL allow only the campaign `advertiser_id` to call it. It SHALL validate the campaign exists and is not hidden, the application exists, belongs to the campaign, is not hidden, and is in `submitted` status. It SHALL require `price_ton`, `ad_type`, `creative_text`, `creative_media_type`, `creative_media_ref`, and optional `posting_params`. It SHALL create a deal in `DRAFT` with `source_type = campaign`, set `campaign_id` and `campaign_application_id`, set `channel_id` and `channel_owner_id` from the application, and set the application status to `accepted`. It SHALL enforce campaign `max_acceptances`; if current accepted count is already at limit, it SHALL reject with HTTP 409 and SHALL NOT create a deal. It SHALL return HTTP 409 if a deal already exists for the application.

#### Scenario: Advertiser accepts application under limit
- **WHEN** the advertiser accepts a submitted campaign application and the campaign has remaining acceptance capacity
- **THEN** the application becomes `accepted` and a `DRAFT` deal is created

#### Scenario: Future accepts blocked after limit reached
- **WHEN** an advertiser attempts to accept another offer after accepted count equals `max_acceptances`
- **THEN** the response is HTTP 409 and no additional deal is created

## ADDED Requirements

### Requirement: Campaign acceptance limit enforcement is transaction-safe
The system SHALL enforce `max_acceptances` for campaign-offer acceptance in a single database transaction with campaign-level row locking. The accepted-count check and deal creation SHALL occur in the same locked transaction scope so parallel accept requests cannot exceed the configured limit.

#### Scenario: Concurrent accepts cannot exceed max_acceptances
- **WHEN** multiple accept requests for the same campaign are submitted concurrently near the acceptance limit
- **THEN** at most `max_acceptances` accepts succeed and all excess requests fail with conflict

### Requirement: Limit transition closes campaign and remaining offers
When an acceptance causes campaign accepted count to reach `max_acceptances`, the system SHALL transition campaign lifecycle to `closed_by_limit`, set campaign compatibility inactive state, and auto-reject remaining submitted offers for that campaign. After this transition, owner apply and further accept operations for that campaign SHALL be blocked.

#### Scenario: Accept reaching cap closes campaign
- **WHEN** the acceptance that reaches `max_acceptances` commits successfully
- **THEN** campaign lifecycle becomes `closed_by_limit` and remaining submitted offers are auto-rejected
