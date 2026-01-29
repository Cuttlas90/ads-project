## Context
Backend and bot services currently use Poetry-managed pyproject.toml files. The team wants uv-native dependency management with PEP 621 metadata and dependency groups for development tooling.

## Goals / Non-Goals
- Goals:
  - Migrate backend and bot to PEP 621 `[project]` metadata and `[dependency-groups]`.
  - Use uv as the documented installation/execution tool across Python services.
  - Keep Docker and compose workflows functional without introducing domain logic.
- Non-Goals:
  - No changes to runtime behavior, APIs, or business logic.
  - No new services or infrastructure changes.
  - No change to frontend tooling.

## Decisions
- Use PEP 621 `[project]` metadata with a `dev` dependency group for black/ruff/pytest.
- Use a standard build backend (setuptools) that supports editable installs with uv.
- Update Makefile/README and project conventions to reference uv rather than Poetry.
- Keep Dockerfiles uv-based; adjust install flags only if required by the new pyproject layout.

## Risks / Trade-offs
- Tooling drift if some contributors still use Poetry; mitigate with docs and Makefile guidance.
- uv version differences could affect group handling; mitigate by documenting minimum uv version.

## Migration Plan
- Convert backend/pyproject.toml and bot/pyproject.toml to PEP 621 + dependency groups.
- Update project.md to reflect uv usage for Python dependency management.
- Update Makefile and README to use uv commands.
- Validate that docker compose builds and local tests run with uv-installed dev deps.

## Open Questions
- None.
