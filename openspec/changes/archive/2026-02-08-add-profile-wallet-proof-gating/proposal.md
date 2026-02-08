# Change: Add profile wallet proof flow and funding wallet gating

## Why
The current wallet API accepts any non-empty string and the advertiser can enter funding flow without a payout-ready wallet, which can break downstream refund handling. We need a verified wallet ownership flow in Profile and an earlier funding-time guard so wallet readiness is enforced before escrow funding attempts.

## What Changes
- Add a Profile wallet connection flow based on TonConnect-derived address plus backend proof verification.
- Require fresh proof on every wallet update and persist the verified wallet address to the user record.
- Extend authenticated profile payloads to expose wallet status for cheap UI/route gating.
- Hard-block advertiser funding actions when wallet is missing; show an in-page modal with one-click jump to Profile and return back to the funding screen after setup.
- Keep wallet setup optional at role-selection time for both roles (not a global onboarding hard requirement).
- Explicitly defer owner-side mandatory enforcement timing (candidate: before `creative_submit`) to a later change.

## Capabilities

### New Capabilities
- None.

### Modified Capabilities
- `user-wallets`: Replace non-empty string wallet updates with TonConnect proof-backed wallet ownership verification and update semantics.
- `m11-ui-support`: Add Profile wallet connect UX and funding-flow wallet-missing hard-block modal with deep-link/return behavior.
- `telegram-auth`: Extend `/auth/me` response requirements to include wallet status needed for frontend guards.

## Impact
- Affected specs: `user-wallets` (modified), `m11-ui-support` (modified), `telegram-auth` (modified).
- Affected APIs: `/auth/me` response shape; wallet-related user endpoints (proof challenge/verify and/or updated wallet update contract).
- Affected code:
  - Backend: auth/users routes, wallet schemas, TON wallet-proof verification service, optional nonce/challenge persistence, tests.
  - Frontend: Profile wallet section, funding view guard + modal, auth store/types, routing return-path handling, tests.
- Dependencies/systems: TonConnect wallet proof flow in frontend/backend integration.
- Out of scope: owner-side hard-block before `creative_submit`, deal FSM/state transition changes, mandatory wallet at onboarding role selection.
