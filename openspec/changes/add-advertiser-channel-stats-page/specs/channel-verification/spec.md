## MODIFIED Requirements

### Requirement: Telegram stats fetching and raw payload storage
On successful permission checks, the system SHALL perform a Telethon preflight before channel stats RPC calls. The preflight MUST include a successful Telethon transport connection and an authorized Telethon session check. Only after preflight success SHALL the system fetch Telegram channel data using `channels.getFullChannel`, `stats.getBroadcastStats`, and a best-effort `premium.getBoostsStatus` call. Verification SHALL attempt to populate `subscribers`, `avg_views`, `language_stats`, and `premium_stats` where available, and SHALL store a combined `raw_stats` JSON object that includes `full_channel`, `statistics`, and `boosts_status` payloads.

Premium ratio derivation in `premium_stats` SHALL prefer `statistics.premium_graph` when parseable, and SHALL fall back to `boosts_status.premium_audience.part/total` when premium graph data is absent. Failure of `premium.getBoostsStatus` SHALL NOT fail channel verification when other verification steps succeed.

#### Scenario: Boosts fallback derives premium ratio
- **WHEN** broadcast stats omit parseable premium graph data and boosts status contains premium audience counts
- **THEN** verification stores snapshot `premium_stats` with premium ratio derived from `part / total`

#### Scenario: Boosts fetch failure does not block verification
- **WHEN** `premium.getBoostsStatus` fails but channel info and broadcast stats are fetched successfully
- **THEN** verification still succeeds, marks the channel verified, and stores a snapshot with available stats

#### Scenario: Telethon preflight fails
- **WHEN** Telethon connection fails or the Telethon session is not authorized
- **THEN** verification stops before Telegram stats RPC calls and no new snapshot is stored
