## Context

The current frontend route structure still treats `/` as a generic landing/home entry, while role preference already exists in backend APIs (`/auth/me`, `PUT /users/me/preferences`). This produces two UX gaps: (1) first-time role selection is not consistently enforced as onboarding, and (2) users can navigate into role-incompatible routes. The change must consolidate entry behavior around profile-based role management and ensure navigation and routing are synchronized with `preferred_role`.

## Goals / Non-Goals

**Goals:**
- Make `/profile` the canonical role-management screen for both first-time and returning users.
- Resolve app entry based on `preferred_role` using `/auth/me` at startup.
- Enforce route access by role with deterministic redirects.
- Render bottom navigation items based on active role and update immediately after role switches.
- Preserve selected role in backend via existing preferences endpoint.

**Non-Goals:**
- Introduce new backend endpoints or schema changes.
- Implement role-specific authorization in backend beyond existing endpoint-level checks.
- Change deal/business FSM behavior.

## Decisions

1) **`/profile` becomes the canonical role screen**
- **Decision:** First-time users (`preferred_role = null`) are routed to `/profile` for role selection; returning users can always use `/profile` to switch roles.
- **Rationale:** One stable location for onboarding + account preference avoids duplicate logic between landing/home/profile.
- **Alternatives considered:** Keep role picker on `/` and add profile later. Rejected because it fragments the role flow and conflicts with the desired UX.

2) **`/` acts as an entry resolver, not a destination**
- **Decision:** `/` performs startup resolution and redirects to:
  - `null` role -> `/profile`
  - `owner` -> `/owner`
  - `advertiser` -> `/advertiser/marketplace`
- **Rationale:** Removes ambiguity around "home" and makes startup deterministic.
- **Alternatives considered:** Keep static landing at `/`. Rejected because users repeatedly hit a screen they no longer need.

3) **Role-aware route guards with role-default fallback**
- **Decision:** Each route is tagged as `owner`, `advertiser`, or `shared`.
  - Missing role trying role-scoped route -> `/profile`
  - Mismatched role deep-link -> redirect to the active role default
- **Rationale:** Prevents users from entering invalid views while keeping deep-link behavior predictable.
- **Alternatives considered:** Allow route access and hide actions only. Rejected because users still reach irrelevant pages.

4) **Role-scoped navigation model**
- **Decision:** Bottom nav is computed from active role.
  - `null`: `Profile`
  - `owner`: `Owner`, `Deals`, `Profile`
  - `advertiser`: `Marketplace`, `Campaign`, `Deals`, `Profile`
- **Rationale:** Navigation should only expose actions relevant to the current role.
- **Alternatives considered:** Always show all links. Rejected due to confusion and accidental cross-role navigation.

5) **Role switch stays on `/profile` and updates nav immediately**
- **Decision:** After successful role update, stay on `/profile`; update store state immediately so nav refreshes without full reload.
- **Rationale:** Matches requested UX and provides immediate feedback.
- **Alternatives considered:** Auto-redirect to role default after switch. Rejected by product decision.

6) **Owner hub retained, advertiser default goes to task route**
- **Decision:** Keep `/owner` as owner hub; advertiser default uses `/advertiser/marketplace`.
- **Rationale:** Owner hub currently contains operational content; advertiser hub is link-heavy and can be skipped on default entry.

### Route Matrix (authoritative)

| Route | Allowed Role | Null Role Redirect | Owner Forbidden Redirect | Advertiser Forbidden Redirect |
|---|---|---|---|---|
| `/` | resolver | `/profile` | n/a | n/a |
| `/profile` | shared (`null`, `owner`, `advertiser`) | stay | stay | stay |
| `/owner` | owner | `/profile` | stay | `/advertiser/marketplace` |
| `/owner/channels/:id/verify` | owner | `/profile` | stay | `/advertiser/marketplace` |
| `/owner/channels/:id/listing` | owner | `/profile` | stay | `/advertiser/marketplace` |
| `/owner/deals` | owner | `/profile` | stay | `/advertiser/marketplace` |
| `/owner/deals/:id/creative` | owner | `/profile` | stay | `/advertiser/marketplace` |
| `/advertiser` | advertiser alias | `/profile` | `/owner` | `/advertiser/marketplace` |
| `/advertiser/marketplace` | advertiser | `/profile` | `/owner` | stay |
| `/advertiser/campaigns/new` | advertiser | `/profile` | `/owner` | stay |
| `/advertiser/deals` | advertiser | `/profile` | `/owner` | stay |
| `/advertiser/deals/:id/review` | advertiser | `/profile` | `/owner` | stay |
| `/advertiser/deals/:id/fund` | advertiser | `/profile` | `/owner` | stay |
| `/deals/:id` | shared (`owner`, `advertiser`) | `/profile` | stay | stay |

## Risks / Trade-offs

- **[Risk] Startup flicker before role resolves** -> **Mitigation:** Add a startup loading gate while `/auth/me` is in-flight.
- **[Risk] Guard and nav logic diverge over time** -> **Mitigation:** Define centralized route metadata used by both guard and nav rendering.
- **[Risk] Shared route `/deals/:id` can still fail backend authorization (403)** -> **Mitigation:** Handle 403 in UI and redirect to role default.
- **[Risk] Profile route becomes overloaded with onboarding and settings** -> **Mitigation:** Keep role block focused and isolate additional settings sections.

## Migration Plan

1. Add role/visibility metadata to router records and introduce a global before-each guard.
2. Convert `/` into a resolver route and add `/profile` view.
3. Replace static nav links with role-computed nav config.
4. Wire profile role mutation flow to stay on `/profile` and update store state.
5. Add tests for startup resolution, role-switch nav update, and forbidden deep-link redirects.

## Open Questions

- None.
