# Change: Channel registry and submission API

## Why
The marketplace needs a persistent, minimal channel registry with explicit ownership so later Telegram permission checks and deal logic can build on it.

## What Changes
- Add channel and channel member data models with migrations and constraints.
- Add authenticated /channels POST and GET endpoints with username normalization and validation.
- Add request/response schemas for channels.
- Add API tests for submit/list/duplicate/unauthorized cases.

## Impact
- Affected specs: new capability channel-registry; touches existing authentication and database/migration conventions.
- Affected code: shared/db/models, backend/app/models, backend/app/api/routes, backend/alembic, backend/tests.
