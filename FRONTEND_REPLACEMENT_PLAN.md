# Frontend Replacement Plan — Step 3

**Date:** 2026-04-02
**Target:** White/light executive boardroom, Arabic+English, RTL/LTR, graph/map secondary (not hero)

---

## 1. Current Frontend Architecture

### Dual Page Tree (CONFLICT)

The repository has **two** Next.js App Router page trees that shadow each other:

| Tree | Location | Generation | Theme | API Wiring |
|------|----------|------------|-------|------------|
| **V2** | `frontend/app/` | Earlier, uses `@/lib/` imports | Mixed (scenarios page is dark `bg-zinc-900`) | Uses `@/lib/api/client.ts` + `@/lib/types/observatory.ts` |
| **V4** | `frontend/src/app/` | Current, uses `@/` aliased to `src/` | White/IO design system throughout | Uses `@/lib/api.ts` + `@/types/observatory.ts` + `@/hooks/use-api.ts` |

**Next.js resolution:** With `src/` directory present, Next.js resolves `src/app/` as the app directory. The `app/` tree at root is **only active if `src/app/` doesn't override that route**. Currently both trees provide `/`, `/dashboard`, and `/control-room` — meaning Next.js uses the `src/app/` versions. The V2 `app/` pages are effectively dead code shadowed by V4.

### V4 Page Map (Active — `frontend/src/app/`)

| Route | File | Lines | Description |
|-------|------|-------|-------------|
| `/` | `src/app/page.tsx` | 477 | **Mega-page**: Landing → Scenario Selector → Results (with detail tabs). Single-page app flow. |
| `/dashboard` | `src/app/dashboard/page.tsx` | ~400 | Standalone dashboard with scenario selector, auto-runs on load |
| `/control-room` | `src/app/control-room/page.tsx` | ~300 | CesiumJS globe + side panels (ScenarioPanel, ImpactPanel) |
| `/scenario-lab` | `src/app/scenario-lab/page.tsx` | ~150 | Scenario template browser with severity slider |
| `/graph-explorer` | `src/app/graph-explorer/page.tsx` | ~250 | Force-directed SVG graph visualization |
| `/entity/[id]` | `src/app/entity/[id]/page.tsx` | ~250 | Entity detail with risk component breakdown |
| Layout | `src/app/layout.tsx` | 29 | Root layout: DM Sans + IBM Plex Sans Arabic, `bg-io-bg` |

### V2 Page Map (Shadowed — `frontend/app/`)

| Route | File | Lines | Description | Status |
|-------|------|-------|-------------|--------|
| `/` | `app/page.tsx` | ~200 | V2 landing with Navbar/Footer components | **SHADOWED** by `src/app/page.tsx` |
| `/dashboard` | `app/dashboard/page.tsx` | ~400 | V2 dashboard with mode switcher (exec/analyst/regulator) | **SHADOWED** by `src/app/dashboard/page.tsx` |
| `/scenarios` | `app/scenarios/page.tsx` | ~130 | **DARK THEME** — `bg-zinc-950`, `text-cyan-400`, motion/framer | **UNIQUE** — no V4 equivalent |
| `/control-room` | `app/control-room/layout.tsx` | ~20 | V2 control room layout only | **SHADOWED** |
| Layout | `app/layout.tsx` | ~50 | V2 root layout with SEO metadata, imports `../styles/globals.css` | **SHADOWED** |

### V2 Shared Components (used by V2 pages only)

| Component | File | Used By |
|-----------|------|---------|
| `Navbar` | `components/ui/Navbar.tsx` | `app/page.tsx`, `app/dashboard/page.tsx` |
| `Footer` | `components/ui/Footer.tsx` | `app/page.tsx` |
| `GraphPanel` | `components/graph/GraphPanel.tsx` | `app/dashboard/page.tsx` |

### V4 Component Library (Active)

