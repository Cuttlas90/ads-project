## ADDED Requirements
### Requirement: Bot-mediated deal messaging
The system SHALL expose `POST /deals/{id}/messages` requiring authentication. It SHALL allow only the deal advertiser or channel owner to send messages. It SHALL require a non-empty `text` payload, persist a `deal_events` row with `event_type = message` and the message text in `payload`, and relay the message to the counterparty via the Telegram bot using the recipient’s `telegram_user_id`. It SHALL return HTTP 201 with the stored message metadata.

#### Scenario: Message forwarded to counterparty
- **WHEN** an advertiser sends a message on a deal
- **THEN** a message event is stored and the bot forwards the text to the channel owner
