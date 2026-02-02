## Context

The M11 UI must deliver full Telegram-native owner + advertiser journeys. The backend currently lacks several read and workflow endpoints (deal inbox/detail/timeline, escrow status, creative approval gating, role preference). Deal state progression must remain explicit (FSM table only), funding must occur after creative approval, and all auth must rely on Telegram initData. The UI will be Vue 3 + Vite + TypeScript with Telegram theme variables and TONConnect via `@tonconnect/ui`.

## Goals / Non-Goals

**Goals:**
- Provide backend capabilities required by the M11 UI: deal inbox/detail/timeline, creative approval workflow, escrow gating, media upload to Telegram, role preference persistence, and listing/marketplace adjustments.
- Ensure deal lifecycle is explicit and creative-first (approval before funding) while preserving the transition table as the single source of truth.
- Define a clear, secure media upload path that returns Telegram `file_id` for creatives.
- Enable UI auto-redirect based on persisted role and communicate role changeability in Profile.

**Non-Goals:**
- Implement admin tooling or any manual verification paths.
- Introduce alternative auth mechanisms (JWT, sessions, cookies, OAuth).
- Expand beyond TON payments or add fiat support.

## Decisions

1) **FSM update with explicit creative edit loop**
- **Decision:** Add `CREATIVE_CHANGES_REQUESTED` and enforce transitions:
  - `ACCEPTED -> CREATIVE_SUBMITTED` (owner)
  - `CREATIVE_SUBMITTED -> CREATIVE_APPROVED` (advertiser)
  - `CREATIVE_SUBMITTED -> CREATIVE_CHANGES_REQUESTED` (advertiser)
  - `CREATIVE_CHANGES_REQUESTED -> CREATIVE_SUBMITTED` (owner)
  - `CREATIVE_APPROVED -> FUNDED` (system, after escrow confirmation)
- **Rationale:** Keeps creative approval explicit and audit-friendly, avoids implicit “request edits” semantics, and aligns funding after approval.
- **Alternatives considered:** Reusing `FUNDED` or `CREATIVE_SUBMITTED` with implicit events only; rejected due to the “explicit FSM only” constraint.

2) **Escrow gating moved to creative approval**
- **Decision:** `POST /deals/{id}/escrow/init` and `POST /deals/{id}/escrow/tonconnect-tx` require `CREATIVE_APPROVED` (not `ACCEPTED`). Funding confirmation transitions to `FUNDED`.
- **Rationale:** Enforces the required flow: advertiser approves creative before funding, matching UI expectations and business policy.
- **Alternative:** Allow funding at `ACCEPTED` and rely on UI to block; rejected because backend must be authoritative.

3) **Deal timeline and inbox endpoints**
- **Decision:** Add `GET /deals` (role-filtered), `GET /deals/{id}`, `GET /deals/{id}/events`, and `GET /deals/{id}/escrow`.
- **Rationale:** UI needs read access for inbox, detail, timeline, and funding status without embedding business logic.
- **Alternative:** Push timeline to front-end by combining multiple endpoints; rejected for complexity and missing data coupling.

4) **Telegram media upload via private storage channel**
- **Decision:** Introduce `TELEGRAM_MEDIA_CHANNEL_ID` and `POST /deals/{id}/creative/upload` that uploads to Bot API and returns `creative_media_ref` = Telegram `file_id`.
- **Rationale:** Ensures consistent Telegram-native media handling and aligns with creative storage requirements.
- **Alternative:** Client uploads media elsewhere and passes URL; rejected because `creative_media_ref` is specified as Telegram `file_id`.

5) **User role preference persisted on user record**
- **Decision:** Add `preferred_role` field on `users` and expose `PUT /users/me/preferences`; include in `/auth/me`.
- **Rationale:** Enables auto-redirect and avoids extra round trips on app load.
- **Alternative:** Store preference only on client; rejected because UI should survive reinstall/device changes.

6) **Marketplace formats include format_id**
- **Decision:** Add `id` to `formats[]` in `GET /marketplace/listings` response.
- **Rationale:** Required to create deals from listing formats without extra fetch.

7) **Listing editor read endpoint**
- **Decision:** Add `GET /channels/{channel_id}/listing` returning listing + formats for owners.
- **Rationale:** Simplifies editor initialization and prevents extra queries.

8) **Deal inbox pagination and state filtering**
- **Decision:** `GET /deals` supports pagination and `state` filtering.
- **Rationale:** Enables scalable inbox and state-based views without loading all deals.

9) **Timeline cursor pagination**
- **Decision:** `GET /deals/{id}/events` supports cursor pagination for long histories.
- **Rationale:** Avoids large payloads on heavily active deals and keeps UI responsive.

10) **Listing missing response shape**
- **Decision:** `GET /channels/{channel_id}/listing` returns an empty response with `has_listing = false` when no listing exists.
- **Rationale:** Simplifies editor UX by avoiding error handling for a normal “no listing yet” state.

11) **Bot messaging CTA (no in-app chat)**
- **Decision:** Provide a UI button that deep-links the user to the system bot for deal messaging (e.g., `t.me/<bot>?start=deal_<id>`).
- **Rationale:** Maintains the no in-app chat constraint while enabling communication.

12) **Frontend test stack**
- **Decision:** Use Vitest for frontend unit tests and Playwright for end-to-end UI flows.
- **Rationale:** Vitest fits the Vite stack for fast component/unit testing; Playwright covers critical Telegram UI journeys.

## Risks / Trade-offs

- **[Risk] Event ordering ambiguity in timeline** → **Mitigation:** Sort by `created_at` + deterministic tie-breaker (e.g., event id).
- **[Risk] Media channel leakage** → **Mitigation:** Restrict `TELEGRAM_MEDIA_CHANNEL_ID` to private, do not expose channel IDs to clients, enforce owner-only upload.
- **[Risk] FSM regressions** → **Mitigation:** Update transition table tests and add guardrails for creative/escrow endpoints.
- **[Risk] Client confusion about funding order** → **Mitigation:** UI state-based CTA panel and clear copy (approval required before funding).
- **[Risk] Preference field migration** → **Mitigation:** Add nullable column with safe default and backfill as needed.

## Migration Plan

- Add `preferred_role` column to `users` (nullable) via Alembic.
- Update deal FSM transition table and add `CREATIVE_CHANGES_REQUESTED` enum constant.
- Update escrow endpoints to require `CREATIVE_APPROVED`.
- Introduce new API routes for deals, timeline, escrow status, listing read, and creative upload.
- Add `TELEGRAM_MEDIA_CHANNEL_ID` configuration and validate on upload.

## Open Questions

- None.
