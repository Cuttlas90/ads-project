## ADDED Requirements
### Requirement: Backend health endpoint
The backend service SHALL expose a `GET /health` endpoint that returns HTTP 200 with JSON body `{"status": "ok", "database": "connected"}`.

#### Scenario: Health check response
- **WHEN** a client requests `GET /health`
- **THEN** the response status is 200 and the JSON body matches the required structure

## MODIFIED Requirements
### Requirement: Backend package layout
The backend service SHALL include `backend/app/__init__.py` and `backend/tests/__init__.py`, plus minimal entrypoints in `backend/app/main.py` and `backend/app/worker/celery_app.py` to support the health endpoint and a Celery stub. No additional business logic is permitted in the skeleton.

#### Scenario: Minimal backend package
- **WHEN** a developer opens the backend package files
- **THEN** only package initialization, the `/health` endpoint, and the Celery stub are present
