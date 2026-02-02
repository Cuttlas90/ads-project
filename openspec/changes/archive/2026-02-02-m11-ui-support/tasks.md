## 1. Data Model & Migrations

- [x] 1.1 Add `preferred_role` to `users` (nullable) and create Alembic migration
- [x] 1.2 Add `CREATIVE_CHANGES_REQUESTED` to DealState enum and update DB constraints/migration if needed

## 2. Deal FSM & Core Endpoints

- [x] 2.1 Update deal transition table to include creative submit/approve/request-edits and funding after approval
- [x] 2.2 Add `GET /deals` with role + state filtering and pagination
- [x] 2.3 Add `GET /deals/{id}` with participant display fields
- [x] 2.4 Add `GET /deals/{id}/events` with merged deal/escrow timeline and cursor pagination
- [x] 2.5 Add creative endpoints: `POST /deals/{id}/creative/submit`, `/approve`, `/request-edits`

## 3. Escrow & TONConnect Adjustments

- [x] 3.1 Gate `POST /deals/{id}/escrow/init` to `CREATIVE_APPROVED`
- [x] 3.2 Gate `POST /deals/{id}/escrow/tonconnect-tx` to `CREATIVE_APPROVED`
- [x] 3.3 Add `GET /deals/{id}/escrow` for funding status polling

## 4. Marketplace & Listings Read Paths

- [x] 4.1 Include `format_id` in `GET /marketplace/listings` formats
- [x] 4.2 Add `GET /channels/{channel_id}/listing` returning listing + formats or `has_listing = false`

## 5. Telegram Media Upload Support

- [x] 5.1 Add `TELEGRAM_MEDIA_CHANNEL_ID` to settings and config validation
- [x] 5.2 Implement Bot API media upload helper returning `file_id`
- [x] 5.3 Add `POST /deals/{id}/creative/upload` to return `creative_media_ref`

## 6. Auth & Preferences

- [x] 6.1 Extend `/auth/me` response to include `preferred_role`
- [x] 6.2 Add `PUT /users/me/preferences` endpoint

## 7. Frontend Foundation (Telegram-native)

- [x] 7.1 Add Telegram theme tokens and global styles; wire to app entry
- [x] 7.2 Build Telegram UI component library (`TgButton`, `TgCard`, `TgInput`, `TgList`, `TgBadge`, `TgModal`, `TgSkeleton`, `TgToast`, `TgStatePanel`)
- [x] 7.3 Configure router + layout (top bar, safe area, optional bottom nav)
- [x] 7.4 Implement Pinia stores (auth, channels, listings, deals, campaigns)
- [x] 7.5 Implement API client with initData header + service modules

## 8. Owner Journey Screens

- [x] 8.1 Channels list (skeleton/empty/error) + add channel flow
- [x] 8.2 Channel verify screen with permission errors
- [x] 8.3 Listing editor with formats CRUD and validation
- [x] 8.4 Owner deals inbox
- [x] 8.5 Owner creative submit flow (upload -> submit)

## 9. Advertiser Journey Screens

- [x] 9.1 Marketplace browse with filters, search, and start-deal flow
- [x] 9.2 Campaign request create (TON-only budget)
- [x] 9.3 Advertiser deals inbox
- [x] 9.4 Advertiser creative approve / request edits flow
- [x] 9.5 Funding flow using TONConnect and escrow polling

## 10. Shared Deal Detail

- [x] 10.1 Deal detail page with timeline and state-based action panel
- [x] 10.2 Bot messaging deep-link CTA on deal detail

## 11. Backend Tests

- [x] 11.1 Add FSM transition tests for creative submit/approve/request-edits and funding after approval
- [x] 11.2 Add deal inbox tests for role + state filtering and pagination
- [x] 11.3 Add deal detail tests with participant display fields and authorization checks
- [x] 11.4 Add timeline cursor pagination tests (deal + escrow events ordering)
- [x] 11.5 Add creative endpoints tests (submit/approve/request-edits)
- [x] 11.6 Add escrow gating tests for creative-approved requirement and escrow status endpoint
- [x] 11.7 Add marketplace listings test for `format_id` presence
- [x] 11.8 Add listing read endpoint tests (`has_listing=false` behavior)
- [x] 11.9 Add user preference endpoint tests and `/auth/me` preferred_role response
- [x] 11.10 Add Telegram media upload helper/endpoint tests (mock Bot API, file_id returned)

## 12. QA & Tooling

- [x] 12.1 Update eslint/prettier config (if missing) and fix lint issues
- [x] 12.2 Add Vitest configuration and base unit test setup for frontend
- [x] 12.3 Add Playwright configuration for end-to-end UI flows
- [x] 12.4 Ensure `npm run build` passes
- [x] 12.5 Run backend tests impacted by FSM/endpoint changes
