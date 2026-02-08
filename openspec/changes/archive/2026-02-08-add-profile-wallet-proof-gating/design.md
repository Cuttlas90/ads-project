## Context

The current wallet flow is weakly validated and too late in the deal lifecycle:
- `PUT /users/me/wallet` accepts any non-empty string today.
- `/auth/me` does not expose wallet readiness, so frontend guards cannot make wallet-aware routing decisions cheaply.
- Advertiser funding UX (`/advertiser/deals/:id/fund`) currently proceeds to TONConnect transaction generation without first enforcing refund-readiness.
- Downstream payout/refund services already require stored wallet addresses, so missing wallets can fail late when funds settlement is attempted.

This change introduces a profile-centered wallet ownership flow using TonConnect proof, then uses wallet status to hard-block advertiser funding until wallet readiness is satisfied.

## Goals / Non-Goals

**Goals:**
- Verify wallet ownership via TonConnect proof before storing `ton_wallet_address`.
- Support wallet updates, with re-proof required for every update.
- Expose wallet readiness in `/auth/me` to enable cheap frontend guards.
- Hard-block advertiser funding actions when wallet is missing.
- Provide in-page modal guidance from funding to profile, with one-click jump and return path back to funding.
- Keep wallet setup optional during role selection for both roles.

**Non-Goals:**
- Enforcing owner wallet before `creative_submit` in this change (deferred).
- Making wallet setup globally mandatory during onboarding.
- Changing deal FSM transitions or escrow watcher behavior.
- Redesigning TON funding payload generation for deal funding itself.

## Decisions

1) **Use proof-based wallet registration in Profile**
- **Decision:** Introduce a TonConnect-proof-backed wallet registration/update flow as the canonical path for setting `ton_wallet_address`.
- **Rationale:** Prevents arbitrary string submission and ties stored wallet identity to cryptographic wallet ownership.
- **Alternatives considered:**
  - Keep non-empty string validation only: rejected as insufficient trust model.
  - Manual wallet entry plus regex/network-format validation: rejected because format validity is not ownership proof.

2) **Use challenge/verify API shape for proof flow**
- **Decision:** Backend wallet API will follow a challenge/verify pattern (challenge payload for proof request, then proof verification + wallet persistence).
- **Rationale:** Keeps verification server-authoritative and supports replay protection controls.
- **Implementation direction:** Persist challenge records in a DB table with fields needed for one-time and expiry checks (e.g., nonce, user_id, expires_at, consumed_at).
- **Alternatives considered:**
  - Redis-only challenge state with key TTL: rejected for this MVP in favor of migration-first durability and easier audit/debug in database-backed flows.
  - Single-shot update endpoint with no challenge: rejected due to weaker anti-replay posture.
  - Client-side-only proof checks: rejected because trust must remain server-side.

3) **Expose wallet readiness through `/auth/me`**
- **Decision:** Extend `/auth/me` response with both `ton_wallet_address` and `has_wallet`.
- **Rationale:** Startup and route guards already rely on `/auth/me`; wallet readiness should be available in the same bootstrap call.
- **Alternatives considered:**
  - Separate wallet status endpoint: rejected for extra request overhead and guard complexity.
  - Expose only `ton_wallet_address` or only `has_wallet`: rejected because the UI needs both explicit readiness and current wallet value for state rendering.

4) **Advertiser funding guard is hard-blocking**
- **Decision:** Funding flow blocks advertiser actions until wallet readiness is true.
- **Rationale:** Refund flows require advertiser wallet; allowing funding without wallet introduces late settlement failure risk.
- **Alternatives considered:**
  - Soft warning while allowing funding: rejected because it allows avoidable operational failure.

5) **Funding-to-Profile UX uses modal + return path**
- **Decision:** If wallet is missing in funding view, show an in-page modal with one-click jump to Profile and preserve a `next` return path back to the same funding route.
- **Rationale:** Keeps user in context, minimizes dead-end navigation, and shortens recovery loop.
- **Alternatives considered:**
  - Silent redirect to Profile: rejected due to abrupt context loss.
  - Error banner only: rejected due to low completion guidance.

6) **Wallet updates overwrite stored address after successful proof**
- **Decision:** Each successful proof can replace the existing stored wallet address.
- **Rationale:** Users may rotate wallets; backend should support controlled updates while preserving ownership guarantees.
- **Alternatives considered:**
  - Immutable first wallet only: rejected for poor usability and support burden.

7) **Owner-side hard enforcement remains deferred**
- **Decision:** Do not enforce owner wallet at owner action points in this change. Capture as deferred follow-up (candidate check point: before `creative_submit`).
- **Rationale:** Keeps current scope focused on advertiser funding risk while preserving forward path for owner-side release readiness.

8) **Challenge TTL is fixed to 5 minutes for MVP**
- **Decision:** Standardize wallet proof challenge expiration at 5 minutes.
- **Rationale:** Provides enough time for Telegram Mini App -> wallet app -> proof -> callback while keeping replay window short.
- **Alternatives considered:**
  - Longer TTL (10-15 minutes): rejected due to larger replay window.
  - Very short TTL (<2 minutes): rejected for poor mobile UX and higher retry rate.

## Risks / Trade-offs

- **[Risk] TonConnect proof verification can be implemented incorrectly and accept forged proofs** -> **Mitigation:** Add strict server-side proof verification tests (valid/invalid signature, domain mismatch, expired challenge, replayed challenge).
- **[Risk] Added wallet checks in funding flow may increase conversion friction** -> **Mitigation:** Provide explicit modal guidance, one-click navigation, and return path back to funding.
- **[Risk] `/auth/me` contract change can break frontend typing/tests if not coordinated** -> **Mitigation:** Update backend schema + frontend types/store in the same change and add contract tests.
- **[Risk] Challenge lifecycle complexity (expiry/replay) may add operational edge cases** -> **Mitigation:** Keep challenge TTL short, enforce one-time use, and fail closed with user-visible retry guidance.
- **[Risk] Deferred owner enforcement leaves a known release-time failure path for owners without wallets** -> **Mitigation:** Document deferral clearly and schedule follow-up change before broader production rollout.

## Migration Plan

1. Update specs for `user-wallets`, `m11-ui-support`, and `telegram-auth` to define proof-based wallet flow, funding guard behavior, and `/auth/me` wallet readiness contract.
2. Add backend API/schema changes for wallet proof challenge/verification and `/auth/me` response extension; add DB-backed challenge storage with one-time usage and 5-minute TTL validation.
3. Update frontend auth types/store bootstrap handling for new wallet status fields.
4. Add Profile wallet-connect UI flow using TonConnect proof.
5. Add funding-view hard-block modal and Profile deep-link with `next` return behavior.
6. Add backend and frontend tests for new contracts and guard behavior.
7. Roll out behind existing environments, verify staging flows for:
   - wallet connect/update
   - missing-wallet funding block
   - Profile return-to-funding
8. Rollback strategy:
   - Keep existing wallet field schema backward-compatible.
   - If issues occur, disable frontend funding hard-block and temporarily fall back to existing wallet update path while retaining data.

## Open Questions

- None.
