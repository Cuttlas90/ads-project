## 1. Backend API Surface

- [x] 1.1 Add or reuse a response schema for listing-scoped creative upload returning `creative_media_ref` and `creative_media_type`
- [x] 1.2 Add `POST /listings/{listing_id}/creative/upload` route wiring in listings API
- [x] 1.3 Ensure create-deal-from-listing behavior remains `DRAFT` and continues requiring creative media fields

## 2. Listing-Scoped Upload Behavior

- [x] 2.1 Validate listing existence and active state before accepting upload
- [x] 2.2 Validate uploaded file media type as `image/*` or `video/*` and reject others with HTTP 400
- [x] 2.3 Upload accepted media through `BotApiService.upload_media` and return Telegram `file_id` + normalized media type
- [x] 2.4 Map Telegram/config failures to controlled HTTP 502 responses

## 3. Marketplace Start Deal UX (Upload-First)

- [x] 3.1 Replace free-text media type input with explicit `image`/`video` selector
- [x] 3.2 Replace manual media ref input with file-picker upload flow and visible upload status/error states
- [x] 3.3 Update creative text input to multiline entry in Start deal modal
- [x] 3.4 Block "Start deal" submission until upload has succeeded and media fields are present
- [x] 3.5 Submit listing deal payload using media fields returned by upload response
- [x] 3.6 Reset uploaded media state when selected listing/format changes or modal closes

## 4. Configuration and Operational Clarity

- [x] 4.1 Add `TELEGRAM_MEDIA_CHANNEL_ID` example entry to `.env.example`
- [x] 4.2 Document required private channel setup and bot admin permissions for media upload

## 5. Test Coverage

- [x] 5.1 Add backend tests for listing-scoped upload success, inactive listing rejection, invalid media type, and Telegram failure handling
- [x] 5.2 Add/adjust frontend tests for Start deal upload-first behavior and payload correctness
- [x] 5.3 Keep existing deal-scoped owner upload tests passing as regression coverage

## 6. Verification

- [x] 6.1 Run targeted backend and frontend test suites covering new upload-first flow
- [x] 6.2 Validate OpenSpec change artifacts are complete and consistent before implementation handoff
