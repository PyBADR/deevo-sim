# MASTER ANALYSIS — Impact Observatory v4 Gap Assessment

**Source of Truth:** Production-Ready Engineering Specification v4 + Extension Pack + Canonical JSON Schema v4
**Repository:** PyBADR/impact-observatory (main branch, post-merge)
**Date:** 2026-04-02
**Scope:** Complete gap analysis between current repo state and v4 production contract

---

## 1. MASTER ANALYSIS

### 1.1 Architectural Distance Assessment

The current repository implements a **10-stage synchronous pipeline** (Scenario → Physics → Graph Snapshot → Propagation → Financial → Sector Risk → Regulatory → Decision → Explanation → Output) with a monolithic in-memory execution model. The v4 spec mandates a **9-stage asynchronous pipeline** (Scenario → Physics → Graph → Propagation → Financial → Risk → Regulatory → Decision → Explanation) with run-level persistence, queue-backed execution, and per-entity result storage.

**Critical structural gaps:**

**Execution Model.** Current: single synchronous POST returns full result. v4: POST /api/v1/runs returns 202 Accepted immediately; worker executes asynchronously; GET endpoints retrieve persisted results. This is the single largest architectural change — it requires a worker process, outbox table, run status tracking, and per-stage persistence.

**Data Granularity.** Current: system-level aggregate stress (one BankingStress, one InsuranceStress, one FintechStress per run). v4: entity-level stress (one BankingStress per bank entity, one InsuranceStress per insurer entity, one FintechStress per fintech entity). Every stress engine must be refactored from aggregate to per-entity computation.

**Identity System.** Current: string IDs with no format constraint, bilingual name fields (name/name_ar). v4: UUIDv7 throughout, no bilingual fields on domain objects (bilingual presentation is a UI concern only).

**Schema Structure.** Current schemas use GCC-simplified fields (severity 0-1, stress_score 0-100 composites, liquidity_gap_usd, claims_surge_pct). v4 uses regulatory-precise fields (LCR, NSFR, CET1, CAR for banking; solvency_ratio, reserve_ratio, combined_ratio for insurance; service_availability, settlement_delay_minutes for fintech) with explicit breach_flags objects.

**Authentication.** Current: API key via X-IO-API-Key header. v4: Bearer JWT with principal extraction, role-based access, and idempotency-key enforcement on writes.

**Missing Layers (entirely absent):**
- Business Impact Layer (LossTrajectoryPoint, TimeToFailure, RegulatoryBreachEvent, BusinessImpactSummary)
- Time Engine (temporal simulation loop, shock decay, propagation delay, TimeStepState, EntityTemporalImpact)
- Scenario DNA (ScenarioDna, TriggerEvent, SectorImpactLink)
- Executive Decision Explanation (cause_effect_chain, LossTranslation, board_message, regulator_message)
- Run persistence model (runs table, stage status tracking, version bundle)
- Worker/queue infrastructure (run_worker, retry_worker, outbox)
- Regulatory mode (AuditLogEntry, ComplianceReport, regulator view)
- Real-time layer (WebSocket streaming, event channels)

### 1.2 Reusable Infrastructure Assessment

Despite the gaps, approximately 60% of the computational logic is architecturally sound and reusable after field-level refactoring:

**Strong foundations:** Pipeline orchestration pattern (stage-by-stage with timing), service engine pattern (each sector in its own engine.py), Pydantic v2 model structure with VersionedModel base, financial loss formula (matches v4 conceptually), decision priority formula (5-factor weighted sum matches v4 exactly), propagation convergence loop, GCC constants and calibration data, Docker Compose infrastructure, FastAPI application skeleton.

**Moderate refactoring needed:** All three stress engines (banking, insurance, fintech) — formulas are correct in principle but must be restructured for entity-level output with v4 field names. Financial engine — must add per-entity output and v4 fields (revenue_at_risk, capital_after_loss, liquidity_after_loss, impact_status). Decision engine — must add action_type enum, reason_codes, preconditions, execution_window_hours, requires_override, expected_loss_reduction, expected_flow_recovery. Regulatory engine — must restructure from current alert-level model to v4 aggregate ratios + breach_level + mandatory_actions.

**Must be rebuilt or created from scratch:** Run persistence layer, async execution model, Time Engine, Business Impact Layer, Scenario DNA, Executive Explanation, RBAC (5 roles), JWT auth, API route structure (/api/v1 with 9+ endpoints), error system (structured error envelope with codes), idempotency, versioning system (4-dimension version bundle).

### 1.3 Risk Assessment

**Highest risk:** The async execution model change touches every layer. If the worker infrastructure is unstable, no endpoint works. Mitigation: implement synchronous-first with a thin async wrapper that can be replaced by queue-backed worker later.

**Medium risk:** Entity-level stress computation may surface numeric edge cases not present in aggregate mode (division by zero on per-entity LCR when projected_cash_outflows_30d = 0). Mitigation: defensive clipping and v4-mandated fallback rules.

