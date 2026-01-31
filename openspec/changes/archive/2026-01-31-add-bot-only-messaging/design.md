## Context
The product requires bot-only negotiation: users converse with a Telegram bot rather than any in-app chat UI. The bot must list eligible deals, require explicit selection for each message, store an audit trail, and forward messages to the counterparty.

## Goals / Non-Goals
- Goals:
  - Implement polling-based Telegram update handling in the bot service.
  - Provide `/deals` menu for DRAFT/NEGOTIATION deals only.
  - Require `/deal <id>` selection before each message; store selection in DB.
  - Persist message events in `deal_events` and include deal context in outbound text.
  - Provide reply-keyboard shortcuts for `/deal <id>` on received messages.
- Non-Goals:
  - Webhook-based updates.
  - In-app chat UI.
  - Media upload/forwarding (text only).

## Decisions
- **Selection state storage:** Use a DB table `deal_message_selections` keyed by user_id to survive bot restarts.
- **Flow:** `/deals` shows a reply keyboard of eligible deals; `/deal <id>` sets selection; next text message is sent and selection is cleared.
- **Eligibility:** Only deals in `DRAFT` or `NEGOTIATION` and only when the user is a participant.
- **User not registered:** Bot responds “Please open the app to register” and does not process the message.
- **Non-text messages:** Bot responds “Text only, please.”

## Risks / Trade-offs
- Polling loops must avoid duplicate processing; the bot will track the last update id per run.
- Reply keyboards are simpler than inline callbacks but less flexible.

## Migration Plan
1. Add migration + model for `deal_message_selections`.
2. Implement bot polling loop and command/message handlers.
3. Add tests for menu selection, message forwarding, and DB persistence.

## Open Questions
- None (polling and reply keyboard confirmed).
