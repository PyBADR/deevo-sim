# FINAL EXECUTION BLUEPRINT — Impact Observatory | مرصد الأثر

**Date:** 2026-04-02
**Step:** 10 — Consolidated Execution Plan (LOCKED)
**Synthesizes:** Steps 1–9 + Stage 0–4 execution results + gap analysis
**Status:** V1 in-memory mode VERIFIED (28/28 tests). This blueprint defines the REMAINING work to reach production V2.

---

## Current State (Post V1 Execution)

### What Was Done (Stages 0–4)

| Stage | Result | Key Artifacts |
|-------|--------|---------------|
| Stage 0: FIX | main.py rewritten to V1-minimal (130 lines), 13 broken imports removed, lifespan stripped | `backend/app/main.py`, `backend/app/api/health.py` |
| Stage 1: CLEAN | `backend/src/` deleted (167 files), entrypoints aligned to `app.main:app`, credentials standardized to IO_ prefix | `Makefile`, `Procfile`, `Dockerfile.backend`, `docker-compose.yml`, `db/init.sql`, `.env.example`, `.github/workflows/ci.yml` |
| Stage 2: WIRE | `run_v4_pipeline()` wired into POST /runs, serializer built, all 10 GET endpoints return Hormuz data, RBAC enforced | `backend/app/api/v1/routes/runs.py` |
| Stage 3: BUILD | Frontend hooks rewritten (12 v4 hooks), api.ts aligned, page.tsx fetches all sections in parallel, RBAC mirrored in `rbac.ts`, 5 legacy pages stubbed | `frontend/src/lib/api.ts`, `frontend/src/hooks/use-api.ts`, `frontend/src/lib/rbac.ts`, `frontend/src/app/page.tsx` |
| Stage 4: VERIFY | 28/28 pytest PASS (0.45s), ruff clean on V4 paths, frontend builds clean (14kB main + 116kB first load) | `backend/tests/test_v4_e2e.py` |

### What Remains Uncommitted

**215 working-tree changes** (154 deletions, 33 modifications, 28 new files). No commits made, no tags set, no rollback branch created. All work exists only in the working tree.

---

## 1. FILES TO CHANGE FIRST (Foundation Layer)

Priority: These must be committed before any further development. They represent the V1 foundation and all current working-tree changes.

### 1A. Backend Core (Modified — commit as-is)

| # | File | Change Type | What Changed | Source Plan |
|---|------|-------------|-------------|-------------|
| 1 | `backend/app/main.py` | MODIFIED | Rewritten to V1-minimal: 13 broken imports removed, lifespan stripped, v4 router as hard import, legacy routers wrapped in try/except | Step 10 GAP 0 |
| 2 | `backend/app/api/health.py` | MODIFIED | Removed `app.api.auth` dependency, /version returns dict not VersionResponse | Step 10 GAP 0 |
| 3 | `backend/app/services/financial/engine.py` | MODIFIED | V4 pipeline compatibility fixes | Step 6 §2.1 |
| 4 | `backend/app/services/banking/engine.py` | MODIFIED | V4 pipeline compatibility fixes | Step 6 §2.2 |
| 5 | `backend/app/services/insurance/engine.py` | MODIFIED | V4 pipeline compatibility fixes | Step 6 §2.3 |
| 6 | `backend/app/services/fintech/engine.py` | MODIFIED | V4 pipeline compatibility fixes | Step 6 §2.4 |
| 7 | `backend/app/services/decision/engine.py` | MODIFIED | V4 pipeline compatibility fixes | Step 6 §2.6 |
| 8 | `backend/app/services/explainability/engine.py` | MODIFIED | V4 pipeline compatibility fixes | Step 6 §2.7 |
| 9 | `backend/app/services/explainability/__init__.py` | MODIFIED | Import path fixes | Step 6 |

### 1B. Backend New Files (Untracked — stage and commit)

