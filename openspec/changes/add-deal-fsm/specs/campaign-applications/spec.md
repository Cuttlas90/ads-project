## MODIFIED Requirements
### Requirement: Campaign application persistence
The system SHALL persist campaign applications in a `campaign_applications` table with fields `id`, `campaign_id` (FK to `campaign_requests.id`), `channel_id` (FK to `channels.id`), `owner_id` (FK to `users.id`), `proposed_format_label` (required), `message` (nullable), `status` (required, default `submitted`), and `created_at`. It SHALL enforce unique `(campaign_id, channel_id)` and SHALL index `campaign_id`, `owner_id`, and `channel_id`. Allowed `status` values are `submitted`, `withdrawn`, `accepted`, and `rejected`.

#### Scenario: Duplicate application prevented
- **WHEN** a second application is created for the same `campaign_id` and `channel_id`
- **THEN** the database constraint prevents the insert
