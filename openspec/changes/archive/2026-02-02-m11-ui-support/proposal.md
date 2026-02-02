## Why

The M11 UI requires end-to-end, Telegram-native flows that depend on missing backend capabilities (deal inbox/timeline, creative approval before funding, role preference, and media upload). Without these, the UI cannot call real APIs or reflect the correct deal state progression.

## What Changes

- Add backend read endpoints for deals (inbox, detail, timeline) and escrow status to power state-based UI.
- Introduce explicit creative approval flow with a changes-requested state and gate escrow funding until creative approval.
- Add Telegram media upload endpoint to obtain `file_id` for creative assets via a private storage channel.
- Persist user role preference and expose it in `/auth/me` for auto-redirect; UI informs users they can change role later in Profile.
- Extend marketplace listings to include format IDs for deal creation; add a listing read endpoint for the editor.
- Build the M11 Telegram-native UI screens (owner + advertiser journeys) wired to the new and existing backend APIs.

## Capabilities

### New Capabilities
- `m11-ui-support`: Backend capabilities required for the M11 Telegram-native UI flows (deal inbox/timeline, creative approval gating, role preference, media upload).

### Modified Capabilities
- `deal-management`: Add explicit creative approval and changes-requested states and transitions; align deal lifecycle with creative-first funding.
- `escrow-management`: Gate escrow init/tonconnect to `CREATIVE_APPROVED` and align funding transition timing.
- `marketplace-discovery`: Include listing format IDs in marketplace listing responses.
- `listing-management`: Add listing read endpoint(s) to support the listing editor UI.
- `telegram-auth`: Persist and return `preferred_role` for auto-redirect.
- `telegram-integration`: Support media upload to Telegram with `TELEGRAM_MEDIA_CHANNEL_ID`.
- `ton-integration`: Gate TONConnect payloads to `CREATIVE_APPROVED` deals.

## Impact

- Backend: new endpoints, FSM transition table changes, and a user preference field (migration required).
- Telegram Bot API: new media upload path to a private storage channel.
- Frontend: role-based routing decisions, creative approval flow UX, and funding after approval.
- Frontend: implement polished Telegram-style UI pages, components, and API integration for the full M11 journey.
