## MODIFIED Requirements

### Requirement: Bot publishing via Telegram Bot API
The system SHALL publish using Telegram Bot API based on both `placement_type` and `creative_media_type`. For `placement_type = post`, it SHALL publish to feed using `sendMessage` (text-only), `sendPhoto` (image), or `sendVideo` (video). For `placement_type = story`, it SHALL publish through Bot API story capability using the corresponding media payload. It SHALL include `creative_text` as message/caption/story text as supported by the selected method and SHALL use `creative_media_ref` as the media reference when required. On success it SHALL store `posted_message_id`, `posted_content_hash`, and `posted_at` on the deal.

#### Scenario: Story creative is posted through Bot API
- **WHEN** a scheduled deal has `placement_type = story`
- **THEN** the system publishes it using Bot API story capability and stores the resulting posted metadata
