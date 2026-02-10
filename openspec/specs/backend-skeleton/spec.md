# backend-skeleton Specification

## Purpose
TBD - created by archiving change add-monorepo-skeleton. Update Purpose after archive.
## Requirements
### Requirement: Backend package layout
The backend service SHALL include backend/app/__init__.py and backend/tests/__init__.py, plus minimal entrypoints in backend/app/main.py and backend/app/worker/celery_app.py. The backend package SHALL include backend/app/settings.py, backend/app/logging.py, backend/app/api/__init__.py, backend/app/api/router.py, backend/app/api/deps.py, backend/app/api/routes/__init__.py, and backend/app/api/routes/health.py to wire the FastAPI app, configuration, logging, and the /health route. No additional business logic is permitted in the skeleton.

#### Scenario: Minimal backend package
- **WHEN** a developer opens the backend package files
- **THEN** only package initialization, settings/logging setup, API routing, the /health endpoint, and the Celery stub are present

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

### Requirement: Backend settings configuration
The backend service SHALL implement configuration using pydantic-settings and load values from environment variables. It SHALL define ENV (default "dev"), APP_NAME (default "Telegram Ads Marketplace API"), LOG_LEVEL (default "INFO"), DATABASE_URL (default "postgresql+psycopg://ads:ads@postgres:5432/ads"), REDIS_URL (default "redis://redis:6379/0"), CELERY_BROKER_URL (default to REDIS_URL), and CELERY_RESULT_BACKEND (default to REDIS_URL). The settings module SHALL expose a cached get_settings() accessor, and pydantic-settings SHALL be listed as a runtime dependency in backend/pyproject.toml.

#### Scenario: Settings defaults
- **WHEN** no environment overrides are provided
- **THEN** settings load with the documented default values

#### Scenario: Settings overrides
- **WHEN** environment variables are set for the listed fields
- **THEN** the settings values match the provided environment values

### Requirement: Backend logging configuration
The backend service SHALL configure logging in backend/app/logging.py using the LOG_LEVEL setting and apply that configuration once during application startup. The configuration MUST NOT cause startup errors and SHOULD keep uvicorn loggers aligned to the configured level.

#### Scenario: Logging configured
- **WHEN** the application starts
- **THEN** logs are emitted at the configured level without configuration errors

### Requirement: Backend API routing
The backend service SHALL define a root APIRouter in backend/app/api/router.py and include the health route from backend/app/api/routes/health.py at path /health. The FastAPI application in backend/app/main.py SHALL include this root router.

#### Scenario: Router wiring
- **WHEN** the FastAPI application is initialized
- **THEN** the root router is included and the /health route is served via the router

### Requirement: Backend dependency scaffold
The backend service SHALL include a PEP 621 `backend/pyproject.toml` with `[project]` metadata and `[dependency-groups]`. The `dev` dependency group SHALL include black, ruff, and pytest. Poetry-specific sections MUST NOT be required for managing backend dependencies.

#### Scenario: Backend dependencies present
- **WHEN** a developer inspects `backend/pyproject.toml`
- **THEN** the file defines `[project]` metadata and a `dev` dependency group containing black, ruff, and pytest

