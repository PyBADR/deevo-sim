# Execution Blueprint — Step 10 (LOCKED)

**Date:** 2026-04-02
**Scope:** Consolidated execution plan synthesizing Steps 1-9
**Flagship:** Hormuz Closure — 14D — Severe (shock 4.25)
**Outcome:** Working V1 with full pipeline → API → dashboard rendering

---

## Master Dependency Chain

```
Step 1 (Audit) ─── identifies conflicts ───────────────────────┐
Step 2 (Rename) ── cosmetic + credential alignment ────────────┤
Step 5 (Models) ── single source of truth ─────────────────────┤
                                                                ▼
                                                    STAGE 1: CLEAN
                                                    Remove dead code
                                                    Align entrypoints
                                                    Fix credentials
                                                                │
Step 9 (V1 Scope) ── pipeline wiring gap ──────────────────────┤
Step 7 (Biz Impact) ── post-pipeline engines ──────────────────┤
                                                                ▼
                                                    STAGE 2: WIRE
                                                    Pipeline → API
                                                    Serialize results
                                                    Validate endpoints
                                                                │
Step 3 (Frontend) ── replace shell ────────────────────────────┤
Step 4 (Dashboard) ── panel structure ─────────────────────────┤
Step 8 (RBAC) ── permission guards ────────────────────────────┤
                                                                ▼
                                                    STAGE 3: BUILD
                                                    Dashboard shell
                                                    Core panels
                                                    Timeline panels
                                                    RBAC guards
                                                                │
                                                                ▼
                                                    STAGE 4: VERIFY
                                                    End-to-end tests
                                                    Output validation
                                                    Audit hash check
```

---

## STAGE 1: CLEAN (Files to Change First)

**Goal:** Remove dead code, resolve all architectural conflicts (CONFLICT-1 through CONFLICT-5 from Step 1), align credentials and entrypoints. Zero new features — only subtraction and alignment.

### 1A. Remove `backend/src/` Dead Code Tree

**Source:** Step 1 (CONFLICT-1, CONFLICT-3), Step 2 (Phase 2), Step 5 (Phase 1)

**Pre-check:** Verify no cross-imports exist.
```
grep -r "from src\." backend/app/   → must return 0 results
grep -r "import src\." backend/app/ → must return 0 results
```

**Files to REMOVE (120 files):**

| # | Path | Reason |
|---|------|--------|
| 1 | `backend/src/__init__.py` | Dead entrypoint tree |
| 2 | `backend/src/main.py` | Duplicate entrypoint — CONFLICT-1 |
| 3 | `backend/src/api/` (14 files) | Duplicate routes — CONFLICT-1 |
| 4 | `backend/src/connectors/` (4 files) | Unused adapters |
| 5 | `backend/src/core/` (3 files) | Duplicate config — CONFLICT-5 |
| 6 | `backend/src/db/` (4 files) | Duplicate DB clients |
| 7 | `backend/src/engines/` (38 files) | Duplicate engines — CONFLICT-3 |
| 8 | `backend/src/graph/` (4 files) | Duplicate graph loader |
| 9 | `backend/src/i18n/` (2 files) | Duplicate labels |
| 10 | `backend/src/models/` (3 files) | V0 ingest models (canonical.py = separate concern, but entire `src/` tree goes) |
| 11 | `backend/src/normalization/` (2 files) | Unused |
| 12 | `backend/src/orchestration/` (1 file) | Unused stub |
| 13 | `backend/src/rules/` (3 files) | Duplicate of `app/core/constants.py` thresholds |
| 14 | `backend/src/schemas/` (13 files) | Dead duplicate — Step 5 Location C |
| 15 | `backend/src/services/` (16 files) | Duplicate services |

**Exception — preserve before removal:**
- `backend/src/models/canonical.py` → Copy to `backend/app/models/canonical_ingest.py` as V0 ingest reference (optional, no runtime dependency)
- `backend/src/engines/physics/` and `backend/src/engines/math/` → If any algorithms are NOT duplicated in `backend/app/intelligence/`, flag before deletion. Cross-check during pre-check.

### 1B. Align Entrypoints to `app.main:app`

**Source:** Step 2 (Category G)

**Files to EDIT (3 files):**

| # | File | Line | Old | New |
|---|------|------|-----|-----|
| 1 | `Makefile` | 85 | `uvicorn src.main:app` | `uvicorn app.main:app` |
| 2 | `Procfile` | 1 | `uvicorn src.main:app` | `uvicorn app.main:app` |
| 3 | `Dockerfile.backend` | 24 | `uvicorn src.main:app` | `uvicorn app.main:app` |

### 1C. Remove V2 Frontend Dead Code

**Source:** Step 3 (Phase 1), Step 1 (CONFLICT-2, CONFLICT-4)

**Files to REMOVE (11 files):**

| # | Path | Reason |
|---|------|--------|
| 1 | `frontend/app/page.tsx` | Shadowed by `src/app/page.tsx` |
| 2 | `frontend/app/layout.tsx` | Shadowed by `src/app/layout.tsx` |
| 3 | `frontend/app/dashboard/page.tsx` | Shadowed by `src/app/dashboard/page.tsx` |
| 4 | `frontend/app/scenarios/page.tsx` | Dark theme (`bg-zinc-950`) — no V4 equivalent needed |
| 5 | `frontend/app/control-room/layout.tsx` | Shadowed by `src/app/control-room/` |
| 6 | `frontend/app/api/run-scenario/route.ts` | V2 API route — verify if V4 has equivalent before removing |
| 7 | `frontend/app/api/scenarios/route.ts` | V2 API route — verify |
| 8 | `frontend/app/api/audit/[id]/route.ts` | V2 API route — verify |
| 9 | `frontend/styles/globals.css` | Superseded by `src/theme/globals.css` — CONFLICT-4 |
| 10 | `frontend/components/ui/Navbar.tsx` | Only used by V2 pages |
| 11 | `frontend/components/ui/Footer.tsx` | Only used by V2 pages |

