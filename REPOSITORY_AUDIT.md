# Repository Audit — deevo-sim → Impact Observatory | مرصد الأثر

**Date:** 2026-04-02
**Scope:** Full repository structure, reusability assessment, conflict identification, KEEP/REFACTOR/REMOVE/REPLACE matrix
**Target Product:** Impact Observatory — GCC executive decision intelligence platform
**Target Identity:** White/light boardroom aesthetic, bilingual (AR+EN), no dark/cyber/neon branding

---

## 1. Repository Structure

### Root Files
| File | Size | Purpose |
|------|------|---------|
| `docker-compose.yml` | 2KB | 4 services: api, postgres (PostGIS 16), neo4j 5.18, redis 7 |
| `Dockerfile.backend` | — | Python 3.12 backend container |
| `Makefile` | 5KB | Dev/test/build commands, references `src.main:app` |
| `railway.toml` | — | Railway deployment config |
| `vercel.json` | — | Vercel frontend config |
| `Procfile` | — | Heroku-style process file |
| `README.md` | — | Project documentation |
| `API.md` | — | API documentation |
| `AUDIT_REPORT.md` | — | Previous audit |
| `MASTER_ANALYSIS_v4.md` | — | V4 spec analysis |
| `.gitignore`, `LICENSE` | — | Standard |

### Major Directories
| Directory | Size | File Count | Description |
|-----------|------|------------|-------------|
| `backend/app/` | 2.7MB | ~90 .py | **Primary backend** — used by docker-compose (`app.main:app`) |
| `backend/src/` | 1.0MB | ~80 .py | **Secondary backend** — used by Makefile (`src.main:app`) |
| `backend/seeds/` | 428KB | 9 .py (5346 lines) | Seed data: actors, airports, corridors, events, flights, ports, vessels |
| `backend/tests/` | 1.1MB | ~25 files | Unit + integration tests |
| `frontend/src/` | 364KB | ~40 .tsx/.ts | **V4 frontend** — IO branded, white theme, design system |
| `frontend/app/` | 88KB | ~12 files | **V2 frontend** — older pages, some dark elements |
| `frontend/lib/` | 144KB | ~15 files | Shared libraries: API client, types, i18n, RBAC, simulation |
| `frontend/components/` | 32KB | 3 files | Shared UI: GraphPanel, Footer, Navbar |
| `packages/@deevo/` | 92MB (incl. node_modules) | 14 src files | GCC knowledge graph + constants — **already TypeScript** |
| `config/` | — | 1 file | `project.yml` |
| `db/` | — | 1 file | `init.sql` |
| `nginx/` | — | 1 file | `nginx.conf` reverse proxy |
| `docs/` | — | 4 files | Migration plan/report, roadmap, runbook |
| `.github/workflows/` | — | 1 file | `ci.yml` |

---

## 2. Critical Architectural Conflicts

### CONFLICT-1: Dual Backend Entrypoint
- **`backend/app/main.py`** (220 lines) — FastAPI with GraphClient, PipelineStatusTracker, LifecycleOrchestrator, 12 router imports. **Used by docker-compose.**
- **`backend/src/main.py`** (108 lines) — Simpler FastAPI with X-API-Key auth, 13 router imports, v1 API. **Used by Makefile.**
- **Impact:** Different routers, different auth, different service initialization. Cannot run both simultaneously. CI/CD ambiguity.

### CONFLICT-2: Dual Frontend Page Trees
- **`frontend/app/`** — V2 pages: landing, dashboard, scenarios, control-room layout. Older, some dark elements.
- **`frontend/src/app/`** — V4 pages: landing, dashboard, control-room, entity detail, graph explorer, scenario lab. IO-branded, white theme.
- **Impact:** Next.js App Router resolves `app/` over `src/app/` by default. V2 pages may shadow V4 pages depending on Next.js config.

