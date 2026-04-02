# Business Impact + Time Layer Plan — Step 7 (LOCKED)

**Date:** 2026-04-02
**V4 Spec:** §16 (Business Impact), §17 (Time Engine), §19 (Executive Explanation)
**Goal:** Loss trajectory, time-to-failure, regulatory breach timeline, severity/status mapping — end-to-end from backend service through API to UI panel

---

## 1. Layer Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                    V4 Pipeline (9 stages)                    │
│  Scenario → Physics → Graph → Propagation → Financial →     │
│  Sector Risk → Regulatory → Decision → Explanation          │
└─────────────────────┬───────────────────────────────────────┘
                      │ All stage outputs feed into:
                      ▼
┌─────────────────────────────────────────────────────────────┐
│              POST-PIPELINE LAYER (§16 + §17)                │
│                                                             │
│  ┌──────────────────────┐  ┌──────────────────────────────┐ │
│  │ business_impact_svc  │  │ time_engine_svc (§17)        │ │
│  │ (§16)                │  │                              │ │
│  │                      │  │ Input: Scenario, FlowState[] │ │
│  │ Input: All impacts   │  │ Output:                      │ │
│  │ Output:              │  │  - TimeStepState[]           │ │
│  │  - LossTrajectory[]  │  │  - EntityTemporalImpact[]    │ │
│  │  - TimeToFailure[]   │  │                              │ │
│  │  - BreachEvents[]    │  │ Shock decay:                 │ │
│  │  - BizImpactSummary  │  │ S(t) = S₀ × (1-d)^t         │ │
│  │  - ExecutiveExpl     │  └──────────────────────────────┘ │
│  └──────────────────────┘                                   │
└─────────────────────┬───────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────────┐
│                    API LAYER                                 │
│  GET /runs/{id}/business-impact                             │
│  GET /runs/{id}/timeline                                    │
│  GET /runs/{id}/regulatory-timeline                         │
│  GET /runs/{id}/executive-explanation                       │
└─────────────────────┬───────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────────┐
│                    UI LAYER                                  │
│  Dashboard Tab: Timeline                                    │
│   ├── BusinessImpactTimeline (Recharts AreaChart)           │
│   └── RegulatoryBreachTimeline (vertical event list)        │
│  Dashboard Tab: Overview                                    │
│   ├── KPICard: Time to First Failure                        │
│   ├── KPICard: Business Severity                            │
│   └── KPICard: Executive Status                             │
│  Dashboard Tab: Regulatory                                  │
│   ├── RegulatoryNotes (audit log table)                     │
│   └── AnalystTrace (pipeline stage cards)                   │
└─────────────────────────────────────────────────────────────┘
```

---

## 2. Required Services

### 2.1 `services/business_impact/engine.py` (EXISTS — ~250 lines)

**Current state:** Functional. Computes cascading impacts across sectors, generates loss trajectory, time-to-failure predictions, and regulatory breach events.

**Input contract:**

```python
async def compute_business_impact(
    run_id: str,
    scenario: Scenario,
    financial: list[FinancialImpact],
    banking: list[BankingStress],
    insurance: list[InsuranceStress],
    fintech: list[FintechStress],
    regulatory: RegulatoryState,
) -> BusinessImpactResult
```

**Output contract:**

```python
@dataclass
class BusinessImpactResult:
    summary: BusinessImpactSummary           # §16.3.1
    loss_trajectory: list[LossTrajectoryPoint]  # §16.2.1
    time_to_failures: list[TimeToFailure]       # §16.2.2
    breach_events: list[RegulatoryBreachEvent]  # §16.2.3
    executive_explanation: ExecutiveDecisionExplanation  # §19.1.1
