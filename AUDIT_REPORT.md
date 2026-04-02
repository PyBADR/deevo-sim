# Impact Observatory | مرصد الأثر — Complete Repository Audit

**Date:** 2026-04-02
**Branch:** `claude/infallible-davinci`
**Base:** `main` @ `f72fa4c` — "feat: DecisionCore → Impact Observatory v1 (#1)"
**Git status:** Clean — no uncommitted changes

---

## Executive Summary

The branding transformation from "Deevo Sim" to "Impact Observatory | مرصد الأثر" is **largely complete** at the surface level (README, package.json, page titles, API titles). However, the repository has accumulated **significant structural debt** from iterative development:

1. **Dual backend structure** — `backend/app/` (Phase 7, complex, unused entry) vs `backend/src/` (v1, active entry per Makefile). Only `src/` is wired to `uvicorn src.main:app`.
2. **Dual frontend structure** — `frontend/app/` (old routes) vs `frontend/src/app/` (active). Next.js uses `src/app` when present; the root `app/` is never served.
3. **Duplicated engine modules** — physics/physics_core, math/math_core, scenario/scenario_engine appear in both `backend/app/` and `backend/src/`, some with different implementations.
4. **Docker naming** — `docker-compose.yml` still uses `deevo` DB names and passwords.

**Active paths (what actually runs):**
- Backend: `backend/src/main.py` via `uvicorn src.main:app`
- Frontend: `frontend/src/app/` (Next.js src convention)

---

## KEEP
*Infrastructure and code that works as-is and should be reused unchanged.*

### Infrastructure
- `docker-compose.yml` — Full stack definition (Postgres+PostGIS, Neo4j, Redis, API); needs credential rename only
- `backend/Dockerfile` — Production container for the Python API
- `frontend/Dockerfile` — Production container for Next.js
- `Dockerfile.backend` — Root-level backend Dockerfile (used by Railway)
- `nginx/nginx.conf` — Reverse proxy config for production stack
- `railway.toml` — Railway deployment config
- `vercel.json` — Vercel API rewrite config (already correct)
- `Makefile` — Complete dev/prod/test automation, already Impact Observatory branded
- `db/init.sql` — PostgreSQL init with correct Impact Observatory schema (runs, decision_actions tables)
- `.github/workflows/ci.yml` — CI pipeline (lint → test-backend → test-frontend)
- `.gitignore`, `frontend/.gitignore` — Standard ignores
- `Procfile` — Keep for Heroku fallback

