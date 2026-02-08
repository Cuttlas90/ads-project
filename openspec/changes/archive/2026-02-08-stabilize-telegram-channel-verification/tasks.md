## 1. Telegram Integration and Session Readiness

- [x] 1.1 Finalize `Settings` and `.env.example` contract for MTProto connectivity, including strict all-or-none validation for `TELEGRAM_MTPROXY_HOST`, `TELEGRAM_MTPROXY_PORT`, and `TELEGRAM_MTPROXY_SECRET`.
- [x] 1.2 Extend `TelegramClientService` to expose explicit authorization/readiness checks used by backend services before stats-dependent operations.
- [x] 1.3 Add/normalize controlled integration errors for incomplete MTProxy config and unauthorized Telethon session states.

## 2. Channel Verification Hardening

- [x] 2.1 Enforce Telethon preflight order in `verify_channel`: connect, authorization gate, then stats RPCs.
- [x] 2.2 Ensure all Telegram upstream failures in verification map to controlled `ChannelVerificationError` outcomes without partial persistence.
- [x] 2.3 Map verification upstream dependency failures to HTTP 502 in `/channels/{id}/verify` while preserving existing 403/404 behavior for business denials.
- [x] 2.4 Add structured phase-level logs (`bot_check`, `telethon_connect`, `telethon_auth`, `stats_fetch`, `persist`) with normalized failure reasons and redacted sensitive data.

## 3. Telethon Auth Bootstrap Flow

- [x] 3.1 Implement an operator-only backend bootstrap command for Telethon authorization (phone, OTP, optional 2FA) that is not invoked by request handlers.
- [x] 3.2 Persist authorized session material to the configured durable session source and support explicit session replacement.
- [x] 3.3 Ensure bootstrap flow never logs OTP, 2FA password, or raw session secrets.
- [x] 3.4 Document bootstrap and re-authorization runbook for staging/production operations.

## 4. Test Coverage and Verification

- [x] 4.1 Add/expand unit tests for Telethon integration readiness checks and MTProxy validation behavior.
- [x] 4.2 Add/expand channel verification tests for unauthorized Telethon session, MTProto transport failure, and no-partial-persistence guarantees.
- [x] 4.3 Add route-level tests confirming HTTP 502 mapping for Telegram upstream dependency failures.
- [x] 4.4 Run targeted backend tests for Telegram integration and channel verification, then run `openspec validate stabilize-telegram-channel-verification --strict`.