```

**Sub-computations:**

| Function | Formula | Output |
|----------|---------|--------|
| `compute_loss_trajectory()` | Per-timestep: `direct_loss + propagated_loss = cumulative_loss`. Velocity = Δloss/Δt. Acceleration = Δvelocity/Δt. | `LossTrajectoryPoint[]` at system, sector, and entity scope |
| `compute_time_to_failure()` | Linear extrapolation from current rate: `t_fail = (threshold - current) / rate_of_change`. 5 failure types. | `TimeToFailure[]` per entity and failure type |
| `detect_breach_events()` | Scan each timestep for metric crossing threshold. 8 metric types × all entities. | `RegulatoryBreachEvent[]` with `first_breach` flag |
| `compute_summary()` | Aggregate: peak loss, peak timestep, first failure, breach counts, severity, status. | `BusinessImpactSummary` |
| `generate_executive_explanation()` | Cause-effect chain + loss translation + action explanations + board/regulator messages. | `ExecutiveDecisionExplanation` |

### 2.2 `services/time_engine/engine.py` (EXISTS — ~200 lines)

**Current state:** Functional. Simulates timestep-by-timestep entity state evolution with shock decay.

**Input contract:**

```python
async def simulate_timeline(
    run_id: str,
    scenario: Scenario,
    flow_states: list[FlowState],
    financial: list[FinancialImpact],
) -> list[TimeStepState]
```

**Core formula:**
```
ShockEffective(t) = ShockIntensity × (1 - shock_decay_rate)^t
```

**Output:** `TimeStepState[]` — one per timestep, each containing:
- `shock_intensity_effective` (decayed shock at this step)
- `entity_impacts: EntityTemporalImpact[]` (per-entity impact, flow, loss, delta, status)
- `aggregate_loss`, `aggregate_flow`, `regulatory_breach_count`, `system_status`

### 2.3 `services/reporting/engine.py` (EXISTS — ~200 lines)

Consumes business impact outputs to generate three report modes. No changes needed for this layer.

---

## 3. Required Domain Models (All Exist in `backend/app/domain/models/business_impact.py` + `time_engine.py`)

### 3.1 Loss Trajectory — `LossTrajectoryPoint` (§16.2.1)

```python
class LossTrajectoryPoint(BaseModel):
    run_id: str                    # UUIDv7 run reference
    scope_level: "entity"|"sector"|"system"
    scope_ref: str                 # Entity UUID, sector name, or "system"
    timestep_index: int            # 0-based
    timestamp: str                 # ISO-8601 UTC
    direct_loss: float             # Direct loss at this timestep
    propagated_loss: float         # Propagated loss at this timestep
    cumulative_loss: float         # Sum of all losses to date
    revenue_at_risk: float         # Revenue at risk
    loss_velocity: float           # dL/dt (rate of change per step)
    loss_acceleration: float       # d²L/dt² (acceleration per step²)
    status: "stable"|"deteriorating"|"critical"|"failed"
```

**Computation:** For each timestep `t` and each scope (system, sector, entity):
```
direct_loss(t) = Σ [entity.exposure × shock_effective(t) × propagation_factor(t)]
propagated_loss(t) = Σ [contagion from neighboring entities via transmission coefficients]
cumulative_loss(t) = cumulative_loss(t-1) + direct_loss(t) + propagated_loss(t)
loss_velocity(t) = cumulative_loss(t) - cumulative_loss(t-1)
loss_acceleration(t) = loss_velocity(t) - loss_velocity(t-1)
status(t) = classify(cumulative_loss(t), thresholds)
```

### 3.2 Time to Failure — `TimeToFailure` (§16.2.2)

```python
class TimeToFailure(BaseModel):
    run_id: str
    scope_level: "entity"|"sector"|"system"
    scope_ref: str
    failure_type: "liquidity_failure"|"capital_failure"|"solvency_failure"|"availability_failure"|"regulatory_failure"
    failure_threshold_value: float  # Regulatory minimum
    current_value_at_t0: float      # Value at start of simulation
    predicted_failure_timestep: int | None  # null if no failure predicted
    predicted_failure_timestamp: str | None
    time_to_failure_hours: float | None
    confidence_score: float         # 0.0–1.0
    failure_reached_within_horizon: bool
