## Context
Sensitive operations (listing verification, posting, escrow release gates) require reliable permission checks against Telegram. We need a centralized module that defines required bot rights, checks bot/admin permissions via Telethon, and returns structured results without side effects.

## Goals / Non-Goals
- Goals:
  - Provide a single source of truth for required bot rights.
  - Provide structured permission check results for bot and user checks.
  - Keep Telegram checks read-only and free of business logic.
  - Provide a small domain helper to convert results into explicit failures.
- Non-Goals:
  - Any DB reads/writes or reliance on stored roles.
  - Channel listing, deal logic, escrow logic, retries, caching, or stats fetching.

## Decisions
- Decision: Use Telethon-native rights names for the required bot rights set.
  - Rationale: Reduces translation risk and keeps checks aligned with Telethon objects.
- Decision: Permission checks return a structured result with `ok`, `is_admin`, `missing_permissions`, `present_permissions`.
  - Rationale: Callers need context for user feedback and auditing; booleans alone are insufficient.
- Decision: Check functions do not raise on failure; only the domain helper may raise.
  - Rationale: Keeps Telegram checks reusable and side-effect free.
- Decision: Add a domain helper `ensure_permissions` that raises a domain-level exception using a context string.
  - Rationale: Separates Telegram logic from business rule enforcement.

## Alternatives Considered
- Alternative: Embed permission checks in each business feature.
  - Rejected: Duplicates logic and risks inconsistent required rights.
- Alternative: Use stored DB roles instead of Telegram.
  - Rejected: Telegram is the source of truth per project constraints.

## Risks / Trade-offs
- Telethon types and rights flags may differ between channels and megagroups; tests should mock Telethon responses to validate rights mapping behavior.
- Strictly minimal required rights could change in future; keeping a central constant makes updates explicit.

## Migration Plan
- No migration needed. This is additive and does not modify existing data or APIs.

## Open Questions
- None.
