# Business Impact + Time Layer Plan — Step 7 (LOCKED)

**Date:** 2026-04-02
**Spec Sections:** v4 §16 (Business Impact), §17 (Time Engine), §16.5 (Severity Mapping)
**Pipeline Position:** Post-pipeline (runs after 9-stage core, before API serialization)

---

## 1. Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                    V4 PIPELINE (9 stages)                    │
│  scenario → physics → graph → propagation → financial →     │
│  risk → regulatory → decision → explanation                  │
└──────────────────────────┬──────────────────────────────────┘
                           │
                    V4PipelineResult
                           │
              ┌────────────┼────────────┐
              ▼            ▼            ▼
     ┌────────────┐ ┌───────────┐ ┌────────────────┐
     │  Business   │ │   Time    │ │   Executive    │
     │  Impact     │ │  Engine   │ │  Explanation   │
     │  §16        │ │  §17      │ │  §19           │
     └─────┬──────┘ └─────┬─────┘ └───────┬────────┘
           │              │               │
           ▼              ▼               ▼
  BusinessImpactSummary  TimeStepState[]  ExecutiveDecisionExplanation
  LossTrajectoryPoint[]                   CauseEffectLink[]
  TimeToFailure[]                         LossTranslation
  RegulatoryBreachEvent[]                 ExecutiveActionExplanation[]
           │              │               │
           └──────────────┼───────────────┘
                          ▼
                   API Serialization
                   (/runs/{id}/business-impact, /timeline, /regulatory-timeline)
                          │
                          ▼
                   Frontend Dashboard
                   (Timeline tab, Overview KPIs, Regulatory tab)
```

---

## 2. Loss Trajectory

### 2.1 Domain Model (EXISTS — `backend/app/domain/models/business_impact.py`)

```python
class LossTrajectoryPoint(BaseModel):
    run_id: str
    scope_level: Literal["entity", "sector", "system"]
    scope_ref: str            # entity UUID, sector name, or "system"
    timestep_index: int       # 0-indexed
    timestamp: str            # ISO-8601 UTC
    direct_loss: float        # Direct loss at timestep
    propagated_loss: float    # Propagated loss at timestep
    cumulative_loss: float    # Sum of all losses to date
    revenue_at_risk: float    # Revenue at risk
    loss_velocity: float      # Loss rate of change per step
    loss_acceleration: float  # Loss acceleration per step²
    status: Literal["stable", "deteriorating", "critical", "failed"]
```

### 2.2 Computation (EXISTS — `backend/app/services/business_impact/engine.py`)

**Function:** `compute_business_impact()` lines 46–89

**Formula:**
```
ShockEffective(t) = ShockIntensity × (1 - shock_decay_rate)^t
StepLoss(t)       = TotalExposure × ShockEffective(t) × 0.65 × 0.005
DirectLoss        = StepLoss × 0.6
PropagatedLoss    = StepLoss × 0.4
CumulativeLoss    = Σ StepLoss(0..t)
RevenueAtRisk     = CumulativeLoss × 0.8
Velocity          = StepLoss(t) - StepLoss(t-1)
Acceleration      = Velocity(t) - Velocity(t-1)
```

**Status thresholds** (relative to total financial impact):
- `stable`: cumulative < 20% of total
- `deteriorating`: 20–50%
- `critical`: 50–80%
- `failed`: > 80%

**Current limitation:** Always generates at `scope_level="system"`. Per-entity and per-sector trajectories not yet computed.

### 2.3 Refactors Needed

| # | Change | Risk | Priority |
|---|--------|------|----------|
| 1 | Add per-entity trajectory loop (iterate entities, compute individual LossTrajectoryPoint[]) | LOW | P2 |
| 2 | Add per-sector aggregation (group entities by `entity_type`, sum losses) | LOW | P2 |
| 3 | Replace hardcoded `0.65 × 0.005` with scenario-derived propagation factor from `V4PipelineResult.propagation_factors` | MEDIUM | P1 |
| 4 | Use actual `time_config.time_granularity_minutes` for timestep sizing instead of daily | LOW | P2 |

---

## 3. Time to Failure

### 3.1 Domain Model (EXISTS — `backend/app/domain/models/business_impact.py`)

```python
class TimeToFailure(BaseModel):
    run_id: str
    scope_level: Literal["entity", "sector", "system"]
    scope_ref: str
    failure_type: Literal[
        "liquidity_failure", "capital_failure", "solvency_failure",
        "availability_failure", "regulatory_failure"
    ]
    failure_threshold_value: float
    current_value_at_t0: float
    predicted_failure_timestep: Optional[int]   # null if no failure
    predicted_failure_timestamp: Optional[str]
    time_to_failure_hours: Optional[float]
    confidence_score: float                     # 0.0–1.0
    failure_reached_within_horizon: bool
