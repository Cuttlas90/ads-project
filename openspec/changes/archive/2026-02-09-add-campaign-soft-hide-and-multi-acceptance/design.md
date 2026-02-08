## Context

Campaign creation and offer collection currently support only one accepted offer per campaign because `deals.campaign_id` is unique and the accept route hard-stops after the first deal. Advertisers also lack a safe cleanup mechanism for stale campaigns and related offers, creating noisy campaign/offer pages. The requested behavior adds campaign/offer soft-hide, introduces acceptance-cap limits per campaign, and enables multiple accepted offers (and deals) for a single campaign while preserving existing deal lifecycle and history integrity.

## Goals / Non-Goals

**Goals:**
- Allow advertiser campaign cleanup via soft-hide delete without breaking foreign-key references or deal history.
- Ensure campaign soft-hide also hides related offers from campaign/offer pages.
- Keep accepted offers visible through deal detail/history and maintain deal continuity.
- Enable multi-deal campaigns by removing one-deal-per-campaign DB/API constraints.
- Add `max_acceptances` (default `10`) and enforce accept limits safely under concurrent requests.
- Introduce explicit campaign lifecycle states (`active`, `hidden`, `closed_by_limit`) and deterministic behavior transitions.
- Auto-close remaining submitted offers when acceptance limit is reached.

**Non-Goals:**
- Redesign of the deal FSM or escrow flow.
- Frontend UX implementation details beyond backend contract implications.
- Re-introducing hard deletes for campaigns or offers.

## Decisions

1. Campaign lifecycle is explicit state, not inferred flags
- Decision: Add `lifecycle_state` on campaigns with allowed values `active`, `hidden`, `closed_by_limit`.
- Rationale: A single explicit lifecycle state avoids ambiguous combinations of boolean flags and gives clean filtering semantics.
- Alternative considered: infer lifecycle from `is_active` + accepted-count; rejected because it creates fragile implicit rules and hard-to-debug list behavior.

2. Soft-hide delete is implemented as state transition + visibility timestamp
- Decision: `DELETE /campaigns/{campaign_id}` transitions campaign lifecycle to `hidden`, records hide metadata (`hidden_at`, optionally `hidden_by_user_id`), and no physical row deletion occurs.
- Rationale: Preserves referential integrity with offers/deals and keeps auditability.
- Alternative considered: hard delete with cascades; rejected because deals and application history must remain accessible.

3. Offers are soft-hidden in lockstep with campaign hide
- Decision: On campaign hide, mark related offers hidden (`hidden_at`) in the same transaction.
- Rationale: Ensures campaign page and offer page stay clean and consistent immediately after delete.
- Alternative considered: campaign-only hide with offer filtering by campaign state; rejected because direct offer list endpoints still risk surfacing stale records unless every query is perfectly constrained.

4. Accepted offers remain visible through deal surfaces
- Decision: Campaign/offer pages omit hidden records, but deal detail/history remains source of truth and continues to expose accepted deal-linked context.
- Rationale: Matches user requirement and keeps negotiations/payments traceable.
- Alternative considered: hide accepted offers everywhere after campaign hide; rejected as it would obscure active/finished business records.

5. Multi-deal campaigns remove unique campaign constraint
- Decision: Drop `ux_deals_campaign_id` while keeping `ux_deals_campaign_application_id`.
- Rationale: Allows multiple accepted offers (one deal per accepted offer) for the same campaign while still preventing duplicate deal creation per offer.
- Alternative considered: keep unique campaign and introduce child campaign clones; rejected as unnecessary complexity.

6. Acceptance cap is campaign-level and defaults to 10
- Decision: Add `max_acceptances` (integer, default `10`, minimum `1`) on campaigns.
- Rationale: Provides explicit conversion control and default behavior without per-request tuning.
- Alternative considered: unlimited accepts by default; rejected due to budget/ops risk.

