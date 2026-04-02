# Impact Observatory | مرصد الأثر — Controlled Replatforming Execution Plan

Generated: 2 April 2026

---

## 1. REPOSITORY AUDIT — FILE INVENTORY

### Total: ~280 unique source files (excluding node_modules, .next, .git, __pycache__)

| Directory | Files | Total Size | Purpose |
|---|---|---|---|
| `backend/app/` | 62 | ~490 KB | FastAPI app (legacy entrypoint) |
| `backend/src/` | 68 | ~340 KB | FastAPI src (parallel entrypoint) |
| `backend/seeds/` | 9 + 15 golden | ~230 KB | GCC seed data + expected outputs |
| `backend/tests/` | 30 | ~280 KB | Pytest suites (unit + integration) |
| `frontend/app/` | 6 | ~210 KB | Next.js App Router pages (old) |
| `frontend/src/` | 22 | ~200 KB | Next.js src components (new) |
| `frontend/lib/` | 12 | ~120 KB | API client, types, engines |
| `frontend/components/` | 4 | ~30 KB | Root-level UI components |
| `packages/@deevo/` | 10 | ~120 KB | GCC constants + knowledge graph (TS) |
| `config/` + `docs/` + root | 15 | ~180 KB | Config, docs, Docker, CI |

---

## 2. KEEP / REFACTOR / REMOVE / REPLACE MATRIX

### KEEP — Zero-change assets (copy as-is)

| File/Module | Size | Reason |
|---|---|---|
| `packages/@deevo/gcc-knowledge-graph/src/nodes.ts` | 22 KB | 76 GCC entity nodes — production data |
| `packages/@deevo/gcc-knowledge-graph/src/edges.ts` | 40 KB | 191 GCC dependency edges — production data |
| `packages/@deevo/gcc-knowledge-graph/src/scenarios.ts` | 33 KB | 17 scenario templates — production data |
| `packages/@deevo/gcc-knowledge-graph/src/types.ts` | 4.8 KB | TypeScript types for graph |
| `packages/@deevo/gcc-knowledge-graph/src/validation.ts` | 4.7 KB | Graph validation logic |
| `packages/@deevo/gcc-knowledge-graph/src/graph.ts` | 8 KB | Graph construction logic |
| `packages/@deevo/gcc-knowledge-graph/src/index.ts` | 1.2 KB | Package export barrel |
| `packages/@deevo/gcc-knowledge-graph/migrations/001_gcc_graph.sql` | 7.4 KB | PostgreSQL migration |
| `packages/@deevo/gcc-constants/src/index.ts` | 6.8 KB | GCC regulatory constants |
| `packages/@deevo/gcc-constants/src/freshness.ts` | 4.2 KB | Data freshness scoring |
| `frontend/lib/types/observatory.ts` | 14 KB | V4 type contracts (60+ types) |
| `frontend/src/types/observatory.ts` | 4.6 KB | Additional observatory types |
| `frontend/src/i18n/ar.json` | 8.4 KB | Arabic translations |
| `frontend/src/i18n/en.json` | 3.4 KB | English translations |
| `frontend/lib/i18n.ts` | 5.6 KB | i18n engine + bilingual labels |
| `backend/seeds/expected_outputs/*.json` | 24 KB | 15 golden test fixtures |
| `backend/app/core/rbac.py` | 4.5 KB | RBAC matrix (translate to TS) |
| `backend/app/core/constants.py` | 3 KB | GCC constants (translate to TS) |
| `config/project.yml` | 2.2 KB | Project identity config |

### REFACTOR — Keep logic, change language/framework

