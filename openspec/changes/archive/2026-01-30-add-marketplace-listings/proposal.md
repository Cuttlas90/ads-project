# Change: Add marketplace listings and discovery

## Why
Channel owners need a structured way to monetize their channels, and advertisers need a read-only marketplace to discover verified channels and compare formats/prices.

## What Changes
- Add listing and listing format persistence with ownership constraints.
- Add owner-only APIs to create/update listings and manage listing formats.
- Add marketplace browse endpoint with filters, search, sorting, and pagination.
- Add repository query logic for marketplace joins and filtering.

## Impact
- Affected specs: listing-management (new), marketplace-discovery (new)
- Affected code: backend models, Alembic migrations, API routes/schemas, repository queries, tests