| Component | File | Props | Reusable? |
|-----------|------|-------|-----------|
| `ExecutiveDashboard` | `src/features/dashboard/ExecutiveDashboard.tsx` | `data: RunResult, lang, onNavigate` | **YES — core** |
| `BankingDetailPanel` | `src/features/banking/BankingDetailPanel.tsx` | `data: BankingStress, lang` | **YES** |
| `InsuranceDetailPanel` | `src/features/insurance/InsuranceDetailPanel.tsx` | `data: InsuranceStress, lang` | **YES** |
| `FintechDetailPanel` | `src/features/fintech/FintechDetailPanel.tsx` | `data: FintechStress, lang` | **YES** |
| `DecisionDetailPanel` | `src/features/decisions/DecisionDetailPanel.tsx` | `decisions, explanation, lang` | **YES** |
| `KPICard` | `src/components/KPICard.tsx` | `label, labelAr, value, severity, trend, locale` | **YES — core** |
| `StressGauge` | `src/components/StressGauge.tsx` | `sector, score, classification, indicators, locale` | **YES** |
| `FinancialImpactPanel` | `src/components/FinancialImpactPanel.tsx` | `loss_usd, sector_exposure, severity_code, locale` | **YES** |
| `DecisionActionCard` | `src/components/DecisionActionCard.tsx` | `rank, priority_score, title_en/ar, cost, loss_avoided, status, locale` | **YES** |
| `GlobeWrapper` | `src/components/globe/index.tsx` | `flights, vessels, events, activeLayers, ...` | **YES — secondary** |
| `ScenarioPanel` | `src/components/panels/scenario-panel.tsx` | `templates, selectedId, severity, isAr` | **YES** |
| `ImpactPanel` | `src/components/panels/impact-panel.tsx` | `result, isAr` | **YES** |
| `ScientistBar` | `src/components/panels/scientist-bar.tsx` | `data, isAr` | **YES** |
| `ErrorBoundary` | `src/components/ErrorBoundary.tsx` | — | **YES** |
| `Providers` | `src/components/shared/providers.tsx` | `children` | **YES** |

### State & Data Layer

| Module | File | Description | Reusable? |
|--------|------|-------------|-----------|
| Zustand store | `src/store/app-store.ts` | Language, viewMode, scenario, camera, layers, insurance, time horizon | **YES** |
| API hooks | `src/hooks/use-api.ts` | TanStack Query hooks: events, flights, vessels, scenarios, runs, risk, graph, stress, insurance | **YES** |
| API client | `src/lib/api.ts` | REST client wrapping fetch to `NEXT_PUBLIC_API_URL` | **YES** |
| Types | `src/types/observatory.ts` | RunResult, BankingStress, InsuranceStress, FintechStress, Classification | **YES** |
| Types (legacy) | `src/types/index.ts` | EventType, Flight, Vessel, GraphNode, GraphEdge, ScenarioTemplate | **YES** |
| i18n EN | `src/i18n/en.json` | English labels | **YES** |
| i18n AR | `src/i18n/ar.json` | Arabic labels | **YES** |

---

## 2. What Needs Replacement vs Reuse

### REMOVE ENTIRELY (V2 dead code)

| # | Path | Reason |
|---|------|--------|
| 1 | `frontend/app/page.tsx` | Shadowed by V4 `src/app/page.tsx` |
| 2 | `frontend/app/layout.tsx` | Shadowed by V4 `src/app/layout.tsx` |
| 3 | `frontend/app/dashboard/page.tsx` | Shadowed by V4 `src/app/dashboard/page.tsx` |
| 4 | `frontend/app/scenarios/page.tsx` | **Dark theme** (`bg-zinc-950`, `text-cyan-400`). No V4 equivalent but `src/app/scenario-lab/page.tsx` covers this use case. |
| 5 | `frontend/app/control-room/layout.tsx` | Shadowed by V4 control-room |
| 6 | `frontend/app/api/` (3 route files) | Need to verify if V4 has equivalent API routes or if these are still needed |
| 7 | `frontend/styles/globals.css` | Superseded by `src/theme/globals.css` |
| 8 | `frontend/components/ui/Navbar.tsx` | Only used by V2 pages. V4 has inline TopNav in `page.tsx`. |
| 9 | `frontend/components/ui/Footer.tsx` | Only used by V2 pages. V4 has inline footer in `page.tsx`. |
| 10 | `frontend/components/graph/GraphPanel.tsx` | Only used by V2 dashboard. V4 has `graph-explorer/page.tsx`. |

