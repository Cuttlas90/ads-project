## Why

Advertisers currently see only shallow channel metrics in marketplace cards, which is not enough to evaluate channel quality before starting a deal. We need a dedicated stats experience with Telegram-parity metrics so decision-making is based on full channel performance, not partial snapshots.

## What Changes

- Add an advertiser-accessible channel statistics page reachable by tapping the channel name/title from marketplace listings.
- Add backend stats-read capabilities for the latest channel snapshot, including normalized scalar metrics, chart payloads, and explicit data-availability states for each metric/chart.
- Resolve and expose Telegram async graph metrics needed for parity views (when available), while preserving graceful behavior when data is missing or Telegram reports insufficient data.
- Enrich premium audience metrics using Telegram boosts status (`premium.getBoostsStatus`) and persist derived premium ratio for downstream consumers.
- Extend marketplace listing payloads with stable channel identity fields needed for stats-page navigation.
- Define UI behavior for unavailable metrics/charts: hide optional sections or render placeholders without blocking the page.

## Capabilities

### New Capabilities
- `advertiser-channel-stats`: Advertiser channel analytics read model, API contract, and stats page UX for parity-focused metric exploration.

### Modified Capabilities
- `marketplace-discovery`: Marketplace listing response includes channel identity needed for click-through to channel stats.
- `m11-ui-support`: Advertiser marketplace allows channel-name navigation to stats; stats UI must handle unavailable metrics/charts with placeholders or hidden sections.
- `channel-verification`: Verification snapshots include premium audience enrichment from boosts status and persist related raw payloads for parity-driven reads.

## Impact

- Affected backend areas: channel verification service, channel/marketplace schemas, new stats endpoint and serializers, Telegram metric normalization logic.
- Affected frontend areas: marketplace card interaction, advertiser route map, new channel stats page, chart/placeholder rendering states.
- Affected APIs: `GET /marketplace/listings` response shape, plus new advertiser stats read endpoint(s).
- Telegram dependency surface expands for parity reads: broadcast stats, async graph loading, and boosts status.
- No required migration expected for initial rollout because enriched metrics can be stored in existing JSON snapshot fields.
