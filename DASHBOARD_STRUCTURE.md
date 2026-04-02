# Dashboard Structure — Step 4 (LOCKED)

**Date:** 2026-04-02
**Route:** `/dashboard`
**Layout:** Tab-based single-page dashboard shell
**Design:** White/light, boardroom executive, `bg-io-bg` / `bg-io-surface`

---

## 1. Exact Page Structure

```
/dashboard
│
├── DashboardHeader
│   ├── Brand mark (IO logo + "Impact Observatory" / "مرصد الأثر")
│   ├── Scenario label + severity badge
│   ├── Language toggle (EN ↔ AR)
│   ├── Mode toggle (Executive | Analyst | Regulator)
│   └── Run Scenario button
│
├── TabBar
│   ├── Overview        (default)
│   ├── Banking
│   ├── Insurance
│   ├── Fintech
│   ├── Decisions
│   ├── Timeline
│   ├── Graph           (secondary)
│   ├── Map             (secondary)
│   └── Regulatory
│
└── TabContent (renders based on active tab)
    │
    ├── [Overview]
    │   ├── TopSummary (6 KPI cards — single horizontal row)
    │   │   ├── Headline Loss
    │   │   ├── Peak Day
    │   │   ├── Time to First Failure
    │   │   ├── Business Severity
    │   │   ├── Executive Status
    │   │   └── Affected Entities
    │   │
    │   ├── CorePanels (2-column grid)
    │   │   ├── LEFT (60%):  FinancialImpactPanel
    │   │   └── RIGHT (40%): StressGauge × 3 (Banking + Insurance + Fintech)
    │   │
    │   └── DecisionActions (3 cards in a row)
    │       ├── DecisionActionCard rank=1
    │       ├── DecisionActionCard rank=2
    │       └── DecisionActionCard rank=3
    │
    ├── [Banking]
    │   └── BankingDetailPanel (full width)
    │
    ├── [Insurance]
    │   └── InsuranceDetailPanel (full width)
    │
    ├── [Fintech]
    │   └── FintechDetailPanel (full width)
    │
    ├── [Decisions]
    │   ├── DecisionDetailPanel (top 70%)
    │   └── ExplanationPanel (bottom 30%)
    │
    ├── [Timeline]
    │   ├── BusinessImpactTimeline (top 50%)
    │   └── RegulatoryBreachTimeline (bottom 50%)
    │
    ├── [Graph]
    │   └── EntityGraphPanel (contained, max-height 700px)
    │
    ├── [Map]
    │   └── GlobeWrapper (contained, max-height 600px, bg-io-primary)
    │
    └── [Regulatory]
        ├── RegulatoryNotes (top 60%)
        └── AnalystTrace (bottom 40%)
```

---

## 2. Complete Component List

### Shell Components (NEW — to build)

| # | Component | File | Responsibility |
|---|-----------|------|---------------|
| 1 | `DashboardShell` | `src/app/dashboard/page.tsx` | Page-level orchestrator: fetches RunResult, manages active tab, passes data to children |
| 2 | `DashboardHeader` | `src/components/shell/DashboardHeader.tsx` | Top bar: brand, scenario info, language/mode toggles, run button |
| 3 | `TabBar` | `src/components/shell/TabBar.tsx` | Horizontal tab navigation with active state, scrollable on mobile |

### Top Summary Components (REUSE existing)

| # | Component | File | Responsibility |
|---|-----------|------|---------------|
| 4 | `KPICard` | `src/components/KPICard.tsx` | Single metric card with label, value, severity coloring, trend arrow, RTL border |

**6 KPI instances in TopSummary:**

| Position | Metric | Data Source | Severity Logic |
|----------|--------|------------|----------------|
| 1 | Headline Loss | `headline.total_loss_usd` | `>$5B` = critical, `>$2B` = severe, `>$1B` = high |
| 2 | Peak Day | `headline.peak_day` / `horizon_days` | Always "normal" |
| 3 | Time to First Failure | `min(banking.time_to_liquidity_breach_hours, insurance.time_to_claims_failure_hours, fintech.time_to_payment_failure_hours)` | `<72h` = critical, `<168h` = severe |
| 4 | Business Severity | `headline.severity_code` | Derived from scenario severity float |
| 5 | Executive Status | `computeStatus(headline, banking, insurance, fintech)` | Composite: any CRITICAL sector → CRITICAL |
| 6 | Affected Entities | `headline.affected_entities` | `>20` = high, `>10` = medium |