### Backend — Active (`backend/src/`)
- `backend/src/main.py` — Clean FastAPI entry point, correct branding, graceful DB fallback
- `backend/src/core/config.py` — Settings with CORS origin list, env-based config
- `backend/src/core/project.py` — Project metadata
- `backend/src/api/auth.py` — X-API-Key authentication
- `backend/src/api/routes/health.py` — Health check endpoint
- `backend/src/api/routes/scenarios.py` — Scenario CRUD
- `backend/src/api/routes/scores.py` — Risk scores
- `backend/src/api/routes/graph.py` — Graph queries
- `backend/src/api/routes/insurance.py` — Insurance routes
- `backend/src/api/routes/decision.py` — Decision routes
- `backend/src/api/v1/runs.py` — Full pipeline execution, human-in-the-loop approval, audit trail
- `backend/src/api/v1/scenarios.py` — Scenario templates endpoint
- `backend/src/db/neo4j.py` — Neo4j async connection with graceful skip
- `backend/src/db/postgres.py` — PostgreSQL async connection
- `backend/src/db/redis.py` — Redis async connection
- `backend/src/models/canonical.py` — Canonical domain models
- `backend/src/models/orm.py` — SQLAlchemy ORM models
- `backend/src/schemas/` (all 10 files) — Pydantic schemas: banking_stress, base, decision, edge, entity, explanation, financial_impact, fintech_stress, flow_state, insurance_stress, regulatory_state, scenario
- `backend/src/services/run_orchestrator.py` — Main pipeline executor wiring all 12 services
- `backend/src/services/scenario_service.py` — Scenario template lookup and run retrieval
- `backend/src/services/state.py` — Global in-memory state initialization
- `backend/src/services/audit_service.py` — Decision action audit trail
- `backend/src/services/reporting_service.py` — Multi-mode report generation
- `backend/src/services/seed_data.py` — GCC entity seed data (31 entities)
- `backend/src/services/banking_service.py` — Basel III banking stress calculations
- `backend/src/services/insurance_service.py` — IFRS-17 insurance stress calculations
- `backend/src/services/fintech_service.py` — Payment/fintech disruption modeling
- `backend/src/services/financial_service.py` — GDP-weighted financial impact
- `backend/src/services/decision_service.py` — Priority-ranked decision actions
- `backend/src/services/explainability_service.py` — 20-step causal chain explanations
- `backend/src/services/propagation_service.py` — Impact propagation across entities
- `backend/src/services/physics_service.py` — Physics engine coordination
- `backend/src/services/db_service.py` — Database persistence layer
- `backend/src/services/entity_graph_service.py` — Entity relationship graph
- `backend/src/graph/loader.py` — Graph data loading
- `backend/src/graph/queries.py` — Cypher/graph queries
- `backend/src/graph/schema.py` — Graph schema definitions
- `backend/src/normalization/normalizer.py` — Input data normalization
- `backend/src/i18n/labels.py` — Bilingual (AR/EN) label registry
- `backend/src/connectors/base.py` — Base connector interface
- `backend/src/connectors/conflict_adapter.py` — Conflict data adapter
- `backend/src/connectors/flight_adapter.py` — Flight data adapter
- `backend/src/connectors/maritime_adapter.py` — Maritime data adapter
- `backend/src/rules/banking_thresholds.py` — Basel III threshold constants
- `backend/src/rules/gcc_regulatory_rules.py` — GCC regulatory rule definitions
- `backend/src/rules/insurance_thresholds.py` — Insurance threshold constants
- `backend/requirements.txt` — All 16 Python dependencies (FastAPI, SQLAlchemy, Neo4j, Mesa, etc.)
- `backend/pyproject.toml` — Ruff linter config
- `backend/runtime.txt` — Python 3.11 runtime pin
- `backend/seeds/` (actors, airports, corridors, events, flights, ports, scenario_seeds, vessels, loader) — GCC seed data for 6 scenarios
- `backend/seeds/expected_outputs/` (16 JSON files) — Golden regression test fixtures
- `backend/tests/` — Test suite (integration, unit, golden suite)