| # | File | What It Is | Source Plan |
|---|------|-----------|-------------|
| 10 | `backend/app/api/v1/` (entire directory) | V4 canonical API: runs.py, scenarios.py, schemas/, __init__.py | Step 9 §3.1 |
| 11 | `backend/app/core/` | rbac.py (5 roles, 19 permissions), security.py (auth middleware), errors.py (typed error classes), settings.py (IO_ config) | Step 8, Step 10 GAP 2 |
| 12 | `backend/app/domain/` | 16 Pydantic v2 domain models (canonical source of truth) | Step 5 §2 |
| 13 | `backend/app/orchestration/pipeline_v4.py` | 9-stage V4 pipeline orchestrator | Step 6 §1 |
| 14 | `backend/app/seeds/` | hormuz_v1.py (flagship scenario), scenario_seeds.py | Step 9 §1 |
| 15 | `backend/app/services/business_impact/` | BusinessImpactSummary engine (§16) | Step 7 §2 |
| 16 | `backend/app/services/regulatory/` | RegulatoryState engine (§7.7) | Step 6 §2.5 |
| 17 | `backend/app/services/time_engine/` | Timeline simulation engine (§17) | Step 7 §3 |
| 18 | `backend/tests/test_v4_e2e.py` | 28 E2E tests covering all endpoints, RBAC, envelope format | Step 9 §6 |

### 1C. Infrastructure (Modified — commit as-is)

| # | File | What Changed | Source Plan |
|---|------|-------------|-------------|
| 19 | `Makefile` | `src.main:app` → `app.main:app`, `observatory_admin` → `io_admin` | Step 2 Category G |
| 20 | `Procfile` | `src.main:app` → `app.main:app` | Step 2 Category G |
| 21 | `Dockerfile.backend` | CMD from `src.main:app` → `app.main:app` | Step 2 Category G |
| 22 | `docker-compose.yml` | Credentials aligned: deevo → io_admin, IO_ env prefix, io_graph_2026 | Step 2 Category D, Step 10 GAP 2 |
| 23 | `db/init.sql` | GRANT `observatory_admin` → `io_admin` | Step 10 GAP 8 |
| 24 | `backend/.env.example` | Rewritten from DC7_ to IO_ prefix | Step 10 GAP 10 |
| 25 | `.github/workflows/ci.yml` | DC7_ → IO_ env vars | Step 10 GAP 11 |

### 1D. Frontend (Modified + New)

| # | File | Change Type | What Changed | Source Plan |
|---|------|-------------|-------------|-------------|
| 26 | `frontend/src/app/page.tsx` | MODIFIED | runScenario rewritten: POST /runs → parallel GET 10 endpoints → compose RunResult | Step 3 §6, Step 9 §3.3 |
| 27 | `frontend/src/lib/api.ts` | MODIFIED | observatory namespace rewritten: legacy methods removed, 4 V4 methods added, IO API key header | Step 10 GAP 4 |
| 28 | `frontend/src/hooks/use-api.ts` | MODIFIED | 14 legacy hooks removed, 12 V4 hooks added | Step 10 GAP 5 |
| 29 | `frontend/src/lib/rbac.ts` | NEW | 5 roles, 19 permissions, mirrors backend exactly | Step 8 §2 |
| 30 | `frontend/theme/globals.css` | NEW | IO design system base styles with CSS variables | Step 3 §2 |
| 31 | `frontend/src/app/globals.css` | MODIFIED | Imports from theme/globals.css | Step 3 §2 |
| 32 | `frontend/tailwind.config.ts` | MODIFIED | Content paths fixed: `./src/**/*.{js,ts,jsx,tsx,mdx}` | Step 1 CONFLICT-4 |
| 33 | 5 stubbed pages | MODIFIED | control-room, graph-explorer, scenario-lab, dashboard, entity/[id] → "Coming in V2" | Step 3 §5 |

### 1E. Deleted Files (154 files — in working tree, not committed)

| # | Path | Count | Reason | Source Plan |
|---|------|-------|--------|-------------|
| 34 | `backend/src/` (entire tree) | ~167 files | Duplicate backend: dual entrypoint, duplicate engines, dead schemas | Step 1 §4 REMOVE |

### Tests to Run After Committing Group 1

```bash
# T1: Backend boots
cd backend && PYTHONPATH=. python -c "from app.main import app; print('Boot OK, routes:', len(app.routes))"

# T2: No src imports
grep -r "from src\." backend/app/ | wc -l  # must be 0

# T3: Full E2E suite
cd backend && PYTHONPATH=. python -m pytest tests/test_v4_e2e.py -v --tb=short  # 28/28

# T4: Ruff clean on V4 paths
cd backend && python -m ruff check app/api/v1/ app/domain/ --exit-zero

# T5: Frontend builds
cd frontend && npm run build  # Exit 0, no errors
```

---

## 2. FILES TO CHANGE SECOND (V2 Feature Layer)

Priority: After V1 foundation is committed. These are the remaining items from Steps 1–9 that were planned but deferred from the V1 execution sprint.

