## 1. Implementation
- [x] 1.1 Add settings module using pydantic-settings with required fields, defaults, and cached get_settings().
- [x] 1.2 Add logging configuration module and wire it into application startup (depends on 1.1).
- [x] 1.3 Create API router package (api/router.py, api/routes/health.py, api/deps.py) and include it from main.py.
- [x] 1.4 Update /health response to return {"status": "ok"} without database checks.
- [x] 1.5 Add pydantic-settings to backend/pyproject.toml dependencies.
- [x] 1.6 Add tests for health, settings defaults/overrides, and logging configuration (depends on 1.1-1.4).
- [x] 1.7 Validate: run pytest; confirm docker compose builds and /health responds as expected (depends on 1.1-1.6).
