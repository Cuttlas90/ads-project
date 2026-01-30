## 1. Implementation
- [x] 1.1 Add shared DB models for listings and listing formats plus backend wrappers and exports.
- [x] 1.2 Create Alembic migration for `listings` and `listing_formats` with constraints and cascade behavior.
- [x] 1.3 Add Pydantic schemas for listing/format payloads and marketplace responses (including pagination metadata).
- [x] 1.4 Implement `/listings` owner APIs with ownership checks and error handling.
- [x] 1.5 Implement marketplace repository query logic with filters, search, sorting, and pagination.
- [x] 1.6 Implement `/marketplace/listings` route and wire into API router.
- [x] 1.7 Add API tests for listing and listing format endpoints (success + auth/ownership + conflict cases).
- [x] 1.8 Add repository tests for filter combinations, search+filter AND logic, and pagination determinism.
- [x] 1.9 Add marketplace API tests for filters, sorting, pagination, and invalid parameter handling.
- [x] 1.10 Add unit tests for any new or modified helpers/schemas/validators introduced while implementing the above.

## 2. Validation
- [x] 2.1 Run backend tests: `cd /home/mohsen/ads-project/backend && source .venv/bin/activate && DATABASE_URL=sqlite:// pytest`.
