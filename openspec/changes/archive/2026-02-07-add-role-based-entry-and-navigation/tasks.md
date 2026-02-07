## 1. Route Metadata and Entry Resolution

- [x] 1.1 Add route metadata that classifies each route as `owner`, `advertiser`, `shared`, or `resolver`.
- [x] 1.2 Implement startup role bootstrap (`/auth/me`) with a loading gate before first route resolution.
- [x] 1.3 Convert `/` into an entry resolver that redirects to `/profile`, `/owner`, or `/advertiser/marketplace` based on `preferred_role`.

## 2. Profile Role Management UX

- [x] 2.1 Create/repurpose `/profile` view as the canonical role-management screen for first-time selection and later switching.
- [x] 2.2 Implement role selection actions in Profile using `PUT /users/me/preferences`.
- [x] 2.3 Keep users on `/profile` after role update and refresh in-memory role state immediately.
- [x] 2.4 Update copy to explicitly state role can be changed later from Profile.

## 3. Role-Scoped Navigation

- [x] 3.1 Replace static bottom navigation links with role-derived nav config.
- [x] 3.2 Render nav sets per role (`null`, `owner`, `advertiser`) and hide links for other roles.
- [x] 3.3 Ensure navigation updates live in the same session after role switches.

## 4. Guard and Redirect Behavior

- [x] 4.1 Add global route guard enforcing role-scoped access rules from the route matrix.
- [x] 4.2 Redirect null-role users who open role-scoped routes to `/profile`.
- [x] 4.3 Redirect mismatched deep links to role defaults (`/owner` for owner, `/advertiser/marketplace` for advertiser).
- [x] 4.4 Keep `/deals/:id` and `/profile` as shared routes and add role-default fallback when shared deal detail authorization fails.

## 5. Verification and Regression Coverage

- [x] 5.1 Add frontend unit tests for entry resolution and guard redirects.
- [x] 5.2 Add frontend unit tests for role-scoped nav rendering and live nav update after role switch.
- [x] 5.3 Add e2e coverage for first-time user flow (`null role -> /profile -> save role`) and returning user routing.
- [x] 5.4 Add e2e coverage for forbidden deep-link redirects for both roles.
- [x] 5.5 Run `npm test`, `npm run build`, and `npm run lint` in `frontend/` and fix regressions.