```

**Computation:** For each entity and failure type:
```
rate = (current_value - value_at_prev_step) / timestep_duration
if rate < 0:  # deteriorating
    steps_to_failure = (current_value - threshold) / abs(rate)
    time_to_failure_hours = steps_to_failure × timestep_duration_hours
    confidence = min(1.0, steps_observed / 5)  # more data → higher confidence
else:
    time_to_failure = None  # not failing
```

**Failure type → metric mapping:**

| Failure Type | Metric | Threshold Source |
|-------------|--------|-----------------|
| `liquidity_failure` | `BankingStress.lcr` | `RegulatoryProfile.lcr_min` (default 1.0) |
| `capital_failure` | `BankingStress.capital_adequacy_ratio` | `RegulatoryProfile.capital_adequacy_min` (default 0.08) |
| `solvency_failure` | `InsuranceStress.solvency_ratio` | `RegulatoryProfile.insurance_solvency_min` |
| `availability_failure` | `FintechStress.service_availability` | `RegulatoryProfile.fintech_availability_min` |
| `regulatory_failure` | `RegulatoryState.breach_level` | Any breach_level ≥ "major" |

### 3.3 Regulatory Breach Timeline — `RegulatoryBreachEvent` (§16.2.3)

```python
class RegulatoryBreachEvent(BaseModel):
    run_id: str
    timestep_index: int
    timestamp: str
    scope_level: "entity"|"sector"|"system"
    scope_ref: str
    metric_name: "lcr"|"nsfr"|"cet1_ratio"|"capital_adequacy_ratio"|"solvency_ratio"|"reserve_ratio"|"service_availability"|"settlement_delay_minutes"
    metric_value: float            # Actual value at breach
    threshold_value: float         # Regulatory threshold crossed
    breach_direction: "below_minimum"|"above_maximum"
    breach_level: "minor"|"major"|"critical"
    first_breach: bool             # True if this is the first breach of this metric for this entity
    reportable: bool               # True if breach_level ≥ "major"
```

**Computation:** At each timestep, for each entity:
```python
for metric_name, metric_value, threshold, direction in entity_metrics:
    if direction == "below_minimum" and metric_value < threshold:
        breach = True
    elif direction == "above_maximum" and metric_value > threshold:
        breach = True

    if breach:
        breach_level = classify_breach(metric_value, threshold)
        # "minor" = within 10% of threshold
        # "major" = 10-25% beyond threshold
        # "critical" = >25% beyond threshold
        first_breach = not previously_breached(entity, metric_name)
        reportable = breach_level in ("major", "critical")
```

**Metric → breach direction mapping:**

| Metric | Direction | Source |
|--------|-----------|--------|
| `lcr` | `below_minimum` | Banking |
| `nsfr` | `below_minimum` | Banking |
| `cet1_ratio` | `below_minimum` | Banking |
| `capital_adequacy_ratio` | `below_minimum` | Banking |
| `solvency_ratio` | `below_minimum` | Insurance |
| `reserve_ratio` | `below_minimum` | Insurance |
| `service_availability` | `below_minimum` | Fintech |
| `settlement_delay_minutes` | `above_maximum` | Fintech |

### 3.4 Business Severity Mapping — `BusinessImpactSummary.business_severity`

```python
business_severity: "low"|"medium"|"high"|"severe"
```

**Mapping logic:**

| Severity | Peak Cumulative Loss (USD) | Critical Breach Count | System TTF (hours) |
|----------|---------------------------|----------------------|--------------------|
| `low` | < $500M | 0 | > 720 or None |
| `medium` | $500M – $2B | 1–3 | 336–720 |
| `high` | $2B – $5B | 4–10 | 72–336 |
| `severe` | > $5B | > 10 | < 72 |

**Formula:**
```python
def compute_severity(peak_loss, critical_count, system_ttf):
    loss_band = classify_loss(peak_loss)        # 0=low, 1=medium, 2=high, 3=severe
    breach_band = classify_breaches(critical_count)  # 0-3
    ttf_band = classify_ttf(system_ttf)         # 0-3
    composite = max(loss_band, breach_band, ttf_band)  # Worst-case wins
    return ["low", "medium", "high", "severe"][composite]
