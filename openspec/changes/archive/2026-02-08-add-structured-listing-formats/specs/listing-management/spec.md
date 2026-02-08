## MODIFIED Requirements

### Requirement: Listing format persistence
The system SHALL persist listing formats in a `listing_formats` table with fields `id`, `listing_id` (FK to `listings.id`), `placement_type` (required enum: `post` or `story`), `exclusive_hours` (required integer, minimum 0), `retention_hours` (required integer, minimum 1), `price` (required decimal with fixed scale of 2, representing TON), `created_at`, and `updated_at`. It SHALL enforce unique `(listing_id, placement_type, exclusive_hours, retention_hours)` and SHALL cascade delete formats when a listing is deleted.

#### Scenario: Duplicate structured terms per listing
- **WHEN** two formats with the same `placement_type`, `exclusive_hours`, and `retention_hours` are created for the same listing
- **THEN** the database constraint prevents the insert

### Requirement: Update listing endpoint
The system SHALL expose `PUT /listings/{id}` requiring authentication. It SHALL allow only the listing owner to update `is_active` and return HTTP 200 with the updated listing. It SHALL return HTTP 404 when the listing does not exist and HTTP 403 when the caller is not the owner. It SHALL NOT call Telegram APIs. When the owner sets `is_active = true`, the listing SHALL have at least one listing format; otherwise the request SHALL return HTTP 400.

#### Scenario: Owner cannot activate empty listing
- **WHEN** a listing owner sets `is_active = true` on a listing with zero formats
- **THEN** the response is HTTP 400 and the listing remains inactive

### Requirement: Create listing format endpoint
The system SHALL expose `POST /listings/{id}/formats` requiring authentication. It SHALL allow only the listing owner to create a format with `placement_type`, `exclusive_hours`, `retention_hours`, and `price` and return HTTP 201 with the format data. It SHALL return HTTP 404 when the listing does not exist, HTTP 403 when the caller is not the owner, and HTTP 409 when the structured format terms conflict within the listing.

#### Scenario: Owner adds structured format
- **WHEN** a listing owner submits valid `placement_type`, `exclusive_hours`, `retention_hours`, and `price`
- **THEN** the response is HTTP 201 and the format is persisted

### Requirement: Update listing format endpoint
The system SHALL expose `PUT /listings/{id}/formats/{format_id}` requiring authentication. It SHALL allow only the listing owner to update `placement_type`, `exclusive_hours`, `retention_hours`, and/or `price` and return HTTP 200 with the updated format. It SHALL return HTTP 404 when the listing or format does not exist, HTTP 403 when the caller is not the owner, and HTTP 409 when the updated structured format terms conflict within the listing.

#### Scenario: Owner updates structured format hours
- **WHEN** a listing owner updates `exclusive_hours` or `retention_hours` for an existing format
- **THEN** the response is HTTP 200 with the updated format

### Requirement: Listing read endpoint for editor
The system SHALL expose `GET /channels/{channel_id}/listing` requiring authentication and owner role. It SHALL return the listing summary and its formats when a listing exists. Format entries SHALL include `id`, `placement_type`, `exclusive_hours`, `retention_hours`, and `price`. If no listing exists, it SHALL return HTTP 200 with `has_listing = false`.

#### Scenario: Owner loads listing editor with structured formats
- **WHEN** a channel owner calls `/channels/{channel_id}/listing`
- **THEN** the response includes listing data and structured format fields or `has_listing = false` when no listing exists
