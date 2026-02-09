# campaign-requests Specification

## Purpose
TBD - created by archiving change add-campaign-requests. Update Purpose after archive.
## Requirements
### Requirement: Campaign request persistence
The system SHALL persist campaign requests in a `campaign_requests` table with fields `id`, `advertiser_id` (FK to `users.id`), `title` (required), `brief` (required), `budget_usdt` (nullable decimal), `budget_ton` (nullable decimal), `preferred_language` (nullable), `start_at` (nullable timestamp), `end_at` (nullable timestamp), `min_subscribers` (nullable int), `min_avg_views` (nullable int), `lifecycle_state` (required enum: `active`, `hidden`, `closed_by_limit`), `max_acceptances` (required int, default `10`, minimum `1`), `hidden_at` (nullable timestamp), `is_active` (legacy compatibility flag), `created_at`, and `updated_at`. It SHALL index `advertiser_id` and SHALL support filtering by lifecycle state for backend queries.

For campaign-driven deal acceptance, when explicit deal `price_ton` is omitted in acceptance payload, the system SHALL treat campaign `budget_ton` as the default accepted deal price source.

#### Scenario: Campaign budget can default accepted deal price
- **WHEN** an advertiser accepts a campaign application without sending `price_ton`
- **THEN** campaign `budget_ton` is used as the deal price source

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

#### Scenario: List returns only caller campaigns
- **WHEN** a user requests `GET /campaigns`
- **THEN** the response includes only their campaigns

#### Scenario: Hidden campaigns excluded from list
- **WHEN** a user requests `GET /campaigns`
- **THEN** the response excludes hidden campaigns from `items` and `total`

### Requirement: View campaign request endpoint
The system SHALL expose `GET /campaigns/{id}` requiring authentication. It SHALL return the campaign request when the authenticated user is the `advertiser_id` and the campaign is not hidden. It SHALL return HTTP 403 when the user does not own the campaign and HTTP 404 when the campaign does not exist or is hidden.

#### Scenario: Non-owner denied
- **WHEN** a user requests a campaign they do not own
- **THEN** the response is HTTP 403

#### Scenario: Hidden campaign read returns not found
- **WHEN** the advertiser requests a campaign that is soft-hidden
- **THEN** the response is HTTP 404

### Requirement: Soft-hide campaign delete endpoint
The system SHALL expose `DELETE /campaigns/{id}` requiring authentication. It SHALL allow only the campaign advertiser to invoke it. Instead of physical deletion, it SHALL soft-hide the campaign by setting `lifecycle_state = hidden`, setting `hidden_at` to the current timestamp, and setting `is_active = false`. Repeated delete requests for the same already-hidden campaign SHALL be idempotent and SHALL return HTTP 204.

#### Scenario: Advertiser soft-hides campaign
- **WHEN** the advertiser calls `DELETE /campaigns/{id}` on an active campaign
- **THEN** the response is HTTP 204 and the campaign lifecycle becomes `hidden`

#### Scenario: Delete is idempotent
- **WHEN** the advertiser calls `DELETE /campaigns/{id}` on a campaign already in `hidden`
- **THEN** the response is HTTP 204 and no duplicate side effects are produced

### Requirement: Owner campaign discovery endpoint
The system SHALL expose `GET /campaigns/discover` requiring authentication. It SHALL return campaigns discoverable by channel owners and SHALL include only campaigns with lifecycle state `active`. Campaigns in `hidden` or `closed_by_limit` SHALL NOT be returned. The endpoint SHALL support `page` and `page_size` query parameters plus optional basic `search` text filtering on campaign title/brief, and return a paginated response with `page`, `page_size`, `total`, and `items`.

#### Scenario: Owner sees only active campaigns
- **WHEN** an owner calls `GET /campaigns/discover`
- **THEN** the response includes only campaigns in lifecycle `active`

#### Scenario: Owner uses basic search
- **WHEN** an owner calls `GET /campaigns/discover` with a `search` query
- **THEN** only active campaigns matching the title/brief search criteria are returned

### Requirement: Owner campaign discovery payload
Each `GET /campaigns/discover` item SHALL include fields required to evaluate and apply: `id`, `advertiser_id`, `title`, `brief`, `budget_ton`, `preferred_language`, `min_subscribers`, `min_avg_views`, `max_acceptances`, `created_at`, and `updated_at`.

#### Scenario: Owner receives campaign screening context
- **WHEN** an owner loads campaign discovery results
- **THEN** each campaign item contains screening and budget fields needed before applying

