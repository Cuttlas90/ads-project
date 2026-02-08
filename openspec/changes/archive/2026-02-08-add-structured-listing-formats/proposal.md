## Why

Listing formats are currently free-form labels plus price, so owners can type anything and advertisers cannot reliably compare or filter inventory by placement type and delivery guarantees. We need structured ad format terms now to support trustworthy marketplace matching and deterministic automation for posting and post-lifecycle enforcement.

## What Changes

- Replace free-form listing format terms with structured fields: `placement_type` (`post` or `story`), `exclusive_hours`, `retention_hours`, and `price_ton`.
- Require each listing to have at least one structured format (`post` or `story`) before activation/marketplace eligibility.
- **BREAKING**: Update listing format create/update/read contracts and marketplace response shape to use structured fields instead of relying on arbitrary label text.
- Lock listing-derived delivery terms into deals created from listings so later negotiation cannot silently change exclusivity/retention commitments.
- Extend automated posting/verification lifecycle to enforce the new format terms, including story publish handling and retention/exclusivity checks in workers.

## Capabilities

### New Capabilities
- None.

### Modified Capabilities
- `listing-management`: Change listing format persistence and owner APIs from free-form labels to structured placement and timing terms, including listing-level readiness constraints.
- `marketplace-discovery`: Return and filter marketplace inventory by structured placement/timing fields instead of label-only semantics.
- `deal-management`: Persist and lock listing-derived format terms on listing-sourced deals as contractual posting parameters.
- `deal-posting`: Add publish behavior selection based on structured placement type, including story placement support.
- `deal-verification`: Add verification and lifecycle enforcement semantics for exclusivity and retention windows.
- `m11-ui-support`: Update owner listing editor and advertiser marketplace/deal entry expectations to use structured format fields.

## Impact

- Affected specs: `listing-management`, `marketplace-discovery`, `deal-management`, `deal-posting`, `deal-verification`, `m11-ui-support`.
- Affected APIs: `/listings/{id}/formats`, `/channels/{channel_id}/listing`, `/marketplace/listings`, listing-sourced deal creation/representation paths.
- Affected code:
  - Backend: listing/listing_format models and migration, listing/marketplace/deal schemas and routes, repository filtering/sorting logic.
  - Workers/services: posting and verification workers plus Telegram publishing helpers for story-aware behavior and retention/exclusivity checks.
  - Frontend: owner listing editor and marketplace format display/filter inputs.
- Dependencies/systems: Telegram Bot API publishing for both post/story placements, Telethon inspection paths used by verification, Celery scheduled jobs for lifecycle checks.
