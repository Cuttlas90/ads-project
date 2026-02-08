# deal-verification Specification

## Purpose
TBD - created by syncing change add-deal-posting-verification-payouts. Update Purpose after archive.
## Requirements
### Requirement: Post integrity verification job
The system SHALL run a periodic verification job that inspects `POSTED` deals. It SHALL fetch the Telegram post or story via Telethon, verify the published content exists, and compare the current content hash with `posted_content_hash`. It SHALL check that visibility remains intact for at least the deal `retention_hours` window, and it SHALL evaluate exclusivity for the same placement type during the deal `exclusive_hours` window.

#### Scenario: Placement-scoped exclusivity holds
- **WHEN** a posted deal remains visible for the full retention window and no additional content of the same `placement_type` is published during the exclusivity window
- **THEN** the system transitions the deal to `VERIFIED`

### Requirement: Tamper detection and refund trigger
If the published content is deleted, edited (content hash mismatch), or exclusivity is violated before the retention window ends, the system SHALL mark the deal as tampered and transition it to `REFUNDED` as a system action.

#### Scenario: Additional post breaches post exclusivity
- **WHEN** a `placement_type = post` deal has another post published during its exclusivity window
- **THEN** the system transitions the deal to `REFUNDED` and triggers a refund

#### Scenario: Additional story breaches story exclusivity
- **WHEN** a `placement_type = story` deal has another story published during its exclusivity window
- **THEN** the system transitions the deal to `REFUNDED` and triggers a refund

### Requirement: Verification window source
The system SHALL store `verification_window_hours` on the deal and derive it from listing format retention terms for listing-sourced deals (`verification_window_hours = retention_hours`). If listing retention terms are not available, it SHALL default to 24 hours.

#### Scenario: Listing retention sets verification window
- **WHEN** a listing-sourced deal is posted with `retention_hours = 48`
- **THEN** `verification_window_hours` is set to 48

#### Scenario: Default verification window
- **WHEN** a deal lacks explicit retention-based verification terms
- **THEN** `verification_window_hours` is set to 24

