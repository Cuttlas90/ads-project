## 1. Backend Data Model and API Contract

- [x] 1.1 Add a DB model and Alembic migration for wallet proof challenges with one-time and expiry tracking (e.g., nonce/challenge, user binding, expires_at, consumed_at, created_at) and indexes for lookup.
- [x] 1.2 Add/update backend schemas for wallet challenge and wallet proof verification request/response payloads.
- [x] 1.3 Extend `/auth/me` response contract to include both `ton_wallet_address` (nullable) and `has_wallet` (boolean).
- [x] 1.4 Retire or gate the legacy non-proof wallet update path so wallet persistence cannot bypass proof verification.

## 2. Wallet Proof Verification Flow

- [x] 2.1 Implement a backend TonConnect proof verification service that validates signature payloads and app-domain binding.
- [x] 2.2 Implement `POST /users/me/wallet/challenge` to issue an authenticated one-time challenge with fixed 5-minute TTL.
- [x] 2.3 Implement `POST /users/me/wallet/verify` to validate proof, enforce user-bound challenge checks, and persist/update `ton_wallet_address`.
- [x] 2.4 Enforce atomic single-use challenge consumption and reject replayed, expired, or cross-user challenges.
- [x] 2.5 Ensure each successful wallet update requires fresh proof and overwrites prior wallet address only after verification passes.

## 3. Frontend Profile and Funding UX

- [x] 3.1 Update frontend API types and auth store bootstrap handling for `/auth/me` wallet fields (`ton_wallet_address`, `has_wallet`).
- [x] 3.2 Add frontend user service methods for wallet challenge and wallet proof verification endpoints.
- [x] 3.3 Implement Profile wallet connect/update UI using TonConnect proof flow and render wallet-connected status.
- [x] 3.4 Keep role selection/switching independent of wallet setup so users can continue without wallet during onboarding.
- [x] 3.5 Update funding view to hard-block advertiser funding actions when `has_wallet = false`, show in-page modal, and provide one-click navigation to `/profile`.
- [x] 3.6 Add and handle `next` return-path behavior so users can return from Profile to the same funding route after successful wallet setup.

## 4. Test Coverage

- [x] 4.1 Add backend tests for wallet challenge issuance, 5-minute TTL behavior, and successful wallet proof verification.
- [x] 4.2 Add backend negative tests for invalid proof, domain mismatch, replayed challenge, expired challenge, and cross-user challenge use.
- [x] 4.3 Add backend `/auth/me` tests verifying wallet fields for both wallet-present and wallet-missing users.
- [x] 4.4 Add/expand frontend tests for Profile wallet connect UX, optional wallet during role flow, funding hard-block modal, and return-path handling.

## 5. Documentation and Validation

- [x] 5.1 Update docs (`README.md` and relevant API notes) to describe wallet proof flow, funding gating behavior, and `/auth/me` wallet fields.
- [x] 5.2 Update `.env.example` only if new wallet-proof configuration keys are introduced during implementation.
- [x] 5.3 Run targeted backend/frontend tests for this change and run `openspec validate add-profile-wallet-proof-gating --strict`.
