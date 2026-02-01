## Context
The project requires real TON escrow funding with one unique deposit address per deal and explicit FSM-driven state transitions (Project Constitution §6, §8). This change introduces escrow persistence, deterministic address derivation compatible with Tonkeeper wallet standards, and an on-chain watcher that confirms deposits via TonCenter.

## Goals / Non-Goals
- Goals:
  - Deterministic per-deal TON deposit address derivation with no per-deal private key storage.
  - Escrow FSM with auditable transitions and deal binding (ACCEPTED -> FUNDED).
  - TonCenter-based chain scanning with confirmation thresholds and idempotent processing.
  - Bot notifications to advertiser and channel owner when funding is confirmed.
- Non-Goals:
  - Frontend TonConnect UI integration.
  - Payouts/releases, refunds, disputes, KYC/geo, or manual escrow confirmation.

## Decisions
- Wallet version: Use Tonkeeper-valid W5 wallet contract for derived deposit addresses.
- Library: Use `tonutils` for deterministic address derivation with `WalletV5R1` (W5) support.
- Deterministic mapping: `subwallet_id = hash(deal_id) mod 2^31` (unsigned 32-bit range) to avoid unbounded indices while keeping deterministic mapping.
- Expected amount: `expected_amount_ton = deal.price_ton`. Deposits are accepted when total received >= expected. Partial/multiple txs are allowed; overpayment is recorded but not used for payout in this scope.
- Chain provider: TonCenter V3 JSON-RPC, configurable via `TONCENTER_API` and `TONCENTER_KEY` (optional).
- Network defaults: `TON_NETWORK` defaults to `testnet` in `ENV=dev`, `mainnet` otherwise; always overrideable by env.
- Confirmations: `TON_CONFIRMATIONS_REQUIRED` default = 3.
- Scheduler: Celery beat runs the watcher every 60 seconds by default.
- Notification text: send “Funds for deal #<id> deposited” to both parties via the bot upon FUNDED transition.
- Settings: include `TONCONNECT_MANIFEST_URL` now for backend payload generation, even though frontend is out of scope.

## Alternatives considered
- Using TonCenter REST v2 endpoints: rejected in favor of v3 JSON-RPC for consistent tx/query handling.
- Using a high-level TON SDK (pytoniq/TonTools): rejected in favor of minimal derivation-only dependency (`tonsdk`) given chain scanning is done via TonCenter.
- Single-tx-only funding: rejected to allow multiple partial deposits on a per-deal address.

## Risks / Trade-offs
- W5 derivation support in `tonsdk` must be verified; if unsupported, we may need to switch wallet version or library.
- Overpayment handling is deferred; extra funds will remain at the deposit address until release/refund logic is implemented.
- TonCenter API changes or rate limits could affect watcher reliability; adapter is kept minimal with optional API key support.

## Migration Plan
- Add new escrow and escrow_events tables via Alembic migration.
- Add new services (escrow FSM, TON derivation, TonCenter adapter, watcher) and wire endpoints.
- Update deal FSM transition table to allow system-funded transition.
- Add bot notification hook on FUNDED transition.
- Update settings and `.env.example` with TON-related variables.

## Open Questions
- None for proposal stage. If W5 support is missing in `tonsdk`, decision may need revision before implementation.
