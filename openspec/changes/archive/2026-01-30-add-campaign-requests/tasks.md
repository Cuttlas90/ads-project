## 1. Implementation
- [ ] 1.1 Confirm FastAPI/SQLModel patterns via context7 before coding.
- [ ] 1.2 Add `CampaignRequest` and `CampaignApplication` SQLModel definitions in `shared/db/models`, plus exports in `shared/db/base.py`, `shared/db/models/__init__.py`, and `backend/app/models/__init__.py`.
- [ ] 1.3 Create Alembic migration(s) for `campaign_requests` and `campaign_applications` with FKs, indexes, and unique constraints.
- [ ] 1.4 Add Pydantic schemas for campaign requests, applications, and paginated responses.
- [ ] 1.5 Implement `/campaigns` create/list/view routes with validation and ownership checks; wire router.
- [ ] 1.6 Implement `/campaigns/{campaign_id}/apply` and `/campaigns/{campaign_id}/applications` routes, including channel-owner and verified-channel checks plus stats summary.
- [ ] 1.7 Add tests for campaign request CRUD and applications (including error cases and pagination totals).
- [ ] 1.8 Run `cd /home/mohsen/ads-project/backend && source .venv/bin/activate && DATABASE_URL=sqlite:// pytest`.
