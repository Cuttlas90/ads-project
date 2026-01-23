## ADDED Requirements
### Requirement: Backend Poetry scaffold
The backend service SHALL include a Poetry-managed `backend/pyproject.toml` with development dependencies for black, ruff, and pytest.

#### Scenario: Backend dependencies present
- **WHEN** a developer inspects `backend/pyproject.toml`
- **THEN** black, ruff, and pytest are listed as development dependencies

### Requirement: Backend package layout
The backend service SHALL include `backend/app/__init__.py` and `backend/tests/__init__.py` with no application logic.

#### Scenario: Minimal backend package
- **WHEN** a developer opens the backend package files
- **THEN** only package initialization is present and no endpoints or business logic exist
