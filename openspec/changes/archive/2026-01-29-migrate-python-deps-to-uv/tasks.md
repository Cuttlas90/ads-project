## 1. Implementation
- [x] 1.1 Update backend/pyproject.toml to PEP 621 `[project]` metadata with runtime deps and a `dev` dependency group.
- [x] 1.2 Update bot/pyproject.toml to PEP 621 `[project]` metadata with a `dev` dependency group.
- [x] 1.3 Replace Poetry references in README.md with uv-based install/run instructions.
- [x] 1.4 Update Makefile dev/lint/test guidance to use uv commands and keep safe no-op behavior.
- [x] 1.5 Update openspec/project.md to state uv as the Python dependency manager.
- [x] 1.6 Adjust Dockerfiles or other tooling to remain compatible with the new pyproject layout (if needed).
- [x] 1.7 Validate: ensure uv installs dev deps for backend/bot and pytest runs.
