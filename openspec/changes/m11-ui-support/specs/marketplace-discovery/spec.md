## MODIFIED Requirements

### Requirement: Marketplace browse endpoint
The system SHALL expose `GET /marketplace/listings` with optional authentication. It SHALL accept `min_price`, `max_price`, `min_subscribers`, `max_subscribers`, `min_avg_views`, `max_avg_views`, `language`, `min_premium_pct`, `search`, `page` (default 1), `page_size` (default 20), and `sort` (optional: `price`, `subscribers`). It SHALL return a list of listings with channel `username` and `title`, listing formats (`id`, `label`, `price`), and key stats (`subscribers`, `avg_views`, `premium_ratio`) along with pagination metadata. Invalid parameters SHALL return HTTP 400 with a clear error message.

#### Scenario: Browse listings default
- **WHEN** a request calls `/marketplace/listings` with no filters
- **THEN** the response is HTTP 200 and includes listings with required fields and pagination metadata
