## ADDED Requirements

### Requirement: Listing read endpoint for editor
The system SHALL expose `GET /channels/{channel_id}/listing` requiring authentication and owner role. It SHALL return the listing summary and its formats when a listing exists. If no listing exists, it SHALL return HTTP 200 with `has_listing = false`.

#### Scenario: Owner loads listing editor
- **WHEN** a channel owner calls `/channels/{channel_id}/listing`
- **THEN** the response includes listing data and its formats or `has_listing = false` when no listing exists
