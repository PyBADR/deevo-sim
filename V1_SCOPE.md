# V1 Scope Lock — Step 9 (LOCKED)

**Date:** 2026-04-02
**Flagship Scenario:** Hormuz Strait Closure — 14 Day — Severe (shock 4.25/5.0)
**Scenario ID:** `hormuz-closure-v1`
**Goal:** End-to-end pipeline execution producing all 9 outputs, rendered in a single executive dashboard

---

## 1. Flagship Scenario: Hormuz Closure — 14D — Severe

### 1.1 Scenario Parameters (from `backend/app/seeds/hormuz_v1.py`)

| Parameter | Value |
|-----------|-------|
| `scenario_id` | `hormuz-closure-v1` |
| `shock_intensity` | 4.25 (0-5 scale) |
| `horizon_days` | 14 |
| `currency` | USD |
| `market_liquidity_haircut` | 0.35 |
| `deposit_run_rate` | 0.08 |
| `claims_spike_rate` | 0.85 |
| `fraud_loss_rate` | 0.02 |
| `jurisdiction` | GCC |
| `regulatory_version` | 2.4.0 |
| `severity_band` (DNA) | extreme |
| `transmission_mode` (DNA) | mixed |
| `time_granularity` | 1440 min (daily) |
| `time_horizon_steps` | 14 |
| `shock_decay_rate` | 0.05 per step |
| `recovery_rate` | 0.02 per step |

### 1.2 Entity Graph

**12 entities** across 4 sectors:

| Entity ID | Type | Name | Exposure ($B) | Criticality |
|-----------|------|------|---------------|-------------|
| `bank-gcc-001` | bank | GCC Tier-1 Banks | 1,800 | 0.95 |
| `bank-gcc-002` | bank | GCC Tier-2 Banks | 700 | 0.80 |
| `bank-gcc-003` | bank | Islamic Banks | 300 | 0.65 |
| `bank-gcc-004` | bank | Central Bank Reserves | 780 | 0.99 |
| `ins-gcc-001` | insurer | Primary Insurers | 280 | 0.75 |
| `ins-gcc-002` | insurer | Reinsurers | 120 | 0.70 |
| `ins-gcc-003` | insurer | Takaful Operators | 50 | 0.50 |
| `fin-gcc-001` | fintech | Payment Gateways | 90 | 0.85 |
| `fin-gcc-002` | fintech | Digital Banks | 60 | 0.65 |
| `fin-gcc-003` | fintech | Settlement Infrastructure | 30 | 0.90 |
| `mkt-gcc-001` | market_infrastructure | Stock Exchanges | 420 | 0.80 |
| `mkt-gcc-002` | market_infrastructure | Commodity Markets | 540 | 0.85 |

**Total system exposure:** $5,170B

**15 edges** covering 5 relation types: funding (4), insurance (4), payment (3), technology (2), market (2). Transmission coefficients range 0.35-0.85.

### 1.3 Sector Impact Chain (Scenario DNA)

| Step | Source | Target | Channel | Strength | Lag |
|------|--------|--------|---------|----------|-----|
| 1 | market_infrastructure | bank | liquidity | 0.75 | 1 step |
| 2 | bank | insurer | claims | 0.55 | 2 steps |
| 3 | bank | fintech | payment | 0.80 | 1 step |
| 4 | insurer | bank | capital | 0.30 | 3 steps |

---

## 2. V1 Required Outputs — 9 Pipeline Stages + 2 Post-Pipeline

### 2.1 Pipeline Outputs (from `pipeline_v4.py`)

