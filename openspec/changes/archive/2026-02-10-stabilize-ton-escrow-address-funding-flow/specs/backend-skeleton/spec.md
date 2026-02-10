## MODIFIED Requirements

### Requirement: Backend health endpoint
The backend service SHALL expose a GET `/health` endpoint that returns HTTP 200, MUST NOT require database connectivity, and SHALL report configuration readiness. The response JSON SHALL include:
- `status`: `ok` when all required enabled-subsystem checks pass, otherwise `degraded`.
- `checks`: an object with subsystem entries (`backend`, `ton`, `telegram`, `workers`), each containing `ready` (boolean) and `missing` (array of required env variable names not configured).

The endpoint SHALL evaluate required settings from runtime configuration:
- `ton` check when TON is enabled: `TON_HOT_WALLET_MNEMONIC`, `TONCENTER_API`, `TON_FEE_PERCENT`, `TONCONNECT_MANIFEST_URL`.
- `telegram` check when Telegram is enabled: `TELEGRAM_BOT_TOKEN`, `TELEGRAM_API_ID`, `TELEGRAM_API_HASH`.
- `workers` check: broker/backend readiness via `REDIS_URL` or explicit `CELERY_BROKER_URL` and `CELERY_RESULT_BACKEND`.

The endpoint MUST NOT expose secret values; it SHALL only return key names and readiness booleans.

#### Scenario: Fully configured health response
- **WHEN** all required env settings for enabled subsystems are configured
- **THEN** `GET /health` returns HTTP 200 with `status = ok` and empty `missing` arrays for checked subsystems

#### Scenario: Missing TON setting is reported
- **WHEN** TON is enabled and `TONCENTER_API` is missing
- **THEN** `GET /health` returns HTTP 200 with `status = degraded` and `checks.ton.missing` including `TONCENTER_API`

#### Scenario: Health diagnostics never leak secret values
- **WHEN** `GET /health` is requested
- **THEN** response includes only readiness flags and missing env key names, without returning any environment variable values
