## Context

Current deal scheduling metadata (`scheduled_at`) exists on the deal model and is consumed by posting workers, but no user-facing flow reliably captures this value during listing- or campaign-driven negotiations. Campaign offer acceptance also duplicates term entry (`price_ton`, `ad_type`) even though campaign creation and owner application already provide upstream context.

This change aligns both entry flows around one negotiable start datetime and one structured term source:
- Listing flow: advertiser chooses start datetime while starting a deal.
- Campaign flow: owner supplies placement/exclusive/retention during apply; advertiser accepts with creative + start datetime.
- Deal negotiation: start datetime can be adjusted in DRAFT/NEGOTIATION along with creative fields.

## Goals / Non-Goals

**Goals:**
- Make deal start datetime explicit and negotiable before acceptance.
- Persist agreed start datetime as `scheduled_at` used by posting automation.
- Eliminate duplicate campaign accept term entry by deriving placement terms from application and defaulting price from campaign context.
- Keep FSM-driven lifecycle and worker behavior intact.
- Ship matching backend + frontend behavior.

**Non-Goals:**
- Redesign escrow or posting state machine.
- Add manual posting flows outside existing workers.
- Introduce human/manual verification paths.
- Overhaul campaign budgeting semantics beyond what acceptance flow requires.

## Decisions

1. Introduce API-level `start_at` on deal create/update payloads, mapped to deal `scheduled_at` internally.
- Rationale: preserves existing DB/worker contract while giving product-friendly field naming in UI/API.
- Alternative considered: adding separate `start_at` DB column. Rejected to avoid duplicate timing sources.

2. Extend campaign application payload with structured terms (`proposed_placement_type`, `proposed_exclusive_hours`, `proposed_retention_hours`).
- Rationale: campaign acceptance should consume owner-proposed delivery terms directly.
- Alternative considered: keeping free-text `proposed_format_label` only. Rejected because terms cannot be reliably computed.

3. Make campaign acceptance `price_ton` and `ad_type` non-mandatory at API level; derive defaults from campaign/application when omitted.
- Rationale: supports simplified UI while keeping backward compatibility with existing callers.
- Alternative considered: hard remove fields immediately. Rejected to reduce migration risk.

4. Relax campaign-deal placement-term null-only constraint to allow campaign deals to persist placement/exclusive/retention terms.
- Rationale: retention-based end/time computations need concrete values on campaign deals.
- Alternative considered: storing terms only in events/posting_params. Rejected due to weaker queryability and consistency.

5. Preserve current worker contract and add safety fallback: if funded deal has no schedule, assign immediate schedule timestamp.
- Rationale: avoids stuck funded deals while still honoring explicit negotiated schedules.

## Risks / Trade-offs

- [Risk] Budget field reuse as fallback price source can be semantically confusing for multi-accept campaigns. -> Mitigation: keep explicit override field support and document behavior in specs.
- [Risk] New required application term fields can break old clients. -> Mitigation: update UI and backend validation together; keep legacy format label field for compatibility/readability.
- [Risk] Constraint changes on deals can impact existing data assumptions. -> Mitigation: write migration to relax constraint without destructive data rewrites.
- [Risk] Timezone mismatches from datetime-local inputs. -> Mitigation: normalize to ISO UTC before API calls and store timezone-aware datetimes.

## Migration Plan

1. Add campaign application structured-term columns via Alembic migration.
2. Relax deal campaign-term check constraint to allow placement/exclusive/retention on campaign deals.
3. Deploy backend API changes (schemas/routes) with compatibility for legacy accept payload fields.
4. Deploy frontend updates for listing start time, owner apply term inputs, advertiser accept modal.
5. Run backend + frontend tests for listing create/update, campaign apply/accept, and modal payload behavior.

## Open Questions

- Should `start_at` be mandatory before a deal can be accepted, or optional with immediate-post fallback? (initial implementation keeps optional + fallback)
- Should campaign `budget_ton` remain pure budget long-term, or should a dedicated campaign deal price field be introduced in a follow-up change?
