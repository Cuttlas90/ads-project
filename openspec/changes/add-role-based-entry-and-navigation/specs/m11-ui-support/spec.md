## MODIFIED Requirements

### Requirement: UI role choice messaging
The UI SHALL present role selection on the Profile screen for first-time users and SHALL indicate that role can be changed later from the same Profile screen.

#### Scenario: First-time profile role selection copy
- **WHEN** a user with `preferred_role = null` opens the app and is routed to Profile
- **THEN** the Profile screen presents role choices and copy that role can be changed later in Profile

### Requirement: Role-based entry routing
The UI SHALL resolve app entry using `GET /auth/me`. If `preferred_role` is null, it SHALL route to `/profile`. If `preferred_role` is `owner`, it SHALL route to `/owner`. If `preferred_role` is `advertiser`, it SHALL route to `/advertiser/marketplace`. When role is changed on Profile, the UI SHALL call `PUT /users/me/preferences`, persist the selected value, and remain on `/profile`.

#### Scenario: Returning owner bypasses profile picker
- **WHEN** app entry resolves `/auth/me` with `preferred_role = owner`
- **THEN** the user is routed to `/owner` instead of role selection

#### Scenario: Profile role update persists and stays on profile
- **WHEN** a user changes role from Profile
- **THEN** the UI calls `PUT /users/me/preferences` with the selected role and remains on `/profile`

## ADDED Requirements

### Requirement: Role-scoped navigation visibility
The bottom navigation SHALL render only links allowed for the active `preferred_role`.

#### Scenario: Owner navigation set
- **WHEN** active role is `owner`
- **THEN** navigation shows owner links (`/owner`, `/owner/deals`) and `/profile`, and does not show advertiser-only links

#### Scenario: Advertiser navigation set
- **WHEN** active role is `advertiser`
- **THEN** navigation shows advertiser links (`/advertiser/marketplace`, `/advertiser/campaigns/new`, `/advertiser/deals`) and `/profile`, and does not show owner-only links

#### Scenario: Navigation updates after role switch
- **WHEN** a user changes role on `/profile`
- **THEN** the navigation updates in the same session without full page reload

### Requirement: Role-scoped route guard redirects
The UI SHALL enforce role access for role-scoped routes using guard metadata. If `preferred_role` is null, role-scoped routes SHALL redirect to `/profile`. If a user opens a deep link for the opposite role, the UI SHALL redirect to that user's default route (`/owner` for owner, `/advertiser/marketplace` for advertiser).

#### Scenario: Null role blocked from owner route
- **WHEN** a user with `preferred_role = null` opens `/owner/deals`
- **THEN** the app redirects to `/profile`

#### Scenario: Owner blocked from advertiser deep link
- **WHEN** a user with `preferred_role = owner` opens `/advertiser/deals`
- **THEN** the app redirects to `/owner`

#### Scenario: Advertiser blocked from owner deep link
- **WHEN** a user with `preferred_role = advertiser` opens `/owner/channels/42/listing`
- **THEN** the app redirects to `/advertiser/marketplace`

### Requirement: Shared route fallback by role default
The shared deal detail route (`/deals/:id`) SHALL remain accessible to both roles, but when backend authorization fails for the current user, the UI SHALL redirect to the active role default route (`/owner` for owner, `/advertiser/marketplace` for advertiser, `/profile` for null role).

#### Scenario: Shared route authorization failure for advertiser
- **WHEN** an advertiser opens `/deals/:id` and backend returns authorization failure
- **THEN** the app redirects to `/advertiser/marketplace`
