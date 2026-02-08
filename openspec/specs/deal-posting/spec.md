# deal-posting Specification

## Purpose
TBD - created by syncing change add-deal-posting-verification-payouts. Update Purpose after archive.
## Requirements
### Requirement: Auto-post scheduling
The system SHALL schedule auto-posting when a deal is `CREATIVE_APPROVED` and has a `scheduled_at` timestamp. The scheduler SHALL select only deals with `scheduled_at <= now` and SHALL transition the deal to `SCHEDULED` before attempting to publish. Scheduling MUST be idempotent and MUST NOT schedule or post a deal more than once.

#### Scenario: Eligible deal is scheduled
- **WHEN** a deal is `CREATIVE_APPROVED` and `scheduled_at` is in the past
- **THEN** the system transitions the deal to `SCHEDULED` exactly once

### Requirement: Bot publishing via Telegram Bot API
The system SHALL publish using Telegram Bot API based on both `placement_type` and `creative_media_type`. For `placement_type = post`, it SHALL publish to feed using `sendMessage` (text-only), `sendPhoto` (image), or `sendVideo` (video). For `placement_type = story`, it SHALL publish through Bot API story capability using the corresponding media payload. It SHALL include `creative_text` as message/caption/story text as supported by the selected method and SHALL use `creative_media_ref` as the media reference when required. On success it SHALL store `posted_message_id`, `posted_content_hash`, and `posted_at` on the deal.

#### Scenario: Story creative is posted through Bot API
- **WHEN** a scheduled deal has `placement_type = story`
- **THEN** the system publishes it using Bot API story capability and stores the resulting posted metadata

### Requirement: Posting state transition
After a successful publish, the system SHALL transition the deal from `SCHEDULED` to `POSTED` as a system action. If the publish fails, it SHALL keep the deal in `SCHEDULED` and log the failure for retry.

#### Scenario: Successful post updates deal state
- **WHEN** the bot publish succeeds
- **THEN** the deal transitions to `POSTED` and stores message metadata

