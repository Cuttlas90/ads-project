## Context

Current deal negotiation mixes multiple UX paths and state semantics:
- Timeline is rendered oldest-first with raw ISO timestamps.
- Proposal actions are not performed in-context from timeline events.
- `POST /deals/{id}/accept` currently lands in `ACCEPTED`, then legacy creative submit/review screens are required before funding.
- Proposal events from `PATCH /deals/{id}` store changed fields only, so proposal history is not self-contained.
- HTTP messaging does not gate by negotiation state, so post-reject behavior is inconsistent with closed-conversation expectations.

The target product behavior is a negotiation-first detail page where latest proposal recipient can `Edit`, `Approve`, or `Reject` directly, with approval finalizing to `CREATIVE_APPROVED` and rejection terminal.

## Goals / Non-Goals

**Goals:**
- Make deal timeline readable and action-oriented (newest-first + human timestamp formats + event detail interaction).
- Finalize negotiations directly from proposal actions (`Approve` -> `CREATIVE_APPROVED`, `Reject` -> `REJECTED`).
- Ensure newly written proposal events always carry a full proposal snapshot.
- Enforce closed conversation behavior after reject by blocking participant message sends.
- Keep escrow funding contract unchanged (`CREATIVE_APPROVED` -> `FUNDED` on confirmed deposit).

**Non-Goals:**
- Redesign escrow state machine, posting workers, or payout verification logic.
- Introduce new payment rails, manual verification paths, or non-Telegram auth.
- Backfill historical proposal events to reconstruct full snapshots.
- Preserve legacy creative submit/review UX routes as primary negotiation path.

## Decisions

1. Keep endpoint path `POST /deals/{id}/accept` but redefine it as proposal approval.
- Outcome: counterparty approval transitions to `CREATIVE_APPROVED` directly instead of `ACCEPTED`.
- Rationale: minimizes API surface churn while delivering the requested behavior.
- Alternative: add new `/approve` endpoint and deprecate `/accept`. Rejected to avoid client routing split during transition.

2. Add explicit `POST /deals/{id}/reject` for negotiation closure.
- Outcome: counterparty can reject latest proposal in `DRAFT`/`NEGOTIATION`, transitioning to `REJECTED`.
- Rationale: endpoint-level clarity and explicit audit trail for terminal rejection.
- Alternative: overload `PATCH /deals/{id}` with reject flags. Rejected because it weakens FSM clarity.

3. Enforce latest-proposal recipient authorization for approve/reject/edit actions.
- Outcome: sender of latest proposal cannot self-approve/reject, matching negotiation contract.
- Rationale: mirrors existing accept counterparty check and prevents unilateral finalization.
- Alternative: allow either party to approve/reject. Rejected due to ambiguous ownership of latest terms.

4. Store full proposal snapshot for each new `proposal` event.
- Outcome: proposal payload always includes complete negotiable terms (`price_ton`, `ad_type`, placement terms, creative fields, `start_at`, `posting_params`).
- Rationale: old proposal details can be displayed without reconstruction logic.
- Alternative: keep deltas and reconstruct on read. Rejected due to read complexity and fragile history.

5. Switch timeline API ordering and cursor semantics to reverse chronological.
- Outcome: `/deals/{id}/events` returns newest-first; `next_cursor` points to older items.
- Rationale: aligns with chat/timeline UX and requested “all time” descending view.
- Alternative: keep ascending API and reverse in UI only. Rejected because pagination would still be oldest-first at source.

6. Gate message sending to open negotiation states only.
- Outcome: `POST /deals/{id}/messages` accepts only `DRAFT`/`NEGOTIATION`; rejected deals cannot exchange new messages.
- Rationale: enforces terminal close behavior consistently across UI and API.
- Alternative: UI-only block. Rejected because API and bot paths could bypass UI restrictions.

## Risks / Trade-offs

- [Risk] Existing tests and clients assume `accept` leads to `ACCEPTED`. -> Mitigation: update tests and UI copy together; document behavior as breaking in proposal/spec.
- [Risk] Legacy states (`ACCEPTED`, `CREATIVE_SUBMITTED`, `CREATIVE_CHANGES_REQUESTED`) may remain in code but become rarely used. -> Mitigation: keep FSM explicit and mark legacy creative screens as bypassed; optionally remove in a follow-up cleanup change.
- [Risk] Changing timeline ordering can break cursor consumers. -> Mitigation: update frontend events service and add pagination tests for “older page” semantics.
- [Risk] Historical proposal events are incomplete. -> Mitigation: accept no-backfill strategy and allow resetting non-production `deal_events` test data.

## Migration Plan

1. Backend FSM and routes:
- Update transition table and action handling for approve/reject semantics.
- Add reject endpoint and state guards for message sends.
- Update proposal event write-path to persist full snapshots.

2. Timeline API:
- Change merged event sort and cursor comparisons for descending pagination.
- Update backend tests for ordering and cursor continuation.

3. Frontend deal detail:
- Render human-formatted right-aligned timestamps.
- Add event-tap detail view for proposal/message.
- Add latest-proposal recipient action panel (`Edit`, `Approve`, `Reject`) and remove legacy creative-review path usage from negotiation.

4. Data handling in non-production:
- Optionally clear old `deal_events` test data before QA runs to avoid mixed snapshot shapes.

5. Validation:
- Run backend FSM/routes/timeline/messaging tests and frontend deal-detail tests for action availability and formatting behavior.

## Open Questions

- Resolved: retain legacy creative submit/review routes temporarily as compatibility-only paths, and add a follow-up cleanup note to remove them later.
- Resolved: use auto-load on scroll as the default behavior for large timelines.
