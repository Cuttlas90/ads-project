# bot-skeleton Specification

## Purpose
TBD - created by archiving change add-monorepo-skeleton. Update Purpose after archive.
## Requirements
### Requirement: Bot package layout
The bot service SHALL include `bot/app/__init__.py`, a `bot/app/main.py` entrypoint, and `bot/app/settings.py` for environment-based configuration. The bot package MAY include business logic required for bot-only deal messaging and polling-based update handling.

#### Scenario: Bot package includes messaging logic
- **WHEN** a developer opens the bot package files
- **THEN** the bot entrypoint and messaging handlers are present to support bot-only deal messaging

### Requirement: Bot dependency scaffold
The bot service SHALL include a PEP 621 `bot/pyproject.toml` with `[project]` metadata and `[dependency-groups]`. The `dev` dependency group SHALL include black, ruff, and pytest. Poetry-specific sections MUST NOT be required for managing bot dependencies.

#### Scenario: Bot dependencies present
- **WHEN** a developer inspects `bot/pyproject.toml`
- **THEN** the file defines `[project]` metadata and a `dev` dependency group containing black, ruff, and pytest

### Requirement: Bot settings configuration
The bot service SHALL implement configuration using pydantic-settings with a Settings class and a cached `get_settings()` accessor, loading values from environment variables (env_file `.env`). It SHALL include the Telegram integration settings defined in the `telegram-integration` specification.

#### Scenario: Bot settings scaffold
- **WHEN** a developer inspects `bot/app/settings.py`
- **THEN** the Settings class uses pydantic-settings, exposes `get_settings()`, and defines the required Telegram fields