**Lower risk:** Schema migration is mechanical but extensive — every field rename, type change, and new field must be tested against the canonical JSON schema.

---

## 2. KEEP / REFACTOR / REMOVE / REPLACE MATRIX

### 2.1 Backend Files

| File | Verdict | Rationale |
|---|---|---|
| `backend/app/schemas/base.py` | **KEEP** | VersionedModel base class is compatible with v4 |
| `backend/app/schemas/observatory.py` | **REFACTOR** | All 12 models need field-level migration to v4 contracts; restructure to per-entity stress |
| `backend/app/orchestration/pipeline.py` | **REFACTOR** | Stage sequence is correct; must add per-stage persistence, status tracking, and temporal loop entry point |
| `backend/app/services/banking/engine.py` | **REFACTOR** | Core stress logic reusable; must restructure to per-entity output with v4 fields (deposit_outflow, wholesale_funding_outflow, hqla, lcr, nsfr, cet1_ratio, car, breach_flags) |
| `backend/app/services/insurance/engine.py` | **REFACTOR** | Must add v4 fields (premium_drop, claims_spike, reserve_ratio, solvency_ratio, combined_ratio, liquidity_gap, breach_flags) |
| `backend/app/services/fintech/engine.py` | **REFACTOR** | Must add v4 fields (transaction_failure_rate, fraud_loss, service_availability, settlement_delay_minutes, client_churn_rate, operational_risk_score, breach_flags) |
| `backend/app/services/financial/engine.py` | **REFACTOR** | Must produce per-entity FinancialImpact with v4 fields (entity_id, exposure, shock_intensity, propagation_factor, loss, revenue_at_risk, capital_after_loss, liquidity_after_loss, impact_status) |
| `backend/app/services/decision/engine.py` | **REFACTOR** | Priority formula matches v4; must add action_type enum, reason_codes, preconditions, execution_window_hours, requires_override, expected_loss_reduction, expected_flow_recovery, target_level/target_ref |
| `backend/app/services/explainability/engine.py` | **REFACTOR** | Must restructure output to v4 ExplanationPack (run_id, equations block with exact strings, drivers array, stage_traces array with exactly 8 items, action_explanations, assumptions, limitations) |
| `backend/app/services/audit/engine.py` | **REFACTOR** | Reusable for v4 AuditLogEntry generation; needs field alignment |
| `backend/app/services/reporting/engine.py` | **REFACTOR** | Foundation for v4 ComplianceReport; needs restructure |
| `backend/app/services/normalization.py` | **KEEP** | Normalization logic is reusable |
| `backend/app/services/orchestrator.py` | **REFACTOR** | Must integrate with run persistence and temporal engine |
| `backend/app/api/observatory.py` | **REPLACE** | Current POST /observatory/run must be replaced with v4 route structure: POST /api/v1/scenarios, POST /api/v1/runs, GET /api/v1/runs/{run_id}/financial, etc. |
| `backend/app/api/health.py` | **KEEP** | Health endpoint is infrastructure |
| `backend/app/api/decision.py` | **REMOVE** | Superseded by v4 /api/v1/runs/{run_id}/decision route |
| `backend/app/api/graph.py` | **REMOVE** | Graph is internal; not a public v4 endpoint |
| `backend/app/api/incidents.py` | **REMOVE** | Not in v4 contract |
| `backend/app/api/insurance.py` | **REMOVE** | Superseded by v4 /api/v1/runs/{run_id}/insurance route |
| `backend/app/api/models.py` | **REMOVE** | Not in v4 contract |
| `backend/app/api/scenarios.py` | **REPLACE** | Must become v4 POST /api/v1/scenarios with full validation |
| `backend/app/api/scores.py` | **REMOVE** | Not in v4 contract |
| `backend/app/config/settings.py` | **REFACTOR** | Must add v4 env vars (JWT_*, RUN_*, DECISION_WEIGHT_*, threshold defaults, propagation constants) |
| `backend/app/intelligence/engines/gcc_constants.py` | **KEEP** | GCC economic bases, Hormuz multipliers, calibration data reusable |
| `backend/app/intelligence/engines/decision_engine.py` | **KEEP** | DPS/APS mathematical framework reusable alongside v4 decision engine |
| `backend/main.py` | **REFACTOR** | Must mount v4 router structure |
| `backend/src/` (entire directory) | **REMOVE** | Legacy parallel structure; all active code is in backend/app/ |
| `backend/tests/` | **REFACTOR** | Keep test infrastructure; update fixtures to v4 schemas |

### 2.2 Frontend Files

