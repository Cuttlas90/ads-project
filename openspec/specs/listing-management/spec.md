# listing-management Specification

## Purpose
TBD - created by archiving change add-marketplace-listings. Update Purpose after archive.
## Requirements
### Requirement: Listing persistence
The system SHALL persist listings in a `listings` table with fields `id`, `channel_id` (FK to `channels.id`), `owner_id` (FK to `users.id`), `is_active` (default true), `created_at`, and `updated_at`. It SHALL enforce one listing per channel via a unique constraint on `channel_id`.

#### Scenario: One listing per channel
- **WHEN** a second listing is created for the same channel
- **THEN** the database constraint prevents the insert

### Requirement: Listing format persistence
The system SHALL persist listing formats in a `listing_formats` table with fields `id`, `listing_id` (FK to `listings.id`), `label` (required), `price` (required decimal with fixed scale of 2, representing TON), `created_at`, and `updated_at`. It SHALL enforce unique `(listing_id, label)` and SHALL cascade delete formats when a listing is deleted.

#### Scenario: Duplicate label per listing
- **WHEN** two formats with the same label are created for the same listing
- **THEN** the database constraint prevents the insert

### Requirement: Create listing endpoint
The system SHALL expose `POST /listings` requiring authentication. It SHALL accept `channel_id`, verify the caller is the channel owner, create a listing with `is_active = true`, and return HTTP 201 with the listing data. It SHALL return HTTP 404 when the channel does not exist, HTTP 403 when the caller is not the owner, and HTTP 409 when a listing already exists for the channel. It SHALL NOT call Telegram APIs.

#### Scenario: Owner creates listing
- **WHEN** a channel owner posts a valid `channel_id`
- **THEN** the response is HTTP 201 and the listing is stored as active

### Requirement: Update listing endpoint
The system SHALL expose `PUT /listings/{id}` requiring authentication. It SHALL allow only the listing owner to update `is_active` and return HTTP 200 with the updated listing. It SHALL return HTTP 404 when the listing does not exist and HTTP 403 when the caller is not the owner. It SHALL NOT call Telegram APIs.

#### Scenario: Owner deactivates listing
- **WHEN** a listing owner sets `is_active = false`
- **THEN** the listing becomes inactive and HTTP 200 is returned

### Requirement: Create listing format endpoint
The system SHALL expose `POST /listings/{id}/formats` requiring authentication. It SHALL allow only the listing owner to create a format with `label` and `price` and return HTTP 201 with the format data. It SHALL return HTTP 404 when the listing does not exist, HTTP 403 when the caller is not the owner, and HTTP 409 when the label conflicts within the listing.

#### Scenario: Owner adds format
- **WHEN** a listing owner submits a valid `label` and `price`
- **THEN** the response is HTTP 201 and the format is persisted

### Requirement: Update listing format endpoint
The system SHALL expose `PUT /listings/{id}/formats/{format_id}` requiring authentication. It SHALL allow only the listing owner to update `label` and/or `price` and return HTTP 200 with the updated format. It SHALL return HTTP 404 when the listing or format does not exist, HTTP 403 when the caller is not the owner, and HTTP 409 when the label conflicts within the listing.

#### Scenario: Owner updates format price
- **WHEN** a listing owner updates the price for an existing format
- **THEN** the response is HTTP 200 with the updated format

### Requirement: Listing ownership authorization
Listing and listing format modifications SHALL authorize ownership using database membership data only. Callers who are managers SHALL be denied with HTTP 403.

#### Scenario: Manager denied
- **WHEN** a channel manager attempts to create or update a listing or format
- **THEN** the response is HTTP 403

### Requirement: Listing read endpoint for editor
The system SHALL expose `GET /channels/{channel_id}/listing` requiring authentication and owner role. It SHALL return the listing summary and its formats when a listing exists. If no listing exists, it SHALL return HTTP 200 with `has_listing = false`.

#### Scenario: Owner loads listing editor
- **WHEN** a channel owner calls `/channels/{channel_id}/listing`
- **THEN** the response includes listing data and its formats or `has_listing = false` when no listing exists
