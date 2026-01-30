## Context
The marketplace needs a second entry point for advertisers to publish campaign briefs and for channel owners to apply. This change introduces two new data models and APIs without altering the deal/escrow flow yet.

## Goals / Non-Goals
- Goals:
  - Persist campaign requests authored by authenticated users.
  - Allow channel owners to apply with a verified channel and proposed format label.
  - Let advertisers view applicants with basic channel stats in a single call.
- Non-Goals:
  - Deals, escrow, posting, or creative approval workflows.
  - Any new Telegram API calls beyond existing verification flows.

## Decisions
- Data model
  - `campaign_requests` stores advertiser briefs with optional display-only budgets and availability dates.
  - `campaign_applications` stores one application per (campaign, channel), with status defaulting to `submitted`.
- Authorization
  - Any authenticated user may create and manage their own campaign requests.
  - Only the channel owner (via `channel_members.role = owner`) may apply on behalf of a channel.
  - Campaign application listing is restricted to the campaign's advertiser.
- Eligibility gates
  - Applications are accepted only when `campaign_requests.is_active = true` and the channel is verified (`channels.is_verified = true`).
- Stats summary shape
  - Application listings include the latest `channel_stats_snapshots` data, returning `avg_views`, `premium_ratio` (from `premium_stats.premium_ratio`), and `language_stats` reduced to a single top-language entry `{<code>: <ratio>}`. Missing or malformed stats resolve to `null` (language) and `0.0` (premium ratio).
- Pagination
  - Campaign lists and application lists use the `page`, `page_size`, `total`, `items` shape for UI-friendly pagination.

## Risks / Trade-offs
- Stats may be stale because they rely on the latest stored snapshot, but this is acceptable for MVP.
- Joining stats for each application adds query complexity; acceptable given current scale.

## Migration Plan
- Add Alembic migrations for `campaign_requests` and `campaign_applications` with required indexes and constraints.

## Open Questions
- None.