```

### 3.2 Computation (EXISTS — `backend/app/services/business_impact/engine.py`)

**Function:** `compute_business_impact()` lines 100–141

**Logic per sector:**

| Sector | Breach Flag | Failure Type | Threshold Constant | TTF Formula |
|--------|------------|--------------|-------------------|-------------|
| Banking | `lcr_breach` | `liquidity_failure` | `LCR_MIN` (1.0) | `max(24h, 168h / shock_intensity)` |
| Banking | `car_breach` | `capital_failure` | `CAR_MIN` (0.08) | `max(48h, 168h / shock_intensity)` |
| Insurance | `solvency_breach` | `solvency_failure` | `SOLVENCY_MIN` (1.0) | `max(72h, 240h / shock_intensity)` |
| Fintech | `availability_breach` | `availability_failure` | `0.995` | `max(12h, 48h / shock_intensity)` |

**Confidence scores:** Banking liquidity 0.75, Banking capital 0.70, Insurance solvency 0.65, Fintech availability 0.80.

**System-level first failure:** `min(all TTF hours)` → populates `BusinessImpactSummary.system_time_to_first_failure_hours`.

### 3.3 Refactors Needed

| # | Change | Risk | Priority |
|---|--------|------|----------|
| 1 | Add `regulatory_failure` type — trigger when `RegulatoryState.breach_level == "critical"` | LOW | P2 |
| 2 | Use time-engine timestep states to compute TTF dynamically (interpolate from `TimeStepState.entity_impacts[].status`) instead of static formula | MEDIUM | P3 |
| 3 | Per-sector aggregate TTF (`scope_level="sector"`) — min TTF across entities in each sector | LOW | P2 |

---

## 4. Regulatory Breach Timeline

### 4.1 Domain Model (EXISTS — `backend/app/domain/models/business_impact.py`)

```python
class RegulatoryBreachEvent(BaseModel):
    run_id: str
    timestep_index: int
    timestamp: str
    scope_level: Literal["entity", "sector", "system"]
    scope_ref: str
    metric_name: Literal[
        "lcr", "nsfr", "cet1_ratio", "capital_adequacy_ratio",
        "solvency_ratio", "reserve_ratio", "service_availability",
        "settlement_delay_minutes"
    ]
    metric_value: float
    threshold_value: float
    breach_direction: Literal["below_minimum", "above_maximum"]
    breach_level: Literal["minor", "major", "critical"]
    first_breach: bool
    reportable: bool
