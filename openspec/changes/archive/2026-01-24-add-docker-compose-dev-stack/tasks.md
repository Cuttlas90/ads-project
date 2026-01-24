## 1. Implementation
- [x] 1.1 Create `infra/docker-compose.yml` with postgres, redis, backend, worker, frontend, and optional bot profile wiring.
- [x] 1.2 Add dev-focused Dockerfiles for backend and frontend (and bot if enabled by profile).
- [x] 1.3 Implement minimal FastAPI app with `/health` JSON and a Celery app stub.
- [x] 1.4 Add minimal bot entrypoint to support the bot container.
- [x] 1.5 Update `.env.example` with compose-ready variables and placeholders.
- [ ] 1.6 Validate compose boot locally against acceptance criteria (manual run).