**Pre-check:** Verify no V4 file imports from V2 paths.
```
grep -r "from.*app/" frontend/src/    → exclude src/app/ matches
grep -r "../components/ui" frontend/src/ → must return 0
grep -r "../styles" frontend/src/        → must return 0
```

### 1D. Remove V2 Frontend `lib/` Duplicates

**Source:** Step 3 (Section 6), Step 5 (Phase 4)

**Files to REMOVE (7 files):**

| # | Path | Reason | Pre-check |
|---|------|--------|-----------|
| 1 | `frontend/lib/api/client.ts` | Superseded by `src/lib/api.ts` | `grep -r "lib/api/client" frontend/src/` = 0 |
| 2 | `frontend/lib/api/index.ts` | Re-exports V2 client only | same grep |
| 3 | `frontend/lib/types.ts` | Superseded by `src/types/index.ts` | `grep -r "lib/types" frontend/src/` — check for imports |
| 4 | `frontend/lib/i18n.ts` | Superseded by `src/i18n/` JSON | `grep -r "lib/i18n" frontend/src/` = 0 |
| 5 | `frontend/lib/mock-data.ts` | Mock data — not needed with real API | `grep -r "mock-data" frontend/src/` = 0 |
| 6 | `frontend/components/graph/GraphPanel.tsx` | Only used by V2 dashboard | `grep -r "GraphPanel" frontend/src/` = 0 |
| 7 | `frontend/lib/gcc-graph.ts` | Superseded by `@deevo/gcc-knowledge-graph` | `grep -r "gcc-graph" frontend/src/` = 0 |

**Files to KEEP in `lib/`:**

| # | Path | Reason |
|---|------|--------|
| 1 | `frontend/lib/server/rbac.ts` | Active RBAC — needed by Step 8 |
| 2 | `frontend/lib/server/auth.ts` | Active auth — API key validation |
| 3 | `frontend/lib/server/audit.ts` | Active audit trail |
| 4 | `frontend/lib/server/execution.ts` | Active pipeline execution |
| 5 | `frontend/lib/server/store.ts` | Active server-side state |
| 6 | `frontend/lib/server/trace.ts` | Active trace logging |
| 7 | `frontend/lib/types/observatory.ts` | V4 domain mirror — merge into `src/types/` in Stage 3, then delete |
| 8 | `frontend/lib/simulation-engine.ts` | Evaluate — may contain useful client-side logic |
| 9 | `frontend/lib/decision-engine.ts` | Evaluate — may contain useful client-side logic |

### 1E. Cosmetic Renames

**Source:** Step 2 (Phase 1, Category A)

**Files to EDIT (2 files, 3 edits):**

| # | File | Old | New |
|---|------|-----|-----|
| 1 | `LICENSE` line 1 | `Copyright (c) 2026 Deevo Analytics.` | `Copyright (c) 2026 Impact Observatory.` |
| 2 | `LICENSE` line 6 | `permission of Deevo Analytics.` | `permission of Impact Observatory.` |
| 3 | `packages/@deevo/gcc-knowledge-graph/package.json` line 19 | `"author": "Deevo Analytics"` | `"author": "Impact Observatory"` |

### 1F. Database Credential Alignment

**Source:** Step 2 (Phase 3, Category D)

**Files to EDIT (1 file, 6 edits):**

| # | File | Line | Old | New |
|---|------|------|-----|-----|
| 1 | `docker-compose.yml` | 11 | `postgresql://deevo:deevo_secure@postgres:5432/deevo` | `postgresql://observatory_admin:io_pilot_2026@postgres:5432/impact_observatory` |
| 2 | `docker-compose.yml` | 14 | `NEO4J_PASSWORD=deevo_neo4j_2026` | `NEO4J_PASSWORD=io_graph_2026` |
| 3 | `docker-compose.yml` | 32 | `POSTGRES_DB=deevo` | `POSTGRES_DB=impact_observatory` |
| 4 | `docker-compose.yml` | 33 | `POSTGRES_USER=deevo` | `POSTGRES_USER=observatory_admin` |
| 5 | `docker-compose.yml` | 34 | `POSTGRES_PASSWORD=deevo_secure` | `POSTGRES_PASSWORD=io_pilot_2026` |
| 6 | `docker-compose.yml` | 49 | `NEO4J_AUTH=neo4j/deevo_neo4j_2026` | `NEO4J_AUTH=neo4j/io_graph_2026` |

**Post-action:** `docker-compose down -v && docker-compose up -d` to recreate volumes.

### STAGE 1 TEST GATE

| # | Test | Command | Pass Criteria |
|---|------|---------|---------------|
| T1 | Backend starts | `cd backend && uvicorn app.main:app --host 0.0.0.0 --port 8000` | Server starts, no ImportError |
| T2 | No src imports | `grep -r "from src\." backend/app/` | 0 results |
| T3 | Frontend builds | `cd frontend && npm run build` | Exit 0, no errors |
| T4 | Frontend types | `cd frontend && npx tsc --noEmit` | Exit 0 |
| T5 | Docker starts | `docker-compose up -d && docker-compose ps` | All services healthy |
| T6 | Health check | `curl http://localhost:8000/health` | 200 OK |
| T7 | No V2 pages | `ls frontend/app/*.tsx 2>/dev/null` | No results |

**Commit after Stage 1:** `"chore: remove dead code, align entrypoints and credentials to Impact Observatory"`

---

## STAGE 2: WIRE (Files to Change Second)

**Goal:** Make the pipeline produce real data through the API. This is the critical backend wiring that makes V1 functional.

### 2A. Wire Pipeline into POST /runs