```

### 4.2 Computation (EXISTS — `backend/app/services/business_impact/engine.py`)

**Function:** `compute_business_impact()` lines 143–171

**Current breach detection:**

| Source | Breach Flag | Metric Name | Breach Level | Reportable |
|--------|------------|-------------|-------------|-----------|
| `BankingStress.breach_flags.lcr_breach` | LCR below 1.0 | `lcr` | `major` | Yes |
| `BankingStress.breach_flags.car_breach` | CAR below 0.08 | `capital_adequacy_ratio` | `critical` | Yes |
| `InsuranceStress.breach_flags.solvency_breach` | Solvency ratio below 1.0 | `solvency_ratio` | `major` | Yes |

**Missing breach checks (need to add):**

| Source | Breach Flag | Metric Name | Breach Level | Reportable |
|--------|------------|-------------|-------------|-----------|
| `BankingStress.breach_flags.nsfr_breach` | NSFR below 1.0 | `nsfr` | `major` | Yes |
| `BankingStress.breach_flags.cet1_breach` | CET1 below 0.045 | `cet1_ratio` | `critical` | Yes |
| `InsuranceStress.breach_flags.reserve_breach` | Reserve ratio below min | `reserve_ratio` | `major` | Yes |
| `InsuranceStress.breach_flags.liquidity_breach` | Liquidity gap | `solvency_ratio` | `major` | Yes |
| `FintechStress.breach_flags.availability_breach` | Availability below 99.5% | `service_availability` | `major` | Yes |
| `FintechStress.breach_flags.settlement_breach` | Settlement delay > 30min | `settlement_delay_minutes` | `major` | Yes |
| `FintechStress.breach_flags.operational_risk_breach` | Ops risk > 0.8 | — | `minor` | No |

### 4.3 Refactors Needed

| # | Change | Risk | Priority |
|---|--------|------|----------|
| 1 | Add NSFR, CET1, reserve, liquidity, availability, settlement breach events | LOW | P1 |
| 2 | Compute `timestep_index` dynamically from time-engine states instead of hardcoded 2/3/4 | MEDIUM | P2 |
| 3 | Set `first_breach` correctly by tracking per-entity/per-metric breach history across timesteps | LOW | P2 |
| 4 | Determine `breach_level` from magnitude: minor (<10% below threshold), major (10–30%), critical (>30%) | LOW | P2 |

---

## 5. Business Severity Mapping

### 5.1 Domain Model (EXISTS — `backend/app/domain/models/business_impact.py`)

```python
class BusinessImpactSummary(BaseModel):
    run_id: str
    currency: str              # ISO 4217 (e.g., "USD")
    peak_cumulative_loss: float
    peak_loss_timestep: int
    peak_loss_timestamp: str
    system_time_to_first_failure_hours: Optional[float]
    first_failure_type: Optional[str]
    first_failure_scope_ref: Optional[str]
    critical_breach_count: int
    reportable_breach_count: int
    business_severity: Literal["low", "medium", "high", "severe"]
    executive_status: Literal["monitor", "intervene", "escalate", "crisis"]
```

### 5.2 Severity Thresholds (EXISTS — `backend/app/services/business_impact/engine.py`)

```
peak_loss >= 500 (billion units)  → "severe"
peak_loss >= 200                  → "high"
peak_loss >= 50                   → "medium"
peak_loss < 50                    → "low"
```

### 5.3 Severity → Executive Status Mapping (EXISTS — `backend/app/core/constants.py`)

```python
SEVERITY_MAPPING = {
    "low":    "monitor",     # Standard monitoring, no action
    "medium": "intervene",   # Active intervention required
    "high":   "escalate",    # Escalate to senior management
    "severe": "crisis",      # Crisis management activation
}
```

### 5.4 Refactors Needed

| # | Change | Risk | Priority |
|---|--------|------|----------|
| 1 | Make thresholds configurable per jurisdiction (GCC vs global) via `RegulatoryProfile` | LOW | P2 |
| 2 | Add composite severity considering TTF + breach count (not just peak loss) | MEDIUM | P2 |
| 3 | Add bilingual severity labels to constants: `{"low": {"en": "Low", "ar": "منخفض"}, ...}` | LOW | P1 |

---

## 6. Executive Status Mapping

### 6.1 Status Semantics

| Status | Meaning | Dashboard Color | Required Actions |
|--------|---------|----------------|-----------------|
| `monitor` | Within tolerances | `#22C55E` (green) | Standard monitoring cadence |
| `intervene` | Threshold approaching | `#F59E0B` (amber) | Activate mitigation plans |
| `escalate` | Threshold breached | `#F97316` (orange) | Escalate to C-suite / board |
| `crisis` | Systemic failure imminent | `#EF4444` (red) | Crisis management protocol, regulatory notification |