### 2A. Dead Code Removal — V2 Frontend + Legacy Seeds + Legacy APIs

| # | Path | Action | Source Plan | Blocked By |
|---|------|--------|-------------|------------|
| 1 | `frontend/app/` (entire V2 page tree) | DELETE | Step 1 §4, Step 3 §1 | Nothing — can be removed immediately. V4 `src/app/` is canonical. Pre-check: `grep -r "from.*app/" frontend/src/` must return 0 cross-imports. |
| 2 | `frontend/styles/globals.css` | DELETE | Step 1 CONFLICT-4 | Nothing — superseded by `src/theme/globals.css` |
| 3 | `frontend/components/ui/Navbar.tsx` | DELETE | Step 3 §3 | Verify: `grep -r "Navbar" frontend/src/` = 0 |
| 4 | `frontend/components/ui/Footer.tsx` | DELETE | Step 3 §3 | Verify: `grep -r "Footer" frontend/src/` = 0 |
| 5 | `frontend/components/graph/GraphPanel.tsx` | DELETE | Step 3 §3 | Verify: `grep -r "GraphPanel" frontend/src/` = 0 |
| 6 | `frontend/lib/api/` | DELETE | Step 5 §3 | Verify: `grep -r "lib/api/client" frontend/src/` = 0 |
| 7 | `frontend/lib/types.ts` | DELETE | Step 5 §3 | Verify: `grep -r "lib/types" frontend/src/` = 0 |
| 8 | `frontend/lib/i18n.ts` | DELETE | Step 5 §3 | Verify: `grep -r "lib/i18n" frontend/src/` = 0 |
| 9 | `frontend/lib/mock-data.ts` | DELETE | Step 5 §3 | Verify: `grep -r "mock-data" frontend/src/` = 0 |
| 10 | `frontend/lib/gcc-graph.ts` | DELETE | Step 5 §3 | Verify: `grep -r "gcc-graph" frontend/src/` = 0 |
| 11 | `frontend/lib/types/observatory.ts` | MERGE then DELETE | Step 5 §4 | Must merge unique V4 types into `src/types/observatory.ts` first |
| 12 | `backend/seeds/airports.py` | DELETE | Step 1 §4 | Not IO scope (flight tracking) |
| 13 | `backend/seeds/flights.py` | DELETE | Step 1 §4 | Not IO scope (flight tracking) |
| 14 | `backend/seeds/vessels.py` | DELETE | Step 1 §4 | Not IO scope (maritime tracking) |
| 15 | `backend/seeds/ports.py` | DELETE | Step 1 §4 | Not IO scope (maritime tracking) |
| 16 | `backend/seeds/corridors.py` | DELETE | Step 1 §4 | Low priority |
| 17 | `backend/seeds/loader.py` | DELETE | Step 1 §4 | Legacy seed loader |
| 18 | `backend/app/api/scores.py` | DELETE | Step 1 §4 | Legacy scoring — not in V4 spec |
| 19 | `backend/app/api/incidents.py` | DELETE | Step 1 §4 | Legacy incidents — not in V4 spec |
| 20 | `backend/app/api/insurance.py` | DELETE | Step 1 §4 | Legacy insurance — replaced by V4 services |
| 21 | `backend/app/api/decision.py` | DELETE | Step 1 §4 | Legacy decision — replaced by V4 services |

### 2B. Frontend Dashboard Build-Out (New Components)

