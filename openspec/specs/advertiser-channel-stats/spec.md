# advertiser-channel-stats Specification

## Purpose
TBD - created by archiving change add-advertiser-channel-stats-page. Update Purpose after archive.
## Requirements
### Requirement: Advertiser channel stats endpoint
The system SHALL expose read-only `GET /channels/{channel_id}/stats` for authenticated users in advertiser or owner context. It SHALL return channel identity (`channel_id`, `channel_username`, `channel_title`), snapshot metadata (`captured_at`, `snapshot_available`), and normalized metric/chart sections. Advertiser access SHALL be allowed for marketplace-eligible channels. Owner access SHALL be allowed for channels where the caller is recorded as owner or manager. The endpoint SHALL return HTTP 404 when the channel does not exist.

#### Scenario: Advertiser opens stats from marketplace
- **WHEN** an authenticated advertiser requests `/channels/{channel_id}/stats` for a marketplace-eligible channel
- **THEN** the response is HTTP 200 and includes channel identity, snapshot metadata, and normalized stats sections

#### Scenario: Owner reads stats for owned channel
- **WHEN** an authenticated owner requests `/channels/{channel_id}/stats` for a channel they own or manage
- **THEN** the response is HTTP 200 and the endpoint remains read-only

### Requirement: Snapshot-backed stats reads
The stats endpoint SHALL read from persisted `channel_stats_snapshots` only and SHALL select the latest snapshot by `created_at` with `id` as deterministic tie-breaker. It MUST NOT call Telegram APIs during page-read requests. This change SHALL NOT add a dedicated backend refresh mechanism or a user-triggered refresh action for stats pages.

#### Scenario: Latest snapshot is selected deterministically
- **WHEN** multiple snapshots exist for the same channel
- **THEN** the endpoint returns metrics from the newest snapshot by `created_at` and tie-breaks by `id`

#### Scenario: No request-time refresh path
- **WHEN** a user opens the stats page
- **THEN** the endpoint returns persisted snapshot data without triggering Telegram refresh calls

### Requirement: Normalized availability contract
The stats response SHALL normalize Telegram-derived metrics and charts into explicit availability states: `ready`, `missing`, `error`, and `async_pending`. For `ready`, it SHALL include parsed values; for `error`, it SHALL include a short reason when available; for `async_pending`, it SHALL include token metadata if present.

#### Scenario: Missing metric remains explicit
- **WHEN** a metric is absent in the latest snapshot
- **THEN** the endpoint returns that metric with `availability = missing` instead of omitting the metric silently

### Requirement: Telegram graph marker parity
The stats normalization layer SHALL preserve marker semantics from Telegram payloads. It SHALL map `StatsGraph` to `ready`, `StatsGraphAsync` to `async_pending`, and `StatsGraphError` to `error` for each chart metric.

#### Scenario: Async graph token is represented
- **WHEN** a chart value in raw stats is `StatsGraphAsync`
- **THEN** the normalized response marks the chart as `async_pending` and includes the async token metadata when present

### Requirement: Premium audience parity from boosts
The stats contract SHALL expose premium audience metrics with deterministic precedence for ratio derivation: first `statistics.premium_graph`, then `boosts_status.premium_audience.part/total`. It SHALL include `premium_audience.part` and `premium_audience.total` when available from boosts status data.

#### Scenario: Premium ratio derived from boosts fallback
- **WHEN** `statistics.premium_graph` is unavailable and boosts status contains `premium_audience`
- **THEN** the endpoint returns premium ratio computed as `part / total` and includes the premium audience counts