### CONFLICT-3: Duplicate Engine Implementations
- **`backend/app/intelligence/`** — math_core, physics_core, scenario_engine, insurance_intelligence, engines
- **`backend/src/engines/`** — math, math_core, physics, physics_core, scenario, scenario_engine, insurance_intelligence
- **Impact:** Two copies of core algorithms. Unclear which is authoritative. Drift risk.

### CONFLICT-4: Duplicate Style Systems
- **`frontend/styles/globals.css`** — V2 global styles
- **`frontend/src/theme/globals.css`** — V4 design system (IO branded)
- **`frontend/src/app/globals.css`** — V4 app-level styles
- **Impact:** Three CSS entry points. Style conflicts, specificity wars.

### CONFLICT-5: Docker-Compose vs Makefile Credentials
- **docker-compose:** `deevo` / `deevo_secure` / `deevo_neo4j_2026`
- **Makefile:** `observatory_admin` / `io_graph_2026`
- **Impact:** Makefile health checks fail against docker-compose services.

---

## 3. What Is Reusable

### Already Correct (zero work needed)
| Component | Location | Status |
|-----------|----------|--------|
| Design tokens (white/executive palette) | `frontend/tailwind.config.ts` | `io: { bg: '#F8FAFC', surface: '#FFFFFF', primary: '#0F172A', accent: '#1D4ED8' }` |
| Theme tokens | `frontend/src/theme/tokens.ts` | `mode: "light"`, `boardroom_aesthetic`, `no_neon` |
| V4 global CSS | `frontend/src/theme/globals.css` | White theme, RTL support, card/metric utilities |
| Layout with correct metadata | `frontend/src/app/layout.tsx` | Title: "Impact Observatory \| مرصد الأثر", correct fonts |
| V4 Landing page (IO branded) | `frontend/src/app/page.tsx` | 27KB, white executive, bilingual, wired to `/api/v1/runs` |
| V4 Dashboard | `frontend/src/app/dashboard/page.tsx` | KPI cards, stress gauges, decision actions |
| i18n (EN) | `frontend/src/i18n/en.json` | `"product_name": "Impact Observatory"` |
| i18n (AR) | `frontend/src/i18n/ar.json` | Arabic translations |
| GCC Knowledge Graph | `packages/@deevo/gcc-knowledge-graph/` | 76 nodes, 191 edges, 17 scenarios — TypeScript |
| GCC Constants | `packages/@deevo/gcc-constants/` | GCC sector weights, thresholds — TypeScript |

### Reusable with Minor Fixes (already done in this session)
| Component | Location | Fix Applied |
|-----------|----------|-------------|
| Globe wrapper | `frontend/src/components/globe/index.tsx` | `bg-slate-900` → `bg-io-primary` |
| Control room page | `frontend/src/app/control-room/page.tsx` | `bg-slate-900` → `bg-io-primary` |
| Control room component | `frontend/src/components/controls/control-room.tsx` | `bg-slate-900` → `bg-io-primary` |
| Conflict layer colors | `frontend/src/components/globe/conflict-layer.tsx` | `cyber: "#a855f7"` → `cyber: "#1D4ED8"` |