### 6.2 Frontend Display (EXISTS — `frontend/lib/types/observatory.ts`)

```typescript
export const STATUS_COLORS = {
    monitor:   '#22C55E',
    intervene: '#F59E0B',
    escalate:  '#F97316',
    crisis:    '#EF4444',
} as const

export function severityToStatus(severity: BusinessSeverity): ExecutiveStatus {
    const map: Record<BusinessSeverity, ExecutiveStatus> = {
        low: 'monitor', medium: 'intervene', high: 'escalate', severe: 'crisis',
    }
    return map[severity]
}
```

### 6.3 Dashboard Panels Consuming Executive Status

| Panel | Component | Data Source | Field |
|-------|-----------|------------|-------|
| Overview KPI #5 | `KPICard` | `BusinessImpactSummary` | `executive_status` |
| Dashboard Header badge | `DashboardHeader` | `BusinessImpactSummary` | `business_severity` + `executive_status` |
| Timeline tab header | `BusinessImpactTimeline` | `BusinessImpactSummary` | `executive_status` (color-coded) |
| Regulatory tab summary | `RegulatoryNotes` | `BusinessImpactSummary` | `critical_breach_count`, `reportable_breach_count` |

---

## 7. Required Services

### 7.1 Existing Services (Status: IMPLEMENTED)

| # | Service | File | Function | Status |
|---|---------|------|----------|--------|
| 1 | **Business Impact Engine** | `app/services/business_impact/engine.py` | `compute_business_impact()` | ✅ 212 lines. Produces `BusinessImpactSummary` + `LossTrajectoryPoint[]` + `TimeToFailure[]` + `RegulatoryBreachEvent[]`. |
| 2 | **Time Engine** | `app/services/time_engine/engine.py` | `compute_temporal_simulation()` | ✅ 134 lines. Produces `TimeStepState[]` with per-entity `EntityTemporalImpact`. |
| 3 | **Pipeline Orchestrator** | `app/orchestration/pipeline_v4.py` | `run_v4_pipeline()` | ✅ 309 lines. Calls both services as post-pipeline stages. Stores results in `V4PipelineResult`. |
| 4 | **Audit Engine** | `app/services/audit/engine.py` | `compute_sha256()` | ✅ SHA-256 hash of pipeline output for audit traceability. |

### 7.2 Services to Build (Status: NOT YET IMPLEMENTED)

| # | Service | File | Function | Input | Output | Priority |
|---|---------|------|----------|-------|--------|----------|
| 5 | **Executive Explanation Engine** | `app/services/executive_explanation/engine.py` | `compute_executive_explanation()` | `BusinessImpactSummary`, `DecisionPlan`, `ExplanationPack` | `ExecutiveDecisionExplanation` (v4 §19) | P2 |
| 6 | **Breach Enrichment** | `app/services/business_impact/breach_enrichment.py` | `enrich_breach_events()` | `RegulatoryBreachEvent[]`, `TimeStepState[]` | `RegulatoryBreachEvent[]` (with dynamic timestep_index, magnitude-based breach_level) | P2 |

### 7.3 Service Dependency Chain

```
Financial Impact (Stage 5)
    └─ Banking/Insurance/Fintech Stress (Stage 6)
        └─ Regulatory State (Stage 7)
            └─ Decision Plan (Stage 8)
                └─ Explanation Pack (Stage 9)
                    └─ Business Impact Summary (Post-pipeline)
                        └─ Executive Explanation (Post-pipeline)
                    └─ Time Engine Simulation (Post-pipeline, parallel with Business Impact)
```

---

## 8. Required APIs

