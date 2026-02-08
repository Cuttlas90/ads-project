## Context

The backend already supports campaign creation, owner application, advertiser acceptance, and deal creation, but the frontend does not expose a complete role-to-role journey. Advertisers can create campaigns, yet they cannot manage campaign/offers in one coherent workspace; owners also lack a campaign discovery page; and advertisers lack an aggregated offers inbox for fast conversion into `DRAFT` deals.

This change is cross-cutting across backend APIs, frontend routes/views/stores/services, and role-based navigation. It also depends on existing soft-hide lifecycle behavior from campaign APIs and existing deal pages for post-accept continuation.

## Goals / Non-Goals

**Goals:**
- Provide one coherent campaign workflow from campaign creation to `DRAFT` deal creation.
- Keep advertiser campaign management on one page (create form + campaign list).
- Provide owner campaign discovery and application with owned verified channel selection.
- Provide one aggregated advertiser offers inbox sorted by newest offers first.
- Ensure accept action creates a deal and redirects immediately to `/deals/:id`.
- Keep UI label `Delete campaign` while preserving hidden/soft-delete backend semantics.

**Non-Goals:**
- Redesign of deal FSM, escrow flow, or posting/verification steps.
- Changing campaign acceptance capacity semantics (`max_acceptances`) introduced in prior backend change.
- Introducing hard-delete behavior for campaigns or offers.
- Replacing existing marketplace listing-sourced deal flow.

## Decisions

1. Add explicit role-specific campaign discovery and offers APIs
- Decision: introduce dedicated endpoints for owner campaign browsing and advertiser aggregated offers inbox, instead of overloading existing advertiser `GET /campaigns`.
- Rationale: current `GET /campaigns` is advertiser-owned data by design; mixing owner and advertiser behavior in one endpoint increases ambiguity and permission risk.
- Alternatives considered:
  - Add mode query param on `GET /campaigns` (`scope=owner|advertiser`) and branch behavior.
  - Rejected due to high accidental misuse risk and weaker contract clarity.

2. Keep advertiser campaign workspace on existing campaign-create route
- Decision: keep `/advertiser/campaigns/new` and render advertiser campaign list below the create form.
- Rationale: matches requested UX and minimizes navigation churn.
- Alternatives considered:
  - Add separate advertiser campaign index page.
  - Rejected because requirement is explicitly one workspace under the create box.

3. Add owner campaign page as separate route
- Decision: add owner route/page dedicated to campaign discovery and apply flow.
- Rationale: campaign discovery is now a first-class owner action similar to owner deals.
- Alternatives considered:
  - Embed campaigns into owner home dashboard.
  - Rejected because owner home is currently channel/listing oriented and would become overloaded.

4. Aggregated offers inbox is canonical advertiser offer-review surface
- Decision: expose one aggregated offers list for advertiser across all their campaigns, sorted by `created_at DESC`.
- Rationale: fastest review path and directly matches requested behavior.
- Alternatives considered:
  - Per-campaign offer review only.
  - Rejected because it adds extra click depth and slows high-volume review.

5. Owner apply uses explicit verified-channel selection
- Decision: apply form requires choosing from channels owned by caller with `is_verified = true`; an owner may apply to same campaign with multiple channels, still constrained by unique `(campaign_id, channel_id)`.
- Rationale: preserves backend invariants and user intent for multi-channel offers.
- Alternatives considered:
  - Auto-pick first verified channel.
  - Rejected because it hides critical intent and makes multi-channel applications awkward.

6. Accept action redirects immediately to deal detail
- Decision: after successful accept response, frontend navigates directly to `/deals/:id`.
- Rationale: deal detail is the shared continuation surface for both roles and states.
- Alternatives considered:
  - Stay on offers inbox with toast and optional open button.
  - Rejected per explicit requirement for immediate redirect.

7. Delete copy remains user-facing delete while behavior is soft-hide
- Decision: button label remains `Delete campaign`, confirmation/body text explains campaign and related offers will be removed from campaign pages but retained in deal history.
- Rationale: preserves simple wording while avoiding hidden-behavior confusion.
- Alternatives considered:
  - Rename to `Hide campaign`.
  - Rejected because request explicitly keeps delete label.

8. Keep v1 scope operationally simple
- Decision: owner campaign discovery in v1 is limited to pagination + basic search; advertiser offers inbox is strictly flat newest-first (no grouping toggles); apply form stays minimal manual input (no per-channel prefilled template text).
- Rationale: prioritizes delivering the core workflow quickly with clear behavior and low UX/API complexity.
- Alternatives considered:
  - Add advanced discovery filters in v1.
  - Add campaign-grouped offers toggle in v1.
  - Add prefilled proposal templates per channel in v1.
  - Rejected to avoid expanding implementation scope before validating the core flow.

## Risks / Trade-offs

- [Risk] Aggregated offers query can become heavy (campaign join + channel stats lookup) at scale.
  -> Mitigation: paginate aggressively, sort on indexed timestamps, and add focused indexes if needed.
- [Risk] Owner confusion when no verified channels are available to apply.
  -> Mitigation: render explicit empty-state guidance linking to owner channel verification/listing flow.
- [Risk] Duplicate surface between marketplace and owner campaigns may confuse role mental model.
  -> Mitigation: keep role-scoped navigation labels explicit (`Campaigns` for owner, `Offers` for advertiser).
- [Risk] Soft-hide semantics may be misread as hard delete.
  -> Mitigation: add confirmation copy and consistent UI messaging around history/deal persistence.
- [Risk] Immediate redirect after accept can hide context of remaining offers.
  -> Mitigation: include campaign + source breadcrumbs in deal detail and keep offers page accessible from nav.

## Migration Plan

1. Backend API additions and serializer updates
- add owner campaign discovery endpoint contract (active/non-hidden campaigns only).
- add advertiser aggregated offers inbox endpoint contract (newest-first, hidden offers excluded).
- ensure existing apply/accept/delete contracts remain compatible with new UI surfaces.

2. Frontend route/navigation rollout
- add owner campaigns route.
- add advertiser offers route.
- update role-scoped bottom nav to include new pages.

3. Frontend state/service integration
- extend campaign services/types/stores for owner discovery, advertiser campaign workspace list, offers inbox, apply, accept, and delete.
- keep deal service unchanged except immediate redirect consumer behavior.

4. UX and validation integration
- add owned verified channel picker for apply.
- add delete confirmation messaging with hidden semantics.
- add post-accept immediate redirect handling and failure fallbacks.

5. Test rollout
- route guard tests for new owner/advertiser pages.
- page-level tests for list/apply/accept/delete behaviors.
- API contract tests for new discovery and aggregated offers endpoints.

## Open Questions

- None for v1. The scope is locked to basic search + pagination, strictly flat newest-first offers inbox, and a minimal manual apply form.
