# deal-verification Specification

## Purpose
TBD - created by syncing change add-deal-posting-verification-payouts. Update Purpose after archive.

## Requirements
### Requirement: Post integrity verification job
The system SHALL run a periodic verification job that inspects `POSTED` deals. It SHALL fetch the Telegram message via Telethon, verify the message exists, and compare the current content hash with `posted_content_hash`. It SHALL also check that the post has remained visible for at least `verification_window_hours`.

#### Scenario: Post remains valid through window
- **WHEN** a posted deal remains unchanged and visible for the full verification window
- **THEN** the system transitions the deal to `VERIFIED`

### Requirement: Tamper detection and refund trigger
If the message is deleted or edited (content hash mismatch) before the verification window ends, the system SHALL mark the deal as tampered and transition it to `REFUNDED` as a system action.

#### Scenario: Post deleted before verification window
- **WHEN** Telethon indicates the post is missing before the verification window elapses
- **THEN** the system transitions the deal to `REFUNDED` and triggers a refund

### Requirement: Verification window source
The system SHALL store `verification_window_hours` on the deal and derive it from ad type parameters. If not provided, it SHALL default to 24 hours.

#### Scenario: Default verification window
- **WHEN** a deal lacks explicit ad type parameters for verification
- **THEN** `verification_window_hours` is set to 24
