## MODIFIED Requirements
### Requirement: Bot package layout
The bot service SHALL include `bot/app/__init__.py`, a `bot/app/main.py` entrypoint, and `bot/app/settings.py` for environment-based configuration. The bot package MAY include business logic required for bot-only deal messaging and polling-based update handling.

#### Scenario: Bot package includes messaging logic
- **WHEN** a developer opens the bot package files
- **THEN** the bot entrypoint and messaging handlers are present to support bot-only deal messaging
