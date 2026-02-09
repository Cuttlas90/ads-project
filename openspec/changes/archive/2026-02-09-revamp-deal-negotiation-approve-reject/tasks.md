## 1. Backend Negotiation and FSM

- [x] 1.1 Update deal transition definitions and action semantics so proposal approval from `DRAFT`/`NEGOTIATION` finalizes to `CREATIVE_APPROVED`.
- [x] 1.2 Add `POST /deals/{id}/reject` with latest-proposal counterparty authorization and transition to `REJECTED`.
- [x] 1.3 Enforce latest-proposal counterparty checks consistently for approve/reject/edit actions.
- [x] 1.4 Update `PATCH /deals/{id}` proposal event payload generation to persist full proposal snapshots (not partial deltas).
- [x] 1.5 Add state guard to `POST /deals/{id}/messages` so only `DRAFT`/`NEGOTIATION` can send messages.

## 2. Timeline and API Contract

- [x] 2.1 Change `/deals/{id}/events` ordering to reverse chronological (newest first).
- [x] 2.2 Update cursor encoding/decoding and page slicing logic so `next_cursor` fetches older events in descending mode.
- [x] 2.3 Add/adjust route and service tests for descending ordering, cursor continuation, and mixed deal/escrow event merges.

## 3. Frontend Deal Detail UX

- [x] 3.1 Update deal timeline rendering in `DealDetailView` to show right-aligned human-formatted timestamps (`HH:mm`, `dd MMM HH:mm`, `dd MMM yyyy`).
- [x] 3.2 Add event detail interaction on tap: message-text view for `message` events and proposal-parameter view for `proposal` events.
- [x] 3.3 Implement latest-proposal-recipient action panel (`Edit`, `Approve`, `Reject`) in deal detail.
- [x] 3.4 Restrict proposal editing UI to `creative_text`, `start_at`, `creative_media_type`, and `creative_media_ref`; keep other fields read-only.
- [x] 3.5 Remove/bypass legacy creative submit/review navigation from negotiation flows and keep funding path from `CREATIVE_APPROVED` intact.

## 4. Data and Verification

- [x] 4.1 Reset non-production `deal_events` test data where needed to avoid mixed legacy/new proposal payload shapes. (No migration/backfill added; this remains an operational cleanup step for disposable non-production data.)
- [x] 4.2 Update backend tests for approve/reject state transitions, terminal reject behavior, and message blocking after reject.
- [x] 4.3 Update frontend tests for timeline formatting/order, event tap behavior, and action visibility by role/latest proposal ownership.
- [x] 4.4 Run targeted backend and frontend test suites and resolve regressions before implementation sign-off.
