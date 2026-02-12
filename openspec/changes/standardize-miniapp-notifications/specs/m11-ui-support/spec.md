## ADDED Requirements

### Requirement: Notification channel policy by event scope
The UI SHALL route feedback through exactly one notification channel based on event scope: field validation errors SHALL render at field level, recoverable context errors SHALL render as local inline alerts, transient progress/success messages SHALL render as global toasts, and hard prerequisites SHALL render as blocking modals.

#### Scenario: Field validation stays field-local
- **WHEN** a user submits a modal form with invalid or missing media input
- **THEN** the UI shows the validation message at the relevant field and SHALL NOT emit a page-level alert for the same validation event

#### Scenario: Hard prerequisite uses blocking modal
- **WHEN** a funding action is attempted while wallet readiness is false
- **THEN** the UI blocks progression with a blocking modal and SHALL NOT call funding endpoints until prerequisite is resolved

### Requirement: Modal and page feedback isolation
Errors created inside modal flows SHALL remain in the active modal context and SHALL NOT overwrite page-load error panels that describe unrelated page-fetch failures.

#### Scenario: Start deal modal error does not become page error
- **WHEN** media upload fails in the marketplace Start deal modal
- **THEN** the UI shows a modal-local alert for upload failure and SHALL NOT replace marketplace list state with a page-level "Couldn't load listings" error

#### Scenario: Accept modal error does not become offers page error
- **WHEN** creative upload or accept action fails in the advertiser offers Accept modal
- **THEN** the UI shows the failure in the modal context and SHALL keep offers-page loading/error state semantics scoped to offers list retrieval

### Requirement: Global toast stack behavior and deduplication
The app shell SHALL host a single global toast stack for transient feedback anchored near the topbar. Toasts SHALL support tone (`neutral`, `success`, `warning`, `danger`), bounded visible count, manual dismiss, and duplicate suppression for repeated equivalent events within a short deduplication window. Non-blocking toast auto-dismiss durations SHALL be fixed to: `neutral=4s`, `success=5s`, `warning=6s`, `danger=7s`.

#### Scenario: Repeated equivalent polling failure is deduplicated
- **WHEN** escrow polling returns the same failure repeatedly within the deduplication window
- **THEN** the toast stack shows at most one equivalent toast event for that window while preserving current local inline status

#### Scenario: Distinct messages remain visible
- **WHEN** two sequential global events have different message content or tone
- **THEN** both events are shown in toast order subject to max-visible stack limits

#### Scenario: Tone durations follow policy
- **WHEN** toasts are emitted for each tone type
- **THEN** auto-dismiss timing follows `neutral=4s`, `success=5s`, `warning=6s`, and `danger=7s`

### Requirement: Funding notification partitioning
Funding flow feedback SHALL follow fixed channel partitioning: wallet-missing is a blocking modal, escrow init/status failures are local inline alerts in funding context, and successful transaction submission is surfaced as transient global feedback while escrow state progression remains visible in funding status UI.

#### Scenario: Transaction submission uses transient global feedback
- **WHEN** TONConnect transaction submission succeeds
- **THEN** the app emits transient global success feedback and continues escrow polling without replacing the funding status panel

#### Scenario: Escrow status failure remains recoverable local feedback
- **WHEN** `GET /deals/{id}/escrow` fails during funding polling
- **THEN** the UI shows local inline funding error feedback and keeps the user in funding flow for retry/recovery

### Requirement: TONConnect action-feedback harmonization
When the app sends a transaction through TONConnect, action notifications (`before`, `success`, `error`) SHALL be fully app-handled and SHALL NOT be shown as TONConnect-native action notifications. Wallet confirmation/signing UX SHALL remain TONConnect-native.

#### Scenario: No duplicate transaction sent notifications
- **WHEN** a transaction is sent successfully from funding flow
- **THEN** the user receives one canonical app feedback path for submitted state and does not receive an additional conflicting duplicate success notification for the same event

#### Scenario: Action error feedback remains app-owned
- **WHEN** TONConnect action flow returns an error during transaction signing/submission
- **THEN** the user sees app-managed error feedback in policy-defined channels and does not receive a separate TONConnect-native action error notification

### Requirement: Telegram runtime theme-driven notification tokens
Notification surfaces SHALL derive semantic colors from Telegram runtime theme parameters. The UI SHALL apply token priority in order: `Telegram.WebApp.themeParams`, Telegram CSS variable fallbacks, then static app defaults. Theme changes from Telegram runtime SHALL update notification tokens without full app reload.

#### Scenario: Theme change updates notification surfaces
- **WHEN** Telegram emits a runtime theme change event
- **THEN** toast and inline alert tones re-render with updated semantic token values while preserving readability and tone distinctions
