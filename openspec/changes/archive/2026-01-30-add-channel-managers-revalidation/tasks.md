## 1. Implementation
- [x] 1.1 Add request/response schemas for channel managers (create payload, list item) with `telegram_user_id`.
- [x] 1.2 Implement `backend/app/api/routes/channel_managers.py` with POST/DELETE/GET routes, DB-only logic, and explicit error handling (403/404/409).
- [x] 1.3 Wire the new router into `backend/app/api/router.py`.
- [x] 1.4 Implement `revalidate_channel_access` in `backend/app/services/manager_revalidate.py` and add a domain error type that includes channel/user/missing permission metadata.
- [x] 1.5 Add unit tests for revalidation helper (admin ok, missing rights, not admin) using mocked permission checks.
- [x] 1.6 Add API tests for manager CRUD: add success, add duplicate (409), remove success, non-owner add/remove (403), missing user (404), list managers (owner/manager allowed).

## 2. Validation
- [x] 2.1 Run `openspec validate add-channel-managers-revalidation --strict`.
- [x] 2.2 Run backend tests (targeted for manager CRUD and revalidation helper).
