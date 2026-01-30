## Context
Channel membership records express intent, but Telegram admin rights are authoritative for sensitive actions. We need manager CRUD that is DB-only and a reusable revalidation helper that can be called by future sensitive operations without duplicating Telegram permission logic.

## Goals / Non-Goals
- Goals:
  - Allow channel owners to add/remove/list managers by `telegram_user_id` using DB-only operations.
  - Provide a single revalidation helper that checks Telegram admin rights and required permissions.
  - Return explicit, structured domain errors when revalidation fails.
- Non-Goals:
  - No Telegram calls in CRUD routes.
  - No deal, escrow, posting, or channel verification logic updates in this change.
  - No background jobs or UI work.

## Decisions
- Decision: Use `telegram_user_id` in both the POST body and DELETE path parameter, and require the user to already exist in `users`.
  - Rationale: Aligns with existing auth identity and avoids implicit user provisioning. Missing users return HTTP 404.
- Decision: Treat self add/remove as conflicts and return HTTP 409.
  - Rationale: Mirrors duplicate manager conflicts and keeps errors explicit without introducing new status codes.
- Decision: Implement a new domain error (e.g., `ChannelAccessDenied`) that includes `channel_id`, `telegram_user_id`, and `missing_permissions`, while keeping the existing `PermissionDenied` behavior unchanged.
  - Rationale: Existing error lacks fields required by this change; keeping it stable avoids unintended regressions.
- Decision: `revalidate_channel_access` accepts a channel model and uses `channel.telegram_channel_id` (fallback `channel.username` or `channel.id`) to perform `check_user_permissions` while always using `channel.id` in error metadata.
  - Rationale: Ensures Telegram checks are possible before verification while still providing a stable channel id for errors.

## Risks / Trade-offs
- Risk: Strictly requiring existing users means owners must invite or pre-provision managers before adding them.
  - Mitigation: Return a clear 404 so the frontend can surface a specific onboarding prompt.
- Risk: Sensitive endpoints may not yet call the new helper until future changes land.
  - Mitigation: Document the integration point in this proposal and enforce in future apply changes.

## Migration Plan
- No database migrations required; existing `users` and `channel_members` tables are used.

## Open Questions
- None. (Confirmed: manager identifiers use `telegram_user_id`; missing users return an error.)