| # | File to Create | Description | Source Plan | Depends On |
|---|---------------|-------------|-------------|------------|
| 22 | `src/components/shell/AppShell.tsx` | Persistent top nav + sidebar | Step 4 §1 | — |
| 23 | `src/components/shell/TopNav.tsx` | Extracted navigation bar | Step 4 §1 | — |
| 24 | `src/components/shell/TabBar.tsx` | 9 tabs: Overview, Banking, Insurance, Fintech, Decisions, Timeline, Graph, Map, Regulatory | Step 4 §1 | — |
| 25 | `src/components/shell/DashboardHeader.tsx` | Scenario label + severity + language toggle + mode toggle | Step 4 §1 | — |
| 26 | `src/components/dashboard/HeadlineSummary.tsx` | 6 KPI cards in horizontal row | Step 4 §2, Step 9 F3 | KPICard.tsx (exists) |
| 27 | `src/components/dashboard/FinancialOverview.tsx` | Wraps FinancialImpactPanel with 12 per-entity rows | Step 4 §2, Step 9 F4 | FinancialImpactPanel.tsx (exists) |
| 28 | `src/components/dashboard/StressOverview.tsx` | 3× StressGauge (banking + insurance + fintech) | Step 4 §2, Step 9 F5-F7 | StressGauge.tsx (exists) |
| 29 | `src/components/dashboard/DecisionOverview.tsx` | 3× DecisionActionCard ranked | Step 4 §2, Step 9 F8 | DecisionActionCard.tsx (exists) |
| 30 | `src/components/timeline/BusinessImpactTimeline.tsx` | Recharts AreaChart — dual Y-axis, peak annotations | Step 4 §2, Step 7 §5, Step 9 F10 | Recharts (installed) |
| 31 | `src/components/timeline/RegulatoryBreachTimeline.tsx` | Vertical timeline — color-coded dots, entity/threshold/value | Step 4 §2, Step 7 §5, Step 9 F11 | — |
| 32 | `src/components/panels/ExplanationPanel.tsx` | Summary + equations + drivers + stage traces + action explanations | Step 4 §2, Step 9 F9 | — |
| 33 | `src/components/guards/PermissionGate.tsx` | Wraps children, checks `hasPermission(role, permission)` | Step 8 §3, Step 9 F14 | rbac.ts (exists) |

### 2C. Frontend Integration (Edits to Existing Files)

| # | File to Edit | Change | Source Plan |
|---|-------------|--------|-------------|
| 34 | `src/app/dashboard/page.tsx` | Rewrite from stub to DashboardShell: tab state, RunResult routing to child panels | Step 4 §1 |
| 35 | `src/app/layout.tsx` | Wrap children in AppShell, dynamic `dir` attribute from Zustand language state | Step 3 §2, Step 9 F13 |
| 36 | `src/store/app-store.ts` | Add `userRole`, `tenantId`, `principalId` fields | Step 8 §6 |
| 37 | `src/types/observatory.ts` | Add V4 extension fields: `business_impact?`, `loss_trajectory?`, `timeline?`, `regulatory_breaches?` | Step 5 §3 |
| 38 | `src/types/index.ts` | Remove 4 legacy duplicates: `Scenario`, `ScenarioResult`, `DecisionAction`, `DecisionOutput` | Step 5 §5 |
| 39 | `src/i18n/en.json` + `src/i18n/ar.json` | Add all tab labels, KPI labels, panel titles, decision labels, stress classifications from Step 4 §4 | Step 4 §4 |

### 2D. Backend Consolidation (Engine Dedup)

| # | Action | Source → Target | Source Plan |
|---|--------|----------------|-------------|
| 40 | Consolidate scenario engine | 5 files across 3 dirs → `services/scenario/engine.py` + `services/scenario/templates.py` | Step 6 §3.1 |
| 41 | Consolidate physics engine | `intelligence/physics_core/` (7 files) + `intelligence/physics/` (2 files) → `services/physics/engine.py` as facade, keep `intelligence/physics_core/` as pure lib | Step 6 §3.2 |
| 42 | Consolidate propagation engine | `intelligence/engines/propagation_engine.py` + 2 math helpers → `services/propagation/engine.py` | Step 6 §3.3 |
| 43 | Build entity_graph_service | Extract graph-build logic from scenarios/engine.py → `services/graph/engine.py` | Step 6 §2.15 |
| 44 | Refactor schemas/observatory.py | Remove 11 duplicate model defs, import from `app.domain.models`, keep thin API input schemas and LABELS | Step 5 §3.2 |

### 2E. Cosmetic / Branding

| # | File | Change | Source Plan |
|---|------|--------|-------------|
| 45 | `LICENSE` | "Deevo Analytics" → "Impact Observatory" (2 occurrences) | Step 2 Category A |
| 46 | `packages/@deevo/gcc-knowledge-graph/package.json` | `"author": "Deevo Analytics"` → `"author": "Impact Observatory"` | Step 2 Category A |
| 47 | `frontend/.env.production` | Railway URL → `https://api.observatory.deevo.ai` | Step 2 Category C |

### Tests to Run After Each Sub-Group in Group 2