| Module | Source | Size | Refactor Target |
|---|---|---|---|
| **Pipeline Orchestrator** | `backend/app/orchestration/pipeline.py` | 25 KB | TypeScript orchestrator — same 10 stages |
| **Pipeline V4** | `backend/app/orchestration/pipeline_v4.py` | 12 KB | Merge into single TS pipeline |
| **Math Core** (7 modules) | `backend/src/engines/math_core/` | 39 KB | Port Python math → TypeScript |
| **Physics Core** (7 modules) | `backend/src/engines/physics_core/` | 48 KB | Port Python physics → TypeScript |
| **Physics** (9 modules) | `backend/src/engines/physics/` | 33 KB | Port (merge with physics_core) |
| **Insurance Intelligence** (4) | `backend/src/engines/insurance_intelligence/` | 17 KB | Port Python → TypeScript |
| **Scenario Engine** (6 modules) | `backend/src/engines/scenario_engine/` | 75 KB | Port + merge baseline/delta/runner |
| **Decision Engine** | `backend/app/intelligence/engines/decision_engine.py` | 36 KB | Port priority formula + ranking |
| **Propagation Engine** | `backend/app/intelligence/engines/propagation_engine.py` | 20 KB | Port + add convergence epsilon |
| **Monte Carlo** | `backend/app/intelligence/engines/monte_carlo.py` | 16 KB | Port — NumPy → native JS |
| **Audit Engine** | `backend/app/services/audit/engine.py` | 4.3 KB | Port SHA-256 → Node crypto |
| **Regulatory Engine** | `backend/app/services/regulatory/engine.py` | 3.7 KB | Port breach detection |
| **Banking Service** | `backend/src/services/banking_service.py` | 8.8 KB | Port stress calculations |
| **Insurance Service** | `backend/src/services/insurance_service.py` | 6 KB | Port stress calculations |
| **Fintech Service** | `backend/src/services/fintech_service.py` | 5.7 KB | Port stress calculations |
| **Financial Service** | `backend/src/services/financial_service.py` | 5.6 KB | Port loss model |
| **Explainability Service** | `backend/src/services/explainability_service.py` | 7 KB | Port explanation generation |
| **Business Impact** | `backend/app/services/business_impact/engine.py` | 9 KB | Port to TS |
| **Time Engine** | `backend/app/services/time_engine/engine.py` | 4.7 KB | Port + extend per v4 §17 |
| **Reporting Engine** | `backend/src/services/reporting_service.py` | 6.4 KB | Port to TS |
| **Run Orchestrator** | `backend/src/services/run_orchestrator.py` | 10 KB | Port — becomes tRPC procedure |
| **Domain Models** (15 files) | `backend/app/domain/models/` | 34 KB | Translate Pydantic → Zod/Drizzle |
| **Schemas** (12 files) | `backend/src/schemas/` | 13 KB | Translate Pydantic → Zod |
| **Normalizer** | `backend/src/normalization/normalizer.py` | 9 KB | Port to TS |
| **GCC Regulatory Rules** | `backend/src/rules/gcc_regulatory_rules.py` | 3.7 KB | Port rule engine to TS |
| **Banking/Insurance Thresholds** | `backend/src/rules/` | 3.5 KB | Port threshold configs |
| **Graph Loader + Schema** | `backend/src/engines/graph/` | 11 KB | Port Neo4j → Drizzle relations |
| **Graph Queries** | `backend/src/graph/queries.py` | 5.4 KB | Rewrite Cypher → SQL |
| **Seed Loader** | `backend/seeds/loader.py` | 16 KB | Port to TS seed script |
| **Scenario Seeds** | `backend/seeds/scenario_seeds.py` | 37 KB | Port to TS |
| **GCC Physics Config** | `backend/app/intelligence/physics/gcc_physics_config.py` | 15 KB | Port config to TS |
| **CesiumJS Globe** | `frontend/src/components/globe/cesium-globe.tsx` | 5 KB | Keep React — update styling |
| **deck.gl Overlay** | `frontend/src/components/globe/deckgl-overlay.tsx` | 4.4 KB | Keep React — update styling |
| **KPICard** | `frontend/src/components/KPICard.tsx` | 2.8 KB | Restyle to white/executive |
| **StressGauge** | `frontend/src/components/StressGauge.tsx` | 4.9 KB | Restyle to white/executive |
| **DecisionActionCard** | `frontend/src/components/DecisionActionCard.tsx` | 6.2 KB | Restyle to white/executive |
| **FinancialImpactPanel** | `frontend/src/components/FinancialImpactPanel.tsx` | 7.5 KB | Restyle to white/executive |
| **Store** | `frontend/src/store/app-store.ts` | 3.6 KB | Port Zustand shape |
| **Design Tokens** | `frontend/src/theme/tokens.ts` | 2 KB | Restyle white/light palette |
| **Tailwind Config** | `frontend/tailwind.config.ts` | 4.5 KB | Update to executive theme |

### REMOVE — Dead code, duplicates, legacy branding