### Frontend — Active (`frontend/src/`)
- `frontend/src/app/layout.tsx` — Root layout with DM Sans + IBM Plex Arabic fonts
- `frontend/src/app/page.tsx` — Full landing page + scenario selector + results view (already Impact Observatory branded)
- `frontend/src/app/dashboard/page.tsx` — Dashboard route
- `frontend/src/app/dashboard/error.tsx` — Dashboard error boundary
- `frontend/src/app/control-room/page.tsx` — Control room route
- `frontend/src/app/control-room/error.tsx` — Control room error boundary
- `frontend/src/app/graph-explorer/page.tsx` — Graph explorer route
- `frontend/src/app/graph-explorer/error.tsx` — Graph explorer error boundary
- `frontend/src/app/scenario-lab/page.tsx` — Scenario lab route
- `frontend/src/app/scenario-lab/error.tsx` — Scenario lab error boundary
- `frontend/src/app/entity/[id]/page.tsx` — Entity detail route
- `frontend/src/app/error.tsx` — Global error boundary
- `frontend/src/app/globals.css` — Global CSS (if used)
- `frontend/src/components/DecisionActionCard.tsx` — Decision action display
- `frontend/src/components/ErrorBoundary.tsx` — Reusable error boundary
- `frontend/src/components/FinancialImpactPanel.tsx` — Financial impact panel
- `frontend/src/components/KPICard.tsx` — KPI metric card
- `frontend/src/components/StressGauge.tsx` — Stress gauge visualization
- `frontend/src/components/controls/control-room.tsx` — Control room component
- `frontend/src/components/globe/` (all 6 files) — Cesium 3D globe, deck.gl overlay, conflict/flight/vessel layers
- `frontend/src/components/panels/impact-panel.tsx` — Impact panel
- `frontend/src/components/panels/scenario-panel.tsx` — Scenario panel
- `frontend/src/components/panels/scientist-bar.tsx` — Scientist bar panel
- `frontend/src/components/shared/providers.tsx` — React Query + Zustand providers
- `frontend/src/features/banking/BankingDetailPanel.tsx` — Banking stress detail view
- `frontend/src/features/dashboard/ExecutiveDashboard.tsx` — Main executive dashboard
- `frontend/src/features/decisions/DecisionDetailPanel.tsx` — Decision actions detail
- `frontend/src/features/fintech/FintechDetailPanel.tsx` — Fintech stress detail
- `frontend/src/features/insurance/InsuranceDetailPanel.tsx` — Insurance stress detail
- `frontend/src/hooks/use-api.ts` — React Query hooks for API calls
- `frontend/src/i18n/en.json` — English labels
- `frontend/src/i18n/ar.json` — Arabic labels
- `frontend/src/lib/api.ts` — Typed API client
- `frontend/src/store/app-store.ts` — Zustand global state
- `frontend/src/theme/globals.css` — Tailwind base + CSS variables (io-accent, io-primary, etc.)
- `frontend/src/theme/tokens.ts` — Design token definitions
- `frontend/src/types/index.ts` — Shared TypeScript types
- `frontend/src/types/observatory.ts` — Observatory-specific types (RunResult, Language, ViewMode, etc.)
- `frontend/package.json` — Already named "impact-observatory", all correct deps
- `frontend/tailwind.config.ts` — Tailwind config with io-* color tokens
- `frontend/next.config.mjs` — Standalone output, type-checked builds
- `frontend/tsconfig.json` — TypeScript config
- `frontend/middleware.ts` — Next.js middleware
- `frontend/postcss.config.mjs` — PostCSS config

