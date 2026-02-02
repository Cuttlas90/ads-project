## ADDED Requirements

### Requirement: Role-based entry routing
The UI SHALL call `GET /auth/me` on app load to determine `preferred_role`. If `preferred_role` is null, it SHALL display a role picker. When a role is chosen, it SHALL call `PUT /users/me/preferences` and redirect to the selected role's home.

#### Scenario: New user selects role
- **WHEN** the UI loads and `/auth/me` returns `preferred_role = null`
- **THEN** a role picker is shown and selecting a role triggers `PUT /users/me/preferences` before redirect

### Requirement: Role picker messaging
The role picker UI SHALL inform the user that the selected role can be changed later in Profile.

#### Scenario: Role picker explains changeability
- **WHEN** the role picker is displayed
- **THEN** the screen includes copy indicating the role can be changed later in Profile

### Requirement: Bot messaging deep-link
The deal detail UI SHALL provide an action that opens the system bot chat using a deep link containing the deal id.

#### Scenario: Messaging CTA present
- **WHEN** a user views a deal detail page
- **THEN** an "Open bot messages" action is available and links to the system bot with the deal id

### Requirement: Deal timeline rendering
The deal detail UI SHALL render events returned by `GET /deals/{id}/events` in chronological order, displaying event type and timestamp.

#### Scenario: Timeline renders events
- **WHEN** the UI receives events from `/deals/{id}/events`
- **THEN** the timeline lists them in chronological order with timestamps

### Requirement: State-based action panel
The deal detail UI SHALL show only actions valid for the current `deal.state` and user role (e.g., submit creative, approve, request edits, fund).

#### Scenario: Invalid actions hidden
- **WHEN** a deal is in a given state
- **THEN** actions not allowed for that state and role are not displayed

### Requirement: Funding flow uses TONConnect
The funding screen SHALL use TONConnect UI to submit the payload from `POST /deals/{id}/escrow/tonconnect-tx` and SHALL poll `GET /deals/{id}/escrow` until the escrow state is `FUNDED` or `FAILED`.

#### Scenario: Funding flow success
- **WHEN** the advertiser submits the TONConnect transaction
- **THEN** the UI polls escrow status until it reaches `FUNDED` or `FAILED`
