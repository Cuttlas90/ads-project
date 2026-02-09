## 1. Backend Contract Updates

- [x] 1.1 Add deal payload support for `start_at` in listing create, campaign accept, and deal draft update flows.
- [x] 1.2 Add structured campaign application term fields (placement, exclusive, retention) in schemas, models, and routes.
- [x] 1.3 Update campaign accept route to derive acceptance terms from campaign/application context and map `start_at` to deal `scheduled_at`.
- [x] 1.4 Add/adjust Alembic migration(s) for campaign application columns and deal constraint updates.

## 2. Frontend Flow Updates

- [x] 2.1 Update listing start-deal modal to capture and submit start datetime.
- [x] 2.2 Update owner campaign apply UI to collect and submit structured proposal terms.
- [x] 2.3 Update advertiser offer-accept UI to remove duplicate price/ad-type inputs and submit creative + optional start datetime.
- [x] 2.4 Update frontend API types/services/stores for new campaign application and accept payload/response fields.

## 3. Verification

- [x] 3.1 Update backend tests for listing deal creation, campaign application apply, campaign acceptance, and draft start-time negotiation.
- [x] 3.2 Update frontend tests for modified listing/campaign apply/accept forms and payload behavior.
- [x] 3.3 Run targeted backend and frontend test suites and fix regressions.
