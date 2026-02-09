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
The system SHALL include structured format terms for each format in `GET /marketplace/listings` results so the UI can create a deal from a selected format. Each `formats[]` entry SHALL include `id`, `placement_type`, `exclusive_hours`, `retention_hours`, and `price`.

#### Scenario: Marketplace structured format fields present
- **WHEN** a client requests `/marketplace/listings`
- **THEN** each `formats[]` entry includes `id`, `placement_type`, `exclusive_hours`, `retention_hours`, and `price`

### Requirement: Listing read endpoint for editor
The system SHALL expose `GET /channels/{channel_id}/listing` requiring authentication and owner role. It SHALL return the listing summary plus all listing formats for the channel. Each format SHALL include `id`, `placement_type`, `exclusive_hours`, `retention_hours`, and `price`. It SHALL return HTTP 200 with `has_listing = false` when no listing exists and HTTP 403 for non-owners.

#### Scenario: Owner loads listing editor with structured formats
- **GIVEN** a channel owner
- **WHEN** they call `GET /channels/{channel_id}/listing`
- **THEN** the response includes listing data and structured format fields

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
The system SHALL provide Telegram creative upload endpoints that return Telegram `file_id` for both pre-deal listing initiation and post-deal owner creative submission.
- `POST /listings/{listing_id}/creative/upload` SHALL require authentication for the user initiating a listing-based deal and SHALL be usable before deal creation.
- `POST /deals/{id}/creative/upload` SHALL require authentication for the channel owner on that deal.
Both endpoints SHALL accept multipart media (`image` or `video`), upload to Telegram Bot API using a private storage channel configured by `TELEGRAM_MEDIA_CHANNEL_ID`, and return `creative_media_ref` as the Telegram `file_id` along with `creative_media_type`.

#### Scenario: Listing-scoped upload returns file id before deal creation
- **GIVEN** a valid listing media file
- **WHEN** an authenticated user uploads via `/listings/{listing_id}/creative/upload`
- **THEN** the response includes `creative_media_ref` set to the Telegram `file_id` and a normalized `creative_media_type`

#### Scenario: Deal-scoped owner upload remains available
- **GIVEN** a valid media file
- **WHEN** the owner uploads via `/deals/{id}/creative/upload`
- **THEN** the response includes `creative_media_ref` set to the Telegram `file_id` and `creative_media_type`

### Requirement: Start deal flow uses upload-first creative capture
The marketplace Start deal UI SHALL require creative media upload before submitting deal creation. It SHALL provide a multiline creative text input, an explicit media type selector (`image` or `video`), a media file picker, and a start datetime input (`start_at`). It SHALL NOT require manual entry of Telegram `file_id`. On successful upload, it SHALL use returned `creative_media_ref` and `creative_media_type` in the subsequent `POST /listings/{listing_id}/deals` request and include selected `start_at` when provided.

#### Scenario: Listing start deal sends start datetime
- **WHEN** a user uploads media, enters creative text, and selects start datetime in Start deal modal
- **THEN** the UI submits `start_at` with creative fields in `POST /listings/{listing_id}/deals`

### Requirement: Creative approval FSM transitions
The system SHALL support proposal decision transitions directly from negotiation: only the latest-proposal recipient may approve or reject while the deal is in `DRAFT` or `NEGOTIATION`. Approve SHALL finalize the deal to `CREATIVE_APPROVED`, and reject SHALL finalize the deal to `REJECTED`. Legacy creative submit/review screens SHALL be bypassed in the primary deal-detail flow after proposal approval.

#### Scenario: Counterparty approves latest proposal
- **GIVEN** a deal in `DRAFT` or `NEGOTIATION` with a latest proposal from the opposite party
- **WHEN** the latest-proposal recipient approves
- **THEN** the deal transitions to `CREATIVE_APPROVED`

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

### Requirement: Deal event detail interaction
The deal detail UI SHALL open event details when a timeline row is tapped. For `message` events, the detail view SHALL show only message text. For `proposal` events, the detail view SHALL show proposal parameters from event payload; older proposal events SHALL be read-only, while the latest proposal SHALL expose actions only to the proposal recipient.

#### Scenario: Tapping message event shows message only
- **WHEN** a user taps a timeline row for an event with `event_type = message`
- **THEN** the detail view shows only the message text

### Requirement: Deal timeline rendering
The deal detail UI SHALL render events returned by `GET /deals/{id}/events` in reverse-chronological order (newest first). The timestamp SHALL be right-aligned in each event row and formatted as:
- `HH:mm` for events occurring today in the user's local timezone,
- `dd MMM HH:mm` for events in the current year but not today,
- `dd MMM yyyy` for events outside the current year.

#### Scenario: Timeline renders newest-first with human time
- **WHEN** the UI receives events from `/deals/{id}/events`
- **THEN** the timeline lists newest events first and each row shows right-aligned human-formatted time

### Requirement: State-based action panel
The deal detail UI SHALL show proposal actions only when valid for the current deal state and actor. For a deal in `DRAFT` or `NEGOTIATION`, only the latest-proposal recipient SHALL see `Edit`, `Approve`, and `Reject` actions. `Edit` SHALL allow changes to only `creative_text`, `start_at`, `creative_media_type`, and `creative_media_ref`; other proposal fields SHALL be view-only. In `REJECTED` and post-approval states, the negotiation action panel SHALL be hidden.

