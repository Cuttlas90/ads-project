## MODIFIED Requirements

### Requirement: Marketplace listings include format ids
The system SHALL include structured format terms for each format in `GET /marketplace/listings` results so the UI can create a deal from a selected format. Each `formats[]` entry SHALL include `id`, `placement_type`, `exclusive_hours`, `retention_hours`, and `price`.

#### Scenario: Marketplace structured format fields present
- **WHEN** a client requests `/marketplace/listings`
- **THEN** each `formats[]` entry includes `id`, `placement_type`, `exclusive_hours`, `retention_hours`, and `price`

### Requirement: Listing read endpoint for editor
The system SHALL expose `GET /channels/{channel_id}/listing` requiring authentication and owner role. It SHALL return the listing summary plus all listing formats for the channel. Each format SHALL include `id`, `placement_type`, `exclusive_hours`, `retention_hours`, and `price`. It SHALL return HTTP 200 with `has_listing = false` when no listing exists and HTTP 403 for non-owners.

#### Scenario: Owner loads listing editor with structured formats
- **GIVEN** a channel owner
- **WHEN** they call `GET /channels/{channel_id}/listing`
- **THEN** the response includes listing data and structured format fields

## ADDED Requirements

### Requirement: Listing editor uses structured format inputs
The owner listing editor UI SHALL create and update formats using structured inputs only: `placement_type` selector (`post` or `story`), `exclusive_hours`, `retention_hours`, and `price`. It SHALL NOT require or expose free-form label input for listing formats.

#### Scenario: Owner adds structured post format
- **WHEN** an owner submits a format with `placement_type = post`, numeric `exclusive_hours`, numeric `retention_hours`, and `price`
- **THEN** the UI sends the structured payload and the new format appears in the editor list

### Requirement: Marketplace format cards show placement commitments
Marketplace format presentation SHALL display placement and timing commitments for each format (`placement_type`, `exclusive_hours`, `retention_hours`) together with `price` so advertisers can compare offers before selecting a format.

#### Scenario: Advertiser can compare format commitments
- **WHEN** an advertiser views a listing card with multiple formats
- **THEN** each format option shows placement type, exclusivity hours, retention hours, and price
