## MODIFIED Requirements

### Requirement: Campaign request persistence
The system SHALL persist campaign requests in a `campaign_requests` table with fields `id`, `advertiser_id` (FK to `users.id`), `title` (required), `brief` (required), `budget_usdt` (nullable decimal), `budget_ton` (nullable decimal), `preferred_language` (nullable), `start_at` (nullable timestamp), `end_at` (nullable timestamp), `min_subscribers` (nullable int), `min_avg_views` (nullable int), `lifecycle_state` (required enum: `active`, `hidden`, `closed_by_limit`), `max_acceptances` (required int, default `10`, minimum `1`), `hidden_at` (nullable timestamp), `is_active` (legacy compatibility flag), `created_at`, and `updated_at`. It SHALL index `advertiser_id` and SHALL support filtering by lifecycle state for backend queries.

For campaign-driven deal acceptance, when explicit deal `price_ton` is omitted in acceptance payload, the system SHALL treat campaign `budget_ton` as the default accepted deal price source.

#### Scenario: Campaign budget can default accepted deal price
- **WHEN** an advertiser accepts a campaign application without sending `price_ton`
- **THEN** campaign `budget_ton` is used as the deal price source
