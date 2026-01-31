## Context
We need a single canonical Deal entity that merges listing-based and campaign-based entry points. The deal lifecycle must follow the project’s canonical state list and be driven by an explicit FSM with audit logging. Messaging between advertiser and channel owner must be bot-mediated and stored.

## Goals / Non-Goals
- Goals:
  - Provide `deals` and `deal_events` persistence with a strict FSM and transition table.
  - Enforce state changes exclusively through `apply_transition()` and log every transition.
  - Support two entry points that create deals in DRAFT with role-specific edit rules.
  - Relay deal messages via the Telegram bot and store each forward/counter in the DB.
- Non-Goals:
  - Implement escrow funding, posting, or verification flows beyond FSM wiring.
  - Build a Mini App chat UI (messages are bot-mediated only).
  - Define media upload/storage infrastructure (use lightweight references only).

## Decisions
- **FSM compliance:** Keep the canonical state list from `openspec/project.md`. To honor “no state skipping” while allowing a DRAFT acceptance flow, the accept action MAY perform an intermediate transition (DRAFT → NEGOTIATION → ACCEPTED) in one request, writing both events.
- **Event storage:** Use `deal_events` for all audit activity (state transitions, proposals/counters, messages). Each event stores `event_type`, `actor_id`, optional `from_state`/`to_state`, and a JSON payload.
- **Source typing:** Deals store a `source_type` (`listing` | `campaign`) plus the relevant foreign keys. Constraints ensure exactly one source is set.
- **Creative + posting params:** Store `creative_text`, `creative_media_type`, `creative_media_ref`, and `posting_params` (JSON). This supports the required “image/video + text” and a flexible posting parameter without introducing file upload infrastructure.
- **Role-specific draft edits:** Listing-sourced deals lock price/ad_type to the listing format. Campaign-sourced deals allow advertisers to set price/ad_type; channel owners may counter only creative/posting params.

## Risks / Trade-offs
- Using `deal_events` for messages and transitions simplifies schema but requires clear event typing to avoid ambiguity.
- The DRAFT → NEGOTIATION → ACCEPTED auto-advance is slightly more complex but preserves the canonical FSM requirement.

## Migration Plan
1. Add Alembic migration for `deals` and `deal_events` tables and update `campaign_applications.status` constraints.
2. Introduce shared deal models and FSM service module with `apply_transition()`.
3. Add API endpoints for deal creation, draft updates, acceptance, and messaging.
4. Add tests for FSM transitions, endpoint validation, and event logging.

## Open Questions
- None; assume creative media is stored as a reference string and posting params are a JSON object.