### Core Panels (REUSE existing)

| # | Component | File | Responsibility |
|---|-----------|------|---------------|
| 5 | `FinancialImpactPanel` | `src/components/FinancialImpactPanel.tsx` | Loss headline, sector exposure bars, propagation summary, severity badge |
| 6 | `StressGauge` | `src/components/StressGauge.tsx` | SVG arc gauge for banking/insurance/fintech score with classification badge |
| 7 | `DecisionActionCard` | `src/components/DecisionActionCard.tsx` | Ranked action card: priority score, cost, loss avoided, human-in-the-loop button |

### Detail Panels (REUSE existing)

| # | Component | File | Responsibility |
|---|-----------|------|---------------|
| 8 | `BankingDetailPanel` | `src/features/banking/BankingDetailPanel.tsx` | Full banking stress breakdown: CAR, liquidity gap, interbank rate, FX reserves |
| 9 | `InsuranceDetailPanel` | `src/features/insurance/InsuranceDetailPanel.tsx` | Insurance stress: combined ratio, claims surge, reinsurance trigger, lines affected |
| 10 | `FintechDetailPanel` | `src/features/fintech/FintechDetailPanel.tsx` | Fintech stress: payment volume, settlement delays, API availability |
| 11 | `DecisionDetailPanel` | `src/features/decisions/DecisionDetailPanel.tsx` | All decision actions with filtering + explanation narrative |

### Timeline Components (NEW — to build)

| # | Component | File | Responsibility |
|---|-----------|------|---------------|
| 12 | `BusinessImpactTimeline` | `src/components/timeline/BusinessImpactTimeline.tsx` | Recharts area chart: cumulative loss over time (LossTrajectoryPoint[]), day markers, breach annotations |
| 13 | `RegulatoryBreachTimeline` | `src/components/timeline/RegulatoryBreachTimeline.tsx` | Vertical timeline: breach events with severity, agency, timestamp, threshold violated |

### Secondary Panels (REFACTOR existing + NEW)

| # | Component | File | Responsibility |
|---|-----------|------|---------------|
| 14 | `EntityGraphPanel` | `src/components/graph/EntityGraphPanel.tsx` | Force-directed SVG graph (extracted from `graph-explorer/page.tsx`), sector filter, search, node click → entity detail |
| 15 | `GlobeWrapper` | `src/components/globe/index.tsx` | CesiumJS globe with event/flight/vessel layers, contained to bounded height |
| 16 | `ExplanationPanel` | `src/components/panels/ExplanationPanel.tsx` | 20-step causal chain: CauseEffectLink list with icons, sector tags, loss translation |
| 17 | `RegulatoryNotes` | `src/components/panels/RegulatoryNotes.tsx` | Table view: audit log entries with stage, event_type, timestamp, payload preview |
| 18 | `AnalystTrace` | `src/components/panels/AnalystTrace.tsx` | Pipeline stage cards: stage name, duration_ms, input/output hash (SHA-256), status |
| 19 | `FlowRouteView` | `src/components/panels/FlowRouteView.tsx` | (Inside Map tab alongside GlobeWrapper) Simplified trade flow lines on a static map |

### Supporting (REUSE existing)

| # | Component | File | Responsibility |
|---|-----------|------|---------------|
| 20 | `ExecutiveDashboard` | `src/features/dashboard/ExecutiveDashboard.tsx` | **Reuse as the Overview tab renderer** — already has MetricCard grid + SectorStressCard + Decision row |
| 21 | `ErrorBoundary` | `src/components/ErrorBoundary.tsx` | Catch render errors per tab |
| 22 | `Providers` | `src/components/shared/providers.tsx` | TanStack Query + Zustand provider |

---

## 3. Component Responsibilities (Detailed)

### `DashboardShell` (orchestrator)
- Reads `run_id` from URL search params or Zustand store
- Fetches `RunResult` via `POST /api/v1/runs` or `GET /api/v1/runs/{id}`
- Manages `activeTab` state
- Passes `data: RunResult` + `lang: Language` to all child panels
- Shows loading skeleton while fetching
- Shows error state if pipeline unavailable