```

### 3.5 Executive Status Mapping — `BusinessImpactSummary.executive_status`

```python
executive_status: "monitor"|"intervene"|"escalate"|"crisis"
```

**Direct mapping from severity:**

| Business Severity | Executive Status | Board Action Required | Regulatory Notification |
|-------------------|-----------------|----------------------|------------------------|
| `low` | `monitor` | No | No |
| `medium` | `intervene` | Optional briefing | Watch-list only |
| `high` | `escalate` | Mandatory briefing | Formal notification |
| `severe` | `crisis` | Emergency session | Mandatory reporting |

**Formula:**
```python
SEVERITY_TO_STATUS = {
    "low": "monitor",
    "medium": "intervene",
    "high": "escalate",
    "severe": "crisis",
}
executive_status = SEVERITY_TO_STATUS[business_severity]
```

---

## 4. Required APIs

### 4.1 Existing Endpoints (in `api/v1/routes/runs.py`)

All endpoints exist and return data from in-memory run storage:

| # | Endpoint | Method | Response Type | Status |
|---|----------|--------|--------------|--------|
| 1 | `/api/v1/runs` | POST | `RunResult` (full pipeline output) | ✅ EXISTS |
| 2 | `/api/v1/runs/{run_id}/business-impact` | GET | `BusinessImpactSummary` | ✅ EXISTS |
| 3 | `/api/v1/runs/{run_id}/timeline` | GET | `TimeStepState[]` | ✅ EXISTS |
| 4 | `/api/v1/runs/{run_id}/regulatory-timeline` | GET | `RegulatoryBreachEvent[]` | ✅ EXISTS |
| 5 | `/api/v1/runs/{run_id}/executive-explanation` | GET | `ExecutiveDecisionExplanation` | ✅ EXISTS |

### 4.2 Missing API Endpoints (Need to Add)

| # | Endpoint | Method | Response Type | Purpose |
|---|----------|--------|--------------|---------|
| 6 | `/api/v1/runs/{run_id}/loss-trajectory` | GET | `LossTrajectoryPoint[]` | Dedicated endpoint for loss trajectory chart data |
| 7 | `/api/v1/runs/{run_id}/time-to-failure` | GET | `TimeToFailure[]` | Dedicated endpoint for failure predictions |
| 8 | `/api/v1/runs/{run_id}/breach-events` | GET | `RegulatoryBreachEvent[]` | Alias for regulatory-timeline with filtering params |

**Query parameters for filtering:**

```
GET /api/v1/runs/{run_id}/loss-trajectory?scope_level=system&scope_ref=system
GET /api/v1/runs/{run_id}/loss-trajectory?scope_level=sector&scope_ref=banking
GET /api/v1/runs/{run_id}/loss-trajectory?scope_level=entity&scope_ref={entity_id}

GET /api/v1/runs/{run_id}/time-to-failure?failure_type=liquidity_failure
GET /api/v1/runs/{run_id}/time-to-failure?scope_level=entity&scope_ref={entity_id}

