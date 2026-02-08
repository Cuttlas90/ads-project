## 1. Data Model and Migrations

- [x] 1.1 Add campaign lifecycle fields to `CampaignRequest` (`lifecycle_state`, `max_acceptances`, `hidden_at`) and keep `is_active` compatibility behavior.
- [x] 1.2 Add offer visibility field to `CampaignApplication` (`hidden_at`) and ensure status values support auto-reject on limit closure.
- [x] 1.3 Update `Deal` table constraints/model to remove unique `campaign_id` while keeping unique `campaign_application_id`.
- [x] 1.4 Create and review Alembic migration(s) for new columns/defaults/check constraints and dropping `ux_deals_campaign_id`.
- [x] 1.5 Validate migration upgrade/downgrade behavior for fresh DB and existing data.

## 2. Campaign Request API Behavior

- [x] 2.1 Update `POST /campaigns` validation/serialization to accept optional `max_acceptances` with default `10` and minimum `1`.
- [x] 2.2 Update `GET /campaigns` to hide campaigns with `lifecycle_state = hidden` by default.
- [x] 2.3 Update `GET /campaigns/{id}` to return `404` for hidden campaigns while preserving ownership checks.
- [x] 2.4 Implement `DELETE /campaigns/{id}` as soft-hide (`lifecycle_state = hidden`, `hidden_at`, `is_active = false`) with idempotent `204` behavior.

## 3. Offer Visibility and Lifecycle Integration

- [x] 3.1 Implement soft-hide cascade from campaign delete to related campaign applications in the same transaction.
- [x] 3.2 Ensure `GET /campaigns/{campaign_id}/applications` excludes soft-hidden offers.
- [x] 3.3 Update owner apply flow (`POST /campaigns/{campaign_id}/apply`) to allow only `active` campaigns and return `404` for hidden/closed campaigns.
- [x] 3.4 Ensure accepted offers remain reachable via deal detail/history flows even when campaign/offer pages are hidden.

## 4. Multi-Accept Deal Conversion

- [x] 4.1 Refactor campaign acceptance flow to support multiple accepted offers per campaign (no single-deal-per-campaign assumption).
- [x] 4.2 Enforce `max_acceptances` during `POST /campaigns/{campaign_id}/applications/{application_id}/accept` and return conflict when limit reached.
- [x] 4.3 Add campaign-row locking (`FOR UPDATE`) around accepted-count check and deal creation for transaction-safe concurrency.
- [x] 4.4 On limit reach, transition campaign to `closed_by_limit`, set compatibility inactive state, and auto-reject remaining submitted offers.
- [x] 4.5 Block future apply/accept operations once campaign lifecycle is `closed_by_limit`.

## 5. Tests and Validation

- [x] 5.1 Add campaign request tests for `max_acceptances` defaults/validation and hidden visibility semantics.
- [x] 5.2 Add campaign delete tests covering soft-hide idempotency and cascade hide of related offers.
- [x] 5.3 Add application list/apply tests for `active` vs `hidden` vs `closed_by_limit` lifecycle behavior.
- [x] 5.4 Add deal acceptance tests proving multiple deals per campaign are allowed up to limit and blocked after limit.
- [x] 5.5 Add concurrency test(s) for parallel accept requests verifying accepted count never exceeds `max_acceptances`.
- [x] 5.6 Run backend test suite and migration checks; resolve regressions.