| File | Verdict | Rationale |
|---|---|---|
| `frontend/app/layout.tsx` | **KEEP** | Root layout with font configuration |
| `frontend/app/page.tsx` | **REFACTOR** | Landing page needs v4 branding |
| `frontend/app/dashboard/page.tsx` | **REPLACE** | Must be rebuilt as v4 DashboardHome with run-based navigation |
| `frontend/app/api/run-scenario/route.ts` | **REPLACE** | Must proxy to v4 POST /api/v1/runs |
| `frontend/app/api/scenarios/route.ts` | **REFACTOR** | Must proxy to v4 POST /api/v1/scenarios |
| `frontend/app/api/audit/` | **KEEP** | Audit route foundation reusable |
| `frontend/app/control-room/` | **REMOVE** | Not in v4 UI blueprint |
| `frontend/app/demo/` | **REMOVE** | Not in v4 contract |
| `frontend/app/scenarios/` | **REFACTOR** | Align to v4 ScenarioLibraryPage |
| `frontend/lib/types.ts` | **REMOVE** | Superseded by frontend/lib/types/observatory.ts |
| `frontend/lib/types/observatory.ts` | **REPLACE** | Must be rebuilt to match v4 canonical objects exactly |
| `frontend/lib/i18n.ts` | **KEEP** | Bilingual support is a platform requirement |
| `frontend/lib/server/auth.ts` | **REPLACE** | Must implement Bearer JWT validation |
| `frontend/lib/server/rbac.ts` | **REFACTOR** | Must expand from 4 roles to 5 (add operator, regulator) |
| `frontend/lib/server/audit.ts` | **KEEP** | Audit trail infrastructure reusable |
| `frontend/lib/server/trace.ts` | **KEEP** | Trace ID generation reusable |
| `frontend/lib/server/store.ts` | **REFACTOR** | Must align to v4 persistence model |
| `frontend/lib/server/execution.ts` | **REPLACE** | Must call v4 API endpoints |
| `frontend/lib/decision-engine.ts` | **REMOVE** | Client-side decision engine not needed; v4 decisions come from backend |
| `frontend/lib/simulation-engine.ts` | **REMOVE** | Client-side simulation not needed; v4 runs on backend |
| `frontend/lib/mock-data.ts` | **REPLACE** | Must generate v4-compliant mock data |
| `frontend/middleware.ts` | **REFACTOR** | CORS + security headers correct; must add JWT extraction |
| `frontend/styles/globals.css` | **KEEP** | White executive theme and typography correct |
| `frontend/tailwind.config.ts` | **KEEP** | Design system tokens correct |
| `frontend/src/` (entire directory) | **REMOVE** | Legacy parallel structure; all active code is in frontend/app/ and frontend/lib/ |

### 2.3 Infrastructure Files

| File | Verdict | Rationale |
|---|---|---|
| `docker-compose.yml` | **REFACTOR** | Must add worker, retry-worker services |
| `backend/Dockerfile` | **REFACTOR** | Must split into Dockerfile.api and Dockerfile.worker |
| `backend/pyproject.toml` | **REFACTOR** | Must add uuid7, redis, and queue dependencies |
| `frontend/package.json` | **KEEP** | Dependencies correct for Next.js 15 |
| `.env.example` files | **REFACTOR** | Must add all v4 environment variables |

### 2.4 Summary Counts

| Verdict | Backend | Frontend | Infrastructure | Total |
|---|---|---|---|---|
| KEEP | 7 | 7 | 1 | 15 |
| REFACTOR | 14 | 7 | 4 | 25 |
| REMOVE | 6 | 5 | 0 | 11 |
| REPLACE | 2 | 5 | 0 | 7 |
| **NEW (must create)** | **~35** | **~20** | **3** | **~58** |

---

## 3. REPO BUILD MAP

### 3.1 v4 Mandatory Repository Structure vs Current State

