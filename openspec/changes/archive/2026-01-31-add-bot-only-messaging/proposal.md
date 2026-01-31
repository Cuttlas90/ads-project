# Change: Add bot-only deal messaging via polling

## Why
Deal negotiation must happen through a Telegram bot without any in-app messaging UI. The bot needs to mediate messages, store audit events, and guide users through deal selection.

## What Changes
- Add bot-only deal messaging capability with polling-based update handling.
- Add a DB-backed deal selection table for per-message deal selection.
- Modify `bot-skeleton` to allow bot business logic for message mediation.
- Add bot command flows: `/deals` menu (DRAFT/NEGOTIATION only) and `/deal <id>` shortcuts.

## Impact
- Affected specs: `bot-skeleton` (modified), `bot-deal-messaging` (new)
- Affected code: bot service entrypoint + handlers, shared DB models, Alembic migrations, deal event logging
- Depends on: `add-deal-fsm` change (uses `deals` + `deal_events`)
