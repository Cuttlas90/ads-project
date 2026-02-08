## Why

Campaign creation and deal management exist, but there is no complete campaign-to-offer UX path between advertiser and owner roles. This creates a trust gap: campaigns can be created in backend logs, but users do not get a clear UI path from campaign creation to active deals.

## What Changes

- Extend advertiser campaign workspace so `Create campaign` and advertiser campaign list live on one screen, with campaign actions (`View offers`, `Delete campaign`).
- Add owner campaign discovery and application UX so owners can browse active campaigns and apply using a selected owned + verified channel.
- Add advertiser aggregated offers inbox (newest first) across all advertiser campaigns, with direct accept action.
- Keep accept flow as deal-creation boundary: advertiser accepts one offer, adds text/media, and system creates `DRAFT` deal.
- Redirect advertiser immediately to `/deals/:id` after successful accept to continue the shared deal workflow.
- Preserve soft-hide semantics: `Delete campaign` remains the UI label, while backend behavior remains hidden/not physically removed and related offers are hidden from campaign pages.

## Capabilities

### New Capabilities

- None.

### Modified Capabilities

- `campaign-requests`: Expand campaign listing semantics to support owner campaign discovery of active campaigns and advertiser campaign workspace actions.
- `campaign-applications`: Add aggregated advertiser offers inbox semantics, enforce newest-first ordering, and keep multi-channel owner apply behavior (unique per campaign+channel).
- `m11-ui-support`: Add role-specific campaign and offers pages, channel-selection apply UX, post-accept redirect to deal detail, and delete copy/confirmation semantics.

## Impact

- Frontend routes/views/navigation for advertiser campaign workspace, owner campaigns page, and advertiser offers inbox.
- Frontend API/service/store types for campaign discovery, aggregated offers listing, apply, accept, and delete actions.
- Backend campaign and campaign-application API surface for owner discovery and advertiser aggregated offers listing.
- E2E and view-level tests for role flows, sorting behavior, and post-accept redirect into deal detail.
