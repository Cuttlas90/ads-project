## ADDED Requirements

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
