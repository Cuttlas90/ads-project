## Why

The current Start deal flow asks advertisers to manually type `creative_media_type` and Telegram `file_id`, which is not practical for normal users and causes avoidable deal creation failures. We need an upload-first path that obtains a valid Telegram `file_id` automatically, then creates the deal in `DRAFT` with that media reference.

## What Changes

- Add a pre-deal creative upload endpoint scoped to listing initiation (advertiser flow) that accepts image/video multipart files and returns `creative_media_ref` (`file_id`) plus `creative_media_type`.
- Keep listing-based deal creation in `DRAFT`, but formalize the required sequence as: upload media first, then call `POST /listings/{listing_id}/deals` with the returned media fields.
- Update the Start deal UI to remove manual `file_id` entry and use:
  - multiline creative text input
  - explicit media type selector (`image` / `video`)
  - file picker + upload action/status before enabling deal creation
- Keep Telegram media storage via private channel (`TELEGRAM_MEDIA_CHANNEL_ID`) and tighten environment/documentation clarity for channel setup and bot permissions.

## Capabilities

### New Capabilities

- None.

### Modified Capabilities

- `m11-ui-support`: Change Start deal requirements to an upload-first UX and update media upload behavior so advertisers can obtain a Telegram `file_id` before deal creation.
- `listing-management`: Add and define a listing-scoped creative upload endpoint used during deal initiation, including auth and validation requirements.

## Impact

- Backend API changes in listing/deal initiation paths to support pre-deal media upload responses consumed by marketplace deal creation.
- Frontend marketplace Start deal modal updates (form controls, upload state handling, validation, and submission ordering).
- Configuration and operations updates for `TELEGRAM_MEDIA_CHANNEL_ID` usage in `.env`/`.env.example`, including private channel and bot-admin prerequisites.
- Test updates for new upload flow (backend endpoint tests and frontend Start deal interaction tests).