### Reusable Core Intelligence (Python — high value)
| Module | Location | Lines | Description |
|--------|----------|-------|-------------|
| Pipeline orchestrator | `backend/app/orchestration/pipeline.py` | 618 | 9-stage pipeline: Scenario→Physics→Graph→Propagation→Financial→Risk→Regulatory→Decision→Explanation |
| Pipeline v4 | `backend/app/orchestration/pipeline_v4.py` | 308 | V4 extension pipeline |
| Physics core | `backend/app/intelligence/physics_core/` | 7 modules | flow_field, friction, potential_routing, pressure, shockwave, system_stress, threat_field |
| Math core | `backend/app/intelligence/math_core/` | 8 modules | calibration, confidence, disruption, exposure, propagation, proximity, risk, scoring |
| Scenario engine | `backend/app/intelligence/scenario_engine/` | 5 modules | baseline, delta, explanation, inject, runner |
| Insurance intelligence | `backend/app/intelligence/insurance_intelligence/` | 4 modules | claims_surge, portfolio_exposure, severity_projection, underwriting_watch |
| Propagation engine | `backend/app/intelligence/engines/propagation_engine.py` | — | Graph propagation |
| Decision engine | `backend/app/intelligence/engines/decision_engine.py` | — | Decision generation |
| Monte Carlo | `backend/app/intelligence/engines/monte_carlo.py` | — | Stochastic simulation |
| V4 Domain models | `backend/app/domain/models/` | 13 modules | Pydantic v2 models for all v4 canonical objects |
| V4 Services | `backend/app/services/` | 12 modules | audit, banking, business_impact, decision, explainability, financial, fintech, insurance, regulatory, reporting, time_engine, orchestrator |
| V1 API routes | `backend/app/api/v1/` | 4 files | runs, scenarios — v1 REST endpoints |
| Hormuz seed | `backend/app/seeds/hormuz_v1.py` | — | V1 Hormuz scenario seed data |
| GCC constants | `backend/app/intelligence/engines/gcc_constants.py` | — | GCC sector weights |
| RBAC | `backend/app/core/rbac.py` | — | 5 roles, 18 permissions |
| Security | `backend/app/core/security.py` | — | Auth middleware |

---

## 4. KEEP / REFACTOR / REMOVE / REPLACE Matrix

### KEEP (use as-is — 35 items)

| # | Path | Reason |
|---|------|--------|
| 1 | `packages/@deevo/gcc-knowledge-graph/` (all 7 src files) | TypeScript, zero-cost port, 76 nodes/191 edges/17 scenarios |
| 2 | `packages/@deevo/gcc-constants/` (all 3 src files) | TypeScript, GCC sector weights + freshness |
| 3 | `frontend/tailwind.config.ts` | IO design tokens already correct |
| 4 | `frontend/src/theme/tokens.ts` | White/boardroom design rules |
| 5 | `frontend/src/theme/globals.css` | IO CSS variables, RTL, utility classes |
| 6 | `frontend/src/app/layout.tsx` | Correct metadata, fonts, structure |
| 7 | `frontend/src/app/page.tsx` | V4 landing, 27KB, IO branded, wired to API |
| 8 | `frontend/src/app/dashboard/page.tsx` | V4 executive dashboard |
| 9 | `frontend/src/app/scenario-lab/page.tsx` | V4 scenario lab |
| 10 | `frontend/src/app/graph-explorer/page.tsx` | V4 graph explorer |
| 11 | `frontend/src/app/entity/[id]/page.tsx` | V4 entity detail |
| 12 | `frontend/src/app/control-room/page.tsx` | V4 control room (dark fixed) |
| 13 | `frontend/src/components/globe/` (all 6 files) | CesiumJS globe + layers (dark fixed) |
| 14 | `frontend/src/components/controls/control-room.tsx` | Control room component (dark fixed) |
| 15 | `frontend/src/components/panels/` (3 files) | scenario-panel, impact-panel, scientist-bar |
| 16 | `frontend/src/components/KPICard.tsx` | KPI card component |
| 17 | `frontend/src/components/StressGauge.tsx` | Sector stress gauge |
| 18 | `frontend/src/components/FinancialImpactPanel.tsx` | Financial impact panel |
| 19 | `frontend/src/components/DecisionActionCard.tsx` | Decision action card |
| 20 | `frontend/src/components/ErrorBoundary.tsx` | Error boundary |
| 21 | `frontend/src/features/` (all 5 feature panels) | Banking, Dashboard, Decisions, Fintech, Insurance detail panels |
| 22 | `frontend/src/hooks/use-api.ts` | API hook |
| 23 | `frontend/src/store/app-store.ts` | Zustand store |
| 24 | `frontend/src/i18n/` (en.json, ar.json) | Bilingual translations |
| 25 | `frontend/src/lib/api.ts` | V1 API client |
| 26 | `frontend/src/types/observatory.ts` | V4 TypeScript types |
| 27 | `frontend/src/app/globals.css` | App-level globals |
| 28 | `frontend/src/app/*/error.tsx` (4 files) | Error pages |
| 29 | `frontend/src/components/shared/providers.tsx` | Provider wrapper |
| 30 | `frontend/components/graph/GraphPanel.tsx` | SVG graph panel |
| 31 | `frontend/components/ui/Footer.tsx` | IO branded footer |
| 32 | `frontend/components/ui/Navbar.tsx` | IO branded navbar |
| 33 | `frontend/.env.example`, `.env.production` | Environment configs |
| 34 | `frontend/tsconfig.json`, `package.json` | Build config |
| 35 | `.github/workflows/ci.yml` | CI pipeline |

