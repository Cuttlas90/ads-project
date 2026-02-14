## Why

User-facing notifications in the Mini App are currently inconsistent across flows (inline state panels, modal badges, and TONConnect native notifications), which makes outcomes and next actions unclear. As funding and offer flows become more asynchronous, a single notification policy is needed now to keep behavior predictable and reduce user confusion.

## What Changes

- Define a Mini App notification policy with four explicit channels: field-level error, local inline alert, global toast, and blocking modal.
- Set global toast placement near topbar and fixed tone durations (`neutral=4s`, `success=5s`, `warning=6s`, `danger=7s`) for consistent timing behavior.
- Standardize event-to-channel mapping for high-impact advertiser flows: funding, marketplace Start deal modal, offers Accept modal, and profile wallet flow.
- Define deduplication and priority rules so repeated async failures (for example polling errors) do not spam users.
- Fully app-handle TONConnect action feedback (`before`, `success`, `error`) while keeping TONConnect wallet signing UX.
- Add Telegram theme integration rules so notification surfaces use semantic tokens derived from `Telegram.WebApp.themeParams` with safe fallbacks.

## Capabilities

### New Capabilities

- None.

### Modified Capabilities

- `m11-ui-support`: Add normative notification-channel policy, modal/page feedback isolation, funding-specific notification behavior, TONConnect feedback harmonization, and Telegram theme-param driven notification theming.

## Impact

- Frontend app shell/layout to host global notification stack.
- Frontend Telegram UI primitives (`TgToast`, inline alert/state components) and shared notification state/composable.
- Frontend view flows: `FundingView`, `MarketplaceView`, `AdvertiserOffersView`, and `ProfileView`.
- Frontend tests (unit/component/e2e) covering channel routing, dedup behavior, funding outcomes, and theme-change reactions.
- No backend API contract changes expected.
