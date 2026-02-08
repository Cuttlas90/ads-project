## MODIFIED Requirements

### Requirement: Campaign request persistence
The system SHALL persist campaign requests in a `campaign_requests` table with fields `id`, `advertiser_id` (FK to `users.id`), `title` (required), `brief` (required), `budget_usdt` (nullable decimal), `budget_ton` (nullable decimal), `preferred_language` (nullable), `start_at` (nullable timestamp), `end_at` (nullable timestamp), `min_subscribers` (nullable int), `min_avg_views` (nullable int), `lifecycle_state` (required enum: `active`, `hidden`, `closed_by_limit`), `max_acceptances` (required int, default `10`, minimum `1`), `hidden_at` (nullable timestamp), `is_active` (legacy compatibility flag), `created_at`, and `updated_at`. The system SHALL index `advertiser_id` and SHALL support filtering by lifecycle state for backend queries. Budget fields SHALL be display-only and SHALL NOT enforce payment or escrow behavior.

#### Scenario: Campaign request stored with defaults
- **WHEN** an authenticated user creates a campaign request with `title` and `brief`
- **THEN** the request is stored with `advertiser_id` set to that user, `lifecycle_state = active`, and `max_acceptances = 10`

#### Scenario: Hidden campaign marks compatibility flag
- **WHEN** a campaign lifecycle transitions to `hidden` or `closed_by_limit`
- **THEN** `is_active` is set to `false` for compatibility with legacy inactive checks

### Requirement: Create campaign request endpoint
The system SHALL expose `POST /campaigns` requiring authentication. It SHALL accept `title` and `brief` plus optional `budget_usdt`, `budget_ton`, `preferred_language`, `start_at`, `end_at`, `min_subscribers`, `min_avg_views`, and `max_acceptances`. It SHALL set `advertiser_id` to the authenticated user, validate non-empty `title`/`brief`, validate budgets are `>= 0` when provided, validate `end_at > start_at` when both are provided, and validate `max_acceptances >= 1` when provided. It SHALL default `max_acceptances` to `10` and initialize `lifecycle_state = active`. It SHALL return HTTP 201 with the created campaign request. It SHALL return HTTP 400 for validation errors.

#### Scenario: Invalid max_acceptances rejected
- **WHEN** a request provides `max_acceptances = 0`
- **THEN** the response is HTTP 400

#### Scenario: Invalid date range rejected
- **WHEN** a request provides `start_at` and `end_at` where `end_at <= start_at`
- **THEN** the response is HTTP 400

### Requirement: List campaign requests endpoint
The system SHALL expose `GET /campaigns` requiring authentication. It SHALL return only campaigns where `advertiser_id` matches the authenticated user. It SHALL exclude campaigns with `lifecycle_state = hidden` from the default response. It SHALL support `page` and `page_size` query parameters (positive integers) and return a paginated response with `page`, `page_size`, `total`, and `items` containing campaign request data.

#### Scenario: Hidden campaigns excluded from list
- **WHEN** a user requests `GET /campaigns` after soft-hiding one of their campaigns
- **THEN** the hidden campaign is not included in `items` and not counted in `total`

### Requirement: View campaign request endpoint
The system SHALL expose `GET /campaigns/{id}` requiring authentication. It SHALL return the campaign request when the authenticated user is the `advertiser_id` and the campaign is not hidden. It SHALL return HTTP 403 when the user does not own the campaign and HTTP 404 when the campaign does not exist or is hidden.

#### Scenario: Hidden campaign read returns not found
- **WHEN** the advertiser requests a campaign that is soft-hidden
- **THEN** the response is HTTP 404

## ADDED Requirements

### Requirement: Soft-hide campaign delete endpoint
The system SHALL expose `DELETE /campaigns/{id}` requiring authentication. It SHALL allow only the campaign advertiser to invoke it. Instead of physical deletion, it SHALL soft-hide the campaign by setting `lifecycle_state = hidden`, setting `hidden_at` to the current timestamp, and setting `is_active = false`. Repeated delete requests for the same already-hidden campaign SHALL be idempotent and SHALL return HTTP 204.

#### Scenario: Advertiser soft-hides campaign
- **WHEN** the advertiser calls `DELETE /campaigns/{id}` on an active campaign
- **THEN** the response is HTTP 204 and the campaign lifecycle becomes `hidden`

#### Scenario: Delete is idempotent
- **WHEN** the advertiser calls `DELETE /campaigns/{id}` on a campaign already in `hidden`
- **THEN** the response is HTTP 204 and no duplicate side effects are produced
