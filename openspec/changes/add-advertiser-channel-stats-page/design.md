## Context

The current marketplace view exposes only summary stats (`subscribers`, `avg_views`, `premium_ratio`) and does not provide a deep channel analytics view for advertisers. The backend already persists `raw_stats` snapshots during channel verification, including Telegram `stats.broadcastStats` payloads, and now also stores boosts status data used for premium audience derivation.  

For full parity, the stats page must support mixed Telegram metric types:
- scalar metrics (for example `StatsAbsValueAndPrev`, `StatsPercentValue`)
- ready chart payloads (`StatsGraph`)
- async-token chart payloads (`StatsGraphAsync`)
- explicit unavailable/error states (`StatsGraphError`, missing fields)

This change spans backend contracts, frontend routing/navigation, and telemetry normalization.

## Goals / Non-Goals

**Goals:**
- Provide a channel stats page linked from marketplace channel names/titles and shared read-only with owners.
- Serve a typed, normalized stats contract from backend snapshots for reliable frontend rendering.
- Support full metric parity behavior by representing Telegram async/error graph states explicitly.
- Preserve graceful UX when metrics/charts are unavailable (placeholder or section hide).
- Include premium audience metrics based on boosts status when broadcast premium graph is absent.

**Non-Goals:**
- Recreate Telegram pixel-perfect visual styling in this phase.
- Build live real-time polling identical to Telegram’s native app behavior.
- Add new authentication modes (Telegram initData remains the only auth).
- Introduce mandatory database schema changes for the initial rollout.

## Decisions

### 1. Marketplace-to-stats navigation uses `channel_id` as stable key
**Decision:** Extend marketplace listing response to include `channel_id`, and route advertiser clicks to `/advertiser/channels/:channelId/stats`.

**Rationale:** `channel_id` is the canonical identity for joining snapshots, listings, and channel metadata. It avoids ambiguity and extra lookups from `listing_id` to channel.

**Alternatives considered:**
- Use `listing_id` in route and resolve server-side each request.
  - Rejected: adds indirection and couples stats navigation to listing lifecycle.

### 2. Stats page reads from persisted snapshots, not direct Telegram calls
**Decision:** Introduce a backend read endpoint that serves the latest persisted snapshot for a channel and a normalized response model for the UI. The endpoint is shared for advertisers and owners as read-only access.

**Rationale:** Snapshot-backed reads keep page latency deterministic, avoid per-view Telethon dependency, and maintain a single audited source of truth.

**Alternatives considered:**
- Call Telegram directly from the stats endpoint for each page load.
  - Rejected: high latency/failure exposure and higher Telegram rate-limit risk.

### 3. Normalize metrics into explicit availability states
**Decision:** Backend response includes section-level and metric-level availability states (for example `ready`, `missing`, `error`, `async_pending`) plus normalized values when present.

**Rationale:** Frontend can implement deterministic rendering behavior without parsing Telegram TL internals.

**Alternatives considered:**
- Return raw Telegram JSON only and parse in frontend.
  - Rejected: fragile, duplicates parsing logic, and couples UI to Telegram schema volatility.

### 4. Async graph parity handled via token-aware representation
**Decision:** For `StatsGraphAsync`, preserve token metadata in stored raw data and expose them as `async_pending` in normalized API unless resolved payload is present. The design allows progressive enhancement to resolve tokens (for example verification-time or controlled refresh flow) without breaking the API contract.

**Rationale:** Tokens are part of Telegram’s native stats model and may be unavailable/expired. Explicit status is safer than pretending data exists.

**Alternatives considered:**
- Force immediate token resolution on every read request.
  - Rejected: couples page load to Telegram availability and increases request-time failure.

### 5. Premium ratio source preference is deterministic
**Decision:** Premium ratio derivation order is:
1. `statistics.premium_graph` if present and parseable
2. `boosts_status.premium_audience.part/total` if present and valid
3. unavailable (or `0.0` only where existing downstream compatibility requires it)

**Rationale:** This reflects actual Telegram payload behavior observed in production channels where premium graph is absent but boosts premium audience exists.

**Alternatives considered:**
- Treat missing premium graph as always `0.0`.
  - Rejected: incorrect for channels with premium audience available through boosts.

### 6. Missing-data UX policy is explicit and non-blocking
**Decision:** Page sections render according to availability:
- `ready`: render value/chart
- `async_pending`/`missing`: hide chart sections by default; render non-blocking placeholder for scalar/value-only metrics
- `error`: placeholder with brief reason (for example “Not enough data”)

**Rationale:** Advertiser should still get value from partial data and never face a blank/broken page.

### 7. Refresh policy remains verification-cadence-only in this change
**Decision:** This change adds no explicit “refresh stats now” user action and no dedicated backend async-graph refresh mechanism. Stats freshness relies on existing channel verification cadence.

**Rationale:** Keeps scope focused on parity read-model and navigation while avoiding operational complexity from ad-hoc refresh flows.

## Risks / Trade-offs

- **[Risk] Async graph tokens expire before resolution** -> **Mitigation:** represent token-based metrics as `async_pending` and keep UI fallback behavior deterministic.
- **[Risk] Large raw payloads increase API response size** -> **Mitigation:** serve normalized contract; do not expose full raw JSON to frontend by default.
- **[Risk] Metric semantics drift as Telegram types evolve** -> **Mitigation:** centralize normalization/parsing in backend and add focused tests for marker types.
- **[Risk] Marketplace contract change impacts existing clients** -> **Mitigation:** additive response change (`channel_id`) with backward-compatible fields.
- **[Trade-off] Snapshot-backed reads can be stale** -> **Mitigation:** retain re-verification flow and show snapshot timestamp in stats response.

## Migration Plan

1. Finalize spec deltas for `advertiser-channel-stats`, `marketplace-discovery`, `m11-ui-support`, and `channel-verification`.
2. Implement backend additive contracts:
- marketplace response adds `channel_id`
- stats read endpoint and normalized serializer
- premium derivation consistency checks
3. Implement frontend navigation and stats page route for advertiser role.
4. Implement placeholder/hide behavior for missing or unavailable metrics/charts.
5. Validate with channels that contain mixed marker types (`StatsGraph`, `StatsGraphAsync`, `StatsGraphError`) and boosts premium audience.
6. Rollout with no required DB migration; rollback by disabling new route/page and retaining existing marketplace behavior.

## Resolved Product Decisions

- Stats endpoint is shared with owners as a read-only route.
- Unavailable chart sections default to hidden.
- Stats freshness relies on existing verification refresh cadence.
- No dedicated refresh mechanism is added in this change.
