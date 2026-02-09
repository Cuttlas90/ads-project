## Why

Deal negotiation is fragmented across timeline, detail actions, and legacy creative-review screens, which makes simple approve/reject decisions slow and unclear. Proposal and message history is also hard to read because timestamps are raw ISO strings and proposal events do not always preserve full terms.

## What Changes

- Redesign deal-detail negotiation UX so timeline is newest-first, human-time formatted, and event rows can be opened for contextual details.
- Add proposal-centric actions directly from deal detail: latest proposal recipient can `Edit`, `Approve`, or `Reject`.
- Change approve semantics so negotiation approval finalizes directly to `CREATIVE_APPROVED` (bypassing legacy creative submit/review screens).
- Add explicit reject action for negotiation and make `REJECTED` terminal for participant actions and deal messaging.
- Persist full proposal snapshots for all newly-created proposal events to make proposal history self-contained.
- **BREAKING**: Change `POST /deals/{id}/accept` lifecycle outcome from `ACCEPTED` flow to direct creative-approved finalization.

## Capabilities

### New Capabilities
- None.

### Modified Capabilities
- `deal-management`: Update negotiation actions, state-transition semantics, timeline ordering contract, and proposal-event payload requirements.
- `m11-ui-support`: Replace raw timeline rendering with descending, human-formatted event UI and add proposal/message event detail interactions with in-place negotiation actions.
- `deal-messaging`: Restrict message sending to open negotiation states and block post-reject messaging.

## Impact

- Backend APIs: `/deals/{id}/events`, `/deals/{id}/accept` (approve semantics), new reject action endpoint, `/deals/{id}` patch proposal payload behavior, `/deals/{id}/messages` state gating.
- FSM/state handling: transition table changes and route-level action validation for approve/reject terminal behavior.
- Frontend flows: `DealDetailView` timeline rendering, event detail UX, and action panel behavior; removal/bypass of legacy creative submit/review route usage.
- Bot and messaging consistency: align deal-message eligibility with terminal reject behavior.
- Tests: backend FSM/routes/timeline/message tests and frontend deal-detail interaction tests.
