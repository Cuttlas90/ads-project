## Context

The backend currently verifies Telegram `initData` hashes using `sha256(bot_token)` as the HMAC secret. That derivation matches Telegram Login Widget verification, but the frontend sends Telegram Mini App `window.Telegram.WebApp.initData`, which uses a different secret derivation (`HMAC_SHA256(key="WebAppData", msg=bot_token)`).

This mismatch causes valid Mini App payloads to fail backend authentication. The product direction is explicit: Mini App-only auth on API endpoints, with no Login Widget support and no backward compatibility requirement.

## Goals / Non-Goals

**Goals:**
- Align backend signature verification with Telegram Mini App validation semantics.
- Ensure authentication accepts valid Mini App payloads and rejects Login Widget-style signatures.
- Align automated tests with Mini App-only auth behavior to prevent regression.

**Non-Goals:**
- Supporting Telegram Login Widget payloads.
- Dual-mode compatibility toggles or migration windows.
- Introducing any alternative auth mechanisms beyond Telegram Mini App `initData`.

## Decisions

1) **Use Mini App key derivation exclusively**
- **Decision:** Derive the `initData` verification secret as `HMAC_SHA256(key="WebAppData", msg=bot_token)` and use it to compute the final HMAC over the data-check-string.
- **Rationale:** This matches Telegram Mini App validation documentation and the payload source used by the frontend.
- **Alternative considered:** Keep `sha256(bot_token)` or support both algorithms. Rejected because that corresponds to Login Widget behavior and conflicts with Mini App-only policy.

2) **Codify rejection of Login Widget signatures**
- **Decision:** Add explicit test coverage that Login Widget-style hash derivation is rejected by the verifier.
- **Rationale:** Prevents accidental reintroduction of dual-mode or legacy behavior.
- **Alternative considered:** Implicit rejection only. Rejected because explicit regression tests are clearer and safer.

3) **Standardize test helper behavior**
- **Decision:** Update all backend test helper `build_init_data` implementations to produce Mini App-correct hashes.
- **Rationale:** Test fixtures must model production semantics; currently many tests rely on legacy derivation and mask the issue.
- **Alternative considered:** Keep local helper variants per file. Rejected because drift risk is high and this bug already spread through duplicated helpers.

## Risks / Trade-offs

- **[Risk] Existing non-Mini-App clients break** → **Mitigation:** Accepted intentionally; scope is Mini App-only auth with no backward compatibility.
- **[Risk] Incomplete helper migration in tests leaves false negatives** → **Mitigation:** Update every auth helper occurrence and add a dedicated verifier regression test for both accepted and rejected signature models.
- **[Risk] Documentation confusion between Telegram auth products** → **Mitigation:** Add concise inline comments and spec wording that this path is for Mini App `initData`, not Login Widget auth.

## Migration Plan

- Update verification logic to Mini App derivation.
- Update all backend auth helper generators in tests to Mini App derivation.
- Add/adjust tests to assert:
  - valid Mini App payloads authenticate;
  - Login Widget-style hashes fail;
  - existing `auth_date` and required-field validations remain enforced.
- Run targeted backend tests for auth dependency and routes.

Rollback strategy is straightforward (revert change), but no compatibility fallback will be introduced in the forward path.

## Open Questions

- None.