```
repo/                              STATUS
├── pyproject.toml                 EXISTS (needs refactor)
├── alembic.ini                    MISSING — must create
├── migrations/                    MISSING — must create
│   ├── env.py
│   └── versions/
├── app/
│   ├── main.py                    EXISTS as backend/main.py (refactor)
│   ├── core/
│   │   ├── config.py              EXISTS as backend/app/config/settings.py (refactor)
│   │   ├── constants.py           PARTIAL in gcc_constants.py (refactor)
│   │   ├── logging.py             MISSING — must create
│   │   ├── security.py            MISSING — must create (JWT validation)
│   │   ├── errors.py              MISSING — must create (global error envelope)
│   │   ├── rbac.py                PARTIAL in frontend only (must create backend)
│   │   ├── versioning.py          MISSING — must create (version bundle)
│   │   └── idempotency.py         MISSING — must create
│   ├── api/
│   │   ├── dependencies.py        MISSING — must create
│   │   └── v1/
│   │       ├── router.py          MISSING — must create
│   │       ├── schemas/
│   │       │   ├── common.py      MISSING
│   │       │   ├── scenario_api.py MISSING
│   │       │   ├── run_api.py     MISSING
│   │       │   └── result_api.py  MISSING
│   │       └── routes/
│   │           ├── scenarios.py   EXISTS as backend/app/api/scenarios.py (replace)
│   │           ├── runs.py        MISSING — must create
│   │           ├── financial.py   MISSING — must create
│   │           ├── banking.py     MISSING — must create
│   │           ├── insurance.py   EXISTS as backend/app/api/insurance.py (replace)
│   │           ├── fintech.py     MISSING — must create
│   │           ├── decision.py    EXISTS as backend/app/api/decision.py (replace)
│   │           └── explanation.py MISSING — must create
│   ├── domain/
│   │   ├── models/
│   │   │   ├── scenario.py        PARTIAL in observatory.py (extract+refactor)
│   │   │   ├── entity.py          PARTIAL in observatory.py (extract+refactor)
│   │   │   ├── edge.py            PARTIAL in observatory.py (extract+refactor)
│   │   │   ├── flow_state.py      PARTIAL in observatory.py (extract+refactor)
│   │   │   ├── financial_impact.py PARTIAL in observatory.py (extract+refactor)
│   │   │   ├── banking_stress.py  PARTIAL in observatory.py (extract+refactor)
│   │   │   ├── insurance_stress.py PARTIAL in observatory.py (extract+refactor)
│   │   │   ├── fintech_stress.py  PARTIAL in observatory.py (extract+refactor)
│   │   │   ├── regulatory_state.py PARTIAL in observatory.py (extract+refactor)
│   │   │   ├── decision.py        PARTIAL in observatory.py (extract+refactor)
│   │   │   └── explanation.py     PARTIAL in observatory.py (extract+refactor)
│   │   └── services/
│   │       ├── physics_engine.py  MISSING — must create (currently inline in pipeline)
│   │       ├── graph_builder.py   MISSING — must create (currently inline in pipeline)
│   │       ├── propagation_engine.py MISSING — must create (inline in pipeline)
│   │       ├── financial_engine.py EXISTS as backend/app/services/financial/engine.py
│   │       ├── banking_engine.py  EXISTS as backend/app/services/banking/engine.py
│   │       ├── insurance_engine.py EXISTS as backend/app/services/insurance/engine.py
│   │       ├── fintech_engine.py  EXISTS as backend/app/services/fintech/engine.py
│   │       ├── risk_engine.py     MISSING — must create (aggregates sector engines)
│   │       ├── regulatory_engine.py MISSING — extract from pipeline
│   │       ├── decision_engine.py EXISTS as backend/app/services/decision/engine.py
│   │       ├── explanation_engine.py EXISTS as backend/app/services/explainability/engine.py
│   │       └── orchestrator.py    EXISTS as backend/app/services/orchestrator.py
│   ├── persistence/
│   │   ├── db.py                  MISSING — must create
│   │   ├── base.py                MISSING — must create
│   │   ├── orm/
│   │   │   ├── scenario.py        MISSING — must create
│   │   │   ├── run.py             MISSING — must create
│   │   │   ├── results.py         MISSING — must create
│   │   │   ├── audit.py           MISSING — must create
│   │   │   └── outbox.py          MISSING — must create
│   │   └── repositories/
│   │       ├── scenario_repo.py   MISSING — must create
│   │       ├── run_repo.py        MISSING — must create
│   │       ├── result_repo.py     MISSING — must create
│   │       ├── audit_repo.py      MISSING — must create
│   │       └── outbox_repo.py     MISSING — must create
│   ├── workers/
│   │   ├── queue.py               MISSING — must create
│   │   ├── run_worker.py          MISSING — must create
│   │   └── retry_worker.py        MISSING — must create
│   └── observability/
│       ├── metrics.py             MISSING — must create
│       ├── tracing.py             MISSING — must create
│       └── health.py              EXISTS as backend/app/api/health.py (move)
```

### 3.2 Gap Summary

| v4 Module | Files Required | Files Existing | Files Missing | Coverage |
|---|---|---|---|---|
| core/ | 8 | 1 (partial) | 7 | 12% |
| api/v1/schemas/ | 4 | 0 | 4 | 0% |
| api/v1/routes/ | 8 | 3 (partial) | 5 | 15% |
| domain/models/ | 11 | 1 (monolith) | 10 | 9% |
| domain/services/ | 12 | 7 | 5 | 58% |
| persistence/ | 12 | 0 | 12 | 0% |
| workers/ | 3 | 0 | 3 | 0% |
| observability/ | 3 | 1 (partial) | 2 | 17% |
| **Total** | **61** | **12** | **49** | **20%** |

---

## 4. RBAC PLAN

### 4.1 Current State

The current system has **4 roles** defined in `frontend/lib/server/rbac.ts`: admin, analyst, viewer, api_service. Authentication is API-key based with 3 hardcoded keys (master, pilot, analyst). There is no backend RBAC enforcement — the frontend checks roles before proxying to the backend.

### 4.2 v4 Target State

5 roles: viewer, analyst, operator, admin, regulator. Authentication via Bearer JWT with principal extraction. RBAC enforced at the backend route level via dependency injection.

### 4.3 Migration Plan

**Step 1 — Create backend RBAC module** (`app/core/rbac.py`):
Define the 5-role permission matrix exactly as specified in v4 Section 10.2. Implement a FastAPI dependency (`require_role(*roles)`) that extracts the role from the JWT principal and raises 403 INSUFFICIENT_ROLE if denied.