| File/Module | Size | Reason |
|---|---|---|
| `backend/app/main.py` | 8 KB | **Dual entrypoint conflict** — remove, keep `src/main.py` as canonical reference |
| `backend/app/api/scores.py` | 36 KB | Legacy scoring endpoint — replaced by v4 pipeline |
| `backend/app/api/decision.py` | 41 KB | Legacy decision API — superseded by v4 §8 |
| `backend/app/api/insurance.py` | 29 KB | Legacy insurance API — superseded by v4 |
| `backend/app/api/incidents.py` | 15 KB | Legacy incidents — not in v4 scope |
| `backend/app/api/models.py` | 17 KB | Legacy model admin — not production |
| `backend/app/scenarios/templates.py` | 25 KB | Superseded by `packages/@deevo/gcc-knowledge-graph/src/scenarios.ts` |
| `backend/app/scenarios/runner.py` | 20 KB | Superseded by `src/engines/scenario_engine/runner.py` |
| `backend/app/scenarios/engine.py` | 13 KB | Superseded by `src/engines/scenario/engine.py` |
| `backend/app/services/orchestrator.py` | 40 KB | Legacy orchestrator — replaced by pipeline.py/pipeline_v4.py |
| `backend/app/intelligence/engines/scenario_engines.py` | 46 KB | Mega-file — logic absorbed into `src/engines/` |
| `backend/app/intelligence/math/propagation.py` | 5 KB | Duplicate of `src/engines/math/propagation.py` |
| `backend/app/intelligence/physics/__init__.py` | 3 KB | Duplicate of `src/engines/physics/` |
| `backend/app/intelligence/insurance/__init__.py` | 3.2 KB | Duplicate of `src/engines/insurance_intelligence/` |
| `backend/app/db/models.py` | 27 KB | Legacy ORM — replaced by Drizzle schema |
| `backend/app/db/neo4j.py` | 3.4 KB | Neo4j client — not in Hud Hud stack |
| `backend/app/schemas/observatory.py` | 25 KB | Duplicate of type contracts in frontend |
| `backend/app/config/settings.py` | 2.4 KB | Legacy Pydantic settings |
| `backend/app/connectors/osm/` | 10 KB | OSM connector — not in v4 scope |
| `backend/app/simulation/__init__.py` | 0.8 KB | Empty/stub simulation module |
| `backend/app/decision/__init__.py` | 0.3 KB | Empty decision module |
| `backend/seeds/airports.py` | 25 KB | Aviation data — not in v4 financial scope |
| `backend/seeds/flights.py` | 28 KB | Flight data — not in v4 financial scope |
| `backend/seeds/vessels.py` | 23 KB | Vessel data — not in v4 financial scope |
| `backend/seeds/corridors.py` | 15 KB | Corridor data — replaced by GCC graph |
| `backend/seeds/ports.py` | 17 KB | Port data — replaced by GCC graph |
| `backend/seeds/events.py` | 34 KB | ACLED events — replaced by scenario triggers |
| `backend/seeds/actors.py` | 12 KB | Actor data — not in v4 scope |
| `backend/src/connectors/` | 12 KB | Maritime/flight/conflict adapters — not in v4 |
| `backend/src/api/routes/flights.py` | 12 KB | Flight CRUD — not in v4 |
| `backend/src/api/routes/vessels.py` | 13 KB | Vessel CRUD — not in v4 |
| `backend/src/api/routes/events.py` | 1.3 KB | Events CRUD — not in v4 |
| `backend/src/api/routes/conflicts.py` | 2.5 KB | Conflicts — not in v4 |
| `frontend/app/demo/page.tsx` | 124 KB | **Legacy demo page** — massive, dark-themed, old branding |
| `frontend/app/dashboard/page.tsx` | 46 KB | Legacy dashboard — dark/cyber theme |
| `frontend/app/page.tsx` | 12 KB | Legacy landing — old branding |
| `frontend/app/scenarios/page.tsx` | 7.7 KB | Legacy scenario page — rebuild |
| `frontend/app/control-room/layout.tsx` | 0.5 KB | Legacy layout |
| `frontend/components/ui/Navbar.tsx` | 5 KB | Legacy dark nav bar |
| `frontend/components/ui/Footer.tsx` | 2 KB | Legacy dark footer |
| `frontend/components/graph/GraphPanel.tsx` | 16 KB | Legacy graph panel — dark theme |
| `frontend/lib/decision-engine.ts` | 29 KB | Client-side decision engine — moves to backend |
| `frontend/lib/mock-data.ts` | 25 KB | Mock data — replaced by real API |
| `frontend/lib/simulation-engine.ts` | 11 KB | Client-side sim — moves to backend |
| `frontend/lib/server/` | 20 KB | Next.js server functions — not in new stack |
| `frontend/middleware.ts` | 2 KB | Next.js middleware — not needed |
| `frontend/styles/globals.css` | 5.4 KB | Legacy dark CSS |
| `frontend/src/theme/globals.css` | 3.6 KB | Legacy dark CSS |
| `Dockerfile.backend` | 0.6 KB | Duplicate of backend/Dockerfile |
| `AUDIT_REPORT.md` | 27 KB | Generated report — regenerate |
| `MASTER_ANALYSIS_v4.md` | 39 KB | Analysis doc — archive |
| `GAP_ANALYSIS.html` | 31 KB | Gap analysis — archive |
| `REPLATFORMING_GAP_ANALYSIS.html` | 34 KB | Gap analysis — archive |
| `Procfile` | 76 B | Heroku leftover |