**Source:** Step 9 (Section 3.1, task B1)

**File to EDIT:** `backend/app/api/v1/routes/runs.py`

**Changes:**
1. Import `build_hormuz_v1_scenario` from `app.seeds.hormuz_v1`
2. Import `run_v4_pipeline` from `app.orchestration.pipeline_v4`
3. In `create_run()` endpoint, after creating `run_data`:
   - Build scenario from seed
   - Execute `run_v4_pipeline(scenario, run_id=run_id)`
   - Serialize `V4PipelineResult` into `_run_results[run_id]`
   - Set `_runs[run_id]["status"] = "completed"`

### 2B. Build Result Serializer

**Source:** Step 9 (task B2)

**File to EDIT:** `backend/app/api/v1/routes/runs.py`

**New function: `serialize_pipeline_result(result: V4PipelineResult, run_id: str) -> dict`**

Must produce dict with keys matching all GET endpoints:
- `financial` → `[fi.model_dump() for fi in result.financial_impacts]`
- `banking` → aggregate + per-entity from `result.banking_stresses`
- `insurance` → aggregate + per-entity from `result.insurance_stresses`
- `fintech` → aggregate + per-entity from `result.fintech_stresses`
- `decision` → `result.decision_plan.model_dump()`
- `explanation` → `result.explanation_pack.model_dump()`
- `business_impact` → `result.business_impact.model_dump()` (includes loss_trajectory, time_to_failures, breach_events)
- `timeline` → `[ts.model_dump() for ts in result.timeline]`
- `regulatory_state` → `result.regulatory_state.model_dump()`
- `executive_explanation` → empty dict (deferred to P2)

### 2C. Refactor API Schemas

**Source:** Step 5 (Phase 2)

**File to EDIT:** `backend/app/schemas/observatory.py`

**Changes:**
1. Remove duplicate model definitions (Entity, Edge, FlowState, FinancialImpact, BankingStress, InsuranceStress, FintechStress, DecisionAction, DecisionPlan, RegulatoryState, ExplanationPack)
2. Import all from `app.domain.models`
3. Keep `ScenarioInput` → rename to `ScenarioCreateRequest` (thin API input)
4. Keep `ObservatoryOutput` envelope → update to reference domain models
5. Keep `LABELS` dict, `FLOW_STAGES`, `PROJECT` identity constants

### 2D. Add Status Polling Endpoint

**Source:** Step 9 (task B3)

**File to EDIT:** `backend/app/api/v1/routes/runs.py`

**New endpoint:** `GET /runs/{run_id}/status` → returns `{ run_id, status, created_at, completed_at }`

### 2E. Frontend Type Alignment

**Source:** Step 5 (Phase 3)

**File to EDIT:** `frontend/src/types/observatory.ts`

**Changes:**
1. Add optional V4 extension fields to `RunResult`:
   - `business_impact?: BusinessImpactSummary`
   - `loss_trajectory?: LossTrajectoryPoint[]`
   - `regulatory_breaches?: RegulatoryBreachEvent[]`
   - `pipeline_stages?: StageTrace[]`
   - `timeline?: TimeStepState[]`
2. Add missing type definitions (import from `lib/types/observatory.ts` or inline):
   - `BusinessImpactSummary`, `LossTrajectoryPoint`, `TimeToFailure`, `RegulatoryBreachEvent`, `TimeStepState`, `EntityTemporalImpact`
3. Fix field drift in `lib/types/observatory.ts`:
   - `metric_type` → `metric_name` in `RegulatoryBreachEvent`
   - Align `ExplanationDriver` fields to backend (`driver`, `magnitude`, `unit`)

### 2F. Frontend RBAC Alignment

**Source:** Step 8 (Section 2)

**File to EDIT:** `frontend/lib/server/rbac.ts`

**Changes:** Add 8 missing permissions to align with backend's 19:
- `read_banking`, `read_insurance`, `read_fintech`
- `read_business_impact`, `read_timeline`, `read_regulatory_timeline`, `read_executive_explanation`
- `launch_run_with_overrides`

Update role-permission mappings for all 5 roles.

### STAGE 2 TEST GATE

| # | Test | Command | Pass Criteria |
|---|------|---------|---------------|
| T8 | Pipeline executes | `curl -X POST http://localhost:8000/api/v1/runs -H "X-IO-API-Key: io_master_key_2026"` | 202, returns `run_id` |
| T9 | Financial data | `curl http://localhost:8000/api/v1/runs/{id}/financial -H "X-IO-API-Key: io_viewer_key_2026"` | 200, array of 12 FinancialImpact objects |
| T10 | Banking data | `curl .../runs/{id}/banking ...` | 200, 4 BankingStress with `lcr < 1.0` |
| T11 | Insurance data | `curl .../runs/{id}/insurance ...` | 200, 3 InsuranceStress with `solvency_ratio < 1.0` |
| T12 | Fintech data | `curl .../runs/{id}/fintech ...` | 200, 3 FintechStress |
| T13 | Decision data | `curl .../runs/{id}/decision ...` | 200, `actions` array length = 3 |
| T14 | Explanation data | `curl .../runs/{id}/explanation ...` | 200, has `summary`, `drivers`, `stage_traces` |
| T15 | Business impact | `curl .../runs/{id}/business-impact ...` | 200, `business_severity = "severe"`, `executive_status = "crisis"` |
| T16 | Timeline data | `curl .../runs/{id}/timeline ...` | 200, array length = 14 |
| T17 | RBAC block | `curl .../runs/{id}/decision -H "X-IO-API-Key: io_viewer_key_2026"` | 403 |
| T18 | Pipeline speed | Measure `duration_ms` from POST response | < 500ms |
| T19 | Audit hash | Check POST response body for `audit_hash` | Non-empty, 64 hex chars |
| T20 | Frontend types | `cd frontend && npx tsc --noEmit` | Exit 0 |