**Step 2 — Create JWT security module** (`app/core/security.py`):
Validate Bearer tokens using JWT_PUBLIC_KEY, JWT_ISSUER, JWT_AUDIENCE. Extract principal_id and role. Return an AuthContext object.

**Step 3 — Wire into every route**:
Each v4 route handler must declare its required roles via the dependency:
- POST /scenarios: analyst, operator, admin, regulator
- POST /runs: analyst, operator, admin, regulator
- POST /runs with overrides: operator, admin, regulator only
- GET /financial, /banking, /insurance, /fintech, /explanation: all 5 roles
- GET /decision: analyst, operator, admin, regulator (viewer excluded)
- Force rerun: operator, admin only
- Manage version manifests: admin only
- Archive scenario: admin only

**Step 4 — Migrate frontend auth**:
Replace API-key auth in `frontend/lib/server/auth.ts` with JWT Bearer validation. Update `frontend/lib/server/rbac.ts` to use 5-role matrix. Add operator and regulator roles.

**Step 5 — Decision visibility guard**:
The /decision endpoint must return 403 DECISION_ACCESS_DENIED for viewer role. This is a hard v4 requirement because action recommendations are operationally sensitive.

### 4.4 Role Capability Delta

| Capability | Current (4 roles) | v4 (5 roles) | Delta |
|---|---|---|---|
| Create scenario | admin, analyst | analyst, operator, admin, regulator | +operator, +regulator |
| Launch run | admin, analyst | analyst, operator, admin, regulator | +operator, +regulator |
| Launch with overrides | not implemented | operator, admin, regulator | NEW |
| Read decision | admin, analyst, viewer | analyst, operator, admin, regulator | -viewer, +operator, +regulator |
| Force rerun | not implemented | operator, admin | NEW |
| Manage manifests | admin | admin | same |
| Archive scenario | not implemented | admin | NEW |
| Regulatory override | not implemented | regulator | NEW |

---

## 5. UI FINAL BLUEPRINT

### 5.1 Current Frontend State

The frontend uses Next.js 15 with the App Router. Active pages: dashboard (executive overview), scenarios (list), demo, control-room. The dashboard renders a single-run result with aggregate stress gauges, decision cards, and pipeline metadata. There is a dual code structure: `frontend/app/` (active) and `frontend/src/` (legacy, 36 files).

### 5.2 v4 Required Screens

| Screen | Route | Status | Action |
|---|---|---|---|
| Dashboard Home | `/dashboard` | EXISTS (partial) | REFACTOR — must become run-list portfolio overview |
| Risk Map | `/runs/:runId/risk-map` | MISSING | CREATE — network graph with entity severity, sector filters, timestep scrubber |
| Decision Panel | `/runs/:runId/decision` | MISSING | CREATE — ranked actions, cause-effect narrative, override status |
| Financial Impact | `/runs/:runId/financial-impact` | MISSING | CREATE — loss chart, entity grid, sector drilldown |
| Regulatory Status | `/runs/:runId/regulatory-status` | MISSING | CREATE — breach timeline, reporting checklist |
| Timeline | `/runs/:runId/timeline` | MISSING | CREATE — timestep playback, entity temporal impacts |
| Scenario Library | `/scenarios` | EXISTS (partial) | REFACTOR — must support v4 scenario create/archive |
| Run Detail | `/runs/:runId` | MISSING | CREATE — run status, version bundle, stage progress |
| Compliance Reports | `/runs/:runId/compliance-reports` | MISSING | CREATE — regulator mode, export controls |

### 5.3 Design System (Preserved)

The current design system is preserved and production-ready:
- Typography: DM Sans (EN) + IBM Plex Sans Arabic (AR) + JetBrains Mono (code)
- Theme: bg=#F8FAFC, surface=#FFFFFF, primary=#0F172A, accent=#1D4ED8
- CSS custom properties in globals.css
- Tailwind ds-* namespace tokens
- RTL support via [dir="rtl"] selectors

### 5.4 Frontend Data Access Layer (Must Create)

