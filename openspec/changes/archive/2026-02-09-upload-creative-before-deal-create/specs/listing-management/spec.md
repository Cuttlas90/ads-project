## ADDED Requirements

### Requirement: Listing-scoped creative upload endpoint
The system SHALL expose `POST /listings/{listing_id}/creative/upload` requiring authentication to support listing deal initiation before a deal record exists. It SHALL validate that the listing exists and is active. It SHALL accept multipart media (`image` or `video`) only, upload accepted files to the Telegram Bot API media channel configured by `TELEGRAM_MEDIA_CHANNEL_ID`, and return `{ creative_media_ref, creative_media_type }` where `creative_media_ref` is the Telegram `file_id`.

#### Scenario: Active listing upload succeeds
- **WHEN** an authenticated user uploads a valid image or video for an active listing
- **THEN** the response is HTTP 200 with `creative_media_ref` as Telegram `file_id` and matching `creative_media_type`

#### Scenario: Inactive listing upload is rejected
- **WHEN** a user uploads media for an inactive listing
- **THEN** the response is HTTP 400 and media is not accepted

#### Scenario: Invalid media type is rejected
- **WHEN** a user uploads a non-image and non-video file
- **THEN** the response is HTTP 400 with an invalid media type error

### Requirement: Listing-scoped upload failures are controlled
The listing-scoped upload endpoint SHALL return controlled API errors for Telegram upload and configuration failures. It SHALL return HTTP 502 when Telegram upload fails or required Telegram upload configuration is unavailable.

#### Scenario: Telegram failure surfaces as gateway error
- **WHEN** Telegram media upload fails during `/listings/{listing_id}/creative/upload`
- **THEN** the response is HTTP 502 with a controlled failure detail
