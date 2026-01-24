## MODIFIED Requirements
### Requirement: Bot package layout
The bot service SHALL include `bot/app/__init__.py` and a minimal `bot/app/main.py` entrypoint with no business logic.

#### Scenario: Minimal bot package
- **WHEN** a developer opens the bot package files
- **THEN** only package initialization and the minimal entrypoint are present