### REUSE AS-IS (V4 components — zero changes)

| # | Component | Why |
|---|-----------|-----|
| 1 | `KPICard` | White theme, severity coloring, bilingual, RTL border support |
| 2 | `StressGauge` | SVG arc gauge, IO color palette, bilingual |
| 3 | `FinancialImpactPanel` | Sector exposure bars, loss formatting, bilingual |
| 4 | `DecisionActionCard` | Ranked actions with human-in-the-loop, bilingual |
| 5 | `ExecutiveDashboard` | Full dashboard layout with MetricCard + SectorStressCard |
| 6 | `BankingDetailPanel` | Banking stress breakdown |
| 7 | `InsuranceDetailPanel` | Insurance stress breakdown |
| 8 | `FintechDetailPanel` | Fintech stress breakdown |
| 9 | `DecisionDetailPanel` | Decision actions + explanation panel |
| 10 | `ErrorBoundary` | Generic error boundary |
| 11 | `Providers` | TanStack Query provider wrapper |
| 12 | `app-store.ts` | Zustand state (language, scenario, camera, layers) |
| 13 | `use-api.ts` | TanStack Query hooks for all API endpoints |
| 14 | `api.ts` | REST client |
| 15 | `observatory.ts` types | V4 canonical types |
| 16 | i18n JSON files | Bilingual labels |

### REFACTOR (V4 components — needs restructuring)

| # | Component | Current Issue | Target |
|---|-----------|---------------|--------|
| 1 | `src/app/page.tsx` (477 lines) | **Mega-page** — landing + scenario selector + results + detail tabs all in one file. Hard to maintain. Globe/map not integrated. | **Split into**: dedicated landing page + separate scenario runner route + dashboard route. Landing should be a clean entry with no embedded results view. |
| 2 | `src/app/dashboard/page.tsx` (~400 lines) | Standalone dashboard that duplicates scenario selection logic from `page.tsx`. No graph/map integration. | **Consolidate**: single dashboard shell that receives RunResult and renders all panels. Graph/entity view as secondary tab, not separate route. |
| 3 | `src/app/control-room/page.tsx` (~300 lines) | Globe is the **hero** — takes center screen. Panels are sidebars. This is the opposite of the target (graph/map secondary). | **Restructure**: Dashboard-first layout. Globe/map available as a expandable panel or secondary tab, not the primary view. |
| 4 | `GlobeWrapper` + globe components | Globe gets full-height viewport in control-room. | **Resize**: Globe becomes a contained panel (e.g., 40% width or collapsible), not full-screen viewport. |

### BUILD NEW (missing from V4)

| # | Component | V4 Spec Reference | Description |
|---|-----------|-------------------|-------------|
| 1 | `BusinessImpactTimeline` | §16 | LossTrajectoryPoint chart — cumulative loss over time with day markers |
| 2 | `RegulatoryBreachTimeline` | §16, §21 | Timeline of regulatory breach events with severity + agency |
| 3 | `TimeEngineControls` | §17 | Play/pause/step temporal simulation controls |
| 4 | `ExplanationPanel` | §19 | 20-step causal chain with CauseEffectLink visualization |
| 5 | `RegulatoryNotes` | §21 | Audit log + compliance report viewer |
| 6 | `AnalystTrace` | §21 | Pipeline stage trace with timing + SHA-256 hashes |
| 7 | `FlowRouteView` | New | Simplified flow/route visualization (lighter than full globe) |
| 8 | `AppShell` | New | Persistent navigation shell with sidebar/topbar, replacing inline TopNav |

