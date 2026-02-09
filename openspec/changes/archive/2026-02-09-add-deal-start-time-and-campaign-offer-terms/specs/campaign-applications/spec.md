## MODIFIED Requirements

### Requirement: Campaign application persistence
The system SHALL persist campaign applications in a `campaign_applications` table with fields `id`, `campaign_id` (FK to `campaign_requests.id`), `channel_id` (FK to `channels.id`), `owner_id` (FK to `users.id`), `proposed_format_label` (required), `proposed_placement_type` (required enum: `post` or `story`), `proposed_exclusive_hours` (required integer >= 0), `proposed_retention_hours` (required integer >= 1), `message` (nullable), `status` (required, default `submitted`), `hidden_at` (nullable timestamp), and `created_at`. It SHALL enforce unique `(campaign_id, channel_id)` and SHALL index `campaign_id`, `owner_id`, and `channel_id`. Allowed `status` values are `submitted`, `withdrawn`, `accepted`, and `rejected`.

#### Scenario: Application stores structured placement terms
- **WHEN** a channel owner applies to a campaign
- **THEN** the stored application includes placement type and exclusive/retention hours

### Requirement: Apply to campaign endpoint
The system SHALL expose `POST /campaigns/{campaign_id}/apply` requiring authentication. It SHALL validate the campaign exists and has `lifecycle_state = active`, the channel exists and `is_verified = true`, and the authenticated user is the channel owner (`channel_members.role = owner`). It SHALL require `proposed_placement_type`, `proposed_exclusive_hours`, and `proposed_retention_hours`, and accept optional `proposed_format_label` and optional `message`. It SHALL create the application with `status = submitted` and return HTTP 201 with the application data including structured placement terms. It SHALL return HTTP 404 when the campaign does not exist, is hidden, or is closed by limit, and HTTP 404 when the channel does not exist. It SHALL return HTTP 400 for invalid structured term payloads, HTTP 403 when the caller is not the channel owner, and HTTP 409 when a duplicate application exists.

#### Scenario: Owner applies with structured terms
- **WHEN** a channel owner applies to an active campaign with valid placement/exclusive/retention terms
- **THEN** the response is HTTP 201 and the application stores those structured terms

### Requirement: Aggregated offers sorting and payload
`GET /campaigns/offers` SHALL return items sorted by newest offer first (`created_at DESC`, deterministic tie-break by `id DESC`). Each item SHALL include `application_id`, `campaign_id`, `campaign_title`, `channel_id`, `channel_username`, `channel_title`, `owner_id`, `proposed_format_label`, `proposed_placement_type`, `proposed_exclusive_hours`, `proposed_retention_hours`, `status`, and `created_at`.

#### Scenario: Offers inbox includes structured proposal terms
- **WHEN** an advertiser loads the aggregated offers inbox
- **THEN** each offer includes placement type and exclusive/retention values for acceptance decisions
