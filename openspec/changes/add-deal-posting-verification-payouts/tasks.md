## 1. Proposal Validation
- [x] 1.1 Run `openspec validate add-deal-posting-verification-payouts --strict` and fix all issues.

## 2. Data Model & Migrations
- [x] 2.1 Add deal fields for scheduling and posting metadata (`scheduled_at`, `verification_window_hours`, `posted_*`, `verified_at`).
- [x] 2.2 Add escrow release/refund fields (`release_tx_hash`, `refund_tx_hash`, `released_amount_ton`, `refunded_amount_ton`, timestamps).
- [x] 2.3 Add `ton_wallet_address` to users.
- [x] 2.4 Create Alembic migrations and update SQLModel models.

## 3. Deal FSM & Services
- [x] 3.1 Extend deal FSM transitions for scheduling, posting, verification, release, and refund.
- [x] 3.2 Implement auto-post scheduler service and Celery beat task.
- [x] 3.3 Implement bot publishing (sendMessage/sendPhoto/sendVideo) with content hash storage.

## 4. Verification Workflow
- [x] 4.1 Implement Telethon verification service to fetch message and compute hash.
- [x] 4.2 Implement verification watcher task (idempotent) with window enforcement.

## 5. Payout & Refund
- [x] 5.1 Implement TON transfer service for release/refund using TonCenter/tonutils.
- [x] 5.2 Apply fee logic for release and network fee for refunds.
- [x] 5.3 Record transaction hashes and amounts on escrow.

## 6. API Additions
- [x] 6.1 Add `PUT /users/me/wallet` endpoint with validation.

## 7. Tests (Mandatory)
- [x] 7.1 Posting service tests (mock Bot API, scheduled time, metadata stored).
- [x] 7.2 Verification service tests (message exists, deleted, edited).
- [x] 7.3 Payout/refund tests (mock TON transfers, fee calculations, transaction logging).
- [x] 7.4 Celery task tests (idempotent scheduling and verification).
- [x] 7.5 Run backend test suite using: `cd /home/mohsen/ads-project/backend && source .venv/bin/activate && DATABASE_URL=postgresql+psycopg://ads:ads@localhost:5432/ads pytest`
- [x] 7.6 Run bot test suite using: `cd /home/mohsen/ads-project/bot && source .venv/bin/activate && DATABASE_URL=postgresql+psycopg://ads:ads@localhost:5432/ads pytest`
