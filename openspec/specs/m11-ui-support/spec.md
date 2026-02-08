# m11-ui-support Specification

## Purpose
Define the backend and UX requirements needed to support the M11 polished Telegram Mini App UI journeys,
including role preference, marketplace format selection, deal timeline visibility, and creative approval
before funding.
## Requirements
### Requirement: Persist user role preference
The system SHALL store a per-user `preferred_role` with allowed values `owner` or `advertiser`. It SHALL expose
`PUT /users/me/preferences` to update `preferred_role` and return the updated preference. It SHALL include
`preferred_role` in the `/auth/me` response to allow auto-redirect on app load.

#### Scenario: User sets role preference
- **GIVEN** an authenticated user
- **WHEN** they call `PUT /users/me/preferences` with `preferred_role = owner`
- **THEN** the response is HTTP 200 with `preferred_role = owner`
- **AND** subsequent `GET /auth/me` includes `preferred_role = owner`

### Requirement: Marketplace listings include format ids
The system SHALL include `format_id` for each format in `GET /marketplace/listings` results so the UI can
create a deal from a selected format.

#### Scenario: Marketplace format id present
- **WHEN** a client requests `/marketplace/listings`
- **THEN** each `formats[]` entry includes `id`, `label`, and `price`

### Requirement: Listing read endpoint for editor
The system SHALL expose `GET /channels/{channel_id}/listing` requiring authentication and owner role.
It SHALL return the listing summary plus all listing formats for the channel. It SHALL return HTTP 404
if no listing exists and HTTP 403 for non-owners.

#### Scenario: Owner loads listing editor
- **GIVEN** a channel owner
- **WHEN** they call `GET /channels/{channel_id}/listing`
- **THEN** the response includes listing data and its formats

### Requirement: Deal inbox endpoint
The system SHALL expose `GET /deals` requiring authentication with optional `role=owner|advertiser`.
It SHALL return a paginated list of deals visible to that role, including `id`, `state`, `channel_id`,
`channel_username`, `channel_title`, `advertiser_id`, `price_ton`, `ad_type`, `updated_at`.

#### Scenario: Owner views deal inbox
- **GIVEN** a channel owner
- **WHEN** they call `GET /deals?role=owner`
- **THEN** the response includes only deals for channels they own

### Requirement: Deal detail endpoint
The system SHALL expose `GET /deals/{id}` requiring authentication for participants only. It SHALL return
the deal summary plus participant display fields (`channel_username`, `channel_title`, `advertiser_username`,
`advertiser_first_name`, `advertiser_last_name`) when available.

#### Scenario: Participant views deal detail
- **GIVEN** a deal participant
- **WHEN** they call `GET /deals/{id}`
- **THEN** the response includes the deal summary and participant display fields

### Requirement: Deal timeline endpoint
The system SHALL expose `GET /deals/{id}/events` requiring authentication for participants only. It SHALL
return a single chronological list of events from `deal_events` and `escrow_events`, each with
`event_type`, `from_state`, `to_state`, `payload`, `created_at`, and `actor_id` (nullable). Results SHALL
be sorted by `created_at` with a deterministic tie-breaker.

#### Scenario: Timeline shows merged events
- **WHEN** a participant requests `/deals/{id}/events`
- **THEN** the response includes deal and escrow events in chronological order

### Requirement: Creative media upload to Telegram
The system SHALL provide `POST /deals/{id}/creative/upload` requiring authentication for the channel owner.
It SHALL accept multipart media (`image` or `video`), upload to Telegram Bot API using a private storage
channel configured by `TELEGRAM_MEDIA_CHANNEL_ID`, and return `creative_media_ref` as the Telegram `file_id`
along with `creative_media_type`.

#### Scenario: Creative upload returns file id
- **GIVEN** a valid media file
- **WHEN** the owner uploads via `/deals/{id}/creative/upload`
- **THEN** the response includes `creative_media_ref` set to the Telegram `file_id`

