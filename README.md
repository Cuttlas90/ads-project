# Telegram Ads Marketplace

This repository contains the skeleton for a monorepo that will power a Telegram ads marketplace.

## Repository structure
- `backend/` — Python FastAPI backend skeleton (includes `/health`)
- `bot/` — Python bot service (skeleton only for now)
- `frontend/` — Vue 3 + Vite + TypeScript frontend (skeleton only for now)
- `infra/` — Docker Compose stack for local development
- `shared/` — Shared Python modules (DB models/session) used by backend and bot
- `docs/` — Project documentation

## Quick start

## Prerequisites
- Python 3.11+
- uv
- Docker (for local dev stack)
- Node.js + npm (for frontend)

### Local dev stack (Docker)
```bash
cp .env.example .env
docker compose --env-file .env -f infra/docker-compose.yml up --build
```

### TON configuration
Set TON variables in `.env` for escrow funding:
- `TON_FEE_PERCENT`, `TON_HOT_WALLET_MNEMONIC`, `TONCENTER_API`, optional `TONCENTER_KEY`
- `TON_NETWORK` defaults to `testnet` in `ENV=dev`
The escrow watcher runs via Celery beat every 60 seconds.

### Frontend
```bash
cd frontend
npm install
npm run dev
```

### Backend / Bot (uv)
```bash
cd backend
uv pip install -e . --group dev

cd ../bot
uv pip install -e . --group dev
```

### Shared module (local runs)
If you run backend or bot outside Docker, ensure the repo root is on `PYTHONPATH` so `shared/` imports resolve:
```bash
export PYTHONPATH="$(pwd)"
```

### Alembic (backend)
```bash
cd backend
alembic -c alembic.ini upgrade head
alembic -c alembic.ini revision --autogenerate -m "describe_change"
```

### Health check
```bash
curl http://localhost:8000/health
```

## Tooling
Root Makefile commands:
- `make help` — list available commands
- `make dev` — prints guidance for running services
- `make lint` — run configured linters if available
- `make test` — run configured tests if available
- `make test-db` — start Postgres via Docker and run backend DB tests
