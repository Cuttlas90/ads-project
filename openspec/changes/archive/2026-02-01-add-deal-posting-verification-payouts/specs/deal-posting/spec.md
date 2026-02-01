## ADDED Requirements
### Requirement: Auto-post scheduling
The system SHALL schedule auto-posting when a deal is `CREATIVE_APPROVED` and has a `scheduled_at` timestamp. The scheduler SHALL select only deals with `scheduled_at <= now` and SHALL transition the deal to `SCHEDULED` before attempting to publish. Scheduling MUST be idempotent and MUST NOT schedule or post a deal more than once.

#### Scenario: Eligible deal is scheduled
- **WHEN** a deal is `CREATIVE_APPROVED` and `scheduled_at` is in the past
- **THEN** the system transitions the deal to `SCHEDULED` exactly once

### Requirement: Bot publishing via Telegram Bot API
The system SHALL publish posts using the Bot API with the method chosen by `creative_media_type`: `sendMessage` (text-only), `sendPhoto` (image), or `sendVideo` (video). It SHALL include `creative_text` as the caption or message body and SHALL use `creative_media_ref` as the media reference when required. On success it SHALL store `posted_message_id`, `posted_content_hash`, and `posted_at` on the deal.

#### Scenario: Image creative is posted
- **WHEN** a scheduled deal has `creative_media_type = image`
- **THEN** the system publishes via `sendPhoto` and stores the resulting `posted_message_id`

### Requirement: Posting state transition
After a successful publish, the system SHALL transition the deal from `SCHEDULED` to `POSTED` as a system action. If the publish fails, it SHALL keep the deal in `SCHEDULED` and log the failure for retry.

#### Scenario: Successful post updates deal state
- **WHEN** the bot publish succeeds
- **THEN** the deal transitions to `POSTED` and stores message metadata
