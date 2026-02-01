# Change: Add TON escrow funding flow

## Why
The MVP requires real TON escrow funding with deterministic per-deal deposit addresses, on-chain confirmation, and explicit escrow/deal state transitions. This change defines the escrow model, TON address derivation, chain watcher, and funding notifications needed to move deals to FUNDED safely.

## What Changes
- Add escrow persistence, events, and an escrow FSM with explicit transitions.
- Add TON settings, deterministic per-deal deposit address derivation (Tonkeeper-valid W5), and TONConnect payload generation endpoints (backend only).
- Add TonCenter V3 chain adapter and a Celery-beat watcher to detect deposits and confirm funding.
- Extend deal FSM to allow system transition from ACCEPTED to FUNDED when escrow is funded.
- Add bot notifications to advertiser and channel owner when funding is confirmed.

## Impact
- Affected specs: deal-management (modified), escrow-management (new), ton-integration (new), escrow-watcher (new), bot-deal-notifications (new).
- Affected code: backend models/migrations/services/routes/worker, shared DB models, bot notification integration, settings/.env.example, tests.
- Out of scope: frontend TonConnect UI, payouts/releases, refunds, disputes, KYC/geo, manual escrow confirmation.
