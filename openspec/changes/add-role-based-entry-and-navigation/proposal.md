## Why

The first screen currently does not function as a durable entry point for role selection, and users can still land on routes that do not match their selected role. We need a single, predictable role-aware entry and navigation model so role choice is persistent, visible, and enforced in routing.

## What Changes

- Replace the current home/landing entry behavior with a role-aware entry resolver.
- Introduce `/profile` as the canonical screen for first-time role selection and later role switching.
- Keep the user on `/profile` after role changes; update role-specific navigation immediately.
- Make bottom navigation role-aware so users only see links relevant to their active role.
- Add route-guard behavior for all role-scoped routes:
  - when `preferred_role` is missing, redirect to `/profile`
  - when role is mismatched, redirect to that role's default route
- Define explicit default routes:
  - owner default: `/owner`
  - advertiser default: `/advertiser/marketplace`
- Keep shared routes accessible by both roles (for example `/deals/:id` and `/profile`) with role-aware fallback on authorization failures.

## Capabilities

### New Capabilities
- None.

### Modified Capabilities
- `m11-ui-support`: Refine role-based entry routing to profile-first onboarding, add role-scoped navigation visibility, and enforce redirect guards for role-mismatched deep links.

## Impact

- Frontend router: add entry resolver logic, route metadata, and guard redirects.
- Frontend views: repurpose/replace landing UX with a profile role-management screen.
- Frontend app shell: render navigation items based on active role and update immediately after role switches.
- Frontend tests: add/adjust unit and e2e coverage for startup routing, role switching, and forbidden deep-link redirects.
- Backend API: no new endpoint required; reuse existing `/auth/me` and `PUT /users/me/preferences`.