### REPLACE — New implementation required

| Component | Replaces | New Tech |
|---|---|---|
| Express + tRPC server | `backend/src/main.py` (FastAPI) | TypeScript, Express, tRPC |
| Drizzle ORM schema | `backend/app/db/models.py` + `src/models/orm.py` | Drizzle + drizzle-kit |
| Zod validation schemas | `backend/app/domain/models/` + `src/schemas/` | Zod (matches v4 contracts) |
| Manus OAuth | `backend/app/core/security.py` (dev-mode stub) | Manus template auth |
| React 19 + Vite frontend | `frontend/` (Next.js 15) | React 19, Vite, React Router |
| Vitest test suite | `backend/tests/` (Pytest) | Vitest (full stack) |
| White/executive UI | Dark/cyber theme | Light boardroom design system |

---

## 3. PRODUCT RENAME PLAN

### Brand Identity

| Property | Old Value | New Value |
|---|---|---|
| Product name (EN) | Deevo-Sim / Impact Observatory | **Impact Observatory** |
| Product name (AR) | — | **مرصد الأثر** |
| Tagline (EN) | — | Decision Intelligence for GCC Financial Markets |
| Tagline (AR) | — | الذكاء القراري للأسواق المالية الخليجية |
| Package scope | `@deevo/` | `@deevo/` (keep — internal infra package) |
| Repository | `deevo-sim` | Rename when ready, keep `deevo-sim` for now |

### Files requiring rename/rebrand

| File | Change |
|---|---|
| `README.md` | Rewrite — Impact Observatory identity |
| `config/project.yml` | Update product name, tagline, branding |
| `docker-compose.yml` | Service names stay technical |
| `Makefile` | Update help text to "Impact Observatory" |
| `.env.example` | Update app_name references |
| `backend/.env.example` | Update DC7_ prefix → IO_ prefix |
| `frontend/package.json` | Update name to `@deevo/impact-observatory-web` |
| `frontend/src/app/layout.tsx` | Update metadata title/description |
| `frontend/lib/i18n.ts` | Already has "Impact Observatory" labels |
| `nginx/nginx.conf` | Update server_name if needed |
| `railway.toml` | No brand references |
| `.github/workflows/ci.yml` | Update job names |

### String replacements (grep targets)

| Pattern | Replacement | Files affected |
|---|---|---|
| `Deevo` (visible branding) | `Impact Observatory` | README, config, UI strings |
| `deevo-sim` (visible branding) | `impact-observatory` | README, package.json names |
| `Impact Observatory` (already correct) | Keep | Most backend/frontend already use this |
| `مرصد الأثر` (already correct) | Keep | Makefile, i18n labels |

---

## 4. FRONTEND REPLACEMENT PLAN

### Architecture: Next.js 15 (App Router) → React 19 + Vite (SPA)

### Theme: Dark/Cyber → White/Light Executive Boardroom

### Pages (v4 §20 blueprint)