```bash
# After 2A (dead code removal):
cd backend && PYTHONPATH=. python -c "from app.main import app; print('Boot OK')"
cd frontend && npm run build  # verify no broken imports

# After 2B-2C (dashboard build-out):
cd frontend && npx tsc --noEmit  # type-check all new components
cd frontend && npm run build  # production build
# Visual: open http://localhost:3000/dashboard — all 8 core panels + 2 timeline panels

# After 2D (engine consolidation):
cd backend && PYTHONPATH=. python -m pytest tests/test_v4_e2e.py -v --tb=short  # 28/28 must still pass
cd backend && python -m ruff check app/ --exit-zero  # lint all code

# After 2E (branding):
grep -r "Deevo Analytics" . --include="*.py" --include="*.ts" --include="*.json" --include="*.md" | grep -v node_modules | grep -v .git  # must return 0
```

---

## 3. FILES TO ARCHIVE LATER (V3+ Scope)

These files remain in the repository for now. They are not blocking V1 or V2, but should be evaluated for removal or migration in a future sprint.

### 3A. Backend — Evaluate for V3

| # | Path | File Count | Why It Stays | V3 Decision Point |
|---|------|-----------|-------------|-------------------|
| 1 | `backend/app/intelligence/engines/scenario_engines.py` | 1 (~875L) | 17 GCC scenario templates — high business value | Extract to `services/scenario/templates.py` OR move to knowledge graph package |
| 2 | `backend/app/intelligence/engines/propagation_engine.py` | 1 (~700L) | Full BFS/PageRank propagation — needed for V2 (replacing 0.65 stub) | Migrate to `services/propagation/engine.py` when implementing real graph traversal |
| 3 | `backend/app/intelligence/engines/decision_engine.py` | 1 (~900L) | V2 decision engine with richer HITL flow | Evaluate overlap with `services/decision/engine.py` — may merge or keep both |
| 4 | `backend/app/intelligence/engines/monte_carlo.py` | 1 | Monte Carlo simulation — V3 feature (uncertainty bands) | Keep until V3 scope lock |
| 5 | `backend/app/intelligence/physics_core/` | 7 files | Pure physics computations — used by pipeline when physics stage is active | Keep as library; facade in `services/physics/engine.py` will call these |
| 6 | `backend/app/intelligence/math_core/` | 10 files | Pure math: calibration, confidence, disruption, exposure, propagation, proximity, risk, scoring | Keep as library — these are pure functions consumed by engines |
| 7 | `backend/app/intelligence/scenario_engine/` | 5 files | V1-V2 scenario orchestration (mock runner, baseline, inject, delta, explanation) | Consolidate into services in 2D.40, then archive |
| 8 | `backend/app/intelligence/insurance_intelligence/` | 4 files | Claims surge, portfolio exposure, severity projection, underwriting watch | Evaluate overlap with `services/insurance/engine.py` |
| 9 | `backend/app/scenarios/` | 3 files | V1 scenario engine, runner, templates | Consolidate in 2D.40, then archive |
| 10 | `backend/app/db/neo4j.py` | 1 | Neo4j client — V2 will need graph DB | Keep until V2 graph integration decision |
| 11 | `backend/app/graph/__pycache__/` | 6 .pyc files | Orphaned bytecode — no source | Delete (safe, no runtime impact) |
| 12 | `backend/app/connectors/` | ~1 file (osm) | OSM connector — low value | Delete or archive |
| 13 | `backend/seeds/actors.py`, `events.py`, `scenario_seeds.py` | 3 | GCC scenario seeds — used by `scenario_engines.py` | Keep while scenario_engines.py stays |

### 3B. Frontend — Evaluate for V3

| # | Path | Why It Stays | V3 Decision Point |
|---|------|-------------|-------------------|
| 14 | `frontend/lib/server/` (rbac, auth, audit, execution, store, trace) | Active server-side logic used by `frontend/app/` API routes | After 2A deletion of `frontend/app/`, verify if `lib/server/` is still imported anywhere. If not, archive. |
| 15 | `frontend/lib/simulation-engine.ts` | Client-side simulation logic — may be reused for V2 interactive mode | Evaluate for V2 scenario builder |
| 16 | `frontend/lib/decision-engine.ts` | Client-side decision logic | Evaluate for V2 scenario builder |
| 17 | `frontend/middleware.ts` | Route-level middleware | Verify routing rules still apply post-V2 |
| 18 | `packages/@deevo/gcc-knowledge-graph/` | 76 nodes, 191 edges, 17 scenarios — high value | Keep as-is. Scope rename to `@io/` is optional cosmetic (Step 2 Category E) |
| 19 | `packages/@deevo/gcc-constants/` | GCC sector weights + thresholds | Keep as-is |