**Commit after Stage 2:** `"feat: wire V4 pipeline into API, all 10 endpoints return Hormuz data"`

---

## STAGE 3: BUILD (Frontend Dashboard)

**Goal:** Replace the frontend shell and build all dashboard panels to render Hormuz V1 data.

### 3A. Build AppShell + Navigation

**Source:** Step 3 (Phase 2), Step 4 (Section 1)

**Files to CREATE:**
- `frontend/src/components/shell/AppShell.tsx` — persistent top nav + optional sidebar
- `frontend/src/components/shell/TopNav.tsx` — extracted from `page.tsx` inline nav
- `frontend/src/components/shell/TabBar.tsx` — horizontal tab bar (9 tabs from Step 4)
- `frontend/src/components/shell/DashboardHeader.tsx` — scenario label + severity + toggles

**File to EDIT:**
- `frontend/src/app/layout.tsx` — wrap children in `AppShell`

### 3B. Build Data Fetch Hook

**Source:** Step 9 (task F2)

**File to CREATE:** `frontend/src/lib/hooks/useRunResult.ts`
- TanStack Query hook wrapping `POST /runs` + poll `GET /runs/{id}/status` + fetch all sub-endpoints
- Returns unified `RunResult` object

### 3C. Restructure Dashboard Page

**Source:** Step 3 (Phase 3), Step 4 (Section 1)

**File to EDIT:** `frontend/src/app/dashboard/page.tsx`
- Becomes `DashboardShell` orchestrator
- Reads `run_id` from URL params or Zustand
- Manages `activeTab` state
- Renders `DashboardHeader` + `TabBar` + `TabContent` per active tab
- Passes `RunResult` slices to child panels

### 3D. Build Headline Summary Bar

**Source:** Step 4 (Section 2 — 6 KPIs), Step 9 (task F3)

**File to CREATE:** `frontend/src/components/dashboard/HeadlineSummary.tsx`
- 6 `KPICard` instances: Headline Loss, Peak Day, Time to First Failure, Business Severity, Executive Status, Affected Entities
- Horizontal row, responsive wrap

### 3E. Build Core Panels

**Source:** Step 4 (Sections 2-3), Step 9 (tasks F4-F9)

**Files to CREATE (or integrate existing):**
- `frontend/src/components/dashboard/FinancialOverview.tsx` — wraps existing `FinancialImpactPanel` with 12 per-entity rows
- `frontend/src/components/dashboard/StressOverview.tsx` — 3x `StressGauge` (banking + insurance + fintech) in a column
- `frontend/src/components/dashboard/DecisionOverview.tsx` — 3x `DecisionActionCard` in a row

**Existing components to REUSE (zero changes):**
- `src/components/KPICard.tsx`
- `src/components/StressGauge.tsx`
- `src/components/FinancialImpactPanel.tsx`
- `src/components/DecisionActionCard.tsx`
- `src/features/banking/BankingDetailPanel.tsx`
- `src/features/insurance/InsuranceDetailPanel.tsx`
- `src/features/fintech/FintechDetailPanel.tsx`
- `src/features/decisions/DecisionDetailPanel.tsx`

### 3F. Build Timeline Panels

**Source:** Step 4 (Section 2 — Timeline), Step 7 (UI panels), Step 9 (tasks F10-F11)

**Files to CREATE:**
- `frontend/src/components/timeline/BusinessImpactTimeline.tsx`
  - Recharts `AreaChart` consuming `LossTrajectoryPoint[]`
  - Dual Y-axis: cumulative loss (left), daily delta (right)
  - Vertical annotations at peak day and breach points
- `frontend/src/components/timeline/RegulatoryBreachTimeline.tsx`
  - Vertical timeline consuming `RegulatoryBreachEvent[]`
  - Color-coded dots: red=critical, orange=major, yellow=minor
  - Entity name, threshold, actual value, agency

### 3G. Build Explanation Panel

**Source:** Step 4 (Section 2 — Decisions tab)

**File to CREATE:** `frontend/src/components/panels/ExplanationPanel.tsx`
- Renders `ExplanationPack` from API
- Summary text, equation references, driver list, stage trace cards, action explanations

### 3H. Bilingual Labels

**Source:** Step 4 (Section 4 — all label tables)

**File to EDIT:** `frontend/src/i18n/en.json` + `frontend/src/i18n/ar.json`
- Add all tab labels, KPI labels, panel titles, decision labels, stress classification labels from Step 4 Section 4

### 3I. RTL/LTR Toggle

**Source:** Step 3 (Design Principles), Step 9 (task F13)

**File to EDIT:** `frontend/src/app/layout.tsx`
- Dynamic `dir` attribute from Zustand `language` state
- CSS logical properties throughout (already partially in place)

### 3J. RBAC Visibility Guards

**Source:** Step 8 (Sections 3-4), Step 9 (task F14)

**File to CREATE:** `frontend/src/components/guards/PermissionGate.tsx`
- Wraps children, checks `hasPermission(userRole, permission)`
- Hides Decision tab for viewer role
- Hides override buttons for non-admin/non-regulator

**File to EDIT:** `frontend/src/store/app-store.ts`
- Add `userRole`, `tenantId`, `principalId` fields per Step 8 Section 6

### 3K. Merge V4 Types and Delete Duplicate

**Source:** Step 5 (Phase 4-5)

**Files to EDIT:**
- `frontend/src/types/observatory.ts` — merge unique V4 types from `lib/types/observatory.ts`
- `frontend/src/types/index.ts` — remove 4 legacy duplicates: `Scenario`, `ScenarioResult`, `DecisionAction`, `DecisionOutput`

**File to DELETE:** `frontend/lib/types/observatory.ts` (after merge complete)

