## Context
Channel verification already persists snapshots with subscriber/view and language/premium JSON stats. This change introduces listing + format records and a marketplace browse API that joins verified channels, listings, and latest stats with deterministic filtering and sorting.

## Goals / Non-Goals
- Goals:
  - Allow owners to create a single listing per channel with multiple free-form formats and prices.
  - Provide a read-only marketplace endpoint with stable pagination, filters, and search.
  - Ensure marketplace visibility only for verified channels and active listings.
- Non-Goals:
  - Deals, escrow, payments, or negotiation flows.
  - Currency conversion or non-TON currencies.

## Decisions
- Data model:
  - `listings` stores `channel_id` (unique), `owner_id`, `is_active`, `created_at`, `updated_at`.
  - `listing_formats` stores `listing_id`, `label`, `price`, `created_at`, `updated_at` and enforces unique `(listing_id, label)`.
  - Cascade delete listing formats when a listing is deleted.
- Price storage:
  - Use a fixed-scale decimal (numeric with 2 decimal places) representing TON.
- Ownership rules:
  - Listing creation/update is restricted to channel owners only (role `owner`).
  - Managers are not permitted.
  - Ownership checks rely on database state only; no Telegram API calls.
- Latest stats selection:
  - Join to the latest `channel_stats_snapshots` by `created_at` (tie-breaker `id`).
- Filter semantics:
  - Price range matches listings if any format price falls within `[min_price, max_price]`.
  - `sort=price` uses the minimum format price as the primary sort key.
  - `min_avg_views`/`max_avg_views` and `min_subscribers`/`max_subscribers` apply as inclusive ranges.
  - `language` matches when `language_stats` contains the language key with value >= 0.10.
  - `min_premium_pct` compares against `premium_stats.premium_ratio` (missing treated as 0).
  - Search is partial and case-insensitive against channel username/title and combines with filters via AND.
- Pagination/sorting:
  - Default ordering is deterministic (listing `created_at`, then `id`).
  - Sorts are explicit and include a deterministic tie-breaker.
- JSON filtering compatibility:
  - Use SQLAlchemy/SQL functions for JSON extraction; implement SQLite-friendly `json_extract` for tests and PostgreSQL JSON operators in production.

## Risks / Trade-offs
- JSON filtering differs between SQLite and PostgreSQL; mitigated by explicit SQLAlchemy expressions and test coverage on SQLite.
- Decimal precision and serialization must be consistent across API responses and filters.

## Migration Plan
- Add new tables and constraints via Alembic migration.
- Deploy migration before enabling endpoints.

## Open Questions
- None.
