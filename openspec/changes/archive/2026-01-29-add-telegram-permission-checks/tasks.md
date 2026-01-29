## 1. Implementation
- [x] 1.1 Add `backend/app/telegram/permissions.py` with `REQUIRED_BOT_RIGHTS`, `PermissionCheckResult`, `check_bot_permissions`, and `check_user_permissions`.
- [x] 1.2 Add `backend/app/domain/permissions.py` with a domain error type and `ensure_permissions(result, *, context)`.
- [x] 1.3 Confirm any needed package `__init__` exports or local import paths for the new modules.

## 2. Tests
- [x] 2.1 Add table-driven tests for bot permission checks (admin vs non-admin, missing rights) with mocked Telethon responses in `backend/tests/telegram/test_permissions.py`.
- [x] 2.2 Add table-driven tests for user permission checks (not member, not admin, missing rights, full rights).
- [x] 2.3 Add tests for `ensure_permissions` to verify it raises on `ok=False` and no-ops on `ok=True`.

## 3. Validation
- [x] 3.1 Run `pytest backend/tests/telegram/test_permissions.py`.
