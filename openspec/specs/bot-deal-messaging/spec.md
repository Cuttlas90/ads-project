# bot-deal-messaging Specification

## Purpose
TBD - created by archiving change add-bot-only-messaging. Update Purpose after archive.
## Requirements
### Requirement: Deal message selection persistence
The system SHALL persist per-user deal selections in a `deal_message_selections` table with fields `id`, `user_id` (FK to `users.id`), `deal_id` (FK to `deals.id`), and `selected_at`. It SHALL enforce unique `user_id` so only one active selection exists per user and SHALL index `user_id` and `deal_id`.

#### Scenario: Selection stored
- **WHEN** a user selects a deal via `/deal <id>`
- **THEN** the selection is stored and replaces any previous selection for that user

### Requirement: Bot polling updates
The bot service SHALL poll Telegram using the Bot API `getUpdates` method and SHALL NOT use webhooks. It SHALL track the last processed update id within the polling loop to avoid reprocessing updates.

#### Scenario: Polling loop processes updates
- **WHEN** the bot polls and receives message updates
- **THEN** each update is handled once and acknowledged by advancing the update offset

### Requirement: `/deals` menu command
The bot service SHALL handle `/deals` by listing deals where the user is the advertiser or channel owner and the deal state is `DRAFT` or `NEGOTIATION`. It SHALL respond with a reply-keyboard menu where each button contains `/deal <id>` for a single deal. If no eligible deals exist, it SHALL respond with a clear “no deals” message.

#### Scenario: Deals menu shown
- **WHEN** a user sends `/deals`
- **THEN** the bot responds with a reply keyboard containing `/deal <id>` entries for eligible deals

### Requirement: Deal selection command
The bot service SHALL handle `/deal <id>` by validating the deal exists, is in `DRAFT` or `NEGOTIATION`, and the user is a participant. It SHALL store the selection in `deal_message_selections` and respond with an instruction to send the next message for that deal. If the deal is invalid or unauthorized, it SHALL respond with a clear error message.

#### Scenario: Deal selection accepted
- **WHEN** a user sends `/deal <id>` for an eligible deal
- **THEN** the bot stores the selection and confirms the deal is selected

### Requirement: Text message forwarding
When a text message (not a command) is received, the bot SHALL require an active selection. If no selection exists, it SHALL prompt the user to run `/deals`. If a selection exists, it SHALL store a `deal_events` row with `event_type = message`, include the message text and recipient user id in `payload`, forward the message to the counterparty via the bot, and then clear the selection. The forwarded message SHALL include the deal id in the text (e.g., `Deal #<id>:`) and SHALL include a reply-keyboard shortcut `/deal <id>`.

#### Scenario: Message forwarded with deal context
- **WHEN** a user sends a text message after selecting a deal
- **THEN** the counterparty receives a message that includes the deal id and a `/deal <id>` shortcut

### Requirement: Unregistered user handling
If the bot receives a message from a Telegram user that does not exist in the `users` table, it SHALL respond with “Please open the app to register” and SHALL not process the message.

#### Scenario: Unregistered user rejected
- **WHEN** an unknown Telegram user sends a message
- **THEN** the bot responds with a registration instruction and does not persist events

### Requirement: Non-text message handling
If the bot receives a non-text message, it SHALL respond with “Text only, please.”

#### Scenario: Non-text message rejected
- **WHEN** a user sends a sticker or media message
- **THEN** the bot replies with a text-only warning

