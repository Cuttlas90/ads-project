# Change: Add campaign requests and applications

## Why
Advertisers need a way to publish campaign briefs and review channel applicants, while channel owners need a simple workflow to apply with a verified channel and proposed format.

## What Changes
- Add `campaign_requests` persistence for advertiser-authored briefs (display-only budgets).
- Add advertiser-facing APIs to create, list (paginated), and view their campaign requests.
- Add `campaign_applications` persistence to capture channel-owner applications.
- Add owner apply endpoint and advertiser application listing endpoint (paginated) with channel stats summary.
- Add schemas, router wiring, and tests for the new APIs.

## Impact
- Affected specs: `campaign-requests` (new), `campaign-applications` (new).
- Affected code: shared DB models, Alembic migrations, backend API routes/schemas, and backend tests.
