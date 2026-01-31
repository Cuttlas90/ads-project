## 1. Implementation
- [x] 1.1 Add `deals` and `deal_events` models plus Alembic migration; update `campaign_applications.status` allowed values
- [x] 1.2 Implement `DealState` enum, transition table, and `apply_transition()` with unit tests
- [x] 1.3 Add deal creation endpoints for listing selection and campaign application acceptance
- [x] 1.4 Add draft update and accept endpoints with role-based field validation and audit events
- [x] 1.5 Add bot-mediated deal messaging endpoint that stores a deal event per message
- [x] 1.6 Add API tests for deal flows, FSM enforcement, and audit logging
- [x] 1.7 Run backend test suite (`pytest`) and fix failures
