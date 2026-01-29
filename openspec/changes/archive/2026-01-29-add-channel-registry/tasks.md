## 1. Data model and migrations
- [x] 1.1 Add Channel and ChannelMember SQLModel tables in shared/db/models and re-export in backend/app/models.
- [x] 1.2 Update shared/db/base imports so Alembic metadata includes the new tables.
- [x] 1.3 Create Alembic migration to add channels, channel_members, and constraints (unique username, unique member, single owner).

## 2. API and schemas
- [x] 2.1 Add Pydantic schemas for channel input/output and member role.
- [x] 2.2 Implement /channels POST (normalize + validate username, create channel + owner membership, return 201).
- [x] 2.3 Implement /channels GET (list owned/managed channels with role).
- [x] 2.4 Register the channels router in the main API router.

## 3. Tests
- [x] 3.1 Add API tests: submit success, duplicate submit -> 409, list channels, unauthenticated -> 401.
- [x] 3.2 Ensure tests use a real DB session with SQLModel metadata including new tables.

## 4. Validation
- [x] 4.1 Run backend tests covering channels.
- [x] 4.2 Run `openspec validate add-channel-registry --strict`.