### 8.1 Existing Endpoints (Status: IMPLEMENTED)

| # | Method | Path | Permission | Response | Status |
|---|--------|------|-----------|----------|--------|
| 1 | `GET` | `/api/v1/runs/{run_id}/business-impact` | `READ_BUSINESS_IMPACT` | `BusinessImpactSummary` + `LossTrajectoryPoint[]` | ✅ Endpoint exists. Returns `_run_results[run_id]["business_impact"]`. |
| 2 | `GET` | `/api/v1/runs/{run_id}/timeline` | `READ_TIMELINE` | `TimeStepState[]` | ✅ Endpoint exists. Returns `_run_results[run_id]["timeline"]`. |
| 3 | `GET` | `/api/v1/runs/{run_id}/regulatory-timeline` | `READ_REGULATORY_TIMELINE` | `RegulatoryBreachEvent[]` | ✅ Endpoint exists. Returns `_run_results[run_id]["regulatory_timeline"]`. |
| 4 | `GET` | `/api/v1/runs/{run_id}/executive-explanation` | `READ_EXECUTIVE_EXPLANATION` | `ExecutiveDecisionExplanation` | ✅ Endpoint exists. Returns `_run_results[run_id]["executive_explanation"]`. |

### 8.2 API Gap: Pipeline → Result Store Wiring

**Critical issue:** The pipeline (`run_v4_pipeline()`) computes `business_impact`, `timeline`, and breach events, but the `POST /runs` endpoint does **not** call the pipeline. It only creates a run record in `_runs` with status `"queued"`.

**Missing wiring:**
1. `POST /runs` must invoke `run_v4_pipeline()` (or queue it for async execution)
2. Pipeline result must be serialized into `_run_results[run_id]` with keys: `"business_impact"`, `"timeline"`, `"regulatory_timeline"`, `"executive_explanation"`
3. Run status must be updated from `"queued"` → `"running"` → `"completed"` (or `"failed"`)

**Implementation required:**

```python
# In POST /runs handler (after creating run record):
from ..orchestration.pipeline_v4 import run_v4_pipeline

# Build scenario from request
scenario = build_scenario_from_request(request_body)

# Execute pipeline
pipeline_result = run_v4_pipeline(scenario, run_id)

# Serialize to result store
_run_results[run_id] = {
    "financial": [fi.model_dump() for fi in pipeline_result.financial_impacts],
    "banking": pipeline_result.banking_aggregate,
    "insurance": pipeline_result.insurance_aggregate,
    "fintech": pipeline_result.fintech_aggregate,
    "decision": pipeline_result.decision_plan.model_dump() if pipeline_result.decision_plan else {},
    "explanation": pipeline_result.explanation.model_dump() if pipeline_result.explanation else {},
    "business_impact": pipeline_result.business_impact.model_dump() if pipeline_result.business_impact else {},
    "timeline": [ts.model_dump() for ts in pipeline_result.timeline],
    "regulatory_timeline": [],  # Extract from business_impact computation
    "executive_explanation": {},  # From executive explanation engine
}
_runs[run_id]["status"] = "completed"
```

### 8.3 Frontend API Client Additions Needed

In `frontend/src/lib/api.ts`, the `observatory` namespace needs:

| # | Method | Path | Returns | Consumed By |
|---|--------|------|---------|-------------|
| 1 | `api.observatory.businessImpact(runId)` | `GET /runs/{id}/business-impact` | `BusinessImpactSummary` | Overview KPIs, Timeline tab |
| 2 | `api.observatory.timeline(runId)` | `GET /runs/{id}/timeline` | `TimeStepState[]` | Timeline tab (time engine detail) |
| 3 | `api.observatory.regulatoryTimeline(runId)` | `GET /runs/{id}/regulatory-timeline` | `RegulatoryBreachEvent[]` | Timeline tab, Regulatory tab |
| 4 | `api.observatory.executiveExplanation(runId)` | `GET /runs/{id}/executive-explanation` | `ExecutiveDecisionExplanation` | Decisions tab, Executive mode |