| Route | Page | Status | Source of truth |
|---|---|---|---|
| `/` | Landing → redirect to `/dashboard` | NEW | Simple redirect |
| `/dashboard` | Executive Dashboard Home | REPLACE | v4 §20.2 — portfolio overview |
| `/runs/:runId/risk-map` | Network Risk Map | REPLACE | v4 §20.3 — 24%/52%/24% layout |
| `/runs/:runId/decision` | Decision Panel | REPLACE | v4 §20.4 — ranked actions + narrative |
| `/runs/:runId/financial-impact` | Financial Impact | REPLACE | v4 §20.5 — loss charts + entity grid |
| `/runs/:runId/regulatory-status` | Regulatory Status | REPLACE | v4 §20.6 — breach timeline |
| `/runs/:runId/timeline` | Timeline Playback | NEW | v4 §17 — timestep scrubber |
| `/runs/:runId/compliance-reports` | Compliance Reports | NEW | v4 §21 — regulatory mode |
| `/scenarios` | Scenario Library | REPLACE | Arabic catalog + create flow |

### Component migration

| Component | Action | Notes |
|---|---|---|
| `cesium-globe.tsx` | PORT | Keep React component, update container styling |
| `deckgl-overlay.tsx` | PORT | Keep layer configs, update colors |
| `KPICard.tsx` | RESTYLE | White background, navy accent, no dark gradient |
| `StressGauge.tsx` | RESTYLE | Executive palette, no neon/cyber colors |
| `DecisionActionCard.tsx` | RESTYLE | White card, subtle shadow, ranked numbering |
| `FinancialImpactPanel.tsx` | RESTYLE | Light charts, Recharts with executive palette |
| `BankingDetailPanel.tsx` | RESTYLE | White/light executive |
| `InsuranceDetailPanel.tsx` | RESTYLE | White/light executive |
| `FintechDetailPanel.tsx` | RESTYLE | White/light executive |
| `DecisionDetailPanel.tsx` | RESTYLE | White/light executive |
| `ExecutiveDashboard.tsx` | RESTYLE | White/light executive |
| `ErrorBoundary.tsx` | PORT | As-is |
| `Navbar.tsx` | REPLACE | New white executive nav with Arabic-first |
| `Footer.tsx` | REPLACE | Minimal executive footer |
| `GraphPanel.tsx` | REPLACE | New force/hierarchical graph per v4 §20.3 |

### Design system changes

| Token | Old | New |
|---|---|---|
| Background | `#0a0a0a` / `#1a1a2e` | `#FAFBFC` / `#FFFFFF` |
| Card surface | `#16213e` / `#1a1a2e` | `#FFFFFF` |
| Primary accent | `#00d4ff` / neon blue | `#1A365D` (navy) |
| Secondary | `#7c3aed` / purple neon | `#2B6CB0` (blue) |
| Text primary | `#ffffff` | `#1A202C` |
| Text muted | `#94a3b8` | `#718096` |
| Success | `#00ff88` / neon green | `#38A169` |
| Warning | `#ffaa00` / neon amber | `#D69E2E` |
| Danger | `#ff4444` / neon red | `#E53E3E` |
| Border | `rgba(255,255,255,0.1)` | `#E2E8F0` |
| Shadow | none / glow | `0 1px 3px rgba(0,0,0,0.08)` |
| Font EN | Mono / tech | DM Sans |
| Font AR | — | IBM Plex Sans Arabic |
| Border radius | sharp / 4px | 8px / 12px (softer) |

### Dependency changes

| Remove | Add | Reason |
|---|---|---|
| `next` 15.0.0 | `vite` + `@vitejs/plugin-react` | SPA build |
| — | `react-router-dom` | Client routing |
| — | `@trpc/client` + `@trpc/react-query` | tRPC integration |
| — | `zod` | Runtime validation |
| Keep `cesium` 1.123.0 | — | Globe visualization |
| Keep `resium` 1.18.0 | — | React CesiumJS bindings |
| Keep `@deck.gl/*` 9.0.0 | — | Overlay layers |
| Keep `recharts` 2.13.0 | — | Financial charts |
| Keep `zustand` 5.0.0 | — | State management |
| Keep `framer-motion` | — | Transitions |
| Keep `lucide-react` | — | Icons |
| Keep `@tanstack/react-query` | — | Data fetching (behind tRPC) |
| Keep `tailwindcss` | Upgrade to 4.x | CSS framework |

---

## AWAITING NEXT COMMAND

Matrix complete. Ready to execute:
- Step 1: Product rename
- Step 2: Frontend replacement
- Step 3: Dashboard restructuring
- Or any other directed action.
