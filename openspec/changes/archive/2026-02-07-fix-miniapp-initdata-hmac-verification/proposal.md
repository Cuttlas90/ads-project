## Why

Telegram Mini App requests are authenticated with `initData`, but the current backend verification path uses the Telegram Login Widget hash derivation model. This can reject valid Mini App payloads and blocks Telegram-native authentication for real users.

## What Changes

- Correct Telegram Mini App signature verification to use Telegram's Mini App `WebAppData` HMAC key derivation model.
- Explicitly enforce Mini App-only signature validation for API authentication endpoints.
- Remove acceptance of Login Widget signature derivation behavior in auth verification logic and tests.
- Update backend test helpers and auth verification tests to align with Mini App verification semantics.

## Capabilities

### New Capabilities
- None.

### Modified Capabilities
- `telegram-auth`: Update `initData` signature verification requirement to Mini App `WebAppData` derivation and require rejection of Login Widget-style hashes.

## Impact

- Affected code: `backend/app/auth/telegram_initdata.py`, `backend/app/api/deps.py`, and backend auth-adjacent tests under `backend/tests/`.
- Affected behavior: authenticated API access via `X-Telegram-Init-Data` / `initData` query parameter.
- Security/auth posture: strict Mini App auth compatibility with no backward compatibility for Login Widget payloads.