7. Acceptance limit enforcement is transaction-safe using row-level locking
- Decision: In accept endpoint, lock campaign row (`SELECT ... FOR UPDATE`) and compute current accepted/deal count inside the same transaction before creating new deal.
- Rationale: Prevents race conditions where parallel accepts oversubscribe capacity.
- Alternative considered: optimistic checks without locking; rejected because concurrent requests can pass pre-check simultaneously.

8. Limit-reached behavior closes remaining submitted offers automatically
- Decision: After successful accept that reaches cap, transition campaign lifecycle to `closed_by_limit` and bulk-update remaining `submitted` offers to terminal status (`rejected` or `closed`) with optional reason metadata.
- Rationale: Removes ambiguous pending offers and aligns with “auto-mark rejected/closed”.
- Alternative considered: leave submitted offers untouched but block future accepts; rejected because users would see misleading pending offers.

9. Hidden/inactive retrieval policy uses 404 for resource reads/actions
- Decision: For campaign/offer APIs outside deal history, hidden campaigns and hidden offers are treated as not found (`404`) to avoid leaking non-visible resources.
- Rationale: Matches cleanup semantics and avoids exposing hidden identifiers.
- Alternative considered: `400` inactive/hidden; rejected for noisier client branching and less conventional access semantics.

10. Existing `is_active` compatibility is preserved during transition
- Decision: Keep `is_active` for backward compatibility but derive/maintain consistency with lifecycle (`active` => true, others => false).
- Rationale: Minimizes breakage for legacy code paths while new behavior standardizes on lifecycle.
- Alternative considered: remove `is_active` immediately; rejected due to broad code/test impact.

## Risks / Trade-offs

- [Risk] Lifecycle and legacy flags diverge (`lifecycle_state` vs `is_active`) -> Mitigation: enforce updates in one service path and add tests for consistency.
- [Risk] Bulk offer auto-close may hide data users still expect in campaign UI -> Mitigation: ensure deal pages preserve accepted context and expose terminal reason fields where needed.
- [Risk] Row locking can reduce throughput under high contention -> Mitigation: lock only campaign row for short critical section and avoid long-running work inside transaction.
- [Risk] Dropping unique `campaign_id` may affect implicit assumptions in analytics/reporting -> Mitigation: update queries/tests to aggregate by campaign rather than expecting single deal.
- [Risk] 404-on-hidden may complicate debugging -> Mitigation: structured server logs include hidden-state rejection reason.

## Migration Plan

1. Add migration for campaign lifecycle and acceptance controls:
- add `campaign_requests.lifecycle_state` (`active` default)
- add `campaign_requests.max_acceptances` (`10` default, check `>=1`)
- add optional hide metadata columns (`hidden_at`, `hidden_by_user_id`)

2. Add migration for application visibility/control:
- add `campaign_applications.hidden_at`
- ensure status check supports terminal close/reject semantics used by auto-close flow

3. Remove one-deal-per-campaign DB constraint:
- drop unique index/constraint `ux_deals_campaign_id`
- keep `ux_deals_campaign_application_id`

4. Deploy backend logic changes:
- update campaign delete/list/get behavior for lifecycle/hidden rules
- update accept endpoint with transactional lock + cap enforcement + auto-close behavior

5. Update tests:
- add soft-hide cascade and visibility coverage
- add multi-accept + max_acceptances behavior coverage
- add concurrent accept test ensuring cap is never exceeded

6. Rollback strategy:
- if rollback needed before data backfill, keep new columns nullable/defaulted and gate behavior with code path toggle.
- re-adding `ux_deals_campaign_id` after multi-deal data exists is not reversible without data cleanup; rollback requires pre-check and merge/removal strategy.

## Open Questions

- Should auto-closed offers use existing `rejected` status only, or introduce a dedicated `closed` status value?
- Should hidden campaign/offers support an admin-only restore flow now or later?
- Should accepted-count for cap use deals table only, or accepted application status as authoritative with reconciliation checks?
