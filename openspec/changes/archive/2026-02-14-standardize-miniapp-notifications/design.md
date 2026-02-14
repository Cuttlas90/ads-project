## Context

The current UI feedback model is fragmented:
- `TgToast` exists but is not used as a global pattern.
- Page-level `TgStatePanel` is used for many errors, including errors produced inside modal flows.
- Modal success is sometimes shown as `TgBadge`, which does not behave like a notification channel.
- TONConnect action notifications can appear with a different visual language (for example transaction-sent cards), creating mixed feedback patterns in the same flow.

This change is frontend-cross-cutting because it touches shared UI primitives, app shell composition, flow-level error handling, and Telegram runtime theming behavior.

## Goals / Non-Goals

**Goals:**
- Introduce one explicit notification taxonomy and event routing policy across Mini App flows.
- Ensure a single event is surfaced through one intended channel (no duplicated feedback).
- Keep hard blockers explicit (blocking modal) while keeping recoverable issues local to the active context.
- Normalize funding flow feedback so wallet gate, transaction submission, and escrow progression are clearly separated.
- Make notification colors/theme react to `Telegram.WebApp.themeParams` changes at runtime.

**Non-Goals:**
- Redesigning all page layouts or typography.
- Changing backend error payload schema or error taxonomy.
- Replacing TONConnect wallet confirmation UX.
- Modifying deal FSM/business rules.

## Decisions

1. Adopt a four-level notification taxonomy
- Decision: classify feedback into `field`, `local-inline`, `global-toast`, and `blocking-modal`.
- Rationale: each class maps to user intent and urgency, avoiding overloaded one-size-fits-all error panels.
- Alternatives considered:
  - Toast-only model for all feedback.
  - Rejected because form/modal validation and blockers need persistent, contextual UI.

2. Enforce context ownership and isolation
- Decision: modal-origin events stay modal-local; page load failures stay page-local; field validation stays field-local.
- Rationale: users should not see modal failures rewritten as page load failures.
- Alternatives considered:
  - Route all errors through one page-level panel.
  - Rejected due to context loss and misleading copy.

3. Introduce a single global toast host in app shell
- Decision: render one toast stack at shell level, anchored near the topbar (including compact devices), with max-visible cap and tone-based auto-dismiss for non-blocking events.
- Rationale: predictable placement and consistent behavior across routes.
- Alternatives considered:
  - Anchor above bottom nav.
  - Rejected to keep ephemeral feedback near the primary reading focus and away from nav affordances.
  - Per-view toasts.
  - Rejected because it duplicates logic and causes inconsistent stacking/position.

4. Funding flow notification partitioning
- Decision: keep wallet-missing as blocking modal; use inline local alert for escrow/init/poll failures; use global toast for transaction submitted and other transient progress cues.
- Rationale: wallet absence is a hard prerequisite, while escrow/network issues are recoverable and should keep user in context.
- Alternatives considered:
  - Treat every funding error as blocking modal.
  - Rejected because it interrupts retries and overstates recoverable failures.

5. Harmonize TONConnect action feedback with app policy
- Decision: fully app-handle TONConnect action feedback (`before`, `success`, `error`) in app-owned channels; keep wallet connect/signing confirmation UX TONConnect-native.
- Rationale: removes mixed/duplicate notifications and makes notification behavior deterministic across all flows.
- Alternatives considered:
  - Keep TONConnect action `error` notification while app handles `before/success`.
  - Rejected to avoid split responsibility and conflicting recovery guidance.
  - Keep full TONConnect notifications and add app notifications.
  - Rejected due to duplicate “transaction sent/success/error” surfaces.

6. Map Telegram runtime theme params to semantic notification tokens
- Decision: derive notification tokens from `Telegram.WebApp.themeParams` first, then CSS Telegram vars, then static fallback values; update on Telegram `themeChanged` events.
- Rationale: keeps notification surfaces readable and native across Telegram themes.
- Alternatives considered:
  - Static app palette only.
  - Rejected because Telegram theme drift can reduce contrast and perceived integration quality.

## Risks / Trade-offs

- [Risk] Over-suppressing TONConnect notifications can hide useful wallet-state cues.
  -> Mitigation: keep wallet confirmation UI and ensure app-surfaced messages preserve action status.

- [Risk] Telegram themes may produce poor contrast for alert/toast tones.
  -> Mitigation: semantic tokens include guarded fallback values and contrast validation thresholds.

- [Risk] Deduplication may hide repeated but meaningful failures.
  -> Mitigation: dedupe only identical `(scope, tone, message, source)` events within a short window and reset on content change.

- [Risk] Cross-view migration may leave inconsistent legacy paths.
  -> Mitigation: migrate highest-impact flows first and add tests for channel routing behavior.

## Migration Plan

1. Add notification policy primitives (types/tone/scope/dedupe metadata) and global toast host wiring.
2. Add Telegram theme-param token bridge and runtime `themeChanged` update handling.
3. Set toast runtime policy: anchor near topbar; auto-dismiss durations `neutral=4s`, `success=5s`, `warning=6s`, `danger=7s`.
4. Configure TONConnect actions to disable native action notifications and route action feedback through app policy channels.
5. Migrate flow-by-flow in priority order: funding, marketplace Start deal modal, offers Accept modal, profile wallet.
6. Update tests to validate channel routing, dedupe behavior, durations, placement, and theme-driven token application.
7. Rollback path: retain old local handlers behind isolated commits so policy migration can be reverted per flow if needed.

## Open Questions

- None. Placement, durations, and TONConnect notification ownership are resolved in this design.
