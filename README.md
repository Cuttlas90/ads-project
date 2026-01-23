# Telegram Ads Marketplace

This repository contains the skeleton for a monorepo that will power a Telegram ads marketplace.

## Repository structure
- `backend/` — Python backend service (FastAPI later; skeleton only for now)
- `bot/` — Python bot service (skeleton only for now)
- `frontend/` — Vue 3 + Vite + TypeScript frontend (skeleton only for now)
- `infra/` — Infrastructure scaffolding (empty placeholder for now)
- `docs/` — Project documentation

## Quick start

### Frontend
```bash
cd frontend
npm install
npm run dev
```

### Backend / Bot (Poetry)
```bash
cd backend
poetry install

cd ../bot
poetry install
```

## Tooling
Root Makefile commands:
- `make help` — list available commands
- `make dev` — prints guidance for running services
- `make lint` — run configured linters if available
- `make test` — run configured tests if available
