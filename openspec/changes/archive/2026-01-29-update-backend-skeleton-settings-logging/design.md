## Context
The backend skeleton is a single-file FastAPI app with an inline /health endpoint. Compose supplies environment variables via .env, but there is no settings module or logging configuration to standardize behavior.

## Goals / Non-Goals
- Goals:
  - Provide a minimal app package layout with routers, settings, and logging.
  - Ensure /health stays stable and does not depend on database connectivity.
  - Keep compatibility with the existing docker compose workflow.
- Non-Goals:
  - No database session or ORM setup.
  - No auth, Telegram integration, or domain logic.
  - No changes to compose unless required for compatibility.

## Decisions
- Use pydantic-settings for configuration and expose a cached get_settings() helper.
- Default DATABASE_URL and REDIS_URL to the current compose .env.example values; derive Celery URLs from REDIS_URL unless explicitly set.
- Configure logging once in backend/app/logging.py using the LOG_LEVEL setting and keep uvicorn loggers aligned to that level.
- Introduce a root APIRouter in backend/app/api/router.py and include the health route from backend/app/api/routes/health.py.
- Add a minimal backend/app/api/deps.py to centralize dependency helpers (e.g., settings) for future routes.

## Risks / Trade-offs
- Health no longer reflects database connectivity; this is intentional for the skeleton but reduces operational signal.
- Standard logging (not fully JSON) keeps dependencies minimal but offers less structure.

## Migration Plan
- Add settings and logging modules.
- Refactor main.py to include the root router and invoke logging setup.
- Add tests for health, settings defaults/overrides, and logging configuration.
- Update backend dependencies to include pydantic-settings.

## Open Questions
- None.
