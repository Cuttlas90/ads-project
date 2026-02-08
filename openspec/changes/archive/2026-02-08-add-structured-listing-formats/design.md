## Context

Today, listing formats are persisted as free-form `label` + `price`, which lets owners publish arbitrary naming that is hard to compare and impossible to enforce in workers. Marketplace discovery and deal creation therefore depend on loosely interpreted text instead of explicit delivery terms.

The posting pipeline is already automated (`deal-posting` + `deal-verification`) and has a visibility window concept (`verification_window_hours`), so introducing structured format fields should be aligned with existing worker behavior rather than adding parallel ad-hoc logic.

Constraints:
- Keep backend-first, migration-first changes.
- Preserve deterministic marketplace filtering/sorting.
- Keep listing-sourced deal terms contractually locked after deal creation.

## Goals / Non-Goals

**Goals:**
- Replace label-driven listing formats with explicit terms: `placement_type`, `exclusive_hours`, `retention_hours`, `price_ton`.
- Require at least one structured format (`post` or `story`) before a listing is considered sellable.
- Propagate listing format terms into listing-sourced deals as immutable contractual fields.
- Extend posting/verification workers to enforce exclusivity and minimum retention semantics.
- Keep marketplace and owner UI contracts aligned with the structured model.

**Non-Goals:**
- Redesign campaign-sourced deal pricing/format flows.
- Introduce manual moderation workflows.
- Change auth, escrow FSM, or payout architecture.
- Implement advanced channel content classification beyond explicit rules defined in this change.

## Decisions

### 1) Structured listing format schema replaces free-form labels

Decision:
- Evolve `listing_formats` to include:
  - `placement_type` enum/string constrained to `post | story`
  - `exclusive_hours` integer (`>= 0`)
  - `retention_hours` integer (`>= 1`)
  - `price` (existing decimal TON field)
- Add uniqueness on `(listing_id, placement_type, exclusive_hours, retention_hours)` to prevent duplicate commercial offers within one listing.
- Treat legacy `label` as deprecated and remove it from create/update/read contracts in this change.

Rationale:
- Structured terms make filters deterministic and machine-enforceable.
- A dedicated tuple uniqueness constraint prevents duplicate inventory rows while still allowing multiple packages per placement type.

Alternatives considered:
- Keep `label` and add `posting_params` JSON on formats. Rejected because it keeps semantics weak and complicates indexing/filtering.
- Only constrain label vocabulary (`"Post"/"Story"`). Rejected because hours would still remain unstructured.

### 2) “At least one format (post or story)” enforced as readiness, not raw table constraint

Decision:
- A listing can exist with incomplete formats during editing.
- Listing is eligible for activation/marketplace when it has at least one format (`post` or `story`).
- `PUT /listings/{id}` activation to `is_active=true` validates this readiness and returns HTTP 400 if incomplete.
- Marketplace query excludes listings with zero formats.

Rationale:
- Owners need draft iteration without hard DB-level coupling across rows.
- Enforcing non-empty format inventory at activation/eligibility preserves UX while preventing empty listings.

Alternatives considered:
- Require both `post` and `story` before activation. Rejected because it blocks valid single-placement channels.

### 3) Listing-derived terms are copied to deals as immutable fields

Decision:
- Add deal fields for listing-derived terms (`placement_type`, `exclusive_hours`, `retention_hours`) for `source_type=listing`.
- Copy values from selected listing format at `POST /listings/{listing_id}/deals` creation time.
- Treat these fields as immutable for listing-sourced deals during negotiation updates.
- Keep `ad_type` for backward compatibility; set it from `placement_type` for listing-sourced deals.

Rationale:
- Workers need stable, non-editable source-of-truth values.
- Keeping immutable columns avoids reliance on mutable `posting_params`.

Alternatives considered:
- Store these only in `posting_params`. Rejected because `posting_params` is negotiable and not schema-constrained.

### 4) Worker semantics: enforce exclusivity + minimum retention

Decision:
- `retention_hours` is treated as **minimum on-feed duration** (equivalent to minimum verification window), not mandatory deletion time.
- Verification worker checks:
  - Message/story remains available through `posted_at + retention_hours`.
  - Exclusivity is **placement-type scoped** during `posted_at .. posted_at + exclusive_hours`:
    - If the deal placement is `post`, any additional post in the channel is a breach; stories do not breach post exclusivity.
    - If the deal placement is `story`, any additional story in the channel is a breach; feed posts do not breach story exclusivity.
- On violation before retention completes (missing content or exclusivity breach), transition to refund path.
- No auto-delete worker is introduced in this change.

Rationale:
- Matches business wording: “after that can be deleted” means allowed, not required.
- Reuses existing periodic verification architecture and escrow release gating.

Alternatives considered:
- Add forced-delete worker at retention deadline. Rejected as it changes contract from minimum duration to mandatory expiry and adds avoidable operational risk.

### 5) Story publishing path added behind posting service abstraction

Decision:
- Extend posting service dispatch to branch on `placement_type` (`post` vs `story`) in addition to creative media type.
- Keep existing `post` behavior unchanged and explicitly route through Telegram Bot API.
- Add story publishing through Telegram Bot API as the required integration path for `story` placement.

Rationale:
- Business format requires story inventory to be executable, not just labeled.
- Encapsulating publish dispatch minimizes impact on FSM and worker orchestration.

Alternatives considered:
- Keep story as taxonomy only and skip auto-publish support. Rejected because it creates false inventory promises.
- Use Telethon/MTProto as primary story publish path. Rejected for this change to keep one publishing surface (Bot API).

### 6) API/UI contract changes are explicitly breaking

Decision:
- Listing format endpoints and marketplace format payloads expose structured fields (`placement_type`, `exclusive_hours`, `retention_hours`, `price`) and stop depending on `label`.
- Owner listing editor moves from free-text labels to controlled placement + numeric hour inputs.
- Marketplace supports filtering by structured terms.

Rationale:
- Avoids dual-format ambiguity and keeps one canonical contract.

Alternatives considered:
- Dual-read/write compatibility indefinitely. Rejected to avoid long-lived contract drift.

## Risks / Trade-offs

- [Bot API story publishing capability/permissions may vary by deployment] -> Mitigation: validate Bot API rights/capabilities during verification and fail activation with explicit guidance when unsupported.
- [Exclusivity checks may misclassify non-administrative channel activity] -> Mitigation: define explicit exclusion rules (service messages, pinned updates, etc.) and cover with worker tests.
- [Breaking API shape impacts frontend and existing test fixtures] -> Mitigation: land backend + frontend changes in same change set with migration + contract test updates.
- [Legacy listing rows may not map cleanly to new structured fields] -> Mitigation: additive migration with safe defaults + readiness gating, then cleanup migration once data is normalized.
- [Additional worker checks increase Telegram read load] -> Mitigation: keep polling cadence unchanged initially and scope message lookups to bounded time windows.

## Migration Plan

1. Add Alembic migration for new listing format and deal term columns plus constraints/indexes (additive first).
2. Backfill existing listing formats with conservative defaults and derived placement type heuristics; mark incomplete rows as not marketplace-eligible via readiness checks.
3. Update backend schemas/routes/repositories to write/read structured format terms and new deal fields.
4. Update worker logic to evaluate exclusivity + retention using locked deal fields.
5. Update frontend listing editor + marketplace consumers to the new contract.
6. Remove deprecated label-dependent behavior after all API/UI paths are switched.

Rollback strategy:
- Because first migration is additive, rollback can disable new write paths and continue serving legacy fields until cleanup migration is applied.

## Open Questions

- None.