### STAGE 3 TEST GATE

| # | Test | Command | Pass Criteria |
|---|------|---------|---------------|
| T21 | Frontend builds | `cd frontend && npm run build` | Exit 0 |
| T22 | Types check | `cd frontend && npx tsc --noEmit` | Exit 0 |
| T23 | Dashboard loads | Open `http://localhost:3000/dashboard` | No blank panels, no stuck spinners |
| T24 | 6 KPIs render | Visual check: HeadlineSummary bar | All 6 cards show values |
| T25 | Financial panel | Visual: FinancialOverview | 12 entity rows with loss values |
| T26 | Stress gauges | Visual: 3 StressGauge arcs | Banking/Insurance/Fintech all show breach |
| T27 | Decision cards | Visual: 3 DecisionActionCard | Ranked 1-2-3, priority scores shown |
| T28 | Timeline chart | Visual: BusinessImpactTimeline | 14 data points, cumulative curve |
| T29 | Breach timeline | Visual: RegulatoryBreachTimeline | 6+ breach events listed |
| T30 | AR toggle | Click language toggle | All labels switch to Arabic, layout goes RTL |
| T31 | Viewer block | Set viewer API key → reload | Decision tab hidden |

**Commit after Stage 3:** `"feat: executive dashboard shell with all panels rendering Hormuz V1 data"`

---

## STAGE 4: VERIFY (Integration + Audit)

**Goal:** End-to-end validation that the full stack works as a coherent product.

### 4A. End-to-End API Test

**Source:** Step 9 (task I1)

Run automated test sequence:
1. `POST /runs` with admin key → get `run_id`
2. Poll `GET /runs/{id}/status` → wait for `completed`
3. Hit all 10 GET endpoints → validate response shapes against Pydantic models
4. Verify numerical bounds from Step 9 Section 4:
   - Total loss in $9,000B-$9,600B range
   - Banking LCR < 1.0
   - Insurance solvency < 1.0
   - `breach_level = "critical"`
   - `business_severity = "severe"`
   - `executive_status = "crisis"`
   - Timeline has 14 steps
   - Decision actions count = 3, top-1 = `inject_liquidity`

### 4B. RBAC Enforcement Test

1. Viewer key → `GET /decision` → expect 403
2. Analyst key → `GET /decision` → expect 200
3. Invalid key → any endpoint → expect 401
4. Admin key → all endpoints → expect 200

### 4C. Audit Hash Verification

1. Run pipeline twice with identical Hormuz scenario
2. Compare `audit_hash` — must be identical (deterministic)
3. Modify one scenario parameter → hash must differ

### 4D. Frontend Integration Test

1. Load `/dashboard` in browser
2. Verify all 8 core panels render with non-zero data
3. Verify 2 timeline panels render with non-zero data
4. Toggle EN ↔ AR — all labels switch
5. Toggle viewer role — decision panel hides
6. Check no console errors

### 4E. Docker Compose Smoke Test

**Source:** Step 9 (task I4)

```bash
docker-compose down -v
docker-compose up -d
# Wait for health checks
curl http://localhost:8000/health           # API
curl http://localhost:3000                   # Frontend
curl -X POST http://localhost:8000/api/v1/runs -H "X-IO-API-Key: io_master_key_2026"
```

### STAGE 4 TEST GATE (FINAL)

| # | Test | Pass Criteria |
|---|------|---------------|
| T32 | All 10 API endpoints return valid data | Schema-valid, non-empty responses |
| T33 | Numerical bounds match Step 9 Section 4 | Within documented ranges |
| T34 | RBAC enforced on /decision | 403 for viewer, 200 for analyst+ |
| T35 | Audit hash deterministic | Identical inputs → identical hash |
| T36 | Dashboard renders all panels | 8 core + 2 timeline, no blanks |
| T37 | Bilingual toggle works | EN ↔ AR, RTL layout applies |
| T38 | Pipeline < 500ms | Measured from POST response |
| T39 | Docker Compose clean start | All services healthy |
| T40 | Zero console errors in browser | No unhandled exceptions |

**Commit after Stage 4:** `"test: end-to-end validation of V1 Hormuz pipeline and dashboard"`

---

## FILES TO ARCHIVE (Stage 1 removals — preserved in git history)

These files are deleted from the working tree but remain in git history. No archive branch needed — `git log` preserves everything.

### Backend Dead Code (120 files)

```
backend/src/                           # ENTIRE TREE
├── __init__.py
├── main.py                           # Duplicate entrypoint
├── api/ (14 files)                   # Duplicate API routes
├── connectors/ (4 files)             # Unused adapters
├── core/ (3 files)                   # Duplicate config
├── db/ (4 files)                     # Duplicate DB clients
├── engines/ (38 files)               # Duplicate engines
├── graph/ (4 files)                  # Duplicate graph
├── i18n/ (2 files)                   # Duplicate labels
├── models/ (3 files)                 # V0 ingest models
├── normalization/ (2 files)          # Unused
├── orchestration/ (1 file)           # Unused stub
├── rules/ (3 files)                  # Duplicate thresholds
├── schemas/ (13 files)               # Dead V1 schemas
└── services/ (16 files)              # Duplicate services
```

### Frontend Dead Code (18 files)

```
frontend/app/                          # ENTIRE V2 PAGE TREE
├── page.tsx                          # Shadowed landing
├── layout.tsx                        # Shadowed layout
├── dashboard/page.tsx                # Shadowed dashboard
├── scenarios/page.tsx                # Dark theme
├── control-room/layout.tsx           # Shadowed
└── api/ (3 route files)              # V2 API routes

frontend/styles/globals.css            # V2 global styles
frontend/components/ui/Navbar.tsx      # V2 only
frontend/components/ui/Footer.tsx      # V2 only
frontend/components/graph/GraphPanel.tsx # V2 only

frontend/lib/api/client.ts            # V2 API client
frontend/lib/api/index.ts             # V2 re-export
frontend/lib/types.ts                 # V2 types
frontend/lib/i18n.ts                  # V2 i18n
frontend/lib/mock-data.ts             # Mock data
frontend/lib/gcc-graph.ts             # Superseded by package
frontend/lib/types/observatory.ts     # Merged into src/ in Stage 3
```

