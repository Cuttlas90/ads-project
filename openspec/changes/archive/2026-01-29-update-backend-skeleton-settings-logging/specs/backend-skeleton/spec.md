## ADDED Requirements
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

## MODIFIED Requirements
### Requirement: Backend package layout
The backend service SHALL include backend/app/__init__.py and backend/tests/__init__.py, plus minimal entrypoints in backend/app/main.py and backend/app/worker/celery_app.py. The backend package SHALL include backend/app/settings.py, backend/app/logging.py, backend/app/api/__init__.py, backend/app/api/router.py, backend/app/api/deps.py, backend/app/api/routes/__init__.py, and backend/app/api/routes/health.py to wire the FastAPI app, configuration, logging, and the /health route. No additional business logic is permitted in the skeleton.

#### Scenario: Minimal backend package
- **WHEN** a developer opens the backend package files
- **THEN** only package initialization, settings/logging setup, API routing, the /health endpoint, and the Celery stub are present

### Requirement: Backend health endpoint
The backend service SHALL expose a GET /health endpoint that returns HTTP 200 with JSON body {"status": "ok"} and MUST NOT require database connectivity.

#### Scenario: Health check response
- **WHEN** a client requests GET /health
- **THEN** the response status is 200 and the JSON body matches the required structure without requiring a database connection
