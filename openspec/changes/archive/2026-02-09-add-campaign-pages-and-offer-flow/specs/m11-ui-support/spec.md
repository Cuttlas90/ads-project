## ADDED Requirements

### Requirement: Advertiser campaign workspace page
The UI SHALL render advertiser campaign creation and advertiser campaign list on the same screen. The campaign list SHALL be shown below the create form and SHALL provide per-campaign actions to open offers and delete campaign.

#### Scenario: Advertiser sees created campaign under form
- **WHEN** an advertiser successfully creates a campaign
- **THEN** the campaign appears in the workspace list below the create form without navigating to another page

### Requirement: Owner campaigns page and apply channel selection
The UI SHALL provide an owner campaigns page that lists discoverable active campaigns. Applying to a campaign SHALL require selecting one channel from the authenticated user's owned verified channels. If no owned verified channels exist, the UI SHALL block submission and show guidance to verify a channel first.

#### Scenario: Owner apply uses verified channel picker
- **WHEN** an owner applies to a campaign
- **THEN** the apply action submits a selected owned verified `channel_id`

### Requirement: Advertiser aggregated offers inbox page
The UI SHALL provide one advertiser offers page that lists offers across all advertiser campaigns in newest-first order. Each row SHALL expose campaign context and an action to accept the offer by submitting required deal fields (`price_ton`, `ad_type`, `creative_text`, `creative_media_type`, `creative_media_ref`).

#### Scenario: Advertiser reviews newest offers first
- **WHEN** an advertiser opens offers page
- **THEN** offers are presented in newest-first order with accept action available per row

### Requirement: Post-accept redirect to deal detail
After successful offer acceptance, the UI SHALL navigate immediately to `/deals/:id` using the created deal id from accept response.

#### Scenario: Accept opens deal detail immediately
- **WHEN** advertiser accepts an offer successfully
- **THEN** the app redirects to `/deals/{created_deal_id}` in the same interaction flow

### Requirement: Delete campaign label and hidden semantics copy
The campaign action label SHALL be `Delete campaign`. The confirmation or helper copy SHALL explicitly state that campaign and related offers are removed from campaign pages, while existing accepted deals remain available in deal history/detail.

#### Scenario: Delete copy clarifies soft-hide behavior
- **WHEN** advertiser triggers campaign delete
- **THEN** UI copy explains hidden semantics before confirmation while keeping button label as `Delete campaign`
