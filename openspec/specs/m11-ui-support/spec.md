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
The UI SHALL inform users on the role picker screen that the choice can be changed later in Profile.

#### Scenario: Role picker explains changeability
- **WHEN** a new user opens the landing role picker
- **THEN** the screen states that the role can be changed later in Profile
