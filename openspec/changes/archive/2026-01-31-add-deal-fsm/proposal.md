# Change: Add canonical deal FSM and deal creation flows

## Why
The marketplace currently has listings, campaigns, and applications but no canonical Deal entity or lifecycle. We need a single Deal object that converges both entry points and a strict FSM to control state changes, audit transitions, and enforce draft/accept rules.

## What Changes
- Add a canonical `deals` model and `deal_events` audit log with a strict DealState FSM and transition table.
- Add a single `apply_transition()` function as the only allowed way to mutate deal state.
- Add minimal endpoints to create deals from listings and from campaign application acceptance, plus draft update/accept flows.
- Add bot-mediated deal messaging with each forward/counter stored as a deal event.
- **BREAKING** Extend `campaign_applications.status` allowed values to include `accepted` and `rejected`.

## Impact
- Affected specs: `deal-management` (new), `deal-messaging` (new), `campaign-applications` (modified)
- Affected code: backend API routes, shared DB models, Alembic migrations, FSM service layer, bot API integration
