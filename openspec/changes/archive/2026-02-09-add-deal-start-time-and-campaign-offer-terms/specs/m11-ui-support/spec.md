## MODIFIED Requirements

### Requirement: Start deal flow uses upload-first creative capture
The marketplace Start deal UI SHALL require creative media upload before submitting deal creation. It SHALL provide a multiline creative text input, an explicit media type selector (`image` or `video`), a media file picker, and a start datetime input (`start_at`). It SHALL NOT require manual entry of Telegram `file_id`. On successful upload, it SHALL use returned `creative_media_ref` and `creative_media_type` in the subsequent `POST /listings/{listing_id}/deals` request and include selected `start_at` when provided.

#### Scenario: Listing start deal sends start datetime
- **WHEN** a user uploads media, enters creative text, and selects start datetime in Start deal modal
- **THEN** the UI submits `start_at` with creative fields in `POST /listings/{listing_id}/deals`

### Requirement: Owner campaigns page and apply channel selection
The UI SHALL provide an owner campaigns page that lists discoverable active campaigns. Applying to a campaign SHALL require selecting one channel from the authenticated user's owned verified channels and SHALL capture structured proposal terms: `placement_type`, `exclusive_hours`, and `retention_hours`. If no owned verified channels exist, the UI SHALL block submission and show guidance to verify a channel first.

#### Scenario: Owner apply submits structured terms
- **WHEN** an owner applies to a campaign
- **THEN** the UI submits selected channel plus structured placement/exclusive/retention terms

### Requirement: Advertiser aggregated offers inbox page
The UI SHALL provide one advertiser offers page that lists offers across all advertiser campaigns in newest-first order. Each row SHALL expose campaign and proposal context and an action to accept the offer by submitting required creative fields and optional start datetime. The accept UI SHALL NOT require manual `ad_type` input and SHALL NOT require manual `price_ton` input when campaign defaults are available.

#### Scenario: Advertiser accepts offer without duplicate term fields
- **WHEN** advertiser accepts an offer from the aggregated inbox
- **THEN** the accept payload includes creative fields and optional `start_at` without requiring manual ad type or price entry
