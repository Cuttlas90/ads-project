## MODIFIED Requirements

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
- **GIVEN** a valid deal media file
- **WHEN** the channel owner uploads via `/deals/{id}/creative/upload`
- **THEN** the response includes `creative_media_ref` set to the Telegram `file_id` and `creative_media_type`

## ADDED Requirements

### Requirement: Start deal flow uses upload-first creative capture
The marketplace Start deal UI SHALL require creative media upload before submitting deal creation. It SHALL provide a multiline creative text input, an explicit media type selector (`image` or `video`), and a media file picker. It SHALL NOT require manual entry of Telegram `file_id`. On successful upload, it SHALL use returned `creative_media_ref` and `creative_media_type` in the subsequent `POST /listings/{listing_id}/deals` request, which SHALL continue creating the deal in `DRAFT`.

#### Scenario: Start deal is blocked until upload succeeds
- **WHEN** the user has not completed a successful media upload in the Start deal modal
- **THEN** the UI prevents sending `POST /listings/{listing_id}/deals`

#### Scenario: Deal creation uses upload response fields
- **WHEN** media upload succeeds and the user starts a deal
- **THEN** the UI sends `creative_media_ref` and `creative_media_type` from the upload response in `POST /listings/{listing_id}/deals`