### 3C. Infrastructure — Evaluate for V3

| # | Path | V3 Decision Point |
|---|------|-------------------|
| 20 | `nginx/nginx.conf` | Add frontend service routing when deploying V2 multi-service |
| 21 | `railway.toml` | Update for production V2 deployment |
| 22 | `vercel.json` | Update for production V2 deployment |
| 23 | `config/project.yml` | Validate contents match V4 spec |

---

## 4. TESTS TO RUN AFTER EACH STAGE

### Stage Gate Protocol

**Rule: Never proceed to Group N+1 until all Group N tests pass.** Hard gate, not advisory.

### Group 1 Tests (Foundation Commit)

| ID | Test | Command | Pass Criteria | Category |
|----|------|---------|---------------|----------|
| T1 | Backend boots | `cd backend && PYTHONPATH=. python -c "from app.main import app; print(len(app.routes))"` | Prints ≥25, no ImportError | Boot |
| T2 | No src imports | `grep -r "from src\." backend/app/ \| wc -l` | 0 | Hygiene |
| T3 | Health endpoint | `PYTHONPATH=. python -c "from httpx import AsyncClient; ..."` or via test suite | 200, `status=healthy` | API |
| T4 | Pipeline executes | `pytest tests/test_v4_e2e.py::TestPipeline -v` | 3/3 PASS | Pipeline |
| T5 | All 10 GET endpoints | `pytest tests/test_v4_e2e.py -v` | 28/28 PASS | API |
| T6 | RBAC enforced | `pytest tests/test_v4_e2e.py::TestRBAC -v` | 4/4 PASS (viewer blocked from /decision) | Security |
| T7 | Envelope contract | `pytest tests/test_v4_e2e.py::TestEnvelope -v` | trace_id, generated_at, data, warnings | Contract |
| T8 | Ruff V4 paths | `python -m ruff check app/api/v1/ app/domain/ --exit-zero` | 0 errors | Lint |
| T9 | Frontend builds | `cd frontend && npm run build` | Exit 0 | Build |
| T10 | Audit hash present | `pytest tests/test_v4_e2e.py::TestStatus::test_status_has_audit_hash -v` | 64 hex chars | Audit |

### Group 2A Tests (Dead Code Removal)

| ID | Test | Command | Pass Criteria |
|----|------|---------|---------------|
| T11 | No V2 pages | `ls frontend/app/*.tsx 2>/dev/null \| wc -l` | 0 |
| T12 | No V2 styles | `ls frontend/styles/ 2>/dev/null` | empty or not found |
| T13 | No legacy seeds | `ls backend/seeds/airports.py 2>/dev/null` | not found |
| T14 | No legacy APIs | `ls backend/app/api/scores.py 2>/dev/null` | not found |
| T15 | Backend still boots | Same as T1 | ≥25 routes |
| T16 | Frontend still builds | Same as T9 | Exit 0 |
| T17 | E2E still passes | Same as T5 | 28/28 PASS |

### Group 2B–2C Tests (Dashboard Build-Out)

| ID | Test | Command | Pass Criteria |
|----|------|---------|---------------|
| T18 | Types check | `cd frontend && npx tsc --noEmit` | Exit 0 |
| T19 | Build clean | `cd frontend && npm run build` | Exit 0 |
| T20 | Dashboard loads | Open `http://localhost:3000/dashboard` | No blank panels |
| T21 | 6 KPIs render | Visual: HeadlineSummary bar | All cards show values |
| T22 | Financial panel | Visual: 12 entity rows | Loss values > 0 |
| T23 | Stress gauges | Visual: 3 arcs | Banking/Insurance/Fintech show breach |
| T24 | Decision cards | Visual: 3 cards | Ranked 1-2-3 |
| T25 | Timeline chart | Visual: BusinessImpactTimeline | 14 data points |
| T26 | Breach timeline | Visual: RegulatoryBreachTimeline | 6+ events |
| T27 | AR toggle | Click language toggle | Labels switch, RTL |
| T28 | Viewer block | Set viewer key | Decision tab hidden |

### Group 2D Tests (Engine Consolidation)

| ID | Test | Command | Pass Criteria |
|----|------|---------|---------------|
| T29 | E2E regression | `pytest tests/test_v4_e2e.py -v` | 28/28 PASS |
| T30 | Full ruff | `python -m ruff check app/ --exit-zero` | <20 warnings (down from 95) |
| T31 | Import graph clean | `grep -r "from.*intelligence.engines.scenario_engines" app/services/ \| wc -l` | Count matches expected |