| Module | Calls | Status |
|---|---|---|
| `lib/api/client.ts` | Base fetch with JWT, trace_id, envelope parsing | MISSING |
| `lib/api/scenarios.ts` | POST /scenarios, GET /scenarios | MISSING |
| `lib/api/runs.ts` | POST /runs, GET /runs/{id}/* | MISSING |
| `lib/api/financial.ts` | GET /financial | MISSING |
| `lib/api/banking.ts` | GET /banking | MISSING |
| `lib/api/insurance.ts` | GET /insurance | MISSING |
| `lib/api/fintech.ts` | GET /fintech | MISSING |
| `lib/api/decision.ts` | GET /decision | MISSING |
| `lib/api/explanation.ts` | GET /explanation | MISSING |
| `lib/api/business-impact.ts` | GET /business-impact | MISSING |
| `lib/api/timeline.ts` | GET /timeline | MISSING |
| `lib/api/regulatory-timeline.ts` | GET /regulatory-timeline | MISSING |
| `lib/api/executive-explanation.ts` | GET /executive-explanation | MISSING |

### 5.5 Frontend Type System (Must Rebuild)

`frontend/lib/types/observatory.ts` must be completely rebuilt to mirror v4 canonical objects. Current types use GCC-simplified fields; v4 requires entity-level types with UUIDv7 IDs, breach_flags objects, per-entity timestamps, and many additional fields.

---

## 6. BACKEND ALIGNMENT PLAN

### 6.1 Schema Migration (Priority 1)

The monolithic `observatory.py` (621 lines, 12 models) must be split into individual domain model files under `app/domain/models/`. Each model must be field-aligned to v4 canonical JSON schema.

**ScenarioInput → Scenario:** Add scenario_id (UUIDv7), scenario_version (semver), as_of_date, horizon_days, currency, shock_intensity (0-5 range), market_liquidity_haircut, deposit_run_rate, claims_spike_rate, fraud_loss_rate, regulatory_profile object, entities array, edges array, created_by, created_at, status enum. Remove name_ar (UI concern), severity (replaced by shock_intensity).

**Entity:** Replace id/name/name_ar/layer/sector/severity/metadata with entity_id (UUIDv7), entity_type enum (bank/insurer/fintech/market_infrastructure), name, jurisdiction, exposure, capital_buffer, liquidity_buffer, capacity, availability, route_efficiency, criticality, regulatory_classification enum, active boolean.

**Edge:** Replace source/target/weight/propagation_factor/edge_type with edge_id (UUIDv7), source_entity_id, target_entity_id, relation_type enum, exposure, transmission_coefficient, capacity, availability, route_efficiency, latency_ms, active boolean.

**FlowState:** Replace timestep/entity_states/total_stress/peak_entity/converged with timestamp, entity_id, inbound_flow, outbound_flow, net_flow, capacity, availability, route_efficiency, computed_flow, flow_status enum.

**FinancialImpact:** Replace headline_loss_usd/peak_day/time_to_failure_days/severity_code/confidence with entity_id, timestamp, exposure, shock_intensity, propagation_factor, loss, revenue_at_risk, capital_after_loss, liquidity_after_loss, impact_status enum.

**BankingStress:** Replace liquidity_gap_usd/capital_adequacy_ratio/interbank_rate_spike/stress_level/stress_score with entity_id, timestamp, deposit_outflow, wholesale_funding_outflow, hqla, projected_cash_outflows_30d, projected_cash_inflows_30d, lcr, nsfr, cet1_ratio, capital_adequacy_ratio, breach_flags object.

**InsuranceStress:** Replace claims_surge_pct/reinsurance_trigger/combined_ratio/solvency_margin_pct/stress_level/stress_score with entity_id, timestamp, premium_drop, claims_spike, reserve_ratio, solvency_ratio, combined_ratio, liquidity_gap, breach_flags object.

**FintechStress:** Replace payment_failure_rate/settlement_delay_hours/gateway_downtime_pct/stress_level/stress_score with entity_id, timestamp, transaction_failure_rate, fraud_loss, service_availability, settlement_delay_minutes, client_churn_rate, operational_risk_score, breach_flags object.

**DecisionAction:** Replace id/rank/title/title_ar/urgency/value/priority/feasibility/time_effect/cost_usd/loss_avoided_usd/regulatory_risk/sector/description/status with action_id (UUIDv7), run_id, rank (1-3), action_type enum (8 values), target_level enum, target_ref, urgency, value, reg_risk, feasibility, time_effect, priority_score, reason_codes array, preconditions array, expected_loss_reduction, expected_flow_recovery, execution_window_hours, requires_override boolean.

**DecisionPlan:** Replace plan_id/name/name_ar/actions/total_cost_usd/total_loss_avoided_usd/net_benefit_usd/execution_days/sectors_covered with run_id, generated_at, model_version, candidate_count, feasible_count, actions (max 3), dropped_actions_count, constrained_by_rbac, constrained_by_regulation, plan_status enum.

**RegulatoryState:** Replace pdpl_compliant/ifrs17_impact/basel3_car_floor/sama_alert_level/cbuae_alert_level/sanctions_exposure/regulatory_triggers with run_id, timestamp, jurisdiction, regulatory_version, aggregate_lcr, aggregate_nsfr, aggregate_solvency_ratio, aggregate_capital_adequacy_ratio, breach_level enum, mandatory_actions array, reporting_required boolean.

**ExplanationPack:** Replace summary_en/summary_ar/key_findings/causal_chain/confidence_note/data_sources/audit_trail with run_id, generated_at, summary, equations object (4 exact formula strings), drivers array, stage_traces array (exactly 8), action_explanations array, assumptions array, limitations array.

### 6.2 Engine Refactoring (Priority 2)

Each service engine must be updated to consume and produce v4 domain objects:

**Financial engine:** Accept list of Entity + PropagationState. Compute per-entity FinancialImpact using Loss = Exposure × ShockIntensity × PropagationFactor. Compute aggregate_loss and aggregate_revenue_at_risk.

**Banking engine:** Accept list of bank entities + FinancialImpact. Compute per-entity BankingStress with LCR = HQLA / net_cash_outflows_30d, NSFR, CET1, CAR. Set breach_flags by comparing against regulatory_profile thresholds.

**Insurance engine:** Accept list of insurer entities + FinancialImpact. Compute per-entity InsuranceStress with reserve_ratio, solvency_ratio, combined_ratio, liquidity_gap. Set breach_flags.

**Fintech engine:** Accept list of fintech entities + FinancialImpact. Compute per-entity FintechStress with transaction_failure_rate, service_availability, settlement_delay_minutes, operational_risk_score. Set breach_flags.

**Decision engine:** Accept sector results + RegulatoryState. Generate candidate actions from breaches, filter by feasibility, rank by priority formula, apply tie-breaking, return top 3.

### 6.3 New Backend Modules (Priority 3)

| Module | Responsibility | Estimated Complexity |
|---|---|---|
| `app/core/security.py` | JWT validation, principal extraction | Medium |
| `app/core/errors.py` | Global error envelope, error codes | Medium |
| `app/core/rbac.py` | 5-role permission matrix | Low |
| `app/core/idempotency.py` | Idempotency-Key enforcement | Medium |
| `app/core/versioning.py` | 4-dimension version bundle | Medium |
| `app/persistence/` (all) | ORM models, repositories, DB session | High |
| `app/workers/` (all) | Queue consumer, run execution, retry | High |
| `app/api/v1/` (routes+schemas) | All 9+ endpoints with DTOs | High |
| `app/domain/services/time_engine.py` | Temporal simulation loop | High |
| `app/domain/models/business_impact.py` | LossTrajectoryPoint, TimeToFailure, etc. | Medium |
| `app/domain/models/scenario_dna.py` | ScenarioDna, TriggerEvent | Medium |
| `app/domain/models/executive_explanation.py` | ExecutiveDecisionExplanation | Medium |

---

## 7. V1 IMPLEMENTATION PLAN

### 7.1 Phase Definition

V1 delivers the complete v4 contract for a single scenario: **Strait of Hormuz Closure, 14-Day, Severe**. V1 must pass the canonical JSON schema validation for all objects and all 9 API endpoints.

### 7.2 Ordered Implementation Sequence

**Phase 1: Foundation (Days 1-3)**
1. Split observatory.py into individual domain model files under app/domain/models/
2. Align each model field-by-field to v4 canonical schema
3. Create app/core/ modules: config.py, constants.py, errors.py, security.py (stub), rbac.py, versioning.py, idempotency.py (stub)
4. Create app/api/v1/router.py and app/api/v1/schemas/ DTOs
5. Validate all domain models against canonical_json_schema_v4.json

**Decision Gate 1:** Every domain model serializes to JSON that passes the canonical JSON schema. Zero validation errors.

**Phase 2: Engine Alignment (Days 4-6)**
6. Refactor financial_engine.py to produce per-entity FinancialImpact
7. Refactor banking_engine.py to produce per-entity BankingStress with breach_flags
8. Refactor insurance_engine.py to produce per-entity InsuranceStress with breach_flags
9. Refactor fintech_engine.py to produce per-entity FintechStress with breach_flags
10. Refactor decision_engine.py to produce v4 DecisionAction with all new fields
11. Refactor explanation_engine.py to produce v4 ExplanationPack
12. Create regulatory_engine.py producing v4 RegulatoryState

**Decision Gate 2:** Hormuz scenario produces valid output through all 9 stages. Every output object passes JSON schema validation.

**Phase 3: API Layer (Days 7-9)**
13. Create app/api/v1/routes/ for all 9 endpoints
14. Wire RBAC via require_role dependencies
15. Implement standard success envelope (trace_id, generated_at, data, warnings)
16. Implement global error envelope with all error codes
17. Create app/persistence/ ORM models and repositories (minimal: in-memory store for V1)
18. Implement POST /scenarios with full validation (SCN-VAL-001 through SCN-VAL-010)
19. Implement POST /runs with 202 Accepted and synchronous execution behind the scenes

**Decision Gate 3:** All 9 endpoints return valid v4 response envelopes. RBAC enforced. Error codes correct.

**Phase 4: Business Impact + Time Engine (Days 10-12)**
20. Create app/domain/services/time_engine.py with temporal simulation loop
21. Implement ShockEffective(t) = ShockIntensity × (1 - shock_decay_rate)^t
22. Implement LossTrajectoryPoint computation (direct_loss, propagated_loss, cumulative_loss, velocity, acceleration)
23. Implement TimeToFailure computation for all 5 failure types
24. Implement RegulatoryBreachEvent detection and persistence
25. Compute BusinessImpactSummary (peak_cumulative_loss, business_severity, executive_status)
26. Create /business-impact, /timeline, /regulatory-timeline endpoints

**Decision Gate 4:** Hormuz scenario produces temporal output with loss trajectory, time-to-failure, and breach events. Business severity maps correctly.

**Phase 5: Explanation + Scenario DNA (Days 13-14)**
27. Implement ScenarioDna with TriggerEvent and SectorImpactLink for Hormuz
28. Implement ExecutiveDecisionExplanation with cause_effect_chain, loss_translation, board_message, regulator_message
29. Create /executive-explanation endpoint
30. Wire Scenario DNA into scenario create flow

**Decision Gate 5:** Complete Hormuz scenario end-to-end: create scenario → create run → retrieve all results → all outputs pass canonical JSON schema validation.

**Phase 6: Frontend Rebuild (Days 15-18)**
31. Create frontend API client layer (lib/api/)
32. Rebuild TypeScript types from v4 schema
33. Create DashboardHome (run list, portfolio overview)
34. Create RunDetailPage (status, version bundle, stage progress)
35. Create FinancialImpactPage (loss chart, entity grid)
36. Create DecisionPanelPage (ranked actions, narrative)
37. Create RegulatoryStatusPage (breach timeline)
38. Create TimelinePage (timestep playback)

**Phase 7: Cleanup + Validation (Days 19-20)**
39. Remove backend/src/ directory
40. Remove frontend/src/ directory
41. Remove legacy API routes
42. Run full test suite
43. Validate every endpoint against canonical JSON schema
44. Run Hormuz scenario end-to-end and capture golden fixture

**Final Decision Gate:** All v4 endpoints operational. Hormuz scenario passes schema validation. No legacy code paths remain. Test suite green.

---

## 8. RISKS AND SAFEGUARDS

### 8.1 Risk Register

| # | Risk | Probability | Impact | Mitigation |
|---|---|---|---|---|
| R1 | Async execution model introduces race conditions in run status | HIGH | HIGH | Implement synchronous-first with thin async wrapper; add database row locks on run status transitions |
| R2 | Entity-level stress computation reveals numeric edge cases (division by zero in LCR) | MEDIUM | MEDIUM | Add defensive guards: when projected_cash_outflows_30d = 0, set LCR = infinity equivalent (capped at 999.0) per v4 fallback rules |
| R3 | Schema migration breaks existing tests | HIGH | LOW | Run schema migration and test migration in parallel; maintain backward-compatible serialization during transition |
| R4 | v4 canonical JSON schema rejects current mock data format | HIGH | MEDIUM | Generate v4-compliant Hormuz fixture first; validate before any engine work |
| R5 | Time Engine temporal loop diverges for extreme scenarios | MEDIUM | HIGH | Enforce PROPAGATION_MAX_ITERATIONS and PROPAGATION_CONVERGENCE_EPSILON at every timestep; fail stage with NUMERIC_STABILITY_ERROR if non-finite |
| R6 | JWT auth migration locks out development access | MEDIUM | MEDIUM | Implement dev-mode bypass (APP_ENV=dev accepts any valid-format token with configurable issuer) |
| R7 | Legacy backend/src/ code is still imported by active code | LOW | HIGH | Run import analysis before deletion; ensure zero cross-references from app/ to src/ |
| R8 | Frontend dual structure (app/ + src/) causes build conflicts | MEDIUM | MEDIUM | Delete frontend/src/ only after verifying no imports from active app/ reference it |
| R9 | Decision engine tie-breaking order not deterministic | LOW | HIGH | Implement exact v4 tie-breaking: higher reg_risk → higher urgency → lower execution_window_hours → lexicographic action_id |
| R10 | Version bundle not frozen at run creation, causing mid-run drift | MEDIUM | CRITICAL | Snapshot all 4 version dimensions into run row before first stage executes; read from snapshot for all downstream stages |
| R11 | Missing Alembic migrations cause deployment failures | HIGH | HIGH | Create initial migration from v4 schema on Day 1; run migration in CI before any test |
| R12 | Idempotency-Key not enforced, causing duplicate runs | MEDIUM | HIGH | Implement app/core/idempotency.py with PostgreSQL unique constraint on (idempotency_key, request_hash); return original response on replay |

### 8.2 Safeguards

**Schema Validation Gate:** Before any engine refactoring, generate a v4-compliant Hormuz scenario JSON and validate it against canonical_json_schema_v4.json. This fixture becomes the golden input for all subsequent work.

**Incremental Migration:** Never refactor more than one domain model at a time. After each model migration, run the validation suite. If any model fails schema validation, halt and fix before proceeding.

**Feature Flags:** Use APP_ENV-based feature flags to toggle between current and v4 API routes during transition. Both can coexist temporarily on different prefixes (/observatory/* = current, /api/v1/* = v4).

**Rollback Strategy:** All changes go on feature branches. Main branch always has a working (current) system. Feature branches are merged only after passing v4 schema validation.

**Audit Trail Continuity:** The current SHA-256 audit hash mechanism is preserved through the transition. v4 adds run-level audit_hash computation over the full output bundle.

**Test Coverage Gate:** No phase is complete until its Decision Gate passes. Gates are binary: pass or fix. No skipping.

---

*End of Master Analysis. Proceed to COWORK STEP 1 (Repository Audit) on approval.*