**Total archived: ~138 files**

---

## ROLLBACK / SAFEGUARD PLAN

### Pre-Execution Safeguards

| # | Safeguard | When | Command |
|---|-----------|------|---------|
| S1 | Create rollback branch | Before Stage 1 starts | `git checkout -b pre-v1-replatform && git push -u origin pre-v1-replatform` |
| S2 | Tag current state | Before Stage 1 starts | `git tag v0.9-pre-replatform` |
| S3 | Backup Docker volumes | Before credential rename (1F) | `docker-compose exec postgres pg_dumpall > backup_pre_v1.sql` |

### Per-Stage Rollback

| Stage | Rollback Trigger | Rollback Command | Data Loss |
|-------|-----------------|------------------|-----------|
| Stage 1 | Backend won't start after `src/` removal | `git checkout pre-v1-replatform -- backend/src/` | None |
| Stage 1 | Frontend won't build after V2 removal | `git checkout pre-v1-replatform -- frontend/app/ frontend/styles/ frontend/components/` | None |
| Stage 1 | Docker won't start after credential change | `git checkout pre-v1-replatform -- docker-compose.yml` + `docker-compose down -v && docker-compose up -d` | Dev DB data (acceptable) |
| Stage 2 | Pipeline wiring breaks API | `git checkout pre-v1-replatform -- backend/app/api/v1/routes/runs.py` | None (runs.py is the only changed file) |
| Stage 2 | Schema refactor breaks imports | `git checkout pre-v1-replatform -- backend/app/schemas/observatory.py` | None |
| Stage 3 | Dashboard build fails | `git stash` or `git checkout pre-v1-replatform -- frontend/src/` | Loses new components (can be re-created) |
| Stage 3 | Type merge breaks build | `git checkout pre-v1-replatform -- frontend/src/types/ frontend/lib/types/` | None |
| Full | Complete rollback to pre-replatform | `git reset --hard v0.9-pre-replatform` | All V1 work (use only as last resort) |

### Rollback Rules

1. **Never proceed to Stage N+1 until all Stage N tests pass.** This is a hard gate, not advisory.
2. **Each stage gets its own commit.** Rollback is per-stage via `git revert`, not per-file.
3. **Docker volumes are expendable in V1.** All data is recomputable from seeds. Loss of dev DB data is acceptable.
4. **Frontend rollback is safe.** All V4 components are additive — reverting to pre-V1 leaves the existing V4 pages working.
5. **Backend rollback of `runs.py` is safe.** The pipeline code in `orchestration/pipeline_v4.py` is untouched — only the wiring in `runs.py` is new.

---

## EXECUTION SUMMARY

| Stage | Files Removed | Files Edited | Files Created | Tests | Estimated Hours |
|-------|--------------|-------------|--------------|-------|-----------------|
| 1. CLEAN | ~138 | 12 | 0 | T1-T7 | 4h |
| 2. WIRE | 0 | 5 | 0 | T8-T20 | 8h |
| 3. BUILD | 1 (lib/types merge) | 6 | 14 | T21-T31 | 32h |
| 4. VERIFY | 0 | 0 | 0 | T32-T40 | 4h |
| **TOTAL** | **~139** | **23** | **14** | **40 tests** | **~48h** |

### Critical Path

```
S1 (branch) → 1A (remove src/) → 1B (entrypoints) → T1-T2
    → 1C-1D (remove V2) → T3-T4
    → 1E-1F (rename + creds) → T5-T7
    → COMMIT
    → 2A-2B (pipeline wiring) → T8-T19
    → 2C-2F (schemas + types + RBAC) → T20
    → COMMIT
    → 3A-3B (shell + data hook) → 3C (dashboard restructure)
    → 3D-3E (headline + core panels) → 3F-3G (timeline + explanation)
    → 3H-3J (i18n + RTL + RBAC guards) → 3K (type merge)
    → T21-T31
    → COMMIT
    → 4A-4E (full verification suite) → T32-T40
    → COMMIT
    → V1 SHIP
```

---

## GAP ANALYSIS — Full Codebase Audit Against Steps 1-9

Deep audit of every file in the repository against all 9 planning documents. Verified every import, every credential, every dependency. Findings organized by severity.

---

### 🔴 GAP 0: `main.py` CANNOT START — 13 Missing Module Imports (SHOWSTOPPER)

**Discovery:** `backend/app/main.py` imports 24 modules at startup. **13 of these modules do not exist on disk.** The application crashes immediately with `ModuleNotFoundError`.

**Missing modules (verified against filesystem):**