#### Scenario: Sender cannot act on own latest proposal
- **WHEN** the current user is the sender of the latest proposal
- **THEN** `Edit`, `Approve`, and `Reject` actions are not shown

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

### Requirement: Listing editor uses structured format inputs
The owner listing editor UI SHALL create and update formats using structured inputs only: `placement_type` selector (`post` or `story`), `exclusive_hours`, `retention_hours`, and `price`. It SHALL NOT require or expose free-form label input for listing formats.

#### Scenario: Owner adds structured post format
- **WHEN** an owner submits a format with `placement_type = post`, numeric `exclusive_hours`, numeric `retention_hours`, and `price`
- **THEN** the UI sends the structured payload and the new format appears in the editor list

### Requirement: Marketplace format cards show placement commitments
Marketplace format presentation SHALL display placement and timing commitments for each format (`placement_type`, `exclusive_hours`, `retention_hours`) together with `price` so advertisers can compare offers before selecting a format.

#### Scenario: Advertiser can compare format commitments
- **WHEN** an advertiser views a listing card with multiple formats
- **THEN** each format option shows placement type, exclusivity hours, retention hours, and price

### Requirement: Advertiser campaign workspace page
The UI SHALL render advertiser campaign creation and advertiser campaign list on the same screen. The campaign list SHALL be shown below the create form and SHALL provide per-campaign actions to open offers and delete campaign.

#### Scenario: Advertiser sees created campaign under form
- **WHEN** an advertiser successfully creates a campaign
- **THEN** the campaign appears in the workspace list below the create form without navigating to another page

### Requirement: Owner campaigns page and apply channel selection
The UI SHALL provide an owner campaigns page that lists discoverable active campaigns. Applying to a campaign SHALL require selecting one channel from the authenticated user's owned verified channels and SHALL capture structured proposal terms: `placement_type`, `exclusive_hours`, and `retention_hours`. If no owned verified channels exist, the UI SHALL block submission and show guidance to verify a channel first.

#### Scenario: Owner apply submits structured terms
- **WHEN** an owner applies to a campaign
- **THEN** the UI submits selected channel plus structured placement/exclusive/retention terms

### Requirement: Advertiser aggregated offers inbox page
The UI SHALL provide one advertiser offers page that lists offers across all advertiser campaigns in newest-first order. Each row SHALL expose campaign and proposal context and an action to accept the offer by submitting required creative fields and optional start datetime. The accept UI SHALL NOT require manual `ad_type` input and SHALL NOT require manual `price_ton` input when campaign defaults are available.

#### Scenario: Advertiser accepts offer without duplicate term fields
- **WHEN** advertiser accepts an offer from the aggregated inbox
- **THEN** the accept payload includes creative fields and optional `start_at` without requiring manual ad type or price entry

### Requirement: Post-accept redirect to deal detail
After successful offer acceptance, the UI SHALL navigate immediately to `/deals/:id` using the created deal id from accept response.

#### Scenario: Accept opens deal detail immediately
- **WHEN** advertiser accepts an offer successfully
- **THEN** the app redirects to `/deals/{created_deal_id}` in the same interaction flow

### Requirement: Delete campaign label and hidden semantics copy
The campaign action label SHALL be `Delete campaign`. The confirmation or helper copy SHALL explicitly state that campaign and related offers are removed from campaign pages, while existing accepted deals remain available in deal history/detail.

#### Scenario: Delete copy clarifies soft-hide behavior
- **WHEN** advertiser triggers campaign delete
- **THEN** UI copy explains hidden semantics before confirmation while keeping button label as `Delete campaign`

### Requirement: Marketplace channel-name navigation to stats
The advertiser marketplace UI SHALL render channel name/title in each listing card as a tappable navigation target to `/advertiser/channels/:channelId/stats`. It SHALL use `channel_id` from `GET /marketplace/listings` response as the route parameter.

#### Scenario: Advertiser opens stats by tapping channel title
- **WHEN** an advertiser taps the channel name/title on a marketplace listing card
- **THEN** the app navigates to `/advertiser/channels/:channelId/stats` for that listing's `channel_id`

### Requirement: Advertiser stats page partial-data rendering
The advertiser stats page SHALL render partial data without blocking the page. For metrics and charts with `availability = ready`, it SHALL render the value/chart. For chart sections with `availability = missing`, `async_pending`, or `error`, the default behavior SHALL be hidden sections. For scalar/value metrics with unavailable states, the page SHALL render a non-blocking placeholder.

#### Scenario: Missing and async metrics do not break page
- **WHEN** the stats response contains a mix of `ready`, `missing`, and `async_pending` metrics
- **THEN** the page renders available metrics, hides unavailable chart sections by default, and keeps unavailable scalar metrics non-blocking

### Requirement: Shared stats routes by role
The UI SHALL expose stats pages for both roles using role-scoped routes (`/advertiser/channels/:channelId/stats` and `/owner/channels/:channelId/stats`). Advertiser role SHALL access the advertiser route, owner role SHALL access the owner route, and route guards SHALL redirect cross-role deep links to the caller's role default route.

#### Scenario: Owner opens owner stats route
- **WHEN** a user with owner role opens `/owner/channels/:channelId/stats`
- **THEN** the page is accessible in read-only mode

#### Scenario: Owner opens advertiser stats deep link
- **WHEN** a user with owner role opens `/advertiser/channels/:channelId/stats`
- **THEN** the app redirects to `/owner`
