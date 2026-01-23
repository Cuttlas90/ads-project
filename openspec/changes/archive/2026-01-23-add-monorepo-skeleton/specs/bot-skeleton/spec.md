## ADDED Requirements
### Requirement: Bot Poetry scaffold
The bot service SHALL include a Poetry-managed `bot/pyproject.toml` with development dependencies for black, ruff, and pytest.

#### Scenario: Bot dependencies present
- **WHEN** a developer inspects `bot/pyproject.toml`
- **THEN** black, ruff, and pytest are listed as development dependencies

### Requirement: Bot package layout
The bot service SHALL include `bot/app/__init__.py` with no application logic.

#### Scenario: Minimal bot package
- **WHEN** a developer opens the bot package file
- **THEN** only package initialization is present and no business logic exists