### `DashboardHeader`
- **Left:** IO logo + product name (bilingual)
- **Center:** Scenario label + severity badge + horizon
- **Right:** Language toggle, mode toggle (Executive/Analyst/Regulator), "Run Scenario" button
- Mode toggle changes which KPIs and panels are visible (Executive = summary, Analyst = all + trace, Regulator = compliance focus)

### `TabBar`
- Horizontal scrollable tabs
- Active tab: `border-b-2 border-io-accent text-io-accent`
- Inactive: `text-io-secondary hover:text-io-primary`
- Secondary tabs (Graph, Map, Regulatory) visually grouped with a separator
- Tab labels are bilingual (see Section 4)

### `BusinessImpactTimeline`
- **Input:** `LossTrajectoryPoint[]` — `{ day: number, cumulative_loss_usd: number, daily_delta_usd: number }`
- **Render:** Recharts AreaChart with dual Y-axis (cumulative on left, daily delta on right)
- **Annotations:** Vertical lines at peak day, breach points
- **Design:** `bg-io-surface rounded-xl border border-io-border p-5`

### `RegulatoryBreachTimeline`
- **Input:** `RegulatoryBreachEvent[]` — `{ timestamp: string, entity_id: string, threshold_name: string, threshold_value: number, actual_value: number, severity: string, agency: string }`
- **Render:** Vertical timeline with colored dots (red=critical, orange=elevated, yellow=moderate)
- **Design:** Scrollable list inside card container

### `ExplanationPanel`
- **Input:** `CauseEffectLink[]` — `{ step: number, cause: string, cause_ar: string, effect: string, effect_ar: string, sector: string, loss_usd: number }`
- **Render:** Numbered step list with arrow connectors, sector badge, loss amount
- **Design:** Clean list, no neon, IO color palette only

### `RegulatoryNotes`
- **Input:** `AuditLogEntry[]` — `{ id: number, run_id: string, stage: string, event_type: string, payload: object, timestamp: string }`
- **Render:** Sortable table with expandable payload preview
- **Design:** Compact table inside card

### `AnalystTrace`
- **Input:** `PipelineStage[]` — `{ stage: string, status: string, duration_ms: number, input_hash: string, output_hash: string }`
- **Render:** Horizontal pipeline diagram or vertical card list showing each stage with timing
- **Design:** Monospace font for hashes, green/red status indicators

---

## 4. Arabic / English Label Requirements

### Tab Labels

| Tab ID | English | Arabic |
|--------|---------|--------|
| `overview` | Overview | نظرة عامة |
| `banking` | Banking | القطاع البنكي |
| `insurance` | Insurance | التأمين |
| `fintech` | Fintech | الفنتك |
| `decisions` | Decisions | القرارات |
| `timeline` | Timeline | الجدول الزمني |
| `graph` | Entity Graph | رسم الكيانات |
| `map` | Map View | عرض الخريطة |
| `regulatory` | Regulatory | الرقابة |

### Top Summary KPI Labels

| Metric | English | Arabic |
|--------|---------|--------|
| Headline Loss | Headline Loss | إجمالي الخسارة |
| Peak Day | Peak Impact Day | يوم ذروة الأثر |
| Time to First Failure | Time to First Failure | الوقت إلى أول انهيار |
| Business Severity | Business Severity | شدة الأعمال |
| Executive Status | Executive Status | الحالة التنفيذية |
| Affected Entities | Affected Entities | الكيانات المتأثرة |

### Core Panel Titles

| Panel | English | Arabic |
|-------|---------|--------|
| Financial Impact | Financial Impact | الأثر المالي |
| Banking Stress | Banking Stress | ضغط القطاع البنكي |
| Insurance Stress | Insurance Stress | ضغط التأمين |
| Fintech Stress | Fintech Disruption | اضطراب الفنتك |
| Decision Actions | Recommended Actions | الإجراءات المقترحة |
| Explanation | Causal Explanation | التفسير السببي |

### Timeline Labels

