# Wallet Connection Decision Log (2026-02-08)

Status: exploratory decisions captured for future implementation.

## Confirmed decisions

1. Wallet source
- Use TonConnect-derived address with proof.

2. Funding guard (advertiser)
- Hard-block advertiser funding flow when advertiser wallet is missing.
- Rationale: refunds require advertiser wallet.

3. Profile UX for missing wallet in funding flow
- Show in-page modal in funding screen.
- Include one-click jump to Profile.
- Support return path back to funding screen after wallet setup.

4. Wallet updates
- Every wallet update requires a new TonConnect proof.
- On successful proof, backend updates stored wallet address.

5. Auth payload
- Include wallet status in `/auth/me` so route/UI guards can check it cheaply.

## Deferred for later

1. Owner-side enforcement timing
- Candidate policy: hard-block owner actions before `creative_submit`.
- Deferred for later rollout (not required now).

2. Proof protocol details to lock before implementation
- Nonce generation and one-time use.
- Nonce TTL (short expiry).
- Domain binding and replay protection.
