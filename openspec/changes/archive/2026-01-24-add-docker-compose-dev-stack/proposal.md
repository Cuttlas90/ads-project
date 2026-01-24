# Change: Add Docker Compose dev stack

## Why
Developers need a single-command local environment to run the backend, worker, frontend, and dependencies consistently.

## What Changes
- Add a Docker Compose dev stack in `infra/docker-compose.yml` for postgres, redis, backend, worker, frontend, and an optional bot profile.
- Add dev-focused Dockerfiles for backend, frontend, and bot (when enabled).
- Update backend and bot skeleton specs to permit minimal entrypoints (`/health` and bot main).
- Expand `.env.example` with compose-ready environment variables and placeholders.

## Impact
- Affected specs: backend-skeleton, bot-skeleton, local-dev-stack (new)
- Affected code: `infra/docker-compose.yml`, `backend/Dockerfile`, `frontend/Dockerfile`, `bot/Dockerfile`, `.env.example`, `backend/app/main.py`, `backend/app/worker/celery_app.py`, `bot/app/main.py`