| # | Stage | Engine | Output Model | Status |
|---|-------|--------|--------------|--------|
| 1 | scenario | `pipeline_v4.py` (inline) | `Scenario` | READY — seed data loads, no computation |
| 2 | physics | `intelligence/physics_core.py` | System stress scalar | OPTIONAL — graceful degradation if missing |
| 3 | graph | `pipeline_v4.py` (inline) | Entity + Edge lists | READY — pass-through from scenario |
| 4 | propagation | `intelligence/engines.py` | `propagation_factors: dict[str, float]` | STUB — defaults to 0.65 per entity |
| 5 | financial | `services/financial/engine.py` | `List[FinancialImpact]` (12 records) | READY — formula: Loss = Exposure x Shock x PropFactor |
| 6 | risk | banking: `services/banking/engine.py`, insurance: `services/insurance/engine.py`, fintech: `services/fintech/engine.py` | `List[BankingStress]` (4), `List[InsuranceStress]` (3), `List[FintechStress]` (3) | READY — all 3 engines compute per-entity with breach flags |
| 7 | regulatory | `services/regulatory/engine.py` | `RegulatoryState` | READY — aggregates breach flags, classifies breach level |
| 8 | decision | `services/decision/engine.py` | `DecisionPlan` with top-3 `DecisionAction` | READY — 5-factor priority formula, 8 candidate pool |
| 9 | explanation | `services/explainability/engine.py` | `ExplanationPack` | READY — summary, equations, drivers, traces, action explanations |

### 2.2 Post-Pipeline Outputs

| # | Layer | Engine | Output Model | Status |
|---|-------|--------|--------------|--------|
| 10 | business_impact | `services/business_impact/engine.py` | `BusinessImpactSummary` | READY — loss trajectory, time-to-failure, severity mapping |
| 11 | timeline | `services/time_engine/engine.py` | `List[TimeStepState]` (14 steps) | READY — per-entity temporal simulation |

### 2.3 Engine Readiness Summary

| Category | Count | Detail |
|----------|-------|--------|
| READY (compute implemented) | 9 | financial, banking, insurance, fintech, regulatory, decision, explanation, business_impact, time_engine |
| PASS-THROUGH (no computation) | 2 | scenario, graph |
| STUB (hardcoded default) | 1 | propagation (always 0.65) |
| OPTIONAL (graceful skip) | 1 | physics (import guard) |

---

## 3. V1 Build Scope — What Must Be Built

### 3.1 CRITICAL: Pipeline → API Wiring (currently broken)

**The single most critical V1 gap.** `POST /runs` creates run metadata but does NOT invoke `run_v4_pipeline()`. All GET endpoints query `_run_results` which is never populated.

**Required wiring code in `runs.py`:**

```python
# In create_run(), after creating run_data:
from ....seeds.hormuz_v1 import build_hormuz_v1_scenario
from ....orchestration.pipeline_v4 import run_v4_pipeline

scenario = build_hormuz_v1_scenario()
pipeline_result = run_v4_pipeline(scenario, run_id=run_id)

# Serialize pipeline_result into _run_results[run_id]
_run_results[run_id] = serialize_pipeline_result(pipeline_result)
_runs[run_id]["status"] = "completed"
```

**Also required:** `serialize_pipeline_result()` function that converts `V4PipelineResult` into the dict shape expected by GET endpoints (keys: `financial`, `banking`, `insurance`, `fintech`, `decision`, `explanation`, `business_impact`, `timeline`, `regulatory_timeline`, `executive_explanation`).

### 3.2 Backend Tasks (ordered)

| # | Task | File(s) | Effort |
|---|------|---------|--------|
| B1 | Wire `run_v4_pipeline()` into `POST /runs` | `api/v1/routes/runs.py` | 1h |
| B2 | Build `serialize_pipeline_result()` for GET endpoints | `api/v1/routes/runs.py` | 2h |
| B3 | Add `GET /runs/{id}/status` endpoint for polling | `api/v1/routes/runs.py` | 30min |
| B4 | Wire Hormuz seed as default scenario in V1 | `api/v1/routes/runs.py` | 30min |
| B5 | Fix propagation stage to use actual graph traversal (or accept stub) | `pipeline_v4.py` | ACCEPT STUB for V1 |
| B6 | Add `POST /runs/{id}/execute` for scenario-driven execution | `api/v1/routes/runs.py` | 1h |
| B7 | Add basic request validation (scenario_id lookup) | `api/v1/routes/runs.py` | 1h |