| # | Import | Expected File | Status |
|---|--------|---------------|--------|
| 1 | `app.graph.client` (GraphClient) | `backend/app/graph/client.py` | **MISSING** — only `.pyc` bytecode exists |
| 2 | `app.services.pipeline_status` (PipelineStatusTracker) | `backend/app/services/pipeline_status.py` | **MISSING** |
| 3 | `app.services.graph_ingestion` (GraphIngestionService) | `backend/app/services/graph_ingestion.py` | **MISSING** |
| 4 | `app.services.graph_query` (GraphQueryService) | `backend/app/services/graph_query.py` | **MISSING** |
| 5 | `app.services.scoring_service` (ScoringService) | `backend/app/services/scoring_service.py` | **MISSING** |
| 6 | `app.services.physics_service` (PhysicsService) | `backend/app/services/physics_service.py` | **MISSING** — exists in `src/services/` |
| 7 | `app.services.insurance_service` (InsuranceService) | `backend/app/services/insurance_service.py` | **MISSING** — exists in `src/services/` |
| 8 | `app.services.enrichment` (EnrichmentService) | `backend/app/services/enrichment.py` | **MISSING** |
| 9 | `app.api.entities` (router) | `backend/app/api/entities.py` | **MISSING** |
| 10 | `app.api.ingest` (router) | `backend/app/api/ingest.py` | **MISSING** |
| 11 | `app.api.auth` (router) | `backend/app/api/auth.py` | **MISSING** |
| 12 | `app.api.pipeline` (router) | `backend/app/api/pipeline.py` | **MISSING** |
| 13 | `app.api.conflicts` (router) | `backend/app/api/conflicts.py` | **MISSING** |

**Additionally:** `main.py` line 67 calls `GraphSchema()` which is never imported — it exists only in `src/graph/schema.py`.

**Root cause:** Incomplete migration from `backend/src/` to `backend/app/`. The `app/graph/` directory has only compiled `.pyc` files (source deleted). The `app/services/` directory has only 2 of 9 required modules (orchestrator.py, normalization.py).

**Impact:** The entire backend is non-functional. No Step 1-9 plan caught this because all previous reads targeted specific engine files (`services/financial/engine.py`, etc.) which DO exist, but the top-level `main.py` that must load first was never validated against its imports.

**Fix required (NEW Stage 0 — must execute BEFORE Stage 1):**

Two options:

**OPTION A (RECOMMENDED): Rewrite `main.py` for V1-only mode**
- Strip all 13 broken imports
- Remove lifespan handler (Neo4j + Redis + Orchestrator)
- Keep only: health router, v4 router, observatory router, CORS middleware
- V1 needs only in-memory pipeline — no Neo4j, no Redis, no PostgreSQL at runtime
- ~50 lines replacing 220 lines
- Estimated: **2 hours**

**OPTION B: Stub all 13 missing modules**
- Create 8 stub service files with no-op classes
- Create 5 stub API routers with empty endpoints
- Restore `app/graph/` source from `src/graph/` (3 files)
- All stubs just return empty/default — existing code structure preserved
- Estimated: **6 hours**

**Recommendation:** Option A. V1 doesn't use Neo4j, Redis, GraphClient, Orchestrator, or any of the missing API routers. These are all V0/V1 infrastructure that the v4 pipeline bypasses entirely.

---

### 🔴 GAP 1: `app/graph/` Has No Source Files — Only Bytecode (CRITICAL)

**Discovery:** `backend/app/graph/` contains 6 `.pyc` files but **zero `.py` source files**:
```
app/graph/__pycache__/client.cpython-310.pyc
app/graph/__pycache__/schema.cpython-310.pyc
app/graph/__pycache__/queries.cpython-310.pyc
app/graph/__pycache__/nodes.cpython-310.pyc
app/graph/__pycache__/edges.cpython-310.pyc
app/graph/__pycache__/__init__.cpython-310.pyc
```

The equivalent source exists in `backend/src/graph/` (loader.py, queries.py, schema.py).

**Fix:** Covered by GAP 0 Option A (remove import) or Option B (copy from src/).

---

### 🔴 GAP 2: 4 Competing Database Credential Sets (CRITICAL)

**Discovery:** Cross-referencing all config files reveals **4 different credential sets** for the same PostgreSQL database:

| Source | User | Password | Database |
|--------|------|----------|----------|
| `docker-compose.yml` | `deevo` | `deevo_secure` | `deevo` |
| `.env.example` (root) | `observatory_admin` | `io_pilot_2026` | `impact_observatory` |
| `settings.py` defaults | `io_admin` | `io_pilot_2026` | `impact_observatory` |
| `db/init.sql` GRANT | `observatory_admin` | — | — |

**Also:** Neo4j password has 2 variants:
- `docker-compose.yml`: `deevo_neo4j_2026`
- `.env.example` + `settings.py`: `io_graph_2026`

**Also:** `backend/.env.example` uses `DC7_` env prefix, but `settings.py` reads `IO_` prefix. These are completely incompatible — no env var from `backend/.env.example` is actually read by the application.

**Fix required (Stage 1F — expanded):** Standardize ALL to:
- User: `observatory_admin`
- Password: `io_pilot_2026`
- Database: `impact_observatory`
- Env prefix: `IO_` everywhere
- Delete `backend/.env.example` (uses dead `DC7_` prefix) or rewrite with `IO_` prefix

---

### 🟠 GAP 3: `main.py` Lifespan Requires Neo4j + Redis at Boot (HIGH)

**Discovery:** Even after fixing GAP 0, the `lifespan()` handler in `main.py` initializes Neo4j GraphClient, Redis PipelineStatusTracker, and LifecycleOrchestrator. If any service is down, the app crashes.

**Fix:** Covered by GAP 0 Option A (remove lifespan) or add try/except graceful degradation.

---

### 🟠 GAP 4: Frontend `api.ts` Missing 4 V4 Endpoint Methods (HIGH)

**Discovery:** `frontend/src/lib/api.ts` `observatory` namespace is missing:
- `businessImpact(runId)` → `GET /api/v1/runs/{id}/business-impact`
- `timeline(runId)` → `GET /api/v1/runs/{id}/timeline`
- `regulatoryTimeline(runId)` → `GET /api/v1/runs/{id}/regulatory-timeline`
- `executiveExplanation(runId)` → `GET /api/v1/runs/{id}/executive-explanation`

**Fix required (Stage 2E):** Add 4 methods to `api.observatory`.

---

### 🟠 GAP 5: Frontend `use-api.ts` Has Zero V4 Hooks (HIGH)

