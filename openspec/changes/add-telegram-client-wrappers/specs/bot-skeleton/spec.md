# bot-skeleton Specification

## MODIFIED Requirements
### Requirement: Bot package layout
The bot service SHALL include `bot/app/__init__.py`, a minimal `bot/app/main.py` entrypoint with no business logic, and `bot/app/settings.py` for environment-based configuration. The bot package SHALL remain a scaffold and MUST NOT include business logic.

#### Scenario: Minimal bot package
- **WHEN** a developer opens the bot package files
- **THEN** only package initialization, the minimal entrypoint, and the settings scaffold are present (no business logic)

## ADDED Requirements
### Requirement: Bot settings configuration
The bot service SHALL implement configuration using pydantic-settings with a Settings class and a cached `get_settings()` accessor, loading values from environment variables (env_file `.env`). It SHALL include the Telegram integration settings defined in the `telegram-integration` specification.

#### Scenario: Bot settings scaffold
- **WHEN** a developer inspects `bot/app/settings.py`
- **THEN** the Settings class uses pydantic-settings, exposes `get_settings()`, and defines the required Telegram fields
