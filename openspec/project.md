# Telegram Ads Marketplace – Engineering RFC (Project Constitution)

## 1. Purpose

This document defines the **authoritative project specification** for building an MVP Telegram Mini App that acts as an **ads marketplace** connecting advertisers and Telegram channel owners, with a **secure escrow-based deal flow** and **mandatory auto-posting verification**.

This file is the **single source of truth** for Codex agents and contributors. Any implementation decisions must strictly conform to this document and to `/specs/*.md`. Where ambiguity exists, agents must apply **minimal safe assumptions** and document them explicitly.

---

## 2. High-Level Goals

### Functional Goals

* Enable advertisers and channel owners to discover each other via a unified marketplace
* Support negotiation, approvals, escrow, auto-posting, verification, and payout in a single lifecycle
* Use **Telegram-native data and permissions** as the source of truth
* Handle **real TON cryptocurrency payments** end-to-end
* Automatically verify ad delivery before releasing funds

### Engineering Goals

* Backend-first, production-grade architecture
* Explicit state machines (no implicit flows)
* Spec-driven, test-driven implementation
* Clean, readable, open-source–ready codebase

---

## 3. Explicit Non-Goals (MVP)

The following are **out of scope by design**:

* KYC, AML, compliance, or identity verification
* Geo restrictions or jurisdiction handling
* Fiat payments or non-TON chains
* Manual posting or manual escrow confirmation
* External analytics providers (non-Telegram)
* Multi-language UI (English only)

---

## 4. Actors & Roles

### Primary Actors

* **Advertiser** – creates campaigns, funds deals, approves creatives
* **Channel Owner** – lists channels, accepts deals, submits creatives
* **Channel Manager** – delegated user with scoped permissions
* **System** – escrow handler, verifier, scheduler

### Channel Management Rules

* A channel is considered valid if the system bot is added with required permissions
* Managers are stored internally but **must be revalidated against Telegram** on all sensitive actions
* Loss of permissions immediately blocks deal progression

---

## 5. Technology Stack (Locked)

### Backend

* Python 3.x
* FastAPI
* PostgreSQL
* SQLAlchemy / SQLModel
* Alembic (migrations mandatory)

### Async & Jobs

* Celery
* Redis

### Telegram Integration

* **Telethon** (MTProto client – mandatory)
* Telegram Bot API (for messaging & posting)

### Frontend

* Vue 3
* Telegram Mini App SDK
* **Highly polished UI**, Telegram-native look & feel (mandatory)

---

## 6. Payment & Escrow Model

### Currency

* TON blockchain only
* Real funds (no mocks)

### Escrow Design

* **One unique wallet address per deal**
* Funds flow:

```
Advertiser → Deal Wallet → (Verification) → Channel Owner
```

### Fee Model

* Platform fee is a **percentage per deal**
* Fee is deducted **at release time**, not at funding
* Fee value is configurable via environment variables

### Escrow Invariants

* Funds are never released before successful verification
* Any invalidation (deleted/edited post) results in refund
* Escrow state is strictly bound to deal state

---

## 7. Marketplace Model

### Entry Points (Must Converge)

1. Channel Owner Listing
2. Advertiser Campaign Request

Both entry points **must converge immediately** into a single canonical entity:

> **DealDraft**

No parallel flows are allowed beyond this point.

---

## 8. Deal Lifecycle (Canonical FSM)

The deal lifecycle is implemented as an **explicit finite state machine**.

### States

```
DRAFT
NEGOTIATION
REJECTED
ACCEPTED
FUNDED
CREATIVE_SUBMITTED
CREATIVE_APPROVED
SCHEDULED
POSTED
VERIFIED
RELEASED
REFUNDED
```

### FSM Rules

* No state skipping is allowed
* Each transition defines:

  * allowed actor
  * preconditions
  * side effects
  * timeout behavior
* Transitions must be implemented via a **transition table**, not ad-hoc logic

---

## 9. Negotiation & Creative Rules

### Negotiation

* Negotiation is limited to **ad format selection only**
* Price, schedule, and payment terms are fixed once negotiation ends

### Creative Constraints

* Allowed formats: text + image / video
* Editing after advertiser approval is **forbidden**
* Any post modification invalidates verification

---

## 10. Creative Approval Workflow

1. Advertiser submits brief/preferences
2. Channel Owner accepts or rejects
3. Channel Owner submits creative draft
4. Advertiser approves or rejects
5. Upon approval, post is scheduled and auto-published

No step may be bypassed.

---

## 11. Auto-Posting & Verification

### Auto-Posting

* Posts must be published via system bot
* Message ID must be stored

### Verification

* Periodic background jobs verify:

  * message exists
  * content hash unchanged
  * post remains visible for required duration

Only after successful verification:

```
POSTED → VERIFIED → RELEASED
```

---

## 12. Telegram Stats & Permissions

### Stats

* All channel stats must be fetched from Telegram via MTProto
* Examples:

  * subscribers
  * average views
  * language breakdown
  * premium metrics (if available)

### Permissions

* Bot must have required admin permissions
* Permissions are checked:

  * at listing time
  * before funding
  * before posting
  * before release

---

## 13. Messaging Policy

* No chat UI inside Mini App
* All notifications are sent via Telegram bot
* Messages include deep-links to Mini App actions

---

## 14. Timeout & Failure Handling

* All states have realistic timeout windows (24–72h typical)
* Inactivity triggers auto-cancel or refund
* Timeouts are enforced by Celery workers

---

## 15. Testing Requirements

* **All code must be tested**
* Required test coverage:

  * FSM transitions
  * escrow logic
  * permission checks
  * posting & verification
  * API contracts

No untested core logic is acceptable.

---

## 16. Open-Source & Dev Standards

Mandatory:

* `.env.example`
* deterministic setup (`docker-compose` or equivalent)
* migration-first database management
* clean commit history
* clear README with setup & architecture

UI polish is **not optional**.

---

## 17. Spec & Codex Authority Rules

### Priority Order

1. `/specs/*.md`
2. `project.md`
3. Code comments

### Codex Behavior

* Codex must not invent features
* When spec is silent:

  * apply **minimal safe assumptions**
  * document them explicitly

Violations of this hierarchy are considered bugs.

---

## 18. Success Criteria

The MVP is considered successful if:

* End-to-end real TON deal can be completed
* Funds are released only after verified auto-posting
* FSM integrity is preserved
* Codebase is readable, testable, and open-source ready

---

**This document is final and binding.**
