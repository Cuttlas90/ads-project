## RENAMED Requirements
- FROM: `### Requirement: Bot Poetry scaffold`
- TO: `### Requirement: Bot dependency scaffold`

## MODIFIED Requirements
### Requirement: Bot dependency scaffold
The bot service SHALL include a PEP 621 `bot/pyproject.toml` with `[project]` metadata and `[dependency-groups]`. The `dev` dependency group SHALL include black, ruff, and pytest. Poetry-specific sections MUST NOT be required for managing bot dependencies.

#### Scenario: Bot dependencies present
- **WHEN** a developer inspects `bot/pyproject.toml`
- **THEN** the file defines `[project]` metadata and a `dev` dependency group containing black, ruff, and pytest