### Packages (Monorepo)
- `packages/@deevo/gcc-constants/` — GCC freshness/constants package (name can stay, it's a scoped pkg)
- `packages/@deevo/gcc-knowledge-graph/` — GCC graph schema, nodes, edges, scenarios, migrations
- `packages/@deevo/gcc-knowledge-graph/migrations/001_gcc_graph.sql` — Graph schema migration

### Docs
- `README.md` — Already correctly titled "Impact Observatory | مرصد الأثر"
- `LICENSE` — Keep as-is
- `docs/RUNBOOK.md` — Operational runbook

---

## REFACTOR
*Valuable code that needs modification to align with Impact Observatory.*

### Infrastructure
- `docker-compose.yml` — Change `deevo` DB names/passwords to `impact_observatory`/`io_admin`. The Makefile already references `observatory_admin` and `impact_observatory` DB — docker-compose is out of sync.
- `.github/workflows/ci.yml` — Remove `DC7_*` env var prefix (legacy); update to correct DB names matching docker-compose; add `backend/src/` to PYTHONPATH explicitly
- `backend/.env.example` — Audit and update any remaining "deevo" references

### Backend — Active Services
- `backend/src/api/routes/conflicts.py` — Verify this is wired up and needed; may need route prefix alignment
- `backend/src/api/routes/events.py` — Same as above
- `backend/src/api/routes/flights.py` — Verify needed; connects to flight adapter
- `backend/src/api/routes/incidents.py` — Verify needed; connects to incident data
- `backend/src/api/routes/vessels.py` — Verify needed; connects to maritime adapter
- `backend/src/engines/math/` (config, decay, multi_hop, propagation, scoring) — Merge/reconcile with `math_core/` which has overlapping functions (propagation exists in both)
- `backend/src/engines/math_core/` (calibration, confidence, disruption, exposure, gcc_weights, propagation, risk) — Consolidate with `math/` into a single `backend/src/engines/math/` package
- `backend/src/engines/physics/` (boundary, diffusion, flow_field, friction, potential, pressure, shockwave, system_stress, threat_field) — Merge with `physics_core/` (same 7 modules duplicated)
- `backend/src/engines/physics_core/` — Consolidate into `physics/`
- `backend/src/engines/scenario/` (engine, templates, templates_extended) — Merge with `scenario_engine/` (baseline, delta, explanation, inject, mesa_sim, runner)
- `backend/src/engines/scenario_engine/` — Consolidate into `scenario/`
- `backend/src/engines/insurance_intelligence/` — Keep but verify it's used by `insurance_service.py`
- `backend/src/engines/graph/` (loader, schema) — Verify vs `src/graph/` (loader, queries, schema); potential duplication
- `backend/app/seeds/hormuz_v1.py` — Migrate relevant seed data to `backend/seeds/` structure
- `backend/app/intelligence/engines/gcc_constants.py` — Extract GCC constants to canonical location

### Frontend
- `frontend/src/app/dashboard/page.tsx` — Currently likely a stub; needs proper implementation that routes to `ExecutiveDashboard`
- `frontend/src/app/control-room/page.tsx` — Verify it uses `control-room.tsx` component
- `frontend/src/app/graph-explorer/page.tsx` — Verify it's wired to graph API
- `frontend/src/app/scenario-lab/page.tsx` — Verify content
- `frontend/.env.example` — Audit for any deevo references
- `frontend/.env.production` — Review; may need NEXT_PUBLIC_API_URL update

### Documentation
- `API.md` — Rewrite to reflect actual v1 API surface (`/api/v1/runs`, `/api/v1/scenarios`, etc.)
- `MASTER_ANALYSIS_v4.md` — Convert relevant architecture decisions into `docs/ARCHITECTURE.md`; delete the rest
- `docs/MIGRATION_PLAN.md` and `docs/MIGRATION_REPORT.md` — Outdated migration docs; archive or delete

---

## REMOVE
*Dead code, orphaned files, and empty directories that add no value.*

### Backend — Orphaned Old Structure (`backend/app/`)
The entire `backend/app/` directory is **not the active entry point** (Makefile uses `src.main:app`). Many modules have broken imports (e.g., `GraphSchema` imported but not defined in `app/main.py`). All business logic worth keeping has been migrated to `backend/src/`.

- `backend/app/main.py` — Broken imports (GraphSchema undefined), superseded by `src/main.py`
- `backend/app/api/decision.py` — Superseded by `src/api/routes/decision.py`
- `backend/app/api/graph.py` — Superseded by `src/api/routes/graph.py`
- `backend/app/api/health.py` — Superseded by `src/api/routes/health.py`
- `backend/app/api/incidents.py` — Superseded
- `backend/app/api/insurance.py` — Superseded
- `backend/app/api/models.py` — Superseded
- `backend/app/api/observatory.py` — Superseded
- `backend/app/api/scenarios.py` — Superseded
- `backend/app/api/scores.py` — Superseded
- `backend/app/api/v1/router.py` — Superseded
- `backend/app/api/v1/routes/runs.py` — Superseded by `src/api/v1/runs.py`
- `backend/app/api/v1/routes/scenarios.py` — Superseded
- `backend/app/api/v1/schemas/common.py` — Superseded by `src/schemas/`
- `backend/app/config/settings.py` — Superseded by `src/core/config.py`
- `backend/app/connectors/acled/` — Superseded by `src/connectors/conflict_adapter.py`
- `backend/app/connectors/aviation/` — Superseded by `src/connectors/flight_adapter.py`
- `backend/app/connectors/base/` — Superseded by `src/connectors/base.py`
- `backend/app/connectors/csv_import/` — No equivalent needed in v1
- `backend/app/connectors/maritime/` — Superseded by `src/connectors/maritime_adapter.py`
- `backend/app/connectors/osm/` — OpenStreetMap connector not part of v1 scope
- `backend/app/core/` (constants, errors, rbac, security) — Superseded by `src/core/`
- `backend/app/db/models.py` — Superseded by `src/models/`
- `backend/app/db/neo4j.py` — Superseded by `src/db/neo4j.py`
- `backend/app/decision/__init__.py` — Empty, remove
- `backend/app/domain/models/` (all 12 models) — Superseded by `src/schemas/` and `src/models/`
- `backend/app/domain/services/` — Empty directory
- `backend/app/graph/` — Empty (only `__pycache__`), superseded by `src/graph/`
- `backend/app/intelligence/engines/decision_engine.py` — Superseded by `src/services/decision_service.py`
- `backend/app/intelligence/engines/gcc_constants.py` — Extract to `src/` if unique, then remove
- `backend/app/intelligence/engines/monte_carlo.py` — Superseded by `src/engines/`
- `backend/app/intelligence/engines/propagation_engine.py` — Superseded
- `backend/app/intelligence/engines/scenario_engines.py` — Superseded
- `backend/app/intelligence/insurance/claims_uplift.py` — Superseded by `src/engines/insurance_intelligence/`
- `backend/app/intelligence/insurance_intelligence/` (all 4 files) — Duplicate of `src/engines/insurance_intelligence/`
- `backend/app/intelligence/math/propagation.py` — Superseded by `src/engines/math/`
- `backend/app/intelligence/math_core/` (all 8 files) — Duplicate of `src/engines/math_core/`
- `backend/app/intelligence/physics/flow_field.py` — Superseded by `src/engines/physics/`
- `backend/app/intelligence/physics/gcc_physics_config.py` — Extract if unique constants, then remove
- `backend/app/intelligence/physics_core/` (all 7 files) — Duplicate of `src/engines/physics_core/`
- `backend/app/intelligence/scenario_engine/` (all 5 files) — Duplicate of `src/engines/scenario_engine/`
- `backend/app/models/` — Empty directory
- `backend/app/orchestration/pipeline.py` — Superseded by `src/services/run_orchestrator.py`
- `backend/app/orchestration/pipeline_v4.py` — Superseded
- `backend/app/rules/` — Empty directory
- `backend/app/scenarios/engine.py` — Superseded by `src/engines/scenario/`
- `backend/app/scenarios/runner.py` — Superseded
- `backend/app/scenarios/templates.py` — Superseded
- `backend/app/schema/` — Empty directory (only `__pycache__`)
- `backend/app/schemas/base.py` — Superseded by `src/schemas/base.py`
- `backend/app/schemas/observatory.py` — Superseded
- `backend/app/seeds/__init__.py` — Superseded by root `backend/seeds/`
- `backend/app/seeds/hormuz_v1.py` — Migrate relevant data, then remove
- `backend/app/services/audit/engine.py` — Superseded by `src/services/audit_service.py`
- `backend/app/services/banking/engine.py` — Superseded by `src/services/banking_service.py`
- `backend/app/services/business_impact/engine.py` — Superseded by `src/services/financial_service.py`
- `backend/app/services/decision/engine.py` — Superseded by `src/services/decision_service.py`
- `backend/app/services/explainability/engine.py` — Superseded by `src/services/explainability_service.py`
- `backend/app/services/financial/engine.py` — Superseded
- `backend/app/services/fintech/engine.py` — Superseded by `src/services/fintech_service.py`
- `backend/app/services/insurance/engine.py` — Superseded by `src/services/insurance_service.py`
- `backend/app/services/normalization.py` — Superseded by `src/normalization/normalizer.py`
- `backend/app/services/orchestrator.py` — Superseded by `src/services/run_orchestrator.py`
- `backend/app/services/physics/` — Empty directory
- `backend/app/services/propagation/` — Empty directory
- `backend/app/services/regulatory/engine.py` — No equivalent in v1 (not in scope for MVP)
- `backend/app/services/reporting/engine.py` — Superseded by `src/services/reporting_service.py`
- `backend/app/services/scenario/` — Empty directory
- `backend/app/services/time_engine/engine.py` — Not in v1 scope
- `backend/app/simulation/__init__.py` — Empty, remove
- `backend/app/tests/` — Empty test directory
- `backend/.pytest_cache/` — Cache artifacts, should not be in git
- `backend/pytest-cache-files-hnggyd9d` — Stale cache file

### Backend — Other Dead Files
- `backend/src/api/v1/__init__.py` (empty) — Fine to keep but minimal
- `backend/src/orchestration/__init__.py` — Empty orchestration stub (only `__init__.py`), no actual code
- `backend/scripts/run_scenario.py` — Likely superseded by `make test-backend`; verify before removing

### Frontend — Orphaned Old Structure (`frontend/app/`)
Next.js uses `src/app/` when present; the root `frontend/app/` is **never served**. These are stale duplicates.

- `frontend/app/api/audit/[id]/route.ts` — Superseded by backend API
- `frontend/app/api/run-scenario/route.ts` — Superseded by `src/api/v1/runs.py`
- `frontend/app/api/scenarios/route.ts` — Superseded by backend API
- `frontend/app/control-room/layout.tsx` — Never served (root app/ not active)
- `frontend/app/dashboard/page.tsx` — Stale duplicate
- `frontend/app/demo/page.tsx` — Stale demo page
- `frontend/app/layout.tsx` — Never served
- `frontend/app/page.tsx` — Never served (superseded by `src/app/page.tsx`)
- `frontend/app/scenarios/page.tsx` — Never served

### Frontend — Old Components and Lib Outside `src/`
- `frontend/components/graph/GraphPanel.tsx` — Old component outside `src/`, superseded by `src/components/globe/`
- `frontend/components/ui/Footer.tsx` — Old UI component outside `src/`
- `frontend/components/ui/Navbar.tsx` — Old UI component outside `src/`
- `frontend/lib/decision-engine.ts` — Old client-side engine, logic now in backend
- `frontend/lib/i18n.ts` — Superseded by `src/i18n/` JSON files
- `frontend/lib/mock-data.ts` — Mock data, replaced by real API calls
- `frontend/lib/simulation-engine.ts` — Old simulation engine, logic now in backend
- `frontend/lib/server/audit.ts` — Old server-side audit, superseded by backend audit service
- `frontend/lib/server/auth.ts` — Old server auth, superseded by backend X-API-Key auth
- `frontend/lib/server/execution.ts` — Old execution logic, superseded by backend pipeline
- `frontend/lib/server/rbac.ts` — Old RBAC, superseded by backend RBAC
- `frontend/lib/server/store.ts` — Old store, superseded by Zustand store in `src/store/`
- `frontend/lib/server/trace.ts` — Old tracing, not in v1 scope
- `frontend/lib/types.ts` — Superseded by `src/types/`
- `frontend/lib/types/observatory.ts` — Superseded by `src/types/observatory.ts`
- `frontend/styles/globals.css` — Old styles, superseded by `src/theme/globals.css`
- `frontend/modes/` — Empty directory, remove
- `frontend/theme/` — Empty root-level theme dir (different from `src/theme/`), remove
- `frontend/tsconfig.tsbuildinfo` — Build artifact, should be in `.gitignore`

### Documentation
- `MASTER_ANALYSIS_v4.md` — Internal planning artifact, not production documentation
- `docs/MIGRATION_PLAN.md` — The migration is done; this is historical
- `docs/MIGRATION_REPORT.md` — Historical migration report

---

## REPLACE
*Files that must be completely rewritten for Impact Observatory.*

- `docker-compose.yml` — **Replace** all `deevo` references: DB name → `impact_observatory`, user → `observatory_admin`, Neo4j password → `io_graph_2026` (already in Makefile). The Makefile and `docker-compose.yml` are currently **out of sync** — this is a production blocker.

- `config/project.yml` — Currently an empty directory placeholder. **Replace** with actual project configuration: environment settings, feature flags, GCC entity registry reference.

- `config/environments/` — Currently empty. **Replace** with `development.yml`, `staging.yml`, `production.yml` environment config files.

- `config/scenarios/` — Currently empty. **Replace** with canonical scenario YAML definitions (Hormuz, Yemen, cyber, oil shock, banking stress, port disruption) extracted from `backend/seeds/scenario_seeds.py`.

- `config/thresholds/` — Currently empty. **Replace** with threshold YAML files extracted from `backend/src/rules/` (banking, insurance, regulatory thresholds as config not code).

- `docs/ROADMAP.md` — Currently present but needs replacement with Impact Observatory v2 roadmap (globe visualization, real-time data feeds, auth, multi-tenant).

---

## Dependency Audit

### Frontend (`frontend/package.json`) — Status: Good
| Package | Purpose | Status |
|---------|---------|--------|
| `next@^15.0.0` | Framework | KEEP |
| `react@^19.0.0` | UI | KEEP |
| `@tanstack/react-query@^5.60.0` | Data fetching | KEEP |
| `zustand@^5.0.0` | State management | KEEP |
| `cesium@^1.123.0` | 3D globe | KEEP — used by globe components |
| `resium@^1.18.0` | React Cesium | KEEP |
| `@deck.gl/*@^9.1.0` | Geospatial layers | KEEP — used by globe overlay |
| `mapbox-gl@^3.8.0` | 2D map | REVIEW — may conflict with Cesium; verify usage |
| `recharts@^2.13.0` | Charts | KEEP |
| `lucide-react@^0.460.0` | Icons | KEEP |
| `d3-*` | Data viz utilities | KEEP |

### Backend (`backend/requirements.txt`) — Status: Good
| Package | Purpose | Status |
|---------|---------|--------|
| `fastapi==0.111.0` | API framework | KEEP |
| `uvicorn[standard]==0.30.1` | ASGI server | KEEP |
| `sqlalchemy==2.0.30` | ORM | KEEP |
| `asyncpg==0.29.0` | Async Postgres | KEEP |
| `psycopg2-binary==2.9.9` | Sync Postgres | KEEP |
| `neo4j==5.19.0` | Graph DB client | KEEP |
| `redis==5.0.4` | Cache | KEEP |
| `numpy==1.26.4` | Math | KEEP |
| `scipy==1.13.0` | Statistics | KEEP |
| `pydantic==2.7.1` | Validation | KEEP |
| `python-jose[cryptography]==3.3.0` | JWT | KEEP |
| `passlib[bcrypt]==1.7.4` | Password hashing | KEEP |
| `python-multipart==0.0.9` | Form data | KEEP |
| `httpx==0.27.0` | HTTP client | KEEP |
| `mesa==2.3.0` | Agent-based modeling | REVIEW — used only by `mesa_sim.py`; heavyweight dep; consider removing if ABM not in v1 scope |

---

## Critical Issues (Blockers)

1. **docker-compose.yml out of sync with Makefile** — `docker-compose.yml` uses `deevo`/`deevo_secure` credentials; Makefile health checks expect `observatory_admin`/`impact_observatory`. `make status` will always fail until resolved.

2. **`backend/app/main.py` has broken import** — `GraphSchema` is imported but never defined/imported in scope. The `backend/app/` entry point would crash on startup. This is not the active entry point, but it's confusing.

3. **`backend/.pytest_cache/` and `backend/pytest-cache-files-hnggyd9d` in git** — Build artifacts committed to the repo. Should be added to `.gitignore`.

4. **`frontend/tsconfig.tsbuildinfo` in git** — Build artifact. Add to `.gitignore`.

5. **`frontend/app/` is served dead code** — While Next.js won't serve it (uses `src/app/`), it creates confusion and may cause import resolution issues.

6. **In-memory run cache** — `backend/src/api/v1/runs.py` stores results in `_results: dict` (in-memory). Runs are lost on server restart. `db/init.sql` has the right schema for persistence; the persistence write is not yet wired.

---

## File Count Summary

| Category | Files | Notes |
|----------|-------|-------|
| KEEP | ~140 | Active stack, working infrastructure |
| REFACTOR | ~35 | Needs changes but valuable |
| REMOVE | ~120 | Dead code, empty dirs, orphaned structure |
| REPLACE | ~8 | Empty configs, out-of-sync docker |

**Total repo files (excl. node_modules, .git, .next, __pycache__):** ~340 tracked files
**After cleanup:** ~175 files (~48% reduction in tracked code surface)
