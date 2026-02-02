# marketplace-discovery Specification

## Purpose
TBD - created by archiving change add-marketplace-listings. Update Purpose after archive.
## Requirements
### Requirement: Marketplace browse endpoint
The system SHALL expose `GET /marketplace/listings` with optional authentication. It SHALL accept `min_price`, `max_price`, `min_subscribers`, `max_subscribers`, `min_avg_views`, `max_avg_views`, `language`, `min_premium_pct`, `search`, `page` (default 1), `page_size` (default 20), and `sort` (optional: `price`, `subscribers`). It SHALL return a list of listings with channel `username` and `title`, listing formats (`id`, `label`, `price`), and key stats (`subscribers`, `avg_views`, `premium_ratio`) along with pagination metadata. Invalid parameters SHALL return HTTP 400 with a clear error message.

#### Scenario: Browse listings default
- **WHEN** a request calls `/marketplace/listings` with no filters
- **THEN** the response is HTTP 200 and includes listings with required fields and pagination metadata

### Requirement: Marketplace listing eligibility and composition
The marketplace query SHALL include only listings where `listings.is_active = true` and `channels.is_verified = true`. It SHALL join listings with channels, listing formats, and the latest `channel_stats_snapshots` for each channel (by `created_at`, tie-breaker `id`).

#### Scenario: Inactive listing excluded
- **WHEN** a listing is inactive or its channel is unverified
- **THEN** it does not appear in marketplace results

### Requirement: Marketplace filtering and search semantics
Marketplace filters SHALL combine via logical AND. Price range filtering SHALL match listings if any format price falls within `[min_price, max_price]` (inclusive). Subscribers and average views filters SHALL apply inclusive min/max ranges. The `language` filter SHALL match only when `language_stats` contains the requested ISO 639-1 code with value >= 0.10. The `min_premium_pct` filter SHALL compare against `premium_stats.premium_ratio` (0–1 float), treating missing values as 0. The `search` filter SHALL perform case-insensitive partial matching on channel username or title and SHALL combine with all other filters.

#### Scenario: Search combines with filters
- **WHEN** a request includes `search` and `min_subscribers`
- **THEN** results match both the search term and the subscriber filter

### Requirement: Marketplace sorting and pagination
Marketplace pagination SHALL be stable and deterministic. By default, results SHALL order by listing `created_at` then `id`. When `sort=price`, results SHALL order by each listing's minimum format price (ascending) with a deterministic tie-breaker. When `sort=subscribers`, results SHALL order by subscriber count (descending) with a deterministic tie-breaker.

#### Scenario: Stable ordering
- **WHEN** the same query is executed repeatedly
- **THEN** the result ordering is consistent across pages
