## 1. Data model & migrations
- [x] 1.1 Add `deal_escrows` + `escrow_events` models and Alembic migration.
- [x] 1.2 Register escrow models in `shared/db/base.py`.

## 2. Settings & env
- [x] 2.1 Add TON settings (network, confirmations, fee percent, mnemonic, TonCenter API/key, TONCONNECT_MANIFEST_URL).
- [x] 2.2 Update `.env.example` with TON placeholders.

## 3. Escrow FSM + endpoints
- [x] 3.1 Implement EscrowState enum, transition table, and `apply_escrow_transition` with escrow_events.
- [x] 3.2 Implement `POST /deals/{id}/escrow/init` (advertiser-only, idempotent, ACCEPTED-only).

## 4. TON integration
- [x] 4.1 Implement deterministic address derivation (tonutils + WalletV5R1 + hash/mod) and store deposit address.
- [x] 4.2 Implement TONConnect payload builder and `POST /deals/{id}/escrow/tonconnect-tx`.
- [x] 4.3 Implement TonCenter V3 JSON-RPC adapter for tx lookup + confirmations.

## 5. Chain watcher
- [x] 5.1 Add Celery beat schedule (default 60s) for escrow watcher.
- [x] 5.2 Implement idempotent watcher logic to aggregate partial deposits and transition escrow/deal to FUNDED.

## 6. Deal FSM update
- [x] 6.1 Add system transition `ACCEPTED -> FUNDED` and extend FSM tests.

## 7. Bot notifications
- [x] 7.1 Send bot message “Funds for deal #<id> deposited” to advertiser and channel owner on FUNDED transition.

## 8. Tests
- [x] 8.1 Escrow FSM table-driven tests.
- [x] 8.2 TONConnect payload unit tests.
- [x] 8.3 Watcher idempotency tests with mocked adapter.
- [x] 8.4 API tests for escrow init/tonconnect authorization + idempotency.
- [x] 8.5 Bot notification tests.

## 9. Validation & docs
- [x] 9.1 Update README / docs with TON env vars and watcher info.
- [x] 9.2 Run `openspec validate add-ton-escrow-funding --strict` and fix any issues.