### REFACTOR (consolidate/upgrade — 25 items)

| # | Path | Action | Priority |
|---|------|--------|----------|
| 1 | `backend/app/main.py` | **Designate as single entrypoint.** Align Makefile to use `app.main:app`. | P2 |
| 2 | `backend/app/orchestration/pipeline.py` | Keep. Ensure it implements full 9-stage v4 pipeline. | P2 |
| 3 | `backend/app/orchestration/pipeline_v4.py` | Merge into pipeline.py or keep as extension. | P2 |
| 4 | `backend/app/intelligence/physics_core/` (7 files) | Keep as canonical. Remove `backend/src/engines/physics_core/` duplicate. | P2 |
| 5 | `backend/app/intelligence/math_core/` (8 files) | Keep as canonical. Remove `backend/src/engines/math_core/` duplicate. | P2 |
| 6 | `backend/app/intelligence/scenario_engine/` (5 files) | Keep as canonical. Remove `backend/src/engines/scenario_engine/` duplicate. | P2 |
| 7 | `backend/app/intelligence/insurance_intelligence/` (4 files) | Keep as canonical. Remove `backend/src/engines/insurance_intelligence/` duplicate. | P2 |
| 8 | `backend/app/intelligence/engines/` (5 files) | Keep decision_engine, propagation_engine, monte_carlo, gcc_constants. | P2 |
| 9 | `backend/app/domain/models/` (13 files) | Validate against v4 canonical JSON schema. Fill gaps. | P2 |
| 10 | `backend/app/services/` (12 files) | Validate all 12 service engines produce v4-compliant output. | P2 |
| 11 | `backend/app/api/v1/` (4 files) | Validate runs + scenarios endpoints match v4 spec. | P2 |
| 12 | `backend/app/schemas/` (2 files) | Consolidate with `backend/app/domain/models/`. | P2 |
| 13 | `backend/app/core/rbac.py` | Verify 5 roles × 18 permissions match v4 §23. | P2 |
| 14 | `backend/app/seeds/hormuz_v1.py` | Validate against v4 canonical scenario structure. | P3 |
| 15 | `backend/tests/` | Consolidate. Remove duplicate test files. Update imports to `app.*`. | P2 |
| 16 | `docker-compose.yml` | Fix credentials to match Makefile OR vice versa. Add frontend service. | P2 |
| 17 | `Makefile` | Change `src.main:app` → `app.main:app`. Update DB credentials. | P2 |
| 18 | `nginx/nginx.conf` | Add frontend service routing. | P2 |
| 19 | `frontend/lib/types/observatory.ts` | Consolidate with `frontend/src/types/observatory.ts`. | P1 |
| 20 | `frontend/lib/api/client.ts` | Consolidate with `frontend/src/lib/api.ts`. | P1 |
| 21 | `frontend/lib/i18n.ts` | Consolidate with `frontend/src/i18n/`. | P1 |
| 22 | `frontend/lib/server/rbac.ts` | Validate matches backend RBAC. | P2 |
| 23 | `frontend/src/types/index.ts` | `"cyber"` EventType stays (legitimate scenario type). Clean file header. | P1 |
| 24 | `frontend/middleware.ts` | Verify routing rules. | P2 |
| 25 | `db/init.sql` | Validate schema matches v4 domain models. | P2 |

### REMOVE (delete entirely — 42 items)

