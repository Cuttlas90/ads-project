# campaign-requests Specification

## ADDED Requirements
### Requirement: Campaign request persistence
The system SHALL persist campaign requests in a `campaign_requests` table with fields `id`, `advertiser_id` (FK to `users.id`), `title` (required), `brief` (required), `budget_usdt` (nullable decimal), `budget_ton` (nullable decimal), `preferred_language` (nullable), `start_at` (nullable timestamp), `end_at` (nullable timestamp), `min_subscribers` (nullable int), `min_avg_views` (nullable int), `is_active` (default true), `created_at`, and `updated_at`. It SHALL index `advertiser_id` and MAY index `is_active`. Budget fields SHALL be display-only and SHALL NOT enforce payment or escrow behavior.

#### Scenario: Campaign request stored
- **WHEN** an authenticated user creates a campaign request with `title` and `brief`
- **THEN** the request is stored with `advertiser_id` set to that user and `is_active = true`

### Requirement: Create campaign request endpoint
The system SHALL expose `POST /campaigns` requiring authentication. It SHALL accept `title` and `brief` plus optional `budget_usdt`, `budget_ton`, `preferred_language`, `start_at`, `end_at`, `min_subscribers`, and `min_avg_views`. It SHALL set `advertiser_id` to the authenticated user, validate non-empty `title`/`brief`, validate budgets are `>= 0` when provided, and validate `end_at > start_at` when both are provided. It SHALL return HTTP 201 with the created campaign request. It SHALL return HTTP 400 for validation errors.

#### Scenario: Invalid date range rejected
- **WHEN** a request provides `start_at` and `end_at` where `end_at <= start_at`
- **THEN** the response is HTTP 400

### Requirement: List campaign requests endpoint
The system SHALL expose `GET /campaigns` requiring authentication. It SHALL return only campaigns where `advertiser_id` matches the authenticated user. It SHALL support `page` and `page_size` query parameters (positive integers) and return a paginated response with `page`, `page_size`, `total`, and `items` containing campaign request data.

#### Scenario: List returns only caller campaigns
- **WHEN** a user requests `GET /campaigns`
- **THEN** the response includes only their campaigns and includes `total`

### Requirement: View campaign request endpoint
The system SHALL expose `GET /campaigns/{id}` requiring authentication. It SHALL return the campaign request when the authenticated user is the `advertiser_id`. It SHALL return HTTP 403 when the user does not own the campaign and HTTP 404 when the campaign does not exist.

#### Scenario: Non-owner denied
- **WHEN** a user requests a campaign they do not own
- **THEN** the response is HTTP 403