### Group 2E Tests (Branding)

| ID | Test | Command | Pass Criteria |
|----|------|---------|---------------|
| T32 | No "Deevo Analytics" | `grep -rn "Deevo Analytics" --include="*.py" --include="*.ts" --include="*.json" . \| grep -v node_modules \| grep -v .git` | 0 results |
| T33 | Smoke test | `pytest tests/test_v4_e2e.py::TestBoot -v` | 4/4 PASS |

---

## 5. ROLLBACK / SAFEGUARD PLAN

### Pre-Execution Safeguards (NOT YET DONE — must execute before first commit)

| # | Safeguard | Command | When |
|---|-----------|---------|------|
| S1 | Create rollback branch | `git checkout -b pre-v1-replatform && git push -u origin pre-v1-replatform && git checkout main` | Before Group 1 commit |
| S2 | Tag current state | `git tag v0.9-pre-replatform` | Before Group 1 commit |
| S3 | Backup Docker volumes | `docker-compose exec postgres pg_dumpall > backup_pre_v1.sql` (if DB has data) | Before credential changes |

### Per-Group Rollback Procedures

| Group | Rollback Trigger | Rollback Command | Data Loss |
|-------|-----------------|------------------|-----------|
| Group 1 | Backend won't start after commit | `git revert HEAD` (single commit) | Undoes all V1 work — last resort |
| Group 1 | Specific file breaks | `git checkout v0.9-pre-replatform -- <file>` | Targeted file recovery |
| Group 2A | Frontend breaks after V2 removal | `git checkout pre-v1-replatform -- frontend/app/ frontend/styles/ frontend/components/` | None |
| Group 2A | Backend breaks after seed removal | `git checkout pre-v1-replatform -- backend/seeds/` | None |
| Group 2B-2C | Dashboard build fails | `git stash` then debug | Stashed work recoverable |
| Group 2D | Engine consolidation breaks pipeline | `git checkout HEAD~1 -- backend/app/services/ backend/app/intelligence/` | Undoes consolidation only |
| Group 2E | Branding breaks something | `git revert HEAD` | Trivial — cosmetic only |
| Full | Complete rollback | `git reset --hard v0.9-pre-replatform` | ALL V1+V2 work. Last resort ONLY. |

### Rollback Rules

1. **Each group gets its own commit.** Rollback is per-group via `git revert`, never per-file.
2. **Docker volumes are expendable.** All data recomputable from seeds. Loss of dev DB is acceptable.
3. **Frontend rollback is always safe.** V4 components are additive.
4. **Backend rollback of `runs.py` is safe.** Pipeline code in `pipeline_v4.py` is untouched.
5. **Never force-push to main.** Use `git revert` for public history preservation.
6. **Test gates are hard gates.** If Group N tests fail, fix before proceeding. No exceptions.

### Operational Risk Register

| Risk | Probability | Impact | Mitigation | Owner |
|------|-------------|--------|------------|-------|
| Propagation stub (0.65) produces unrealistic cascading | Medium | Medium | Document as known limitation; replace in V2 with BFS/PageRank (Step 6 §3.3) | Backend |
| In-memory store loses data on restart | High | Low (V1) | Acceptable for demo; PostgreSQL persistence in V2 | Backend |
| Financial loss values in $B range unrealistic to clients | Medium | High | Add disclaimer: "sector-level aggregate"; recalibrate exposure in V2 | Product |
| Insurance solvency goes negative | High | Medium | Clamp to 0.0 minimum in engine (done); note in explanation | Backend |
| CORS blocks frontend → backend in dev | Medium | Medium | CORS middleware already in main.py; verify origins list includes localhost:3000 | DevOps |
| Docker service ordering (backend before postgres) | Low | Medium | `depends_on` + healthcheck already in docker-compose.yml | DevOps |
| 95 ruff warnings in legacy routers | Low | Low | All in try/except legacy code; clean in Group 2D consolidation | Backend |
| No git tag/branch safety net exists | High | Critical | **MUST create S1+S2 before any commit** | All |

---

## EXECUTION SEQUENCE SUMMARY

