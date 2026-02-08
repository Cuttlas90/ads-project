## 1. Backend Campaign Discovery and Offers APIs

- [x] 1.1 Add owner campaign discovery endpoint (`GET /campaigns/discover`) with active-only filtering, pagination, and basic search.
- [x] 1.2 Add advertiser aggregated offers endpoint (`GET /campaigns/offers`) scoped to advertiser-owned campaigns.
- [x] 1.3 Implement newest-first ordering (`created_at DESC`, `id DESC`) and hidden-record exclusion for aggregated offers.
- [x] 1.4 Extend response schemas/types for discovery and aggregated-offers payload fields used by UI.
- [x] 1.5 Add backend tests for discovery filtering + search, advertiser scoping, and newest-first ordering.

## 2. Frontend Services, Types, and Stores

- [x] 2.1 Extend `frontend/src/types/api.ts` with owner campaign discovery and aggregated offers item/page models.
- [x] 2.2 Extend `frontend/src/services/campaigns.ts` with methods for discover, aggregated offers list, apply, accept, and delete actions.
- [x] 2.3 Refactor `frontend/src/stores/campaigns.ts` to support advertiser workspace campaigns and owner discovery campaigns.
- [x] 2.4 Add offers inbox state/actions for advertiser aggregated offer fetching and pagination.
- [x] 2.5 Add store-level error/loading handling for apply/accept/delete actions.

## 3. Frontend Routes and Navigation

- [x] 3.1 Add owner campaigns route and page component.
- [x] 3.2 Add advertiser offers route and page component.
- [x] 3.3 Update role-scoped navigation links to expose owner campaigns and advertiser offers pages.
- [x] 3.4 Add route guard coverage tests for new owner/advertiser pages.

## 4. Page UX Flows

- [x] 4.1 Update advertiser campaign create page to render advertiser campaign list below create form.
- [x] 4.2 Add per-campaign actions in advertiser workspace: open offers and `Delete campaign`.
- [x] 4.3 Implement delete confirmation copy that explains hidden semantics while retaining `Delete campaign` label.
- [x] 4.4 Build owner apply flow with owned verified channel picker and blocked-submit empty state when none are available.
- [x] 4.5 Build advertiser aggregated offers accept form and immediate redirect to `/deals/:id` on success.

## 5. End-to-End Validation

- [x] 5.1 Add frontend tests for advertiser workspace render-after-create behavior.
- [x] 5.2 Add frontend tests for owner apply channel picker and multi-channel apply behavior.
- [x] 5.3 Add frontend tests for aggregated offers newest-first rendering and accept redirect behavior.
- [x] 5.4 Add frontend tests for delete-label/copy semantics and campaign removal from workspace list.
- [x] 5.5 Run backend and frontend targeted test suites and resolve regressions.
