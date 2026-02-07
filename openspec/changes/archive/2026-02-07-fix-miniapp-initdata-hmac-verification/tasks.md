## 1. Backend Auth Verification

- [x] 1.1 Update `backend/app/auth/telegram_initdata.py` to derive the signature key with Mini App `WebAppData` HMAC semantics.
- [x] 1.2 Keep existing data-check-string construction and `auth_date` freshness checks intact while switching only signature derivation behavior.
- [x] 1.3 Add explicit inline code note that this verifier is Mini App-only and does not support Login Widget signature derivation.

## 2. Backend Test Fixtures and Coverage

- [x] 2.1 Update all backend `build_init_data` test helpers to generate hashes with Mini App `WebAppData` derivation.
- [x] 2.2 Update `backend/tests/test_telegram_initdata.py` with a regression case asserting Login Widget-style hashes are rejected.
- [x] 2.3 Verify protected route tests (`/auth/me` and other authenticated APIs) pass with Mini App-correct payloads.

## 3. Validation

- [x] 3.1 Run targeted backend auth tests (unit + API) to verify Mini App acceptance and Login Widget rejection.
- [x] 3.2 Run impacted backend test suites that rely on `X-Telegram-Init-Data` helpers to ensure no stale hash model remains.
