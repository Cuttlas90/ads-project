## MODIFIED Requirements

### Requirement: Create deal from listing selection
The system SHALL expose `POST /listings/{listing_id}/deals` requiring authentication. It SHALL require `listing_format_id`, `creative_text`, `creative_media_type`, `creative_media_ref`, and optional `posting_params` and `start_at`. It SHALL validate the listing exists, is active, and the format belongs to the listing. It SHALL create a deal in `DRAFT` with `source_type = listing`, `price_ton`, `ad_type`, `placement_type`, `exclusive_hours`, and `retention_hours` copied from the listing format. If `start_at` is provided, the system SHALL persist it as deal `scheduled_at`.

#### Scenario: Listing selection sets schedule from start_at
- **WHEN** an advertiser submits a valid listing format and creative payload with `start_at`
- **THEN** the response is HTTP 201 with a deal in `DRAFT` and `scheduled_at` equal to the provided `start_at`

### Requirement: Create deal from campaign application acceptance
The system SHALL expose `POST /campaigns/{campaign_id}/applications/{application_id}/accept` requiring authentication. It SHALL allow only the campaign `advertiser_id` to call it. It SHALL validate the campaign exists and is not hidden, the application exists, belongs to the campaign, is not hidden, and is in `submitted` status. It SHALL require `creative_text`, `creative_media_type`, and `creative_media_ref`, and accept optional `start_at`, optional `price_ton`, optional `ad_type`, and optional `posting_params`. It SHALL create a deal in `DRAFT` with `source_type = campaign`, set `campaign_id` and `campaign_application_id`, set `channel_id` and `channel_owner_id` from the application, copy `placement_type`, `exclusive_hours`, and `retention_hours` from the accepted application terms, and set the application status to `accepted`. If `start_at` is provided, it SHALL persist as deal `scheduled_at`. If `price_ton` is omitted, it SHALL default to campaign `budget_ton` and reject acceptance when both are missing or invalid. If `ad_type` is omitted, it SHALL default to the application placement term.

#### Scenario: Campaign acceptance derives terms and scheduling
- **WHEN** the advertiser accepts a submitted campaign application with creative payload and `start_at`
- **THEN** the created deal stores application-derived placement/exclusive/retention terms and `scheduled_at` from `start_at`

### Requirement: Update deal draft proposal
The system SHALL expose `PATCH /deals/{id}` requiring authentication. It SHALL allow updates only when the deal state is `DRAFT` or `NEGOTIATION`. It SHALL enforce role-based field edits as follows:
- For `source_type = listing`: both parties MAY edit `creative_text`, `creative_media_type`, `creative_media_ref`, `posting_params`, and `start_at`; `price_ton`, `ad_type`, `placement_type`, `exclusive_hours`, and `retention_hours` SHALL remain locked.
- For `source_type = campaign`: the advertiser MAY edit `price_ton`, `ad_type`, `creative_*`, `posting_params`, and `start_at`; the channel owner MAY edit `creative_*`, `posting_params`, and `start_at`.
Each update SHALL write a `deal_events` row with `event_type = proposal` and the changed fields in `payload`. If `start_at` is updated, the system SHALL persist it as `scheduled_at`. If the deal is in `DRAFT`, the update SHALL transition it to `NEGOTIATION` via `apply_transition()`.

#### Scenario: Start time is negotiable in draft and negotiation
- **WHEN** either deal participant updates `start_at` on a deal in `DRAFT` or `NEGOTIATION`
- **THEN** the deal proposal is updated with new `scheduled_at` and proposal event payload includes the changed start time
