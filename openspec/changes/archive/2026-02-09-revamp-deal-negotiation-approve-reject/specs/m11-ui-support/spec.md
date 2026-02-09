## ADDED Requirements

### Requirement: Deal event detail interaction
The deal detail UI SHALL open event details when a timeline row is tapped. For `message` events, the detail view SHALL show only message text. For `proposal` events, the detail view SHALL show proposal parameters from event payload; older proposal events SHALL be read-only, while the latest proposal SHALL expose actions only to the proposal recipient.

#### Scenario: Tapping message event shows message only
- **WHEN** a user taps a timeline row for an event with `event_type = message`
- **THEN** the detail view shows only the message text

## MODIFIED Requirements

### Requirement: Creative approval FSM transitions
The system SHALL support proposal decision transitions directly from negotiation: only the latest-proposal recipient may approve or reject while the deal is in `DRAFT` or `NEGOTIATION`. Approve SHALL finalize the deal to `CREATIVE_APPROVED`, and reject SHALL finalize the deal to `REJECTED`. Legacy creative submit/review screens SHALL be bypassed in the primary deal-detail flow after proposal approval.

#### Scenario: Counterparty approves latest proposal
- **GIVEN** a deal in `DRAFT` or `NEGOTIATION` with a latest proposal from the opposite party
- **WHEN** the latest-proposal recipient approves
- **THEN** the deal transitions to `CREATIVE_APPROVED`

### Requirement: Deal timeline rendering
The deal detail UI SHALL render events returned by `GET /deals/{id}/events` in reverse-chronological order (newest first). The timestamp SHALL be right-aligned in each event row and formatted as:
- `HH:mm` for events occurring today in the user's local timezone,
- `dd MMM HH:mm` for events in the current year but not today,
- `dd MMM yyyy` for events outside the current year.

#### Scenario: Timeline renders newest-first with human time
- **WHEN** the UI receives events from `/deals/{id}/events`
- **THEN** the timeline lists newest events first and each row shows right-aligned human-formatted time

### Requirement: State-based action panel
The deal detail UI SHALL show proposal actions only when valid for the current deal state and actor. For a deal in `DRAFT` or `NEGOTIATION`, only the latest-proposal recipient SHALL see `Edit`, `Approve`, and `Reject` actions. `Edit` SHALL allow changes to only `creative_text`, `start_at`, `creative_media_type`, and `creative_media_ref`; other proposal fields SHALL be view-only. In `REJECTED` and post-approval states, the negotiation action panel SHALL be hidden.

#### Scenario: Sender cannot act on own latest proposal
- **WHEN** the current user is the sender of the latest proposal
- **THEN** `Edit`, `Approve`, and `Reject` actions are not shown