### 8.4 TanStack Query Hooks Needed

In `frontend/src/hooks/use-api.ts`:

```typescript
export function useBusinessImpact(runId: string) {
    return useQuery({ queryKey: ['business-impact', runId], queryFn: () => api.observatory.businessImpact(runId) })
}
export function useTimeline(runId: string) {
    return useQuery({ queryKey: ['timeline', runId], queryFn: () => api.observatory.timeline(runId) })
}
export function useRegulatoryTimeline(runId: string) {
    return useQuery({ queryKey: ['regulatory-timeline', runId], queryFn: () => api.observatory.regulatoryTimeline(runId) })
}
export function useExecutiveExplanation(runId: string) {
    return useQuery({ queryKey: ['executive-explanation', runId], queryFn: () => api.observatory.executiveExplanation(runId) })
}
```

---

## 9. Required Persistence

### 9.1 Current State: In-Memory Only

The API layer uses two in-memory dicts in `app/api/v1/routes/runs.py`:

```python
_runs: dict[str, dict] = {}         # Run metadata (id, status, created_at)
_run_results: dict[str, dict] = {}  # Full pipeline results
```

**Problem:** All run data is lost on server restart. No persistence, no history, no audit trail.

### 9.2 Target Persistence Layer

**PostgreSQL tables needed** (using existing PostGIS 16 instance from `docker-compose.yml`):

| # | Table | Primary Key | Key Columns | Indexes | Purpose |
|---|-------|------------|-------------|---------|---------|
| 1 | `runs` | `run_id UUID` | `scenario_id`, `status`, `created_at`, `completed_at`, `model_version`, `audit_hash` | `ix_runs_status`, `ix_runs_created_at` | Run metadata and lifecycle tracking |
| 2 | `loss_trajectory` | `(run_id, scope_ref, timestep_index)` composite | All `LossTrajectoryPoint` fields | `ix_lt_run_id`, `ix_lt_scope` | Per-timestep loss data for charts |
| 3 | `time_to_failure` | `(run_id, scope_ref, failure_type)` composite | All `TimeToFailure` fields | `ix_ttf_run_id` | Failure predictions |
| 4 | `regulatory_breach_events` | `(run_id, scope_ref, metric_name, timestep_index)` composite | All `RegulatoryBreachEvent` fields | `ix_rbe_run_id`, `ix_rbe_reportable` | Breach event log |
| 5 | `business_impact_summaries` | `run_id UUID` | All `BusinessImpactSummary` fields | `ix_bis_severity`, `ix_bis_status` | Aggregate impact per run |
| 6 | `timestep_states` | `(run_id, timestep_index)` composite | `TimeStepState` fields (entity_impacts as JSONB) | `ix_tss_run_id` | Time engine output |
| 7 | `audit_log` | `id SERIAL` | `run_id`, `stage`, `event_type`, `payload JSONB`, `sha256_hash`, `timestamp` | `ix_al_run_id`, `ix_al_timestamp` | SHA-256 audit trail |

### 9.3 SQLAlchemy ORM Models to Add

New file: `backend/app/db/run_models.py`

**Note:** The existing `backend/app/db/models.py` has ORM models for the geospatial/ingest layer (Event, Incident, Alert, Airport, Port, Corridor, Flight, Vessel, etc.). The run persistence models must be in a **separate file** to avoid conflating the two concerns.

### 9.4 Migration Strategy

| Phase | Action | Risk |
|-------|--------|------|
| **V1 (now)** | Keep in-memory store. Pipeline results survive for session duration. | LOW — acceptable for PoC/demo |
| **V2 (P2)** | Add `runs` and `business_impact_summaries` tables. Write-through: store after pipeline, read from DB on GET. | MEDIUM — requires Alembic migration |
| **V3 (P3)** | Add all 7 tables. Full persistence. Historical comparison. Audit log with SHA-256 chains. | MEDIUM — requires connection pool tuning |