| # | Path | Reason |
|---|------|--------|
| **Duplicate Backend (`backend/src/`)** | | |
| 1 | `backend/src/main.py` | Superseded by `app/main.py` |
| 2 | `backend/src/api/` (all 13 route files) | Duplicate of `app/api/` |
| 3 | `backend/src/connectors/` (4 files) | Duplicate connectors: base, conflict, flight, maritime |
| 4 | `backend/src/core/` (3 files) | Duplicate of `app/core/` |
| 5 | `backend/src/db/` (3 files) | Duplicate DB clients |
| 6 | `backend/src/engines/math/` (5 files) | Duplicate of `app/intelligence/math_core/` |
| 7 | `backend/src/engines/math_core/` (7 files) | Duplicate of `app/intelligence/math_core/` |
| 8 | `backend/src/engines/physics/` (9 files) | Duplicate of `app/intelligence/physics_core/` |
| 9 | `backend/src/engines/physics_core/` (7 files) | Duplicate of `app/intelligence/physics_core/` |
| 10 | `backend/src/engines/scenario/` (3 files) | Duplicate of `app/intelligence/scenario_engine/` |
| 11 | `backend/src/engines/scenario_engine/` (6 files) | Duplicate of `app/intelligence/scenario_engine/` |
| 12 | `backend/src/engines/insurance_intelligence/` (4 files) | Duplicate of `app/intelligence/insurance_intelligence/` |
| 13 | `backend/src/engines/graph/` (3 files) | Duplicate graph handling |
| 14 | `backend/src/graph/` (3 files) | Duplicate graph queries |
| 15 | `backend/src/i18n/` (2 files) | Duplicate i18n |
| 16 | `backend/src/models/` (3 files) | Superseded by `app/domain/models/` |
| 17 | `backend/src/normalization/` | Duplicate normalization |
| 18 | `backend/src/orchestration/` | Duplicate orchestration |
| 19 | `backend/src/rules/` (3 files) | Consolidate into `app/core/` or `app/domain/` |
| 20 | `backend/src/schemas/` (12 files) | Superseded by `app/domain/models/` + `app/schemas/` |
| 21 | `backend/src/services/` (15 files) | Superseded by `app/services/` |
| **Legacy Seeds** | | |
| 22 | `backend/seeds/airports.py` | Flight tracking data — not IO scope |
| 23 | `backend/seeds/flights.py` | Flight tracking data — not IO scope |
| 24 | `backend/seeds/vessels.py` | Maritime tracking data — not IO scope |
| 25 | `backend/seeds/ports.py` | Maritime tracking data — not IO scope |
| 26 | `backend/seeds/corridors.py` | Corridor data — low priority |
| 27 | `backend/seeds/loader.py` | Loader for legacy seeds |
| 28 | `backend/seeds/__init__.py` | Init for legacy seeds |
| **Legacy/Duplicate Frontend** | | |
| 29 | `frontend/app/demo/` | **ALREADY DELETED** — 124KB dark legacy page |
| 30 | `frontend/app/page.tsx` | V2 landing — shadows V4 `src/app/page.tsx` |
| 31 | `frontend/app/layout.tsx` | V2 layout — shadows V4 `src/app/layout.tsx` |
| 32 | `frontend/app/dashboard/page.tsx` | V2 dashboard — shadows V4 `src/app/dashboard/page.tsx` |
| 33 | `frontend/app/scenarios/page.tsx` | V2 scenarios page with dark elements (`bg-zinc-900`, `text-cyan-400`) |
| 34 | `frontend/app/control-room/layout.tsx` | V2 control-room layout |
| 35 | `frontend/app/api/` (3 route files) | May conflict with `src/app/` API routes — audit before removing |
| 36 | `frontend/styles/globals.css` | V2 globals — superseded by `src/theme/globals.css` |
| **Legacy Backend APIs** | | |
| 37 | `backend/app/api/scores.py` | Legacy scoring endpoint — not in v4 spec |
| 38 | `backend/app/api/incidents.py` | Legacy incidents — not in v4 spec |
| 39 | `backend/app/api/insurance.py` | Legacy insurance endpoint — replaced by v4 services |
| 40 | `backend/app/api/decision.py` | Legacy decision endpoint — replaced by v4 services |
| **Other** | | |
| 41 | `backend/app/db/neo4j.py` | Neo4j client — evaluate if graph DB still needed vs PostgreSQL-only |
| 42 | `backend/app/connectors/` (osm only remaining) | OSM connector — low value |