**Discovery:** All 14 React Query hooks in `use-api.ts` target legacy endpoints. No hooks for `api.observatory.*`.

**Fix required (Stage 3B):** Create `frontend/src/hooks/use-observatory.ts` with 10 hooks.

---

### 🟠 GAP 6: v4 Router Mount Uses Silent `try/except` (HIGH)

**Discovery:** `main.py` lines 187-191 mounts v4 router inside `try/except ImportError` with only a warning log. If the import fails, all `/api/v1/` endpoints silently vanish.

**Fix required (Stage 2):** Make v4 router import a hard requirement for V1.

---

### 🟡 GAP 7: `Makefile` Health Checks Use Wrong Credentials (MEDIUM)

**Discovery:** `Makefile` `status` target calls `pg_isready -U observatory_admin` and `psql -d impact_observatory`, but docker-compose creates user `deevo` on database `deevo`. Every `make status` call fails.

**Fix:** Resolved by GAP 2 credential standardization.

---

### 🟡 GAP 8: `db/init.sql` GRANTs to Non-Existent User (MEDIUM)

**Discovery:** `init.sql` runs `GRANT ALL TO observatory_admin` but docker-compose creates user `deevo`. The GRANTs silently fail.

**Fix:** Resolved by GAP 2 credential standardization + update init.sql CREATE ROLE if needed.

---

### 🟡 GAP 9: Frontend `.env.production` References Legacy Railway URL (MEDIUM)

**Discovery:** `frontend/.env.production` → `NEXT_PUBLIC_API_URL=https://deevo-cortex-production.up.railway.app`

**Fix required (Stage 1E):** Change to `http://localhost:8000` for V1 local.

---

### 🟡 GAP 10: `backend/.env.example` Uses Dead `DC7_` Prefix (MEDIUM)

**Discovery:** `backend/.env.example` defines vars like `DC7_APP_NAME=DecisionCore Intelligence`, `DC7_ENVIRONMENT=development`. But `settings.py` reads `IO_*` prefix. This file is completely useless and misleading.

**Fix required (Stage 1E):** Either delete or rewrite with `IO_` prefix and correct product name.

---

### 🔵 GAP 11: CI Uses Python 3.11 + Dead `DC7_` Env Vars (LOW)

**Discovery:** `.github/workflows/ci.yml` uses `python-version: "3.11"` and `DC7_POSTGRES_HOST` env vars.

**Fix required (Stage 4):** Update to 3.12 and `IO_*` prefix.

---

### 🔵 GAP 12: No `.env.local.example` for Frontend Dev Keys (LOW)

**Discovery:** Frontend devs won't know which API keys to use. Backend's `core/security.py` has 5 dev keys but no frontend-side documentation.

**Fix required (Stage 2):** Create template with correct key values.

---

### GAP IMPACT ON EXECUTION BLUEPRINT

**GAP 0 forces a new Stage 0 before anything else.** The backend cannot start, which means Stage 1 test T1 (`uvicorn app.main:app`) will fail immediately. The execution sequence must become:

```
Stage 0: FIX main.py (2h)  ← NEW, prerequisite for everything
Stage 1: CLEAN (5h)
Stage 2: WIRE (10h)
Stage 3: BUILD (34h)
Stage 4: VERIFY (4h)
```

---

## UPDATED EXECUTION SUMMARY (with all gaps)

| Stage | Action | Files Removed | Files Edited | Files Created | Tests | Hours |
|-------|--------|--------------|-------------|--------------|-------|-------|
| **0. FIX** | Rewrite main.py for V1-only mode | 0 | 1 | 0 | T0 (server starts) | 2h |
| **1. CLEAN** | Remove dead code, align creds | ~138 | 14 | 0 | T1-T7 | 5h |
| **2. WIRE** | Pipeline → API, types, RBAC | 0 | 8 | 1 | T8-T20 | 10h |
| **3. BUILD** | Dashboard shell + all panels | 1 | 7 | 16 | T21-T31 | 34h |
| **4. VERIFY** | E2E tests, CI fix | 0 | 1 | 0 | T32-T40 | 4h |
| **TOTAL** | | **~139** | **31** | **17** | **41 tests** | **~55h** |

### STAGE 0: FIX (New — Prerequisite for Everything)

**Goal:** Make `backend/app/main.py` bootable by removing 13 broken imports.

**Action:** Rewrite `main.py` to V1-minimal mode:
1. Remove all 7 missing service imports (pipeline_status, graph_ingestion, graph_query, scoring_service, physics_service, insurance_service, enrichment)
2. Remove all 5 missing API router imports (entities, ingest, auth, pipeline, conflicts)
3. Remove `app.graph.client` import (no source files exist)
4. Remove `GraphSchema()` reference (never imported)
5. Replace `lifespan()` handler with no-op or lightweight version (no Neo4j, no Redis, no Orchestrator)
6. Keep: health router, scenarios router, graph router, incidents router, insurance router, decision router, scores router, observatory router, v4 router
7. Keep: CORS middleware, Settings, exception handler
8. Make v4 router import a hard requirement (remove try/except)

**Test T0:** `cd backend && PYTHONPATH=. python -c "from app.main import app; print('OK')"` → must print OK

**Also fix in Stage 0:** Delete `backend/.env.example` (dead `DC7_` prefix) or rewrite with `IO_` prefix.

---

## Decision Gate

This blueprint is **LOCKED**. It is the final plan before code execution.

**Pre-conditions that must be true:**
1. `git status` is clean (no uncommitted changes)
2. `pre-v1-replatform` branch and `v0.9-pre-replatform` tag created
3. Docker volumes backed up (if any dev data worth preserving)

**Execution rule:** Complete each Stage fully before starting the next. No partial stages. No skipping test gates.

Awaiting your command to begin execution — starting with Stage 1A.