GET /api/v1/runs/{run_id}/breach-events?breach_level=critical&reportable=true
GET /api/v1/runs/{run_id}/breach-events?metric_name=lcr&scope_ref={entity_id}
```

### 4.3 Frontend API Client Additions (`src/lib/api.ts`)

```typescript
// Add to api.observatory namespace:
observatory: {
    // Existing:
    run: (input) => RunResult,
    getResult: (runId) => RunResult,
    banking: (runId) => BankingStress,
    insurance: (runId) => InsuranceStress,
    fintech: (runId) => FintechStress,
    decision: (runId) => DecisionPlan,
    explanation: (runId) => ExplanationPack,

    // NEW — Business Impact Layer:
    businessImpact: (runId) => BusinessImpactSummary,
    lossTrajectory: (runId, scope?) => LossTrajectoryPoint[],
    timeToFailure: (runId, failureType?) => TimeToFailure[],
    breachEvents: (runId, filters?) => RegulatoryBreachEvent[],
    executiveExplanation: (runId) => ExecutiveDecisionExplanation,

    // NEW — Timeline:
    timeline: (runId) => TimeStepState[],
}
```

### 4.4 TanStack Query Hooks (`src/hooks/use-api.ts`)

```typescript
// NEW hooks:
useBusinessImpact(runId: string)
useLossTrajectory(runId: string, scope?: { level: string, ref: string })
useTimeToFailure(runId: string, failureType?: string)
useBreachEvents(runId: string, filters?: { breach_level?: string, reportable?: boolean })
useExecutiveExplanation(runId: string)
useTimeline(runId: string)
```

---

## 5. Required Persistence

### 5.1 Current State: In-Memory Only

The V4 API (`api/v1/routes/runs.py`) stores run results in a Python dict:
```python
_run_store: dict[str, RunResult] = {}
```

This means data is lost on server restart. For the business impact layer, we need persistence.

### 5.2 Target: PostgreSQL + PostGIS (Already in docker-compose)

| Table | Model | Columns | Indexes |
|-------|-------|---------|---------|
| `runs` | Run envelope | `run_id` (PK), `scenario_id`, `status`, `created_at`, `completed_at`, `pipeline_stages_completed`, `audit_hash` | `idx_runs_status`, `idx_runs_created_at` |
| `loss_trajectory` | `LossTrajectoryPoint` | `run_id` (FK), `scope_level`, `scope_ref`, `timestep_index`, `timestamp`, `direct_loss`, `propagated_loss`, `cumulative_loss`, `revenue_at_risk`, `loss_velocity`, `loss_acceleration`, `status` | `idx_lt_run_scope` (run_id, scope_level, scope_ref), `idx_lt_timestep` |
| `time_to_failure` | `TimeToFailure` | `run_id` (FK), `scope_level`, `scope_ref`, `failure_type`, `failure_threshold_value`, `current_value_at_t0`, `predicted_failure_timestep`, `time_to_failure_hours`, `confidence_score`, `failure_reached_within_horizon` | `idx_ttf_run` (run_id), `idx_ttf_failure_type` |
| `breach_events` | `RegulatoryBreachEvent` | `run_id` (FK), `timestep_index`, `timestamp`, `scope_level`, `scope_ref`, `metric_name`, `metric_value`, `threshold_value`, `breach_direction`, `breach_level`, `first_breach`, `reportable` | `idx_be_run` (run_id), `idx_be_level` (breach_level), `idx_be_reportable` |
| `business_impact_summary` | `BusinessImpactSummary` | `run_id` (PK/FK), all 12 fields | None (single row per run) |
| `timestep_states` | `TimeStepState` | `run_id` (FK), `timestep_index`, `timestamp`, `shock_intensity_effective`, `aggregate_loss`, `aggregate_flow`, `regulatory_breach_count`, `system_status` | `idx_ts_run_step` (run_id, timestep_index) |
| `entity_temporal_impacts` | `EntityTemporalImpact` | `run_id` (FK), `timestep_index`, `entity_id`, `impact_score`, `impact_delta`, `flow_value`, `flow_delta`, `loss_value`, `loss_delta`, `status` | `idx_eti_run_entity` (run_id, entity_id) |
| `audit_log` | Audit trail | `id` (PK), `run_id` (FK), `stage`, `event_type`, `payload` (JSONB), `timestamp`, `input_hash`, `output_hash` | `idx_audit_run` (run_id), `idx_audit_stage` |

### 5.3 Migration Strategy

**Phase 1 (Current):** Keep in-memory store for development. Business impact data included in `RunResult` response.

**Phase 2 (P2):** Add PostgreSQL persistence. Write after pipeline completes. Read from DB on GET requests.

**Phase 3 (P3):** Add Redis caching for hot runs (last 100 runs). TTL = 1 hour. Fallback to PostgreSQL.

---

## 6. Required UI Panels

### 6.1 Dashboard Tab: Timeline

**Location:** `src/app/dashboard?tab=timeline`

#### `BusinessImpactTimeline` (NEW — `src/components/timeline/BusinessImpactTimeline.tsx`)

| Property | Value |
|----------|-------|
| **Input** | `LossTrajectoryPoint[]` (scope_level=system) |
| **Chart** | Recharts `AreaChart` with dual Y-axis |
| **Left Y-axis** | Cumulative loss (USD) — area fill `#1D4ED8` (io-accent) with 20% opacity |
| **Right Y-axis** | Daily delta (USD) — line `#F97316` (orange) |
| **X-axis** | Day number (from `timestep_index`) |
| **Annotations** | Vertical dashed lines at: peak day (red), first failure (orange), breach events (yellow dots) |
| **Hover** | Tooltip: day, cumulative loss, daily delta, status |
| **Design** | `bg-io-surface rounded-xl border border-io-border p-5` |
| **Bilingual** | Labels from i18n: "الجدول الزمني للأثر التجاري" / "Business Impact Timeline" |