| Element | English | Arabic |
|---------|---------|--------|
| Business Impact Timeline | Business Impact Timeline | الجدول الزمني للأثر التجاري |
| Regulatory Breach Timeline | Regulatory Breach Timeline | الجدول الزمني لاختراق القواعد التنظيمية |
| Cumulative Loss | Cumulative Loss | الخسارة التراكمية |
| Daily Impact | Daily Impact | الأثر اليومي |
| Breach Event | Breach Event | حدث اختراق |
| Threshold | Threshold | الحد الأدنى |

### Secondary Panel Labels

| Panel | English | Arabic |
|-------|---------|--------|
| Entity Graph | Entity Graph | رسم الكيانات |
| Flow / Route View | Trade Flow Map | خريطة التدفق التجاري |
| Regulatory Notes | Regulatory & Audit | الرقابة والتدقيق |
| Analyst Trace | Pipeline Trace | تتبع المعالجة |
| Audit Log | Audit Log | سجل التدقيق |
| Pipeline Stage | Pipeline Stage | مرحلة المعالجة |
| Duration | Duration | المدة |
| Input Hash | Input Hash | بصمة المدخل |
| Output Hash | Output Hash | بصمة المخرج |

### Dashboard Header Labels

| Element | English | Arabic |
|---------|---------|--------|
| Product Name | Impact Observatory | مرصد الأثر |
| Subtitle | Decision Intelligence Platform | منصة ذكاء القرار |
| Run Scenario | Run Scenario | تشغيل السيناريو |
| Executive Mode | Executive | تنفيذي |
| Analyst Mode | Analyst | محلل |
| Regulator Mode | Regulator | رقابي |
| Language Toggle | العربية / English | العربية / English |
| Severity | Severity | الشدة |
| Horizon | Horizon | الأفق الزمني |
| Loading | Analyzing scenario... | جاري تحليل السيناريو... |
| Error | Pipeline unavailable | المعالجة غير متاحة |
| Retry | Retry | إعادة المحاولة |
| Back | Back | رجوع |

### Decision Action Labels

| Element | English | Arabic |
|---------|---------|--------|
| Priority | Priority | الأولوية |
| Urgency | Urgency | الإلحاح |
| Value | Value | القيمة |
| Cost | Cost | التكلفة |
| Loss Avoided | Loss Avoided | الخسائر المتجنبة |
| Time to Act | Time to Act | وقت التنفيذ |
| Owner | Owner | المسؤول |
| Submit for Review | Submit for Review | إرسال للمراجعة |
| Approved | Approved | معتمد |
| Pending Review | Pending Review | بانتظار المراجعة |
| Executing | Executing | قيد التنفيذ |

### Stress Classification Labels

| Level | English | Arabic |
|-------|---------|--------|
| CRITICAL | Critical | حرج |
| ELEVATED | Elevated | مرتفع |
| MODERATE | Moderate | معتدل |
| LOW | Low | منخفض |
| NOMINAL | Nominal | طبيعي |

---

## 5. Data Contract Summary

The dashboard receives a single `RunResult` object from `POST /api/v1/runs`:

```typescript
interface RunResult {
  run_id: string;
  scenario: { label: string; severity: number; horizon_hours: number; template_id: string };
  headline: { total_loss_usd: number; peak_day: number; severity_code: string; affected_entities: number; critical_count: number };
  financial: FinancialImpact[];
  banking: BankingStress;
  insurance: InsuranceStress;
  fintech: FintechStress;
  decisions: DecisionAction[];
  explanation: ExplanationStep[];
  // V4 extensions (P3):
  business_impact?: BusinessImpactSummary;
  loss_trajectory?: LossTrajectoryPoint[];
  regulatory_breaches?: RegulatoryBreachEvent[];
  pipeline_stages?: PipelineStage[];
  audit_log?: AuditLogEntry[];
}
```

All components consume slices of this object. No component fetches its own data — the `DashboardShell` is the single data source.

---

## 6. Decision Gate

This structure is **LOCKED**. Before implementing:

1. V2 `frontend/app/` dead code must be removed (Step 3, Phase 1)
2. `RunResult` type in `src/types/observatory.ts` must be extended with optional V4 fields (`loss_trajectory`, `regulatory_breaches`, `pipeline_stages`, `audit_log`)
3. Backend `POST /api/v1/runs` response must be verified to include all required fields for the Overview tab

Awaiting your command to begin execution.