### REPLACE (new implementation needed — 5 items)

| # | Current | Target | Priority |
|---|---------|--------|----------|
| 1 | Missing: frontend service in docker-compose | Add Next.js frontend container with health check | P1 |
| 2 | Missing: WebSocket support | Real-time streaming per v4 §22 — 5 channels: RunStatus, TimelineStep, Breach, Decision, Explanation | P3 |
| 3 | Missing: Multi-tenant data isolation | Row-level `tenant_id` per v4 §23 (TEN-001→TEN-005) | P3 |
| 4 | Missing: Time Engine UI | Temporal simulation controls per v4 §17 | P3 |
| 5 | Missing: Business Impact Layer | LossTrajectory, TimeToFailure, RegulatoryBreach per v4 §16 | P3 |

---

## 5. Summary Statistics

| Category | Count | Notes |
|----------|-------|-------|
| **KEEP** | 35 items | Already IO-branded, working, v4-aligned |
| **REFACTOR** | 25 items | Consolidation, validation, gap-filling |
| **REMOVE** | 42 items | Duplicates, legacy, out-of-scope |
| **REPLACE** | 5 items | New capabilities needed for v4 completeness |

### Priority Breakdown
| Priority | Action Items | Description |
|----------|-------------|-------------|
| **P1** | 8 | Frontend consolidation (remove v2 `app/` shadows), lib dedup |
| **P2** | 22 | Backend consolidation (remove `src/`), entrypoint unification, docker/makefile alignment, service validation |
| **P3** | 7 | V1 Hormuz, WebSocket, multi-tenant, time engine, business impact |

---

## 6. Recommended Execution Sequence

1. **Remove `frontend/app/` shadow pages** (P1) — eliminates V2/V4 page conflicts
2. **Remove `frontend/styles/globals.css`** (P1) — eliminates V2/V4 style conflicts
3. **Consolidate `frontend/lib/` into `frontend/src/`** (P1) — single source of truth for types/API/i18n
4. **Remove entire `backend/src/` directory** (P2) — eliminates dual entrypoint, 80+ duplicate files
5. **Update `Makefile` to use `app.main:app`** (P2) — align with docker-compose
6. **Update `docker-compose.yml` credentials + add frontend service** (P2)
7. **Remove legacy seeds (airports, flights, vessels, ports)** (P2)
8. **Remove legacy API endpoints (scores, incidents, insurance, decision)** (P2)
9. **Validate v4 domain models against canonical JSON schema** (P2)
10. **Implement P3 features** (WebSocket, multi-tenant, time engine, business impact)

---

## 7. Note on Changes Already Applied

During this session, before the audit-first directive, the following changes were already executed:

| Change | File | Detail |
|--------|------|--------|
| DELETED | `frontend/app/demo/page.tsx` | 124KB legacy dark page removed |
| DELETED | `frontend/app/demo/` directory | Empty directory removed |
| EDITED | `frontend/src/app/control-room/page.tsx` | `bg-slate-900` → `bg-io-primary` |
| EDITED | `frontend/src/components/controls/control-room.tsx` | `bg-slate-900` → `bg-io-primary` |
| EDITED | `frontend/src/components/globe/index.tsx` | `bg-slate-900` → `bg-io-primary`, `text-gray-400` → `text-io-border` |
| EDITED | `frontend/src/components/globe/conflict-layer.tsx` | `cyber: "#a855f7"` → `cyber: "#1D4ED8"` |

These are all P1 dark-remnant cleanups consistent with the target product identity. No structural changes were made.