**Total backend effort:** ~6 hours

### 3.3 Frontend Tasks (ordered)

| # | Task | File(s) | Effort |
|---|------|---------|--------|
| F1 | Replace landing page with IO executive shell | `src/app/page.tsx`, `src/app/layout.tsx` | 4h |
| F2 | Build `RunResult` fetch hook via TanStack Query | `lib/hooks/useRunResult.ts` | 2h |
| F3 | Build Headline Summary bar (5 KPIs) | `components/dashboard/HeadlineSummary.tsx` | 3h |
| F4 | Build Financial Impact panel (table + chart) | `components/dashboard/FinancialImpactPanel.tsx` | 3h |
| F5 | Build Banking Stress panel | `components/dashboard/BankingStressPanel.tsx` | 2h |
| F6 | Build Insurance Stress panel | `components/dashboard/InsuranceStressPanel.tsx` | 2h |
| F7 | Build Fintech Stress panel | `components/dashboard/FintechStressPanel.tsx` | 2h |
| F8 | Build Decision Actions panel (top-3 cards) | `components/dashboard/DecisionPanel.tsx` | 3h |
| F9 | Build Explanation panel (drivers + traces) | `components/dashboard/ExplanationPanel.tsx` | 2h |
| F10 | Build Business Impact Timeline (Recharts line chart) | `components/dashboard/BusinessImpactTimeline.tsx` | 4h |
| F11 | Build Regulatory Breach Timeline | `components/dashboard/RegulatoryBreachTimeline.tsx` | 3h |
| F12 | Bilingual labels (EN/AR) for all components | `lib/i18n/labels.ts` | 2h |
| F13 | RTL/LTR layout toggle | `src/app/layout.tsx`, Tailwind config | 2h |
| F14 | Role-based visibility (viewer cannot see decisions) | `lib/server/rbac.ts` + component guards | 2h |

**Total frontend effort:** ~36 hours

### 3.4 Integration Tasks

| # | Task | Effort |
|---|------|--------|
| I1 | End-to-end test: POST /runs → poll status → GET all 10 endpoints → validate shapes | 4h |
| I2 | Frontend integration test: load dashboard, verify all panels render with Hormuz data | 2h |
| I3 | CORS configuration for frontend → backend (dev mode) | 30min |
| I4 | Docker Compose verification: backend + frontend + postgres start cleanly | 1h |

**Total integration effort:** ~7.5 hours

---

## 4. Expected Hormuz V1 Outputs (Numerical Bounds)

### 4.1 Financial Impact

With shock=4.25, propagation=0.65, and 12 entities:

| Metric | Expected Range | Formula Basis |
|--------|---------------|---------------|
| Total system loss | $9,000B-$9,600B | Sum(Exposure_i x 4.25 x 0.65) across 12 entities |
| Total revenue at risk | $5,100B-$5,500B | loss x (14/14) x 0.8 |
| Entities in breach/default | 8-12 | capital_after < capital_buffer x 0.3 |
| Banking sector loss | $7,000B-$7,600B | 4 banks, exposure=$3,580B |
| Insurance sector loss | $1,100B-$1,300B | 3 insurers, exposure=$450B |
| Fintech sector loss | $450B-$550B | 3 fintechs, exposure=$180B |

### 4.2 Banking Stress

| Metric | Expected Range | Threshold |
|--------|---------------|-----------|
| Aggregate LCR | 0.2-0.5 | Min: 1.0 → **BREACH** |
| Aggregate NSFR | 0.8-1.1 | Min: 1.0 → **LIKELY BREACH** |
| Aggregate CET1 | 0.02-0.06 | Min: 0.045 → **LIKELY BREACH** |
| Aggregate CAR | 0.04-0.09 | Min: 0.08 → **LIKELY BREACH** |
| Total deposit outflow | $600B-$1,200B | deposit_run_rate(0.08) x shock(4.25) |

