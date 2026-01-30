# campaign-applications Specification

## ADDED Requirements
### Requirement: Campaign application persistence
The system SHALL persist campaign applications in a `campaign_applications` table with fields `id`, `campaign_id` (FK to `campaign_requests.id`), `channel_id` (FK to `channels.id`), `owner_id` (FK to `users.id`), `proposed_format_label` (required), `message` (nullable), `status` (required, default `submitted`), and `created_at`. It SHALL enforce unique `(campaign_id, channel_id)` and SHALL index `campaign_id`, `owner_id`, and `channel_id`. Allowed `status` values are `submitted` and `withdrawn`.

#### Scenario: Duplicate application prevented
- **WHEN** a second application is created for the same `campaign_id` and `channel_id`
- **THEN** the database constraint prevents the insert

### Requirement: Apply to campaign endpoint
The system SHALL expose `POST /campaigns/{campaign_id}/apply` requiring authentication. It SHALL validate the campaign exists and `is_active = true`, the channel exists and `is_verified = true`, and the authenticated user is the channel owner (`channel_members.role = owner`). It SHALL create the application with `status = submitted` and return HTTP 201 with the application data. It SHALL return HTTP 404 when the campaign or channel does not exist, HTTP 400 when the campaign is inactive or the channel is unverified, HTTP 403 when the caller is not the channel owner, and HTTP 409 when a duplicate application exists.

#### Scenario: Owner applies successfully
- **WHEN** a channel owner applies to an active campaign with a verified channel
- **THEN** the response is HTTP 201 and the application status is `submitted`

### Requirement: List campaign applications endpoint
The system SHALL expose `GET /campaigns/{campaign_id}/applications` requiring authentication. It SHALL allow access only to the campaign’s `advertiser_id`, returning HTTP 403 otherwise and HTTP 404 when the campaign does not exist. It SHALL return a paginated response with `page`, `page_size`, `total`, and `items`. Each item SHALL include `id`, `channel_id`, `channel_username`, `channel_title`, `proposed_format_label`, `status`, `created_at`, and a stats summary with `avg_views`, `premium_ratio`, and `language_stats` (top language only). It SHALL source stats from the latest `channel_stats_snapshots` for each channel; `premium_ratio` is derived from `premium_stats.premium_ratio` (default `0.0` when missing), and `language_stats` is either `null` or a single-entry map of the highest-ratio language code to its ratio.

#### Scenario: Advertiser reviews applicants
- **WHEN** an advertiser lists applications for their campaign
- **THEN** the response includes applicant channel metadata and stats summary
