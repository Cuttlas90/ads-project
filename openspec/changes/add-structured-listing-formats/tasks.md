## 1. Proposal and Spec Validation

- [ ] 1.1 Run `openspec validate add-structured-listing-formats --strict` and resolve all validation issues before coding.

## 2. Data Model and Migrations

- [ ] 2.1 Add Alembic migration(s) and SQLModel updates for `listing_formats` structured fields: `placement_type`, `exclusive_hours`, `retention_hours`, plus uniqueness on `(listing_id, placement_type, exclusive_hours, retention_hours)`.
- [ ] 2.2 Add deal persistence fields for listing-derived terms (`placement_type`, `exclusive_hours`, `retention_hours`) and update model constraints/indexes as needed for listing-sourced deals.
- [ ] 2.3 Implement migration backfill/compatibility strategy for existing listing format rows and ensure legacy label-dependent paths are safely retired.

## 3. Backend API and Repository Contracts

- [ ] 3.1 Update listing schemas and `/listings/{id}/formats` create/update handlers to accept and return structured format fields only.
- [ ] 3.2 Enforce listing activation readiness in `PUT /listings/{id}` (`is_active=true` requires at least one format) and return HTTP 400 for empty listings.
- [ ] 3.3 Update `GET /channels/{channel_id}/listing` payload shape to expose structured format fields for the owner editor.
- [ ] 3.4 Update marketplace schemas, route validation, and repository filtering/sorting to support `placement_type`, exclusivity and retention range filters, and structured format output.
- [ ] 3.5 Enforce marketplace eligibility to exclude active listings with zero formats.

## 4. Deal Creation and Update Locking

- [ ] 4.1 Update `POST /listings/{listing_id}/deals` to copy `placement_type`, `exclusive_hours`, and `retention_hours` from the selected listing format into the new deal.
- [ ] 4.2 Keep listing-derived fields immutable in `PATCH /deals/{id}` for listing-sourced deals (reject edits to placement/exclusivity/retention alongside locked price/ad type behavior).
- [ ] 4.3 Ensure `verification_window_hours` derivation for listing-sourced deals aligns with retained terms (`retention_hours`) and default fallback behavior.

## 5. Posting and Verification Workers

- [ ] 5.1 Extend Bot API posting dispatch to use `placement_type` + `creative_media_type`, including story publishing path through Bot API capability.
- [ ] 5.2 Update verification worker to validate retention-window visibility for both post and story placements.
- [ ] 5.3 Implement placement-scoped exclusivity checks (`post` checks only posts, `story` checks only stories) during `exclusive_hours` and trigger refund transitions on breach.
- [ ] 5.4 Add guardrails and explicit error handling when Bot API story capability/permissions are unavailable.

## 6. Frontend Listing and Marketplace UX

- [ ] 6.1 Update frontend API types/services for structured listing format payloads and marketplace responses.
- [ ] 6.2 Replace owner listing editor free-text label workflow with structured inputs (`placement_type`, `exclusive_hours`, `retention_hours`, `price`) for create/update.
- [ ] 6.3 Update marketplace format presentation to show placement commitments (type, exclusivity, retention, price) and wire new filter inputs.

## 7. Test Coverage and Validation

- [ ] 7.1 Add/adjust backend listing API tests for structured format validation, duplicate-term conflicts, and activation readiness (empty listing activation denied).
- [ ] 7.2 Add/adjust marketplace repository and API tests for structured format output, eligibility rules, and new placement/hour filters.
- [ ] 7.3 Add/adjust deal API tests confirming listing-derived structured fields are copied at creation and remain immutable during negotiation updates.
- [ ] 7.4 Add/adjust posting and verification worker tests for story publishing path, retention checks, and placement-scoped exclusivity breach handling.
- [ ] 7.5 Add/adjust frontend tests for owner structured-format editor flows and marketplace display/filter behavior.
- [ ] 7.6 Run targeted backend/frontend/bot test suites and rerun `openspec validate add-structured-listing-formats --strict` after implementation updates.