### 9.5 Redis Caching (Optional, P3)

Using existing Redis 7 instance from `docker-compose.yml`:

| Key Pattern | Value | TTL | Purpose |
|-------------|-------|-----|---------|
| `run:{run_id}:status` | Run status string | 24h | Fast status polling |
| `run:{run_id}:business_impact` | JSON-serialized `BusinessImpactSummary` | 1h | Cache hot results |
| `run:{run_id}:timeline` | JSON-serialized `TimeStepState[]` | 1h | Cache time engine output |

---

## 10. Required UI Panels

### 10.1 Timeline Tab Components (from DASHBOARD_STRUCTURE.md)

| # | Component | File | Data Source | API Hook |
|---|-----------|------|------------|----------|
| 1 | `BusinessImpactTimeline` | `src/components/timeline/BusinessImpactTimeline.tsx` | `LossTrajectoryPoint[]` | `useBusinessImpact(runId)` |
| 2 | `RegulatoryBreachTimeline` | `src/components/timeline/RegulatoryBreachTimeline.tsx` | `RegulatoryBreachEvent[]` | `useRegulatoryTimeline(runId)` |

### 10.2 BusinessImpactTimeline — Detailed Spec

**Input:** `LossTrajectoryPoint[]` from `GET /runs/{id}/business-impact`

**Render:** Recharts `AreaChart` with:
- **X-axis:** `timestep_index` (labeled as Day 1, Day 2, ...)
- **Left Y-axis:** `cumulative_loss` (area fill, blue gradient `#1D4ED8` → `#93C5FD`)
- **Right Y-axis:** `loss_velocity` (line, orange `#F97316`)
- **Annotations:**
  - Vertical dashed line at `peak_loss_timestep` (red)
  - Horizontal threshold lines at severity boundaries (50B, 200B, 500B)
  - Status color bands: green (stable) → yellow (deteriorating) → orange (critical) → red (failed)
- **Hover tooltip:** Day, cumulative loss, daily delta, velocity, acceleration, status

**Design:** `bg-io-surface rounded-xl border border-io-border p-5 shadow-sm`

**Bilingual labels:**

| Element | English | Arabic |
|---------|---------|--------|
| Chart title | Business Impact Timeline | الجدول الزمني للأثر التجاري |
| X-axis | Day | اليوم |
| Left Y-axis | Cumulative Loss (USD) | الخسارة التراكمية (دولار) |
| Right Y-axis | Daily Change Rate | معدل التغير اليومي |
| Peak annotation | Peak Day | يوم الذروة |
| Tooltip: Direct | Direct Loss | خسارة مباشرة |
| Tooltip: Propagated | Propagated Loss | خسارة منقولة |

### 10.3 RegulatoryBreachTimeline — Detailed Spec

**Input:** `RegulatoryBreachEvent[]` from `GET /runs/{id}/regulatory-timeline`

**Render:** Vertical timeline with:
- **Each event** = a card with:
  - Colored dot: red (critical), orange (major), yellow (minor)
  - Entity name (from `scope_ref` → entity lookup)
  - Metric name + value vs threshold (e.g., "LCR: 0.72 / min 1.0")
  - Breach direction icon (↓ below_minimum or ↑ above_maximum)
  - `first_breach` badge (if true)
  - `reportable` indicator
- **Sorted by:** `timestep_index` ascending
- **Grouped by:** Entity (collapsible sections)

**Design:** Scrollable list inside `bg-io-surface rounded-xl border border-io-border p-5`

**Bilingual labels:**

| Element | English | Arabic |
|---------|---------|--------|
| Panel title | Regulatory Breach Timeline | الجدول الزمني لاختراق القواعد التنظيمية |
| Breach event | Breach Event | حدث اختراق |
| Metric | Metric | المقياس |
| Threshold | Threshold | الحد الأدنى |
| Actual | Actual | القيمة الفعلية |
| First breach | First Breach | أول اختراق |
| Reportable | Reportable | يتطلب إبلاغ |
| Critical | Critical | حرج |
| Major | Major | كبير |
| Minor | Minor | طفيف |

