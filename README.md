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

### Wallet proof flow
Wallet persistence now uses TonConnect proof challenge/verify endpoints:
- `POST /users/me/wallet/challenge` issues a one-time challenge (TTL: 5 minutes).
- `POST /users/me/wallet/verify` verifies TonConnect proof + app domain and updates `ton_wallet_address`.
- Legacy `PUT /users/me/wallet` is gated and no longer accepts direct wallet strings.

Frontend behavior:
- Profile contains the wallet connect/update flow.
- Advertiser funding (`/advertiser/deals/:id/fund`) is hard-blocked if wallet is missing and shows a modal that links to Profile with `next` return path.
- `/auth/me` now includes `ton_wallet_address` and `has_wallet` for cheap route guards.

### Telethon Bootstrap and Re-Authorization
Channel verification uses Telethon stats calls, so a logged-in Telethon **user account session** is required.
`TELEGRAM_BOT_TOKEN` alone is not enough for this flow.

1. Configure Telegram credentials in `.env`:
`TELEGRAM_API_ID`, `TELEGRAM_API_HASH`, optional MTProxy fields (`TELEGRAM_MTPROXY_HOST`, `TELEGRAM_MTPROXY_PORT`, `TELEGRAM_MTPROXY_SECRET`).
2. Configure a durable session target (recommended):
`TELEGRAM_SESSION_STRING_PATH=/app/.secrets/telethon_session.txt`
3. Run bootstrap explicitly (operator-only, once per environment) to add/refresh the Telethon user session:
```bash
docker compose --env-file .env -f infra/docker-compose.yml exec backend uv run telethon-bootstrap
```
4. Re-authorize by re-running the same command; it replaces the persisted session string.
5. If you change Telegram env values (`TELEGRAM_SESSION_STRING_PATH`, MTProxy fields, API credentials), recreate backend and run bootstrap again.

Notes:
- The bootstrap command prompts for phone, OTP, and 2FA only when needed.
- OTP, 2FA password, and raw session string are not logged by the command.

### Telegram Media Upload Channel
Creative uploads use Telegram Bot API and require a private storage channel:

- Set `TELEGRAM_MEDIA_CHANNEL_ID` in `.env` to the channel chat ID (typically `-100...`).
- Add the bot to that private channel as admin.
- Ensure the bot has permission to send photos/videos in that channel.

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
