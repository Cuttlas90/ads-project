## Context

Channel verification is a backend request flow that combines:
- Bot API checks (bot membership/rights)
- Telethon MTProto calls (full channel + broadcast stats)

Field behavior has shown two independent operational failure modes:
1) MTProto transport path failures (direct DC route blocked or unstable)
2) Telethon session authorization failures (`connect()` succeeds but session is not logged in)

The change already introduces spec-level requirements for:
- Telethon preflight before stats calls
- Controlled failure behavior (`502` for upstream dependency failures)
- Explicit session lifecycle and authorization bootstrap capability
- Optional MTProxy support with strict config validation

This design defines how these requirements are implemented and operated in production without ad-hoc manual recovery steps.

## Goals / Non-Goals

**Goals:**
- Make channel verification deterministic when Telegram dependencies are unavailable.
- Provide an explicit Telethon session lifecycle model (`unauthorized`, `authorizing`, `authorized`, `revoked`) for backend decision-making.
- Provide a controlled operator bootstrap flow to authorize/re-authorize the Telethon service account.
- Keep sensitive auth factors (OTP/2FA/session secrets) out of normal logs and API payloads.
- Preserve verification data integrity: no partial channel/snapshot persistence on Telegram failure paths.

**Non-Goals:**
- Replacing Telethon stats calls with Bot API-only implementations.
- End-user UI for Telethon authorization in the Mini App.
- Automatic OTP retrieval, headless Telegram login bypass, or unattended 2FA handling.
- Reworking unrelated deal/payment FSM logic.

## Decisions

1) **Keep verification as synchronous request-time orchestration with strict preflight**
- **Decision:** Keep `verify_channel` as request-time orchestration, but enforce preflight sequence:
  1. Bot rights check
  2. Telethon transport connect
  3. Telethon authorization check
  4. Stats RPC calls
  5. Transactional persistence
- **Rationale:** Verification is an explicit operator/user action and should return immediate outcome. Preflight order minimizes expensive upstream calls and prevents partial writes.
- **Alternatives considered:** Async queue/Celery verification job. Rejected for now due to added orchestration complexity and weaker immediate UX for channel onboarding.

2) **Introduce explicit Telethon authorization state checks as a first-class readiness gate**
- **Decision:** Treat Telethon authorization as a hard gate for stats operations. If authorization state is not `authorized`, fail verification with controlled upstream error semantics.
- **Rationale:** `connect()` does not imply an authenticated session. Readiness must be derived from `is_user_authorized()`.
- **Alternatives considered:** Attempt stats call and infer authorization from RPC errors. Rejected because errors are noisier and less actionable for operators.

3) **Add controlled operator bootstrap flow for Telethon session authorization**
- **Decision:** Provide an operator-only bootstrap entrypoint (CLI command under backend runtime) that supports phone + OTP + optional 2FA password and writes session material to configured durable storage.
- **Rationale:** Authorization is a lifecycle operation, not a request-time fallback. A dedicated entrypoint removes ad-hoc shell procedures and allows auditability.
- **Alternatives considered:** In-request interactive login prompts. Rejected for security and API contract reasons.

4) **Support MTProto connectivity modes via strict settings contract**
- **Decision:** Support two transport modes in `TelegramClientService`:
  - default direct MTProto
  - MTProxy mode when `TELEGRAM_MTPROXY_HOST/PORT/SECRET` are fully configured
  MTProxy fields are all-or-none with fail-fast validation.
- **Rationale:** MTProto reachability varies by environment; strict config prevents silent misconfiguration.
- **Alternatives considered:** Supporting multiple proxy protocols in this change. Rejected to keep operational surface minimal.

5) **Separate operational error classes from authorization/business denial**
- **Decision:** Maintain current business-denial semantics (`403` for membership/bot-permission denial) and map Telegram upstream dependency failures to `502`.
- **Rationale:** Client behavior differs: permission denial is user/action dependent; upstream Telegram readiness is operational.
- **Alternatives considered:** Returning `500` for all failures. Rejected due to poor diagnosability and unclear retry semantics.

6) **Use log-driven observability for phase-level failures**
- **Decision:** Emit structured logs around verification phases (`bot_check`, `telethon_connect`, `telethon_auth`, `stats_fetch`, `persist`) and normalize failure reason identifiers.
- **Rationale:** Minimal-change observability that works with current stack and supports fast triage.
- **Alternatives considered:** Full metrics/tracing stack introduction in this change. Rejected as out of scope.

## Risks / Trade-offs

- **[Risk] Operator bootstrap remains a manual operational step** → **Mitigation:** Provide a single documented command flow with deterministic prompts and explicit success/failure output.
- **[Risk] Session material leakage via logs or shell history** → **Mitigation:** Never log OTP/2FA/session secrets; require secret injection via environment/secret manager; redact sensitive fields in errors.
- **[Risk] Single Telethon service account becomes an availability bottleneck** → **Mitigation:** Add readiness diagnostics and explicit re-authorization procedure; consider secondary account strategy in a later change if required.
- **[Risk] MTProxy endpoint instability or policy change** → **Mitigation:** Keep direct mode fallback capability and enforce clear startup/runtime errors for invalid proxy config.
- **[Risk] API clients may treat `502` as permanent failure** → **Mitigation:** Document retry semantics for `502` and include stable error detail indicating operational dependency failure.

## Migration Plan

1. Implement/complete Telethon transport config contract in settings and wrapper (including all-or-none MTProxy validation).
2. Add/complete verification preflight gate and ensure persistence guardrails on all failure paths.
3. Add operator bootstrap command for Telethon authorization lifecycle and secure session persistence.
4. Add/expand tests:
   - MTProxy config validation
   - unauthorized-session preflight behavior
   - endpoint mapping (`502`) for upstream failures
   - no partial persistence on failure
5. Update runbooks/docs for staging/production:
   - bootstrap command usage
   - session replacement
   - post-deploy readiness check
6. Rollout:
   - deploy code
   - run bootstrap once per environment
   - verify readiness and channel verification behavior

Rollback strategy:
- Revert change set and return to prior verification behavior.
- Keep session/proxy env values inert if wrapper changes are rolled back.

## Open Questions

- Should production session persistence be standardized on `TELEGRAM_SESSION_STRING` secret storage, or keep filesystem session files as the canonical source?
- What is the required operational access model for bootstrap (container shell only vs dedicated admin job runner)?
- Do we need a dedicated internal readiness endpoint for Telethon authorization/transport status, or are structured logs sufficient for first release?