### Requirement: Creative approval FSM transitions
The system SHALL include the explicit DealState `CREATIVE_CHANGES_REQUESTED`. It SHALL allow:
- `ACCEPTED -> CREATIVE_SUBMITTED` (owner submits creative)
- `CREATIVE_SUBMITTED -> CREATIVE_APPROVED` (advertiser approves)
- `CREATIVE_SUBMITTED -> CREATIVE_CHANGES_REQUESTED` (advertiser requests edits)
- `CREATIVE_CHANGES_REQUESTED -> CREATIVE_SUBMITTED` (owner resubmits)
All transitions SHALL use the deal transition table and write deal events.

#### Scenario: Advertiser requests edits
- **GIVEN** a deal in `CREATIVE_SUBMITTED`
- **WHEN** the advertiser requests edits
- **THEN** the deal transitions to `CREATIVE_CHANGES_REQUESTED`

### Requirement: Escrow init gated by creative approval
The system SHALL allow `POST /deals/{id}/escrow/init` and `POST /deals/{id}/escrow/tonconnect-tx` only when
the deal state is `CREATIVE_APPROVED`. Funding confirmation SHALL transition the deal to `FUNDED`.

#### Scenario: Escrow init rejected before approval
- **GIVEN** a deal in `ACCEPTED` or `CREATIVE_SUBMITTED`
- **WHEN** the advertiser calls `/deals/{id}/escrow/init`
- **THEN** the response is HTTP 400

### Requirement: Escrow status endpoint for funding UI
The system SHALL expose `GET /deals/{id}/escrow` requiring authentication for participants. It SHALL return
`state`, `deposit_address`, `expected_amount_ton`, `received_amount_ton`, and `deposit_confirmations`.

#### Scenario: Funding screen polls escrow
- **GIVEN** an initialized escrow
- **WHEN** the UI calls `/deals/{id}/escrow`
- **THEN** the response includes escrow state and confirmation data

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
The funding screen SHALL check wallet readiness from authenticated user data before funding actions. If the advertiser wallet is missing (`has_wallet = false`), the screen SHALL hard-block funding actions, SHALL show an in-page modal with one-click navigation to `/profile` including a return target (`next`) to the same funding route, and SHALL NOT call `POST /deals/{id}/escrow/init` or `POST /deals/{id}/escrow/tonconnect-tx`. When wallet readiness is true, the funding screen SHALL use TONConnect UI to submit the payload from `POST /deals/{id}/escrow/tonconnect-tx` and SHALL poll `GET /deals/{id}/escrow` until the escrow state is `FUNDED` or `FAILED`.

#### Scenario: Missing wallet blocks funding actions
- **WHEN** an advertiser opens funding for a deal with `has_wallet = false`
- **THEN** funding actions are blocked and an in-page modal prompts navigation to Profile

#### Scenario: Profile jump preserves funding return path
- **WHEN** the advertiser confirms the modal action from funding
- **THEN** the app navigates to Profile with a `next` target for the same funding route

#### Scenario: Funding flow success after wallet setup
- **WHEN** the advertiser returns from Profile with `has_wallet = true` and submits the TONConnect transaction
- **THEN** the UI calls escrow init/payload endpoints and polls escrow status until it reaches `FUNDED` or `FAILED`

### Requirement: Profile wallet connection UX
The Profile UI SHALL include a wallet section that allows authenticated users to connect or update their TON wallet using the backend TonConnect proof flow. Wallet setup SHALL be optional for both owner and advertiser roles and SHALL NOT block role selection or role switching on Profile.

#### Scenario: User can skip wallet during role selection
- **WHEN** a user with no wallet opens Profile and selects a role
- **THEN** role selection succeeds without requiring wallet connection

#### Scenario: User connects wallet from Profile
- **WHEN** a user completes the Profile wallet proof flow successfully
- **THEN** the UI reflects wallet-connected status for that user

