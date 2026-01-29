# Telegram Ads Marketplace

This repository contains the skeleton for a monorepo that will power a Telegram ads marketplace.

## Repository structure
- `backend/` — Python FastAPI backend skeleton (includes `/health`)
- `bot/` — Python bot service (skeleton only for now)
- `frontend/` — Vue 3 + Vite + TypeScript frontend (skeleton only for now)
- `infra/` — Docker Compose stack for local development
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