### 4.3 Insurance Stress

| Metric | Expected Range | Threshold |
|--------|---------------|-----------|
| Aggregate solvency | -2.7 to -3.7 | Min: 1.0 → **BREACH** |
| Aggregate combined ratio | 2.8-3.0 | Max: 1.2 → **BREACH** |
| Aggregate reserve ratio | -1.5 to 0.0 | Min: 0.5 → **BREACH** |
| Claims spike | 3.5-3.7 | 0.85 x 4.25 |

### 4.4 Fintech Stress

Fintech stress engine not included in reads — follow same pattern as banking/insurance. Expected availability breaches under shock 4.25.

### 4.5 Regulatory State

| Metric | Expected |
|--------|----------|
| `breach_level` | `critical` (total breaches >= 6) |
| Mandatory actions | `BASEL3_LCR_REMEDIATION`, `SOLVENCY_CAPITAL_REQUIREMENT`, `SAMA_ALERT_CRITICAL`, `IFRS17_LOSS_RECOGNITION` |
| `reporting_required` | `true` |

### 4.6 Decision Plan

| Metric | Expected |
|--------|----------|
| Candidate pool | 8 action types |
| Applicable actions | 6-8 (most breaches fire) |
| Top-3 actions | `inject_liquidity` (#1), `activate_bcp` (#2), `increase_reserves` or `raise_capital_buffer` (#3) |
| `constrained_by_regulation` | `true` (some actions require override) |

### 4.7 Business Impact Summary

| Metric | Expected |
|--------|----------|
| `peak_cumulative_loss` | >$500B → severity=`severe` |
| `business_severity` | `severe` |
| `executive_status` | `crisis` (from SEVERITY_MAPPING) |
| `system_time_to_first_failure_hours` | 24-72h (banking LCR first) |
| Loss trajectory | 14 timesteps, decaying shock, cumulative loss |
| Regulatory breach events | 6+ breach events across banking/insurance/fintech |

### 4.8 Timeline

| Metric | Expected |
|--------|----------|
| Steps | 14 (daily, matching `time_horizon_steps`) |
| Entity impacts per step | 12 (all entities) |
| System status progression | stable → watch → breach → failed across days 1-7 |
| Peak aggregate loss | Days 2-4 (before shock decay dominates) |

---

## 5. Explicitly OUT OF SCOPE for V1

### 5.1 Backend — Out of Scope

| Item | V4 Spec | Why Deferred |
|------|---------|--------------|
| WebSocket streaming | §21 | V1 uses HTTP polling; real-time streaming is P2 |
| Multi-tenant data isolation | §22 | V1 is single-tenant (`tenant_id="default"`); RLS is P3 |
| Production JWT authentication | §10 | V1 uses dev API keys; JWT is P2 |
| Physics engine (stress modeling) | §7 Stage 2 | Optional with graceful degradation; NOOP in V1 |
| Graph propagation engine | §7 Stage 4 | Stub with 0.65 default; full BFS/PageRank is P2 |
| Monte Carlo uncertainty bands | §5.2 | V1 is deterministic; MC simulation is P3 |
| Executive explanation engine | §19 | Returns empty in V1; narrative generation requires LLM integration (P2) |
| Scenario comparison | §18.3 | Single scenario only; A/B comparison is P2 |
| Audit trail persistence (PostgreSQL) | §9 | V1 computes SHA-256 hash in-memory only; DB audit log is P2 |
| Per-entity loss trajectories | §16.3 | V1 computes system-level trajectory only; per-entity is P2 |
| Regulatory timeline endpoint | §16.4 | Endpoint exists but may return empty until wired |
| Cross-border contagion | §3.13 | V1 limited to GCC member states |

### 5.2 Frontend — Out of Scope

| Item | Why Deferred |
|------|--------------|
| CesiumJS 3D globe | V1 is dashboard-first; globe is secondary view (P2) |
| Entity graph visualization (D3/force) | Secondary panel; defer to P2 |
| Flow/route view | Secondary panel; defer to P2 |
| Dark mode | V1 ships light executive theme only |
| Scenario builder UI | V1 uses Hormuz seed only; custom scenarios via API |
| WebSocket live updates | V1 uses HTTP polling |
| PDF/PPTX export | P2 feature |
| Analyst trace panel (deep) | V1 shows summary explanation; full trace is P2 |
| Multi-language beyond EN/AR | V1 supports English + Arabic only |
| Mobile responsive layout | V1 targets desktop 1440px+ |

### 5.3 Infrastructure — Out of Scope

| Item | Why Deferred |
|------|--------------|
| Neo4j graph database | V1 uses in-memory entity/edge lists |
| Redis caching | V1 uses in-memory stores |
| PostgreSQL for run persistence | V1 uses in-memory `_runs` / `_run_results` dicts |
| Kubernetes deployment | V1 runs on Docker Compose (Mac M4 Max local) |
| CI/CD pipeline | V1 is manual deploy |
| Observability (Prometheus/Grafana) | V1 logs to stdout |

---

## 6. Success Criteria

### 6.1 Pipeline Execution

| Criterion | Measurement |
|-----------|-------------|
| All 9 pipeline stages complete | `stages_completed` count = 9 (or 8 if physics skipped) |
| Post-pipeline: business_impact computed | `business_impact` is not None |
| Post-pipeline: timeline computed | `timeline` has exactly 14 timesteps |
| Pipeline execution time | < 500ms on Mac M4 Max |
| SHA-256 audit hash generated | `audit_hash` is not empty and not "unavailable" |

### 6.2 API Endpoints

| Criterion | Measurement |
|-----------|-------------|
| `POST /runs` returns 202 with `run_id` | Status 202, body contains `run_id` |
| `GET /runs/{id}/financial` returns 12 entity impacts | Array length = 12, each has `loss > 0` |
| `GET /runs/{id}/banking` returns aggregate + per-entity | 4 banking stresses with breach flags |
| `GET /runs/{id}/insurance` returns aggregate + per-entity | 3 insurance stresses with breach flags |
| `GET /runs/{id}/fintech` returns aggregate + per-entity | 3 fintech stresses with breach flags |
| `GET /runs/{id}/decision` returns top-3 actions | Array length = 3, each has `priority_score > 0` |
| `GET /runs/{id}/explanation` returns pack | Has `summary`, `equations`, `drivers`, `stage_traces` |
| `GET /runs/{id}/business-impact` returns summary | Has `business_severity`, `executive_status`, `loss_trajectory` |
| `GET /runs/{id}/timeline` returns 14 steps | Array length = 14, each has `entity_impacts` |
| Auth: viewer blocked from `/decision` | Returns 403 with `DecisionAccessDenied` error |
| Auth: invalid key returns 401 | Returns 401 with `InsufficientRole` error |

### 6.3 Dashboard Rendering

| Criterion | Measurement |
|-----------|-------------|
| Headline bar shows 5 KPIs | Headline Loss, Peak Day, Time to First Failure, Business Severity, Executive Status |
| All 8 core panels render with data | Financial, Banking, Insurance, Fintech, Decision, Explanation, Business Impact Timeline, Regulatory Breach Timeline |
| Bilingual labels render correctly | Toggle EN ↔ AR, all labels update |
| RTL layout works for Arabic | `dir="rtl"` applies, panels reflow |
| Viewer role: decision panel hidden | Component guard hides panel for viewer role |
| No blank panels or loading spinners stuck | All data fetched and rendered within 2s of page load |

### 6.4 Data Integrity

| Criterion | Measurement |
|-----------|-------------|
| Financial loss formula matches spec | Loss_i = Exposure_i x ShockIntensity x PropFactor |
| Banking LCR formula produces breach at shock 4.25 | LCR < 1.0 for all 4 bank entities |
| Insurance solvency breaches at shock 4.25 | Solvency < 1.0 for all 3 insurer entities |
| Regulatory breach_level = "critical" | total_breaches >= 6 |
| Decision top-1 is `inject_liquidity` | Highest priority action for banking LCR breach |
| Business severity = "severe" | peak_cumulative_loss >= $500B threshold |
| Timeline shows degradation then stabilization | Day 1-7 worsening, Day 8-14 partial recovery (decay > recovery) |

---

## 7. V1 Build Sequence (Ordered Implementation)

| Phase | Tasks | Depends On | Duration |
|-------|-------|-----------|----------|
| **Phase A: Backend Wiring** | B1, B2, B3, B4, B7 | Nothing — start here | 6h |
| **Phase B: Frontend Shell** | F1, F13, F12 | Step 3 (FRONTEND_REPLACEMENT_PLAN) | 8h |
| **Phase C: Data Layer** | F2 | Phase A (API must return data) | 2h |
| **Phase D: Core Panels** | F3, F4, F5, F6, F7, F8, F9 | Phase C (data hook ready) | 17h |
| **Phase E: Timeline Panels** | F10, F11 | Phase C | 7h |
| **Phase F: RBAC Guards** | F14 | Phase D (panels exist) | 2h |
| **Phase G: Integration** | I1, I2, I3, I4 | Phase A + Phase D | 7.5h |

**Total estimated effort:** ~49.5 hours
**Critical path:** Phase A → Phase C → Phase D → Phase G

---

## 8. Risk Register

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| Propagation stub (0.65) produces unrealistic cascading | Medium | Medium | Document as known limitation; validate output bounds manually |
| In-memory store loses data on restart | High | Low for V1 | Acceptable for demo; PostgreSQL persistence in P2 |
| Financial loss values in $B range look unrealistic to GCC clients | Medium | High | Add disclaimer: "aggregate sector-level, not institution-level"; recalibrate exposure values if needed |
| Insurance solvency goes negative (mathematical artifact) | High | Medium | Clamp to 0.0 minimum in engine; add note in explanation |
| Frontend build errors from stale Next.js cache | Medium | Low | Clean build script in Makefile |
| CORS blocks frontend → backend in dev | Medium | Medium | Add CORS middleware in FastAPI app startup |
| Docker Compose service ordering (backend before postgres) | Low | Medium | Add `depends_on` + healthcheck |

---

## 9. Decision Gate

This plan is **LOCKED**. Before beginning implementation:

1. **Prerequisite from Step 3:** Frontend replacement plan must be referenced for shell layout (file: `FRONTEND_REPLACEMENT_PLAN.md`)
2. **Prerequisite from Step 4:** Dashboard structure must be referenced for panel placement (file: `DASHBOARD_STRUCTURE.md`)
3. **Prerequisite from Step 5:** Canonical model alignment must be referenced for type imports (file: `CANONICAL_MODEL_ALIGNMENT.md`)
4. **Prerequisite from Step 7:** Business impact + time layer must be referenced for timeline panels (file: `BUSINESS_IMPACT_TIME_LAYER.md`)
5. **Prerequisite from Step 8:** RBAC plan must be referenced for role-gated visibility (file: `RBAC_IMPLEMENTATION_PLAN.md`)
6. **Critical first action:** Phase A (backend wiring) — wire `run_v4_pipeline()` into `POST /runs` so all downstream GET endpoints return real data
7. **V1 ships Hormuz only:** No scenario builder, no custom scenarios. Single flagship scenario exercising full pipeline.

**What must be true before V1 is "done":**
- `POST /runs` triggers full pipeline and returns 202
- All 10 GET endpoints return non-empty, schema-valid responses
- Dashboard renders all 8 core panels + 2 timeline panels with real Hormuz data
- Viewer role is blocked from decision endpoint (403)
- Pipeline completes in < 500ms
- SHA-256 audit hash present on every run

Awaiting your command to begin execution.