**Data flow:**
```
DashboardShell → useLossTrajectory(runId, {level: "system", ref: "system"})
  → BusinessImpactTimeline(data={lossTrajectory}, peakDay, firstFailureDay, breachDays)
```

#### `RegulatoryBreachTimeline` (NEW — `src/components/timeline/RegulatoryBreachTimeline.tsx`)

| Property | Value |
|----------|-------|
| **Input** | `RegulatoryBreachEvent[]` |
| **Layout** | Vertical timeline with colored severity dots |
| **Dot colors** | Critical = `#EF4444`, Major = `#F97316`, Minor = `#F59E0B` |
| **Each event** | Entity name, metric name, actual value vs threshold, breach level badge, timestamp |
| **Filter** | Toggle: All / Critical only / Reportable only |
| **Scroll** | Scrollable container, max-height 400px |
| **Design** | `bg-io-surface rounded-xl border border-io-border p-5` |
| **Bilingual** | "الجدول الزمني لاختراق القواعد التنظيمية" / "Regulatory Breach Timeline" |

**Data flow:**
```
DashboardShell → useBreachEvents(runId)
  → RegulatoryBreachTimeline(events={breachEvents}, filter={breachLevel})
```

### 6.2 Dashboard Tab: Overview (KPI Additions)

Three KPI cards in the top summary consume business impact data:

#### KPI: Time to First Failure

| Property | Value |
|----------|-------|
| **Source** | `BusinessImpactSummary.system_time_to_first_failure_hours` |
| **Display** | Hours formatted: `< 72h` = red, `72-168h` = orange, `168-336h` = yellow, `> 336h` = green, `null` = "No failure predicted" (green) |
| **Label EN** | "Time to First Failure" |
| **Label AR** | "الوقت إلى أول انهيار" |
| **Trend** | None (single-run metric) |

#### KPI: Business Severity

| Property | Value |
|----------|-------|
| **Source** | `BusinessImpactSummary.business_severity` |
| **Display** | Badge: `low` = green, `medium` = yellow, `high` = orange, `severe` = red |
| **Label EN** | "Business Severity" |
| **Label AR** | "شدة الأعمال" |

#### KPI: Executive Status

| Property | Value |
|----------|-------|
| **Source** | `BusinessImpactSummary.executive_status` |
| **Display** | Badge: `monitor` = green, `intervene` = yellow, `escalate` = orange, `crisis` = red |
| **Label EN** | "Executive Status" |
| **Label AR** | "الحالة التنفيذية" |

### 6.3 Dashboard Tab: Regulatory

#### `RegulatoryNotes` (NEW — `src/components/panels/RegulatoryNotes.tsx`)

| Property | Value |
|----------|-------|
| **Input** | `AuditLogEntry[]` (from audit service) |
| **Layout** | Sortable table: Stage, Event Type, Timestamp, Payload preview (expandable) |
| **Columns** | stage, event_type, timestamp, payload (truncated, click to expand) |
| **Sort** | By timestamp (default desc), by stage |
| **Design** | Compact table, `bg-io-surface rounded-xl border border-io-border` |
| **Bilingual** | "الرقابة والتدقيق" / "Regulatory & Audit" |

