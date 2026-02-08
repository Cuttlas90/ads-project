## Context

The current marketplace Start deal modal requires advertisers to manually enter `creative_media_type` and a Telegram `file_id`, then submits `POST /listings/{listing_id}/deals`. This is inconsistent with normal user expectations and leads to invalid payloads.

The codebase already has a Telegram upload helper (`shared/telegram/bot_api.py`) and an upload endpoint, but that endpoint is deal-scoped and owner-only (`POST /deals/{deal_id}/creative/upload`), which cannot be used before a listing deal exists. The desired flow is to upload media first, receive Telegram `file_id`, then create the listing-based deal in `DRAFT` with returned media fields.

Constraints:
- Preserve current deal FSM behavior and creation semantics (`DRAFT` on listing deal creation).
- Keep Telegram Bot API as the media source and `creative_media_ref` as Telegram `file_id`.
- Avoid database schema changes unless strictly necessary.

## Goals / Non-Goals

**Goals:**
- Provide an advertiser-usable pre-deal upload API for marketplace initiation.
- Make Start deal UX upload-first and remove manual `file_id` entry.
- Ensure media type/ref used in create-deal payload come from server upload response.
- Keep operational requirements explicit for `TELEGRAM_MEDIA_CHANNEL_ID` and bot permissions.

**Non-Goals:**
- Redesigning deal FSM transitions or approval/funding logic.
- Replacing Telegram `file_id` with external URLs or third-party storage.
- Implementing bot-chat media ingestion in this change.
- Adding new background workers or asynchronous media processing.

## Decisions

1) Introduce listing-scoped pre-deal upload endpoint  
- **Decision:** Add `POST /listings/{listing_id}/creative/upload` for authenticated users initiating listing deals. Accept multipart file, derive `image|video` from content type, upload via existing Bot API helper, return `{ creative_media_ref, creative_media_type }`.  
- **Rationale:** Keeps deal creation API contract intact while enabling upload before deal creation. Reuses proven Telegram upload path and avoids creating placeholder deals.  
- **Alternatives considered:**  
- Reuse `/deals/{id}/creative/upload` by creating a temporary deal first; rejected due to unnecessary lifecycle side effects.  
- Allow client to submit arbitrary `file_id`; rejected due to poor UX and high validation failure risk.

2) Keep deal creation synchronous and media-required  
- **Decision:** `POST /listings/{listing_id}/deals` continues requiring `creative_text`, `creative_media_type`, and `creative_media_ref`; UI sequence changes, not deal create semantics.  
- **Rationale:** Preserves current backend invariants and downstream posting assumptions while improving input quality upstream.  
- **Alternatives considered:**  
- Make media optional at create time and defer creative attachment; rejected because it changes business semantics and requires wider FSM/UI updates.

3) Upload response is source of truth for media fields  
- **Decision:** Start deal uses media fields returned by upload response when calling create-deal API. The media-type selector remains user-facing guidance/constraint, but backend response controls final payload values.  
- **Rationale:** Prevents type/ref mismatches and keeps payload consistent with Telegram’s accepted media.  
- **Alternatives considered:**  
- Trust user-entered media type during create call; rejected because it recreates current failure mode.

4) Marketplace modal UX update without global modal regression  
- **Decision:** Update Start deal UI only: multiline creative text, explicit media type selector, file picker/upload status, and disabled "Start deal" until upload success. Adjust width/presentation for this modal without globally widening all modal panels.  
- **Rationale:** Solves the immediate usability issue while minimizing unintended layout changes in unrelated modals.  
- **Alternatives considered:**  
- Increase global modal max width; rejected due to cross-screen UI risk.

5) Reuse existing Telegram upload helper and config contract  
- **Decision:** Continue using `BotApiService.upload_media` and `TELEGRAM_MEDIA_CHANNEL_ID` as the storage target requirement. Add clearer env/docs guidance for private channel chat ID and bot admin permissions.  
- **Rationale:** Avoids duplicate Telegram integration logic and keeps one operational path for media upload behavior.  
- **Alternatives considered:**  
- Route uploads through bot long-polling message flow; rejected for larger scope and additional state management needs.

## Risks / Trade-offs

- **[Risk] Orphan uploaded media (upload succeeds, deal creation abandoned)** -> **Mitigation:** Accept as operational trade-off for now; keep uploads in private storage channel and monitor volume.  
- **[Risk] Misconfigured Telegram media channel (`TELEGRAM_MEDIA_CHANNEL_ID`, missing bot rights)** -> **Mitigation:** Preserve explicit gateway error responses and document setup prerequisites in env examples/runbook notes.  
- **[Risk] Large uploads increase request latency/timeouts** -> **Mitigation:** Enforce content-type validation, apply reasonable size limits at API layer, and surface actionable error messages.  
- **[Risk] UI state inconsistency when user changes listing/format after upload** -> **Mitigation:** Reset uploaded media state whenever selected listing/format changes and require fresh upload before submit.

## Migration Plan

1. Add/confirm environment documentation for `TELEGRAM_MEDIA_CHANNEL_ID` (private channel chat ID format and bot admin requirement).  
2. Implement listing-scoped creative upload endpoint + tests (success, invalid media, unauthorized, Telegram failure).  
3. Update marketplace Start deal modal to upload-first flow + tests for disabled/enabled submission and payload correctness.  
4. Deploy backend and frontend together to avoid temporary UX/API mismatch.  
5. Rollback strategy: redeploy previous frontend/backend versions; no database rollback required.

## Open Questions

- What explicit max upload size should be enforced for image/video to balance Telegram limits and API reliability?
