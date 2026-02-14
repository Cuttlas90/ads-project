## 1. Notification Policy Foundation

- [x] 1.1 Define shared notification policy metadata (scope, tone, lifecycle, dedupe key) in frontend shared UI/state layer.
- [x] 1.2 Add a single global toast host in app shell anchored near topbar and wire route-agnostic toast stack behavior.
- [x] 1.3 Add duplicate suppression, max-visible stack handling, and fixed tone durations (`neutral=4s`, `success=5s`, `warning=6s`, `danger=7s`) for global toasts.

## 2. Telegram Theme Integration

- [x] 2.1 Add runtime theme token mapper that reads `Telegram.WebApp.themeParams` and falls back to existing Telegram CSS vars/defaults.
- [x] 2.2 Subscribe to Telegram runtime theme-change events and re-apply semantic notification tokens without reload.
- [x] 2.3 Validate notification tone contrast across light/dark Telegram themes and define guarded fallbacks.

## 3. Flow-Level Notification Migration

- [x] 3.1 Migrate `FundingView` to the agreed channel partition: wallet gate modal, inline funding errors, transient global submission feedback.
- [x] 3.2 Migrate `MarketplaceView` Start deal modal errors/success so modal-origin events remain modal-local and transient events use global toast.
- [x] 3.3 Migrate `AdvertiserOffersView` Accept modal errors/success with modal-local isolation and no page-level error leakage.
- [x] 3.4 Align Profile wallet flow feedback with the same policy for recoverable vs blocking states.

## 4. TONConnect Harmonization

- [x] 4.1 Configure TONConnect action-feedback behavior so action notifications (`before`, `success`, `error`) are fully app-handled and TONConnect-native action notifications are disabled.
- [x] 4.2 Map TONConnect send outcomes to app-managed notification channels and keep wallet-confirmation UX intact.

## 5. Validation and Regression Coverage

- [x] 5.1 Add/adjust unit tests for notification routing, deduplication, and lifecycle behavior.
- [x] 5.2 Add/adjust integration/e2e tests for funding, marketplace Start deal, and offers Accept flow notification outcomes.
- [x] 5.3 Add tests for runtime Telegram theme updates affecting toast/inline alert token application.