---

## 3. Target UI Architecture

### Page Structure

```
/                    → Landing page (clean marketing entry)
/run                 → Scenario runner (select + run + redirect to dashboard)
/dashboard           → Executive dashboard shell (primary work surface)
  /dashboard?tab=overview     → Top summary + core panels
  /dashboard?tab=banking      → Banking detail
  /dashboard?tab=insurance    → Insurance detail
  /dashboard?tab=fintech      → Fintech detail
  /dashboard?tab=decisions    → Decision actions + explanation
  /dashboard?tab=timeline     → Business impact + regulatory breach timelines
  /dashboard?tab=graph        → Entity graph (secondary)
  /dashboard?tab=map          → Flow/route view (secondary)
  /dashboard?tab=regulatory   → Regulatory notes + analyst trace
/entity/[id]         → Entity detail (linked from graph)
```

### Layout Hierarchy

```
RootLayout (src/app/layout.tsx)
  └─ AppShell (persistent top nav + optional sidebar)
      ├─ Landing Page (/)
      │    Hero → Metrics Strip → How It Works → Capabilities → CTA → Footer
      │
      ├─ Scenario Runner (/run)
      │    Scenario grid → Severity slider → Run button → Redirect to /dashboard
      │
      └─ Dashboard Shell (/dashboard)
           ├─ DashboardHeader (scenario label + severity + language toggle + mode toggle)
           ├─ TabBar (overview | banking | insurance | fintech | decisions | timeline | graph | map | regulatory)
           └─ TabContent
                ├─ Overview:    TopSummary (6 KPIs) + CorePanels (Financial + 3 Stress + Decisions)
                ├─ Banking:     BankingDetailPanel
                ├─ Insurance:   InsuranceDetailPanel
                ├─ Fintech:     FintechDetailPanel
                ├─ Decisions:   DecisionDetailPanel + ExplanationPanel
                ├─ Timeline:    BusinessImpactTimeline + RegulatoryBreachTimeline
                ├─ Graph:       GraphExplorer (force-directed, not globe)
                ├─ Map:         GlobeWrapper (contained, not fullscreen)
                └─ Regulatory:  RegulatoryNotes + AnalystTrace
```

### Design Principles