### 10.4 Overview KPIs Consuming Business Impact

| KPI Position | Metric | Data Source | Display |
|-------------|--------|------------|---------|
| #1 Headline Loss | `peak_cumulative_loss` | `BusinessImpactSummary` | Formatted USD with severity coloring |
| #2 Peak Day | `peak_loss_timestep` | `BusinessImpactSummary` | "Day N" / "اليوم N" |
| #3 Time to First Failure | `system_time_to_first_failure_hours` | `BusinessImpactSummary` | "Xh" or "N/A" with severity (< 72h = critical) |
| #4 Business Severity | `business_severity` | `BusinessImpactSummary` | Badge with `SEVERITY_COLORS` |
| #5 Executive Status | `executive_status` | `BusinessImpactSummary` | Badge with `STATUS_COLORS` |

### 10.5 Regulatory Tab Components Consuming Breach Data

| # | Component | Data Source | Purpose |
|---|-----------|------------|---------|
| 1 | `RegulatoryNotes` (top 60%) | `RegulatoryBreachEvent[]` + `RegulatoryState` | Breach event table + aggregate compliance status |
| 2 | `AnalystTrace` (bottom 40%) | `ExplanationPack.stage_traces` | Pipeline execution audit with SHA-256 hashes |

---

## 11. Data Flow Summary

```
POST /api/v1/runs { scenario_id, severity, horizon_hours }
    │
    ▼
run_v4_pipeline(scenario)
    │
    ├─ Stages 1–9 (core pipeline)
    │
    ├─ compute_business_impact() → BusinessImpactSummary
    │   ├─ LossTrajectoryPoint[] (system-level, 30 timesteps max)
    │   ├─ TimeToFailure[] (per-entity, per breach flag)
    │   └─ RegulatoryBreachEvent[] (per-entity, per breach flag)
    │
    ├─ compute_temporal_simulation() → TimeStepState[]
    │   └─ EntityTemporalImpact[] per timestep
    │
    └─ [TODO] compute_executive_explanation() → ExecutiveDecisionExplanation
        ├─ CauseEffectLink[]
        ├─ LossTranslation
        └─ ExecutiveActionExplanation[]
    │
    ▼
_run_results[run_id] = { ... serialized ... }
    │
    ▼
GET /runs/{id}/business-impact  → BusinessImpactSummary + LossTrajectoryPoint[]
GET /runs/{id}/timeline         → TimeStepState[]
GET /runs/{id}/regulatory-timeline → RegulatoryBreachEvent[]
GET /runs/{id}/executive-explanation → ExecutiveDecisionExplanation
    │
    ▼
Frontend hooks: useBusinessImpact(), useTimeline(), useRegulatoryTimeline()
    │
    ▼
Dashboard panels: BusinessImpactTimeline, RegulatoryBreachTimeline, KPIs, RegulatoryNotes
```

---

## 12. Decision Gate

This plan is **LOCKED**. Before implementing:

1. **Pipeline wiring prerequisite:** `POST /runs` must invoke `run_v4_pipeline()` and serialize results to `_run_results` — without this, all GET endpoints return empty
2. **Frontend type prerequisite:** `RunResult` in `src/types/observatory.ts` must include optional `business_impact`, `loss_trajectory`, `regulatory_breaches` fields (Step 5, Phase 3)
3. **V2 dead code prerequisite:** V2 `frontend/app/` must be removed before building new Timeline tab components (Step 3, Phase 1)
4. **API client prerequisite:** `src/lib/api.ts` must add `observatory.businessImpact()`, `observatory.timeline()`, `observatory.regulatoryTimeline()` methods

Awaiting your command to begin execution.
