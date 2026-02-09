# campaign-applications Specification

## Purpose
TBD - created by archiving change add-campaign-requests. Update Purpose after archive.
## Requirements
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

### Requirement: List campaign applications endpoint
The system SHALL expose `GET /campaigns/{campaign_id}/applications` requiring authentication. It SHALL allow access only to the campaign’s `advertiser_id`, returning HTTP 403 otherwise and HTTP 404 when the campaign does not exist or is hidden. It SHALL return only non-hidden applications (`hidden_at IS NULL`) in a paginated response with `page`, `page_size`, `total`, and `items`. Each item SHALL include `id`, `channel_id`, `channel_username`, `channel_title`, `proposed_format_label`, `status`, `created_at`, and a stats summary with `avg_views`, `premium_ratio`, and `language_stats` (top language only). It SHALL source stats from the latest `channel_stats_snapshots` for each channel; `premium_ratio` is derived from `premium_stats.premium_ratio` (default `0.0` when missing), and `language_stats` is either `null` or a single-entry map of the highest-ratio language code to its ratio.

#### Scenario: Advertiser reviews applicants
- **WHEN** an advertiser lists applications for their campaign
- **THEN** the response includes applicant channel metadata and stats summary

#### Scenario: Hidden offers excluded from advertiser offer page
- **WHEN** the advertiser lists applications for a campaign after some offers were soft-hidden
- **THEN** hidden offers are excluded from `items` and from `total`

### Requirement: Campaign hide cascades to related offers
When a campaign is soft-hidden, the system SHALL soft-hide all related campaign applications in the same transaction by setting `hidden_at`. Campaign/offer pages SHALL stop showing those offers after the transaction commits. Accepted offers that already created deals SHALL remain visible through deal detail and deal history endpoints.

#### Scenario: Campaign delete hides related offers
- **WHEN** an advertiser soft-hides a campaign with submitted and accepted offers
- **THEN** all related offers are soft-hidden for campaign/offer pages, and accepted offers remain discoverable through linked deal endpoints

### Requirement: Auto-close remaining offers at campaign acceptance limit
When an application acceptance causes the campaign accepted count to reach `max_acceptances`, the system SHALL auto-close remaining `submitted` applications for that campaign by setting their status to `rejected` with a system reason representing limit closure.

#### Scenario: Reaching limit rejects remaining submitted offers
- **WHEN** an acceptance causes accepted count to equal `max_acceptances`
- **THEN** all remaining `submitted` offers for that campaign are transitioned to `rejected`

### Requirement: Advertiser aggregated offers inbox endpoint
The system SHALL expose `GET /campaigns/offers` requiring authentication. It SHALL return offers (`campaign_applications`) for campaigns owned by the authenticated advertiser across all their campaigns in a single paginated response. It SHALL exclude offers with `hidden_at` set and offers whose campaigns are hidden.

#### Scenario: Advertiser sees one cross-campaign offer inbox
- **WHEN** an advertiser requests `GET /campaigns/offers`
- **THEN** the response includes offers from all campaigns owned by that advertiser, excluding hidden records

### Requirement: Aggregated offers sorting and payload
`GET /campaigns/offers` SHALL return items sorted by newest offer first (`created_at DESC`, deterministic tie-break by `id DESC`). Each item SHALL include `application_id`, `campaign_id`, `campaign_title`, `channel_id`, `channel_username`, `channel_title`, `owner_id`, `proposed_format_label`, `proposed_placement_type`, `proposed_exclusive_hours`, `proposed_retention_hours`, `status`, and `created_at`.

#### Scenario: Offers inbox includes structured proposal terms
- **WHEN** an advertiser loads the aggregated offers inbox
- **THEN** each offer includes placement type and exclusive/retention values for acceptance decisions

### Requirement: Multi-channel owner apply behavior
The system SHALL allow the same owner to apply to the same campaign using different owned verified channels. It SHALL continue enforcing uniqueness only for `(campaign_id, channel_id)` pairs.

#### Scenario: Owner applies from two owned verified channels
- **WHEN** an owner submits applications for one campaign using two distinct owned verified channels
- **THEN** both applications are accepted as long as each `(campaign_id, channel_id)` pair is unique

