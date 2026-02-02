## MODIFIED Requirements

### Requirement: Auth verification endpoint
The backend SHALL expose a protected `/auth/me` route that returns basic user information for verification/testing, including `preferred_role` (nullable).

#### Scenario: Authenticated request
- **WHEN** a request with valid initData calls `/auth/me`
- **THEN** the response includes the authenticated user's identifiers and `preferred_role`

## ADDED Requirements

### Requirement: User role preference endpoint
The backend SHALL expose `PUT /users/me/preferences` requiring authentication. It SHALL accept `preferred_role` with allowed values `owner` or `advertiser`, persist the value on the user record, and return the updated preference.

#### Scenario: User sets role preference
- **WHEN** an authenticated user sets `preferred_role = owner`
- **THEN** the response is HTTP 200 and includes `preferred_role = owner`