#### `AnalystTrace` (NEW — `src/components/panels/AnalystTrace.tsx`)

| Property | Value |
|----------|-------|
| **Input** | `StageTrace[]` (from ExplanationPack.stage_traces) |
| **Layout** | Horizontal pipeline diagram or vertical card list |
| **Each stage** | Stage name, status (green/red/yellow), duration_ms, input_hash (monospace), output_hash (monospace) |
| **Design** | Monospace font for hashes, green = completed, red = failed, yellow = partial |
| **Bilingual** | "تتبع المعالجة" / "Pipeline Trace" |

### 6.4 Zustand Store Additions (`src/store/app-store.ts`)

```typescript
// Add to existing store:
interface AppStore {
    // ... existing fields ...

    // Business Impact Layer (Step 7):
    businessImpact: BusinessImpactSummary | null;
    lossTrajectory: LossTrajectoryPoint[];
    timeToFailures: TimeToFailure[];
    breachEvents: RegulatoryBreachEvent[];
    timelineSteps: TimeStepState[];

    // Actions:
    setBusinessImpact: (data: BusinessImpactSummary) => void;
    setLossTrajectory: (data: LossTrajectoryPoint[]) => void;
    setTimeToFailures: (data: TimeToFailure[]) => void;
    setBreachEvents: (data: RegulatoryBreachEvent[]) => void;
    setTimelineSteps: (data: TimeStepState[]) => void;
}
```

**Note:** These are populated by the `DashboardShell` orchestrator after fetching `RunResult`. Individual panels read from the store via selectors. TanStack Query hooks are the primary data source; Zustand stores derived/transformed state.

---

## 7. End-to-End Data Flow

```
1. User clicks "Run Scenario" on /run page
   └── POST /api/v1/runs { template_id, severity, horizon_hours }

2. Backend pipeline executes 9 stages + post-pipeline
   └── business_impact_service.compute() runs after Stage 9
   └── time_engine_service.simulate() runs in parallel with business_impact

3. RunResult returned to frontend includes:
   └── headline.total_loss_usd, headline.peak_day, headline.affected_entities
   └── banking, insurance, fintech, decisions, explanation (existing)
   └── business_impact: BusinessImpactSummary (NEW)
   └── loss_trajectory: LossTrajectoryPoint[] (NEW)
   └── time_to_failures: TimeToFailure[] (NEW)
   └── breach_events: RegulatoryBreachEvent[] (NEW)
   └── timeline_steps: TimeStepState[] (NEW)

4. DashboardShell stores RunResult in Zustand
   └── Extracts business_impact → setBusinessImpact()
   └── Extracts loss_trajectory → setLossTrajectory()
   └── Extracts breach_events → setBreachEvents()
   └── Extracts time_to_failures → setTimeToFailures()

5. Overview tab reads from store:
   └── KPICard(time_to_first_failure) ← businessImpact.system_time_to_first_failure_hours
   └── KPICard(business_severity) ← businessImpact.business_severity
   └── KPICard(executive_status) ← businessImpact.executive_status

6. Timeline tab reads from store:
   └── BusinessImpactTimeline ← lossTrajectory (scope=system)
   └── RegulatoryBreachTimeline ← breachEvents

7. Regulatory tab reads from store:
   └── RegulatoryNotes ← from audit API (separate fetch)
   └── AnalystTrace ← explanation.stage_traces
```

---

## 8. Decision Gate

This plan is **LOCKED**. Before implementing:

1. **Backend prerequisite:** `services/business_impact/engine.py` must produce all 5 output types with correct field names matching domain models in `domain/models/business_impact.py`
2. **API prerequisite:** `RunResult` type in `frontend/src/types/observatory.ts` must be extended with optional business impact fields (Step 5, Phase 3)
3. **UI prerequisite:** V2 dead code must be removed and dashboard shell must be restructured (Step 3, Phases 1–3) before adding new panels
4. **Persistence prerequisite:** PostgreSQL schema must be designed but implementation deferred to P2. In-memory store is sufficient for V1.

Awaiting your command to begin execution.