```
┌──────────────────────────────────────────────────────────┐
│  S1+S2: CREATE ROLLBACK BRANCH + TAG                     │
│  (git checkout -b pre-v1-replatform; git tag v0.9-...)   │
└─────────────────────────┬────────────────────────────────┘
                          ▼
┌──────────────────────────────────────────────────────────┐
│  GROUP 1: FOUNDATION COMMIT                              │
│  34 items: core + infra + frontend + 154 deletions       │
│  Tests: T1–T10                                           │
│  Commit: "feat: Impact Observatory V1 — pipeline,        │
│           API, RBAC, 28/28 E2E tests"                    │
└─────────────────────────┬────────────────────────────────┘
                          ▼
┌──────────────────────────────────────────────────────────┐
│  GROUP 2A: DEAD CODE REMOVAL                             │
│  21 items: V2 frontend, legacy seeds, legacy APIs        │
│  Tests: T11–T17                                          │
│  Commit: "chore: remove V2 frontend, legacy seeds,       │
│           and legacy API endpoints"                       │
└─────────────────────────┬────────────────────────────────┘
                          ▼
┌──────────────────────────────────────────────────────────┐
│  GROUP 2B+2C: DASHBOARD BUILD-OUT                        │
│  18 items: 12 new components, 6 file edits               │
│  Tests: T18–T28                                          │
│  Commit: "feat: executive dashboard with 9 tabs,         │
│           timeline panels, RBAC guards"                   │
└─────────────────────────┬────────────────────────────────┘
                          ▼
┌──────────────────────────────────────────────────────────┐
│  GROUP 2D: ENGINE CONSOLIDATION                          │
│  5 items: scenario, physics, propagation, graph, schemas │
│  Tests: T29–T31                                          │
│  Commit: "refactor: consolidate engines into services/,  │
│           single module per pipeline stage"               │
└─────────────────────────┬────────────────────────────────┘
                          ▼
┌──────────────────────────────────────────────────────────┐
│  GROUP 2E: BRANDING CLEANUP                              │
│  3 items: LICENSE, package.json author, .env.production  │
│  Tests: T32–T33                                          │
│  Commit: "chore: complete Deevo Analytics →              │
│           Impact Observatory branding"                    │
└─────────────────────────┬────────────────────────────────┘
                          ▼
┌──────────────────────────────────────────────────────────┐
│  V2 SHIP                                                 │
│  Decision Gate: all T1–T33 pass,                         │
│  dashboard renders 8+2 panels with real data,            │
│  single import graph, ruff < 20 warnings                 │
└──────────────────────────────────────────────────────────┘
```

### Estimated Effort

| Group | Items | New Files | Edits | Deletions | Estimated Hours |
|-------|-------|-----------|-------|-----------|-----------------|
| S1+S2 | 2 | 0 | 0 | 0 | 0.5h |
| Group 1 | 34 | 18 | 15 | 154 | **0h** (already done, needs commit only) |
| Group 2A | 21 | 0 | 0 | 21 | 2h |
| Group 2B+2C | 18 | 12 | 6 | 0 | 36h |
| Group 2D | 5 | 4 | 3 | 0 | 12h |
| Group 2E | 3 | 0 | 3 | 0 | 1h |
| **TOTAL** | **83** | **34** | **27** | **175** | **~51.5h** |

**Critical path:** S1/S2 → Group 1 (commit) → Group 2A (clean) → Group 2B+2C (dashboard) → Group 2D (consolidate) → Group 2E (brand) → V2 SHIP

---

## DECISION GATE

This blueprint is **LOCKED**. It is the final execution plan for the deevo-sim → Impact Observatory replatforming.

**What must be true before V2 is "done":**

1. All 33 test gates pass (T1–T33)
2. Dashboard renders all 8 core panels + 2 timeline panels with real Hormuz data
3. All 10 API endpoints return schema-valid, non-empty responses
4. Viewer role is blocked from `/decision` (403) in both backend and frontend
5. Pipeline completes in < 500ms
6. SHA-256 audit hash present on every run, deterministic for identical inputs
7. No "Deevo Analytics" string anywhere in user-facing code
8. Ruff produces < 20 warnings across entire `app/` directory
9. `git log` shows clean per-group commits with no force pushes
10. `pre-v1-replatform` branch and `v0.9-pre-replatform` tag exist as rollback points

**What is explicitly deferred to V3:**
WebSocket streaming (§21), multi-tenant isolation (§22), JWT authentication (§10), Monte Carlo uncertainty bands (§5.2), CesiumJS 3D globe as primary view, PDF/PPTX export, mobile responsive layout, cross-border contagion (§3.13), Neo4j graph database, Redis caching, Kubernetes deployment.
