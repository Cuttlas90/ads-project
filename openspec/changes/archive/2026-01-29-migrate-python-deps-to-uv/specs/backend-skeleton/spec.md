## RENAMED Requirements
- FROM: `### Requirement: Backend Poetry scaffold`
- TO: `### Requirement: Backend dependency scaffold`

## MODIFIED Requirements
### Requirement: Backend dependency scaffold
The backend service SHALL include a PEP 621 `backend/pyproject.toml` with `[project]` metadata and `[dependency-groups]`. The `dev` dependency group SHALL include black, ruff, and pytest. Poetry-specific sections MUST NOT be required for managing backend dependencies.

#### Scenario: Backend dependencies present
- **WHEN** a developer inspects `backend/pyproject.toml`
- **THEN** the file defines `[project]` metadata and a `dev` dependency group containing black, ruff, and pytest
