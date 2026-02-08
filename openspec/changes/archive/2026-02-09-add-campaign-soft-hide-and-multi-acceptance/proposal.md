## Why

Advertisers need to clean up campaign clutter without breaking historical deal data, and the current one-deal-per-campaign rule prevents scaling campaign-to-offer conversion. This change adds safe campaign hiding and controlled multi-acceptance so campaigns can convert multiple owner offers while preserving deal integrity.

## What Changes

- Add advertiser campaign soft-hide semantics: deleting a campaign marks it hidden (not physically removed) and removes it from normal campaign/offer listings.
- Cascade campaign soft-hide to related offers (applications) for campaign/offer pages, while accepted offers remain visible through deal detail and deal history.
- Add campaign lifecycle states to support clear visibility and conversion behavior: `active`, `hidden`, `closed_by_limit`.
- Add `max_acceptances` on campaigns (default `10`) and enforce it when accepting offers.
- Make campaign-offer acceptance transaction-safe so concurrent accepts cannot exceed `max_acceptances`.
- When acceptance limit is reached, block future accepts and auto-mark remaining submitted offers as closed/rejected.
- **BREAKING** Remove the one-deal-per-campaign restriction by dropping unique `deals.campaign_id`, enabling multiple deals from one campaign.
- Define inactive/hidden access behavior for campaign-offer operations (`404` or explicit inactive/hidden rejection) and apply consistently.

## Capabilities

### New Capabilities
- None.

### Modified Capabilities
- `campaign-requests`: Add soft-hide delete behavior, lifecycle state semantics (`active`, `hidden`, `closed_by_limit`), and `max_acceptances` default/validation.
- `campaign-applications`: Add offer soft-hide behavior tied to campaign hide, closed/rejected handling when campaign reaches acceptance limit, and hidden/inactive operation semantics.
- `deal-management`: Allow multiple campaign-sourced deals per campaign by removing unique `campaign_id`, while keeping accept flow safe under concurrent requests and `max_acceptances` enforcement.

## Impact

- Affected backend models: `CampaignRequest`, `CampaignApplication`, and `Deal`.
- Affected API routes: `/campaigns` delete/list/read semantics and `/campaigns/{campaign_id}/applications/{application_id}/accept` limit/concurrency behavior.
- Affected database: Alembic migration(s) for lifecycle/visibility and `max_acceptances` fields plus dropping `ux_deals_campaign_id`.
- Affected tests: campaign delete/hide behavior, offer visibility rules, acceptance limit behavior, and concurrent acceptance safety.
- Downstream UI impact: advertiser campaign pages and offer pages will rely on hidden/closed semantics and acceptance-limit states.
