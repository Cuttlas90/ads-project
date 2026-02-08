## 1. Backend Contracts

- [x] 1.1 Extend `GET /marketplace/listings` response models and query mapping to include `channel_id` per listing item.
- [x] 1.2 Add typed schemas for `GET /channels/{channel_id}/stats` covering channel identity, snapshot metadata, and normalized metric/chart sections.
- [x] 1.3 Add read-only `GET /channels/{channel_id}/stats` route with role-aware access rules (advertiser marketplace-eligible channels, owner/manager-owned channels).

## 2. Stats Read Model & Normalization

- [x] 2.1 Implement latest-snapshot selection logic (`created_at` then `id`) for stats reads.
- [x] 2.2 Implement normalization of Telegram chart markers to availability states (`ready`, `missing`, `error`, `async_pending`) with token/reason passthrough.
- [x] 2.3 Implement premium metric precedence in stats reads: `statistics.premium_graph` first, then `boosts_status.premium_audience.part/total`.
- [x] 2.4 Ensure stats endpoint is snapshot-backed only and does not trigger request-time Telegram refresh calls.

## 3. Verification Enrichment Alignment

- [x] 3.1 Ensure verification snapshots persist `raw_stats.boosts_status` when `premium.getBoostsStatus` succeeds.
- [x] 3.2 Ensure boosts fetch failures remain non-blocking for successful verification and snapshot persistence.
- [x] 3.3 Ensure `premium_stats` payload includes `premium_ratio` and `premium_audience` when derivable from boosts fallback.

## 4. Frontend Routing & Navigation

- [x] 4.1 Add role-scoped stats routes: `/advertiser/channels/:channelId/stats` and `/owner/channels/:channelId/stats`.
- [x] 4.2 Enforce route-guard behavior for cross-role deep links (owner hitting advertiser route redirects to `/owner`, advertiser hitting owner route redirects to `/advertiser/marketplace`).
- [x] 4.3 Update marketplace listing cards so tapping channel name/title navigates to advertiser stats route using `channel_id`.

## 5. Stats Page UI Behavior

- [x] 5.1 Build shared channel stats page layout for advertiser and owner contexts using the normalized backend contract.
- [x] 5.2 Render available metrics/charts normally and hide unavailable chart sections by default.
- [x] 5.3 Render non-blocking placeholders for unavailable scalar/value metrics and keep page usable with partial data.
- [x] 5.4 Show snapshot capture timestamp and indicate read-only context where appropriate.

## 6. Frontend Data Integration

- [x] 6.1 Add frontend API client method for `GET /channels/{channel_id}/stats`.
- [x] 6.2 Add store/composable state handling for loading, success, partial data, and error states on stats pages.
- [x] 6.3 Map normalized availability payloads into chart/value components without parsing raw Telegram TL objects in UI code.

## 7. Backend Test Coverage

- [x] 7.1 Add/extend marketplace endpoint tests to assert `channel_id` is present in listing items.
- [x] 7.2 Add stats endpoint authorization tests for advertiser access, owner/manager read-only access, and disallowed access paths.
- [x] 7.3 Add stats normalization tests for `StatsGraph`, `StatsGraphAsync`, `StatsGraphError`, and missing metrics.
- [x] 7.4 Add premium metric tests to assert precedence and fallback from boosts `premium_audience`.
- [x] 7.5 Add regression test ensuring stats reads do not perform request-time Telegram calls.

## 8. Frontend Test Coverage & Validation

- [x] 8.1 Add route/navigation tests for channel-title click-through and role-guard redirects on stats routes.
- [x] 8.2 Add UI rendering tests verifying unavailable chart sections are hidden and unavailable scalar metrics show placeholders.
- [x] 8.3 Run targeted backend and frontend tests for marketplace, channel verification/stats, and stats page routing/rendering.
- [x] 8.4 Run OpenSpec validation for `add-advertiser-channel-stats-page` after task/spec updates.
