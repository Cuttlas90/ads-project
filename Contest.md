# Telegram Mini App – Ads Marketplace (MVP)

## Goal
Build an MVP Telegram Mini App for an ads marketplace that connects channel owners and advertisers using an escrow-style deal flow.

## Short Project Overview

### Architecture
- Monorepo with clear service boundaries:
  - `frontend/`: Vue 3 + Pinia + Vue Router Telegram Mini App UI.
  - `backend/`: FastAPI API layer + domain/services + Celery workers.
  - `bot/`: Telegram Bot API polling worker for deal messaging.
  - `shared/`: shared SQLModel models/session and Telegram wrappers used by backend and bot.
- Data + jobs:
  - PostgreSQL as source of truth (Alembic migrations).
  - Redis + Celery (`worker` + `beat`) for async/scheduled flows.
  - Scheduled jobs handle escrow scan, auto-posting, and post verification.
- Integrations:
  - Telegram Mini App `initData` auth for API access.
  - Telegram Bot API for messaging/posting/media upload.
  - Telethon (MTProto) for channel verification/stats/permission checks.
  - TON via Toncenter + tonutils for escrow funding, release, and refund.

### Key Decisions
- Telegram-native auth only (no JWT/session auth), aligned with Mini App constraints.
- Explicit deal and escrow finite-state transitions with event logs (`deal_events`, `escrow_events`) instead of implicit status mutation.
- Per-deal escrow address derivation from hot-wallet mnemonic using deterministic subwallet IDs.
- Asynchronous side effects (funding detection, posting, verification, payout/refund) are worker-driven to keep API requests short and deterministic.
- UI uses role-based route access (owner/advertiser/shared) and centralized notification policy (local inline + global toast + blocking modal).

### Future Thoughts
- Wire manager access revalidation into all sensitive actions (funding/posting/release), not just membership records.
- Expand marketplace matching/filtering beyond current pricing/subscriber/views-focused criteria.
- Add broader timeout automation for stalled negotiation/approval phases (not only funding/post-retention paths).
- Improve operational hardening: richer observability, retry/idempotency controls, and alerting around Telegram/TON failures.
- better charts and stats view: currently its only show charts with no interaction, also there is some unsupported data format that should implemented.

### Known Limitations
- System health depends heavily on correct Telegram + TON environment setup; missing keys degrade critical flows.
- Telethon user-session bootstrap is an operator/manual step and adds operational overhead.
- Bot service uses long polling (`getUpdates`) instead of webhooks, which is simpler but less scalable.
- Channel manager support exists, but many critical flows remain owner-centric.
- Mini App intentionally avoids in-app chat; negotiation messaging is bot-mediated text flow.

## Checklist

---

### 1. Marketplace Model (Both Sides Supported)

- [x] Support Channel Owners
- [x] Support Advertisers
- [x] Ensure both entry points converge into a unified deal workflow
- [x] Use Telegram text bot for messaging (no in-app chat)

---

### 2. Channel Owner Listings

- [x] Allow channel owners to list their channel
- [x] Allow setting pricing
- [x] Require adding platform bot as channel admin
- [x] Verify admin rights
- [x] Re-check admin rights before financial/critical operations
- [ ] Support multiple channel managers (PR manager flow)
- [ ] Fetch channel admins with required rights

---

### 3. Advertiser Requests / Campaign Flow

- [x] Allow advertisers to create a campaign brief
- [x] Allow channel owners to apply to campaigns
- [x] Implement practical filters:
  - [x] Pricing
  - [x] Subscribers
  - [x] Average views
  - [ ] Other relevant criteria

---

### 4. Unified Negotiation & Approval Workflow

- [x] Advertiser submits brief
- [x] Channel owner accepts or rejects
- [x] Channel owner drafts creative
- [x] Advertiser approves or requests edits
- [x] Approved post is auto-published at agreed time

---

### 5. Verified Telegram Channel Stats

- [x] Fetch subscribers
- [x] Fetch average views / reach
- [x] Fetch language charts
- [x] Fetch Telegram Premium stats
- [x] Display verified stats in UI

---

### 6. Ad Formats & Pricing

- [x] Support pricing for multiple ad formats within a channel
- [x] MVP supports post format
- [x] Use flexible pricing structure (not strict ad-type schema)

---

### 7. Escrow Deal Flow (TON-Based)

- [x] Advertiser makes payment
- [x] Funds held in escrow
- [x] Auto-post confirms delivery
- [x] Release funds or refund accordingly
- [x] Use new address/wallet per deal or per user (except hot wallet)
- [x] Implement deal lifecycle controls
- [ ] Implement auto-cancel / timeout if deal stalls
- [x] Define clear deal statuses and transitions

---

### 8. Auto-Posting & Verification

- [x] Auto-post approved creative to channel
- [x] Verify post exists
- [x] Verify post is not deleted
- [x] Verify post is not edited
- [x] Ensure post remains live for required duration
- [x] Release funds after successful verification
