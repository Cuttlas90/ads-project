# Change: Migrate Python dependency management to uv + PEP 621

## Why
The repo currently relies on Poetry, but the team wants to standardize on uv and PEP 621 dependency-groups for all Python services. This change removes Poetry-specific metadata and updates tooling instructions to match uv workflows.

## What Changes
- **BREAKING**: Replace Poetry-managed pyproject.toml files with PEP 621 `[project]` metadata and `[dependency-groups]` for backend and bot.
- Update Python dependency installation and execution guidance to use uv (Makefile + README + project conventions).
- Ensure Dockerfiles and compose remain compatible with the new pyproject layout.

## Impact
- Affected specs: backend-skeleton, bot-skeleton
- Affected docs/tooling: openspec/project.md, README.md, Makefile
- Affected code: backend/pyproject.toml, bot/pyproject.toml, Dockerfiles as needed