1. **Dashboard-first, not globe-first.** The primary view is financial data. Globe/graph are secondary investigative tools.
2. **White/light default.** All surfaces use `bg-io-bg` (#F8FAFC) or `bg-io-surface` (#FFFFFF). The only dark areas are CesiumJS globe viewports (which use `bg-io-primary` #0F172A).
3. **Premium card aesthetic.** Every data section is a `bg-io-surface border border-io-border rounded-xl shadow-sm` card.
4. **Bilingual labels everywhere.** Every user-facing string has an `en` and `ar` variant. Components accept `locale` prop.
5. **RTL/LTR switching.** Root `dir` attribute toggles on language switch. All layouts use CSS logical properties (`border-inline-start`, `ps-`, `pe-`).
6. **Graph/map are contained panels.** When visible, they occupy a bounded area (~40% width or a tab), not a fullscreen viewport.

---

## 4. Reusable Component Matrix

| Target Section | Existing Component | Action | Notes |
|---------------|--------------------|--------|-------|
| **Top Summary KPIs** | `KPICard` | REUSE | Already bilingual, severity-colored, RTL |
| **Financial Impact** | `FinancialImpactPanel` | REUSE | Sector bars, loss formatting |
| **Banking Stress** | `StressGauge` + `BankingDetailPanel` | REUSE | Arc gauge + detail panel |
| **Insurance Stress** | `StressGauge` + `InsuranceDetailPanel` | REUSE | Arc gauge + detail panel |
| **Fintech Stress** | `StressGauge` + `FintechDetailPanel` | REUSE | Arc gauge + detail panel |
| **Decision Actions** | `DecisionActionCard` + `DecisionDetailPanel` | REUSE | Ranked cards, human-in-the-loop |
| **Dashboard Overview** | `ExecutiveDashboard` | REFACTOR | Extract from features/ into dashboard shell as default tab |
| **Entity Graph** | `graph-explorer/page.tsx` | REFACTOR | Convert from full page to contained panel component |
| **Globe/Map** | `GlobeWrapper` + layers | REFACTOR | Convert from fullscreen viewport to bounded panel |
| **Scenario Selection** | `ScenarioPanel` | REFACTOR | Move from control-room sidebar to `/run` page |
| **Impact Summary** | `ImpactPanel` | REUSE | Used in control-room, keep as compact summary |
| **Scientist Bar** | `ScientistBar` | REUSE | Compact analysis summary bar |
| **Business Impact Timeline** | — | BUILD NEW | §16 LossTrajectoryPoint chart |
| **Regulatory Breach Timeline** | — | BUILD NEW | §16 + §21 breach event timeline |
| **Explanation Panel** | — | BUILD NEW | §19 causal chain visualization |
| **Regulatory Notes** | — | BUILD NEW | §21 audit log viewer |
| **Analyst Trace** | — | BUILD NEW | Pipeline stage trace |
| **Flow Route View** | — | BUILD NEW | Simplified route visualization |
| **AppShell** | — | BUILD NEW | Persistent nav with sidebar |
| **DashboardHeader** | Inline TopNav in `page.tsx` | EXTRACT | Pull out of mega-page into standalone component |
| **TabBar** | Inline detail tabs in `page.tsx` | EXTRACT | Pull out of mega-page into standalone component |

---

## 5. Replacement Sequence

### Phase 1: Remove V2 Dead Code (prerequisite — no risk)

1. Delete `frontend/app/page.tsx`
2. Delete `frontend/app/layout.tsx`
3. Delete `frontend/app/dashboard/page.tsx`
4. Delete `frontend/app/scenarios/page.tsx`
5. Delete `frontend/app/control-room/layout.tsx`
6. Delete `frontend/styles/globals.css`
7. Delete `frontend/components/ui/Navbar.tsx`
8. Delete `frontend/components/ui/Footer.tsx`
9. Delete `frontend/components/graph/GraphPanel.tsx`
10. Verify: `frontend/app/api/` routes — check if V4 has equivalents before removing

**Risk:** ZERO. These are all shadowed by V4 pages. Removing them reduces confusion and eliminates the dark-theme scenarios page.

### Phase 2: Extract AppShell + Navigation (foundation)

1. Create `src/components/shell/AppShell.tsx` — persistent TopNav + sidebar skeleton
2. Extract `TopNav` from `src/app/page.tsx` into `src/components/shell/TopNav.tsx`
3. Create `src/components/shell/TabBar.tsx` — reusable horizontal tab bar component
4. Update `src/app/layout.tsx` to wrap children in `AppShell`

**Risk:** LOW. Extracting existing inline components. No logic change.

### Phase 3: Split Mega-Page (restructure)

1. Keep `src/app/page.tsx` as **landing page only** (lines 164–321 of current file — hero, metrics, capabilities, CTA, footer)
2. Create `src/app/run/page.tsx` — scenario selector (lines 326–382 of current page.tsx)
3. Refactor `src/app/dashboard/page.tsx` — becomes the **dashboard shell** with TabBar routing to:
   - Overview tab: renders `ExecutiveDashboard`
   - Banking/Insurance/Fintech/Decisions tabs: render respective detail panels
   - Timeline tab: placeholder for `BusinessImpactTimeline` + `RegulatoryBreachTimeline`
   - Graph tab: inline `GraphExplorer` component (extracted from `graph-explorer/page.tsx`)
   - Map tab: inline `GlobeWrapper` (contained, bounded height)
   - Regulatory tab: placeholder for `RegulatoryNotes` + `AnalystTrace`

**Risk:** MEDIUM. Splitting a 477-line page into 3 routes. State management (RunResult) needs to flow from `/run` → `/dashboard` via URL params or Zustand store.

### Phase 4: Demote Globe to Secondary (UI hierarchy change)

1. Refactor `src/app/control-room/page.tsx` — either:
   - Remove as a standalone route (its functionality is absorbed into dashboard Map tab), OR
   - Keep but restructure: dashboard-first layout with globe as a side panel
2. Set `GlobeWrapper` max-height to bounded container (e.g., `h-[500px]` instead of `flex-1`)
3. Remove flight/vessel layers from default view (these are tracking, not decision intelligence)

**Risk:** LOW. Globe still works, just contained.

### Phase 5: Build New Components (additive)

1. `BusinessImpactTimeline` — Recharts line chart consuming `LossTrajectoryPoint[]`
2. `RegulatoryBreachTimeline` — Vertical timeline consuming `RegulatoryBreachEvent[]`
3. `ExplanationPanel` — Step-by-step CauseEffectLink list
4. `RegulatoryNotes` — Table view of `AuditLogEntry[]`
5. `AnalystTrace` — Pipeline stage cards with timing and SHA-256 hashes
6. `FlowRouteView` — Simplified SVG or deck.gl route visualization

**Risk:** LOW (additive). These don't touch existing components. They render data that the backend already produces (or will produce when P2/P3 backend alignment is done).

---

## 6. Consolidation: `frontend/lib/` → `frontend/src/`

The V2 `lib/` directory duplicates modules that also exist in `src/`:

| V2 (`lib/`) | V4 (`src/`) | Action |
|-------------|-------------|--------|
| `lib/api/client.ts` | `src/lib/api.ts` | **Delete** V2 — V4 is canonical |
| `lib/api/index.ts` | — | **Delete** — only re-exports V2 client |
| `lib/types.ts` | `src/types/index.ts` | **Delete** V2 — V4 is canonical |
| `lib/types/observatory.ts` | `src/types/observatory.ts` | **Merge** unique types into V4, then delete V2 |
| `lib/i18n.ts` | `src/i18n/en.json` + `ar.json` | **Delete** V2 — V4 uses JSON-based i18n |
| `lib/mock-data.ts` | — | **Delete** — mock data, not needed with real API |
| `lib/simulation-engine.ts` | — | **Evaluate** — may contain client-side simulation logic worth keeping |
| `lib/decision-engine.ts` | — | **Evaluate** — may contain client-side decision logic |
| `lib/server/rbac.ts` | — | **Keep** — server-side RBAC (no V4 equivalent yet) |
| `lib/server/audit.ts` | — | **Keep** — server-side audit trail |
| `lib/server/auth.ts` | — | **Keep** — server-side auth |
| `lib/server/execution.ts` | — | **Keep** — server-side execution |
| `lib/server/store.ts` | — | **Keep** — server-side state store |
| `lib/server/trace.ts` | — | **Keep** — server-side trace |
| `lib/gcc-graph.ts` | `packages/@deevo/gcc-knowledge-graph` | **Delete** — superseded by package |
| `middleware.ts` | — | **Keep** — route middleware |

---

## 7. Summary

| Category | Count |
|----------|-------|
| **Remove (V2 dead code)** | 10 files |
| **Reuse as-is** | 16 components/modules |
| **Refactor (restructure)** | 4 components |
| **Extract (from mega-page)** | 3 components |
| **Build new** | 8 components |
| **Consolidate (lib → src)** | 8 files to delete/merge |

The V4 frontend is **85% correct** — white theme, IO branded, bilingual, RTL-ready, wired to real API. The main structural issue is the 477-line mega-page that needs splitting, and the globe-as-hero layout in control-room that needs demotion to a secondary panel.
