## Why

Deal timing and campaign-offer terms are inconsistent across flows. Advertisers cannot set a negotiable start date/time when creating deals, and campaign acceptance currently duplicates pricing/ad-type inputs that should be defined earlier in campaign/application steps.

## What Changes

- Add negotiable deal start datetime (`start_at`) to both listing-driven and campaign-driven deal initiation/negotiation flows.
- Persist agreed start datetime as deal `scheduled_at` so posting automation can use a finalized schedule.
- Update listing-driven start-deal UI and API payloads to capture creative + start datetime together.
- Extend campaign-owner apply payload with structured terms (`placement_type`, `exclusive_hours`, `retention_hours`) so acceptance no longer depends on free-text only.
- Update advertiser offer-accept flow to stop requiring manual `ad_type` and to use application-provided placement terms; remove duplicate manual term entry from accept UI.
- Update campaign acceptance handling so deal term derivation is consistent with campaign/apply stages and supports scheduled posting from finalized start time.
- Expand draft negotiation rules to allow start time negotiation alongside creative fields.

## Capabilities

### New Capabilities
- None.

### Modified Capabilities
- `deal-management`: Add negotiable deal start datetime in create/update flows and align campaign acceptance term derivation.
- `campaign-applications`: Require structured placement/exclusive/retention terms on apply and expose them in offer/list payloads.
- `campaign-requests`: Clarify campaign-level numeric term usage for campaign-driven acceptance inputs.
- `m11-ui-support`: Update listing start-deal, owner apply, and advertiser accept UIs to support new term and timing flow without duplicated inputs.

## Impact

- Backend APIs: `/listings/{id}/deals`, `/campaigns/{id}/apply`, `/campaigns/{id}/applications/{id}/accept`, and deal draft update behavior.
- Data model and migrations: campaign application term fields and deal scheduling field usage in negotiation/acceptance.
- Frontend flows: Marketplace start-deal modal, owner campaigns apply form, advertiser offers accept modal.
- Tests: backend API tests for create/apply/accept/update, frontend view/store tests for modified forms and payloads.
