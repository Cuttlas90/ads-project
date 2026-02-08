## ADDED Requirements

### Requirement: Advertiser aggregated offers inbox endpoint
The system SHALL expose `GET /campaigns/offers` requiring authentication. It SHALL return offers (`campaign_applications`) for campaigns owned by the authenticated advertiser across all their campaigns in a single paginated response. It SHALL exclude offers with `hidden_at` set and offers whose campaigns are hidden.

#### Scenario: Advertiser sees one cross-campaign offer inbox
- **WHEN** an advertiser requests `GET /campaigns/offers`
- **THEN** the response includes offers from all campaigns owned by that advertiser, excluding hidden records

### Requirement: Aggregated offers sorting and payload
`GET /campaigns/offers` SHALL return items sorted by newest offer first (`created_at DESC`, deterministic tie-break by `id DESC`). Each item SHALL include `application_id`, `campaign_id`, `campaign_title`, `channel_id`, `channel_username`, `channel_title`, `owner_id`, `proposed_format_label`, `status`, and `created_at`.

#### Scenario: Offers inbox is newest-first
- **WHEN** an advertiser loads the aggregated offers inbox
- **THEN** offers are ordered by most recent `created_at` first

### Requirement: Multi-channel owner apply behavior
The system SHALL allow the same owner to apply to the same campaign using different owned verified channels. It SHALL continue enforcing uniqueness only for `(campaign_id, channel_id)` pairs.

#### Scenario: Owner applies from two owned verified channels
- **WHEN** an owner submits applications for one campaign using two distinct owned verified channels
- **THEN** both applications are accepted as long as each `(campaign_id, channel_id)` pair is unique
