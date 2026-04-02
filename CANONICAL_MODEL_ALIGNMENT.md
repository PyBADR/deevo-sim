# Canonical Model Alignment Plan — Step 5 (LOCKED)

**Date:** 2026-04-02
**Scope:** 16 target models × 4 model locations
**Goal:** Single source of truth per model, backend → frontend type parity, zero duplicate definitions

---

## 1. Model Location Inventory

The codebase has **4 competing model locations**:

| # | Location | Generation | Framework | Role | Status |
|---|----------|------------|-----------|------|--------|
| A | `backend/app/domain/models/` | **V4 canonical** | Pydantic v2 | Domain models with field-level validation, typed enums, breach flags | **AUTHORITY** |
| B | `backend/app/schemas/observatory.py` | **V1 API** | Pydantic v2 | API output contract with bilingual labels, `ObservatoryOutput` envelope | **REFACTOR** → thin serializer on top of A |
| C | `backend/src/schemas/` | **V1 duplicate** | Pydantic v2 (`VersionedModel`) | Near-copy of B split into files, uses `src.schemas.base` imports | **REMOVE** — dead code from `backend/src/` |
| D | `backend/src/models/canonical.py` | **V0 ingest** | Pydantic v2 (`CanonicalBase`) | Geospatial/event/transport ingest models (Flight, Vessel, Port, etc.) | **KEEP** — separate concern (ingest, not domain) |

### Frontend Type Locations

| # | Location | Generation | Role | Status |
|---|----------|------------|------|--------|
| E | `frontend/src/types/observatory.ts` | **V1 API** | TypeScript types consumed by dashboard components (`RunResult`) | **REFACTOR** → align with A |
| F | `frontend/lib/types/observatory.ts` | **V4 mirror** | TypeScript mirror of A (field-exact copy of `backend/app/domain/models/`) | **PROMOTE** → merge into E, then delete file |
| G | `frontend/src/types/index.ts` | **Legacy** | Geo/event/graph types (Event, Flight, Vessel, GraphNode, etc.) | **KEEP** — globe/map layer types, not domain |

---

## 2. Target Model Cross-Reference (16 Models)

### ✅ MATCH — Exists in V4 canonical (Location A), field-complete

| # | Target Model | Backend File (A) | Frontend V4 (F) | Frontend V1 (E) | Backend V1 (B) | Verdict |
|---|-------------|------------------|-----------------|-----------------|----------------|---------|
| 1 | **Scenario** | `scenario.py` — 114 lines, 14 fields + `RegulatoryProfile`, `ScenarioTimeConfig`, `ScenarioDna`, `TriggerEvent`, `SectorImpactLink` sub-models | ✅ `Scenario` interface mirrors A exactly | ❌ Not present (E uses `ScenarioCreate` inline in `RunResult.scenario`) | `ScenarioInput` — simplified (6 fields, no graph) | **A is canonical.** E needs `Scenario` type added. B's `ScenarioInput` is a thin API input — keep as API schema only. |
| 2 | **Entity** | `entity.py` — 13 fields, typed `entity_type`, `regulatory_classification` | ✅ Exact mirror | ❌ Not present | `Entity` in B — simplified (7 fields, `layer`/`sector`/`severity`/`metadata`) | **A is canonical.** B's `Entity` is a graph-display model — rename to `GraphEntity` or remove. |
| 3 | **Edge** | `edge.py` — 11 fields, typed `relation_type` | ✅ Exact mirror | ❌ Not present | `Edge` in B — simplified (5 fields, `source`/`target`/`weight`/`propagation_factor`/`edge_type`) | **A is canonical.** B's `Edge` is a graph-display model — rename to `GraphEdge` or remove. |
| 4 | **FlowState** | `flow_state.py` — 10 fields, typed `flow_status` | ✅ Exact mirror | ❌ Not present | `FlowState` in B — different shape (5 fields, `timestep`/`entity_states` dict/`total_stress`/`peak_entity`/`converged`) | **A is canonical.** B's `FlowState` is a propagation-engine internal — rename to `PropagationSnapshot` or remove. |
| 5 | **FinancialImpact** | `financial_impact.py` — 10 fields, per-entity loss | ✅ Exact mirror | ✅ In E as `FinancialImpact` but **different shape** (aggregate: `headline_loss_usd`, `peak_day`, `severity_code`) | `FinancialImpact` in B — same shape as E (aggregate) | **A is canonical (per-entity).** E and B have an **aggregate** version that maps to `RunResult.headline` — rename to `RunHeadline` (already exists in E). |
| 6 | **BankingStress** | `banking_stress.py` — 12 fields + `BankingBreachFlags` | ✅ Exact mirror | ✅ In E but **different shape** (aggregate: `total_exposure_usd`, `aggregate_stress`, `classification`, `affected_institutions[]`) | `BankingStress` in B — aggregate (7 fields, `stress_score`) | **A is canonical (per-entity).** E has an aggregate wrapper — rename to `BankingStressSummary`. B is a simplified API view. |
| 7 | **InsuranceStress** | `insurance_stress.py` — 8 fields + `InsuranceBreachFlags` | ✅ Exact mirror | ✅ In E but **different shape** (aggregate: `portfolio_exposure_usd`, `claims_surge_multiplier`, `ifrs17_risk_adjustment_pct`, `affected_lines[]`) | `InsuranceStress` in B — aggregate (8 fields, `stress_score`) | **A is canonical (per-entity).** Same pattern as BankingStress. |
| 8 | **FintechStress** | `fintech_stress.py` — 8 fields + `FintechBreachFlags` | ✅ Exact mirror | ✅ In E but **different shape** (aggregate: `payment_volume_impact_pct`, `api_availability_pct`, `affected_platforms[]`) | `FintechStress` in B — aggregate (7 fields, `stress_score`) | **A is canonical (per-entity).** Same pattern. |
| 9 | **DecisionAction** | `decision.py` — 18 fields, typed `action_type`, `target_level`, `reason_codes[]` | ✅ Exact mirror | ✅ In E but **different shape** (simplified: `id`/`action`/`action_ar`/`sector`/`owner`/`urgency`/`value`/`priority`/`cost_usd`/`loss_avoided_usd`) | `DecisionAction` in B — API view (17 fields, `title`/`title_ar`/`status` HITL) | **A is canonical.** E's version is a dashboard-friendly projection — rename to `DecisionActionView`. B's version is the API serialization — align field names. |
| 10 | **DecisionPlan** | `decision.py` — 10 fields, `plan_status` typed | ✅ Exact mirror | ✅ In E but **different shape** (`run_id`/`scenario_label`/`total_loss_usd`/`peak_day`/`actions[]`/`all_actions[]`) | `DecisionPlan` in B — API view (8 fields, `plan_id`/`name`/`sectors_covered[]`) | **A is canonical.** E's version is a dashboard wrapper — rename to `DecisionPlanView`. |
| 11 | **RegulatoryState** | `regulatory_state.py` — 11 fields, typed `breach_level` | ✅ Exact mirror | ❌ Not present in E | `RegulatoryState` in B — **completely different** (GCC-specific: `pdpl_compliant`/`ifrs17_impact`/`sama_alert_level`/`cbuae_alert_level`/`sanctions_exposure`) | **A is canonical (aggregate compliance).** B's version is a GCC-specific regulatory view — rename to `GCCRegulatoryProfile` and keep as supplementary. |
| 12 | **ExplanationPack** | `explanation.py` — 9 fields + `ExplanationDriver`, `StageTrace`, `ActionExplanation`, `Equations` sub-models | ✅ Exact mirror (slight field name differences in sub-models) | ✅ In E but **different shape** (`narrative_en`/`narrative_ar`/`causal_chain: CausalStep[]`) | `ExplanationPack` in B — simplified (7 fields, `summary_en`/`summary_ar`/`key_findings`/`causal_chain: str[]`) | **A is canonical.** E and B are simplified narrative views. |

### ✅ MATCH — Exists in V4 canonical (Location A), in `business_impact.py`

| # | Target Model | Backend File (A) | Frontend V4 (F) | Frontend V1 (E) | Verdict |
|---|-------------|------------------|-----------------|-----------------|---------|
| 13 | **BusinessImpactSummary** | `business_impact.py` — 12 fields, typed `business_severity`, `executive_status` | ✅ Mirror (F adds `time_to_failures[]`, `regulatory_breach_events[]`, `loss_trajectory[]` as nested arrays) | ❌ Not in E | **A is canonical.** F's version bundles related arrays — keep A flat, compose at API layer. |
| 14 | **LossTrajectoryPoint** | `business_impact.py` — 12 fields, typed `status` | ✅ Mirror (F omits `run_id`, `scope_level`, `scope_ref`) | ❌ Not in E | **A is canonical.** F's version is a display projection — acceptable subset. |
| 15 | **TimeToFailure** | `business_impact.py` — 11 fields, typed `failure_type` | ✅ Mirror (F simplified: 6 fields) | ❌ Not in E | **A is canonical.** F's version is a display projection. |
| 16 | **RegulatoryBreachEvent** | `business_impact.py` — 12 fields, typed `metric_name`, `breach_direction`, `breach_level` | ✅ Mirror (F omits `run_id`, `scope_level`, `scope_ref`, uses `metric_type` not `metric_name`) | ❌ Not in E | **A is canonical.** F has minor field name drift — fix. |

---

## 3. Models That Must Be Refactored

### 3.1 Frontend `src/types/observatory.ts` (Location E) — API Response Types

These types serve the dashboard and are consumed by components. They are **aggregate/summary shapes** wrapping the per-entity canonical models. They are NOT wrong — they are a different abstraction layer. The issue is **naming collisions**.

| Current Name in E | Collides With (A) | Refactor Target | Reason |
|-------------------|-------------------|-----------------|--------|
| `FinancialImpact` | `FinancialImpact` (per-entity) | **Keep as-is** — this is `RunHeadline` (already aliased in E line 159) | E's version is the aggregate headline, not per-entity. The `RunResult.headline` field already uses `RunHeadline`. No collision in practice. |
| `BankingStress` | `BankingStress` (per-entity) | **No rename needed** — E's version is the aggregate summary consumed by dashboard. Import paths differentiate. | Dashboard components never import per-entity models from F. |
| `InsuranceStress` | `InsuranceStress` (per-entity) | **Same as above** | |
| `FintechStress` | `FintechStress` (per-entity) | **Same as above** | |
| `DecisionAction` | `DecisionAction` (per-entity) | **No rename needed** — E's version is the dashboard-facing projection. | |

**Decision:** E's types stay as-is for now. They are the **API response contract** consumed by the frontend. The V4 canonical types in F (`frontend/lib/types/observatory.ts`) mirror the backend domain models and will be used when we need per-entity granularity. No rename needed because import paths are different (`@/types/observatory` vs `@/lib/types/observatory`).

### 3.2 Frontend `lib/types/observatory.ts` (Location F) — Field Drift

| Model | Drift | Fix |
|-------|-------|-----|
| `LossTrajectoryPoint` | Missing `run_id`, `scope_level`, `scope_ref` (optional on frontend) | Add as optional fields |
| `TimeToFailure` | Uses `failure_type: FailureType` (broader enum than backend's 5 literals) | Align enum values |
| `RegulatoryBreachEvent` | Uses `metric_type` instead of `metric_name` | Rename to `metric_name` |
| `StageTrace` | Uses `started_at`/`completed_at`/`input_hash`/`output_hash`/`records_processed` instead of backend's `input_ref`/`output_ref`/`notes` | **Keep F's version** — it's richer for the AnalystTrace panel |
| `CauseEffectLink` | Uses `cause`/`effect`/`magnitude`/`confidence` instead of backend's `cause`/`effect`/`business_consequence`/`evidence_metric`/`evidence_value` | Align to backend — add `business_consequence`, `evidence_metric`, `evidence_value` |
| `ExplanationDriver` | Uses `driver_id`/`description`/`contribution_pct` instead of backend's `driver`/`magnitude`/`unit` | Align to backend |

### 3.3 Backend `app/schemas/observatory.py` (Location B) — API Serialization Layer

This file serves as the **API output envelope** (`ObservatoryOutput`). It must become a thin wrapper that:
1. Imports domain models from `app/domain/models/`
2. Adds only serialization-specific fields (`timestamp`, `audit_hash`, `computed_in_ms`, `stage_timings`)
3. Removes duplicate model definitions

| Current B Model | Action | Replacement |
|-----------------|--------|-------------|
| `ScenarioInput` | **KEEP** — API input schema (6 fields). Not a domain model. | Rename to `ScenarioCreateRequest` |
| `FinancialImpact` | **REMOVE** — replace with import from `domain.models` | Use `domain.models.FinancialImpact` for per-entity, keep aggregate as `FinancialHeadline` |
| `BankingStress` | **REMOVE** — replace with import | Use `domain.models.BankingStress` |
| `InsuranceStress` | **REMOVE** — replace with import | Use `domain.models.InsuranceStress` |
| `FintechStress` | **REMOVE** — replace with import | Use `domain.models.FintechStress` |
| `DecisionAction` | **REMOVE** — replace with import | Use `domain.models.DecisionAction` |
| `DecisionPlan` | **REMOVE** — replace with import | Use `domain.models.DecisionPlan` |
| `Entity` | **REMOVE** — replace with import | Use `domain.models.Entity` |
| `Edge` | **REMOVE** — replace with import | Use `domain.models.Edge` |
| `FlowState` | **REMOVE** — replace with import | Use `domain.models.FlowState` |
| `RegulatoryState` | **REFACTOR** — B has GCC-specific fields not in A | Merge GCC fields into A or keep B as `GCCRegulatoryView` extending A |
| `ExplanationPack` | **REMOVE** — replace with import | Use `domain.models.ExplanationPack` |
| `ObservatoryOutput` | **REFACTOR** — keep as API envelope, import all models from A | Becomes a thin composition of domain model imports |
| `LABELS` | **KEEP** — bilingual label dict, not a model | Move to `app/i18n/labels.py` |
| `FLOW_STAGES` | **KEEP** — pipeline metadata | Move to `app/core/constants.py` |
| `PROJECT` | **KEEP** — project identity | Move to `app/core/constants.py` |

---

## 4. Legacy Payloads to Remove

### 4.1 `backend/src/` — Entire Directory (Location C)

| File | Models | Reason for Removal |
|------|--------|--------------------|
| `backend/src/schemas/__init__.py` | Re-exports of 12 schemas | **Dead code.** `docker-compose.yml` uses `app.main:app`, not `src.main:app`. These are never imported at runtime. |
| `backend/src/schemas/scenario.py` | `Scenario`, `ScenarioCreate` | Duplicate of A + B |
| `backend/src/schemas/entity.py` | `Entity` | Duplicate of A |
| `backend/src/schemas/edge.py` | `Edge` | Duplicate of A |
| `backend/src/schemas/flow_state.py` | `FlowState` | Duplicate of A |
| `backend/src/schemas/financial_impact.py` | `FinancialImpact` | Duplicate of A |
| `backend/src/schemas/banking_stress.py` | `BankingStress` | Duplicate of A |
| `backend/src/schemas/insurance_stress.py` | `InsuranceStress` | Duplicate of A |
| `backend/src/schemas/fintech_stress.py` | `FintechStress` | Duplicate of A |
| `backend/src/schemas/decision.py` | `DecisionAction`, `DecisionPlan` | Duplicate of A |
| `backend/src/schemas/explanation.py` | `CausalStep`, `ExplanationPack` | Duplicate of A |
| `backend/src/schemas/regulatory_state.py` | `RegulatoryState` | Duplicate of A |
| `backend/src/schemas/base.py` | `VersionedModel` | Duplicate of A |
| `backend/src/models/canonical.py` | 25+ geospatial/ingest models | **NOT a duplicate of A.** But this file belongs to the ingest pipeline (`backend/src/`), which is dead code per `docker-compose.yml`. Move models worth keeping into `backend/app/connectors/` or delete. |
| `backend/src/models/orm.py` | ORM bindings | Dead code — no SQLAlchemy in `backend/app/` |

**Total removal:** 15 files, ~30 model classes

### 4.2 Frontend Legacy Types to Remove

| Type in `src/types/index.ts` (G) | Reason |
|-----------------------------------|--------|
| `Scenario` (lines 177–183) | Replaced by V4 `Scenario` in F |
| `ScenarioResult` (lines 185–199) | Replaced by `RunResult` in E |
| `DecisionAction` (lines 334–342) | Replaced by V4 `DecisionAction` in F and E |
| `DecisionOutput` (lines 326–332) | Replaced by `DecisionPlan` in F and E |

**Keep in G:** `Event`, `Flight`, `Vessel`, `Airport`, `Port`, `Corridor`, `GraphNode`, `GraphEdge`, `GlobeLayer`, `RiskScore`, `Chokepoint`, `PropagationResult`, `SystemStress`, `InsuranceExposure`, `ClaimsSurge` — these serve the globe/map/graph layers and have no V4 domain equivalent.

### 4.3 Frontend `lib/` Duplicates to Remove

| File | Reason |
|------|--------|
| `frontend/lib/api/client.ts` | Replaced by `src/lib/api.ts` |
| `frontend/lib/api/index.ts` | Re-export of dead client |
| `frontend/lib/types.ts` | Replaced by `src/types/index.ts` |
| `frontend/lib/i18n.ts` | Replaced by `src/i18n/en.json` + `ar.json` |
| `frontend/lib/mock-data.ts` | Mock data — not needed with real API |
| `frontend/lib/gcc-graph.ts` | Replaced by `@deevo/gcc-knowledge-graph` package |

**Keep in `lib/`:** `lib/types/observatory.ts` (V4 mirror — merge useful parts into `src/types/observatory.ts`, then delete), `lib/server/` (RBAC, audit, auth, execution, store, trace — server-side middleware).

---

## 5. Safe Migration Order

### Phase 1: Remove Dead Backend (zero risk — never imported at runtime)

1. Delete `backend/src/schemas/` directory (12 files)
2. Delete `backend/src/models/orm.py`
3. Evaluate `backend/src/models/canonical.py` — if any model is imported by `backend/app/`, move it there first; otherwise delete
4. Delete `backend/src/__init__.py` and empty parent dirs
5. **Verify:** `cd backend && python -c "from app.domain.models import *; print('OK')"` — must pass
6. **Verify:** `cd backend && python -c "from app.schemas.observatory import ObservatoryOutput; print('OK')"` — must pass

**Risk:** ZERO. `docker-compose.yml` entrypoint is `app.main:app`. The `backend/src/` tree is unreachable.

### Phase 2: Refactor Backend API Schemas (low risk — internal wiring change)

1. In `app/schemas/observatory.py`:
   - Remove all duplicate model class definitions (Entity, Edge, FlowState, FinancialImpact, BankingStress, InsuranceStress, FintechStress, DecisionAction, DecisionPlan, ExplanationPack)
   - Replace with imports from `app.domain.models`
   - Keep `ScenarioInput` (rename to `ScenarioCreateRequest`)
   - Keep `ObservatoryOutput` as thin envelope importing domain models
   - Merge B's `RegulatoryState` GCC fields into A's `RegulatoryState` or create `GCCRegulatoryView` extending A
2. Move `LABELS` to `app/i18n/labels.py`
3. Move `FLOW_STAGES`, `PROJECT`, `CORE_OBJECTS`, `RUNTIME_FLOW` to `app/core/constants.py`
4. Update all imports in `app/api/`, `app/scenarios/`, `app/intelligence/` that reference `app.schemas.observatory` models
5. **Verify:** Run full backend test suite. Every API endpoint must return valid JSON matching the schema.

**Risk:** LOW-MEDIUM. Import path changes across ~10 files. No field changes.

### Phase 3: Align Frontend V4 Types (low risk — additive changes)

1. In `frontend/lib/types/observatory.ts` (F):
   - Fix `RegulatoryBreachEvent.metric_type` → `metric_name`
   - Add optional `run_id`, `scope_level`, `scope_ref` to `LossTrajectoryPoint`
   - Align `CauseEffectLink` to backend: add `business_consequence`, `evidence_metric`, `evidence_value`
   - Align `ExplanationDriver` to backend: `driver_id` → `driver`, add `magnitude`, `unit`
2. In `frontend/src/types/observatory.ts` (E):
   - Add `RunResult` optional V4 extension fields: `business_impact?: BusinessImpactSummary`, `loss_trajectory?: LossTrajectoryPoint[]`, `regulatory_breaches?: RegulatoryBreachEvent[]`, `pipeline_stages?: StageTrace[]`, `audit_log?: AuditLogEntry[]`
   - Import V4 types from F where needed, or inline them
3. **Verify:** `cd frontend && npx tsc --noEmit` — must pass

**Risk:** LOW. Additive fields only. No existing component breaks.

### Phase 4: Remove Frontend Duplicates (low risk — dead code cleanup)

1. Remove from `src/types/index.ts` (G): `Scenario`, `ScenarioResult`, `DecisionAction`, `DecisionOutput` (4 interfaces)
2. Update any imports in `src/components/` or `src/features/` that reference removed types — point to E or F
3. Delete `frontend/lib/api/`, `frontend/lib/types.ts`, `frontend/lib/i18n.ts`, `frontend/lib/mock-data.ts`, `frontend/lib/gcc-graph.ts`
4. Merge unique content from `frontend/lib/types/observatory.ts` (F) into `frontend/src/types/observatory.ts` (E), then delete F
5. **Verify:** `cd frontend && npx tsc --noEmit && npm run build` — must pass

**Risk:** LOW-MEDIUM. Must trace all imports before deleting.

### Phase 5: Consolidate to Single Frontend Type File (cleanup)

After Phase 4, the frontend has two type files:
- `src/types/observatory.ts` — V1 API response types + merged V4 domain types
- `src/types/index.ts` — Geo/event/graph types for globe/map layers

This is the correct final state. Two files, two concerns:
- `observatory.ts` = domain models + API contract
- `index.ts` = visualization layer types (globe, graph, events)

No further action needed.

---

## 6. Model Authority Matrix (Final State)

| # | Model | Single Source of Truth | Frontend Type File | API Serializer |
|---|-------|----------------------|-------------------|----------------|
| 1 | Scenario | `backend/app/domain/models/scenario.py` | `src/types/observatory.ts` | `app/schemas/observatory.py::ScenarioCreateRequest` (input only) |
| 2 | Entity | `backend/app/domain/models/entity.py` | `src/types/observatory.ts` | Direct export from domain |
| 3 | Edge | `backend/app/domain/models/edge.py` | `src/types/observatory.ts` | Direct export from domain |
| 4 | FlowState | `backend/app/domain/models/flow_state.py` | `src/types/observatory.ts` | Direct export from domain |
| 5 | FinancialImpact | `backend/app/domain/models/financial_impact.py` | `src/types/observatory.ts` | Direct export from domain |
| 6 | BankingStress | `backend/app/domain/models/banking_stress.py` | `src/types/observatory.ts` | Direct export from domain |
| 7 | InsuranceStress | `backend/app/domain/models/insurance_stress.py` | `src/types/observatory.ts` | Direct export from domain |
| 8 | FintechStress | `backend/app/domain/models/fintech_stress.py` | `src/types/observatory.ts` | Direct export from domain |
| 9 | DecisionAction | `backend/app/domain/models/decision.py` | `src/types/observatory.ts` | Direct export from domain |
| 10 | DecisionPlan | `backend/app/domain/models/decision.py` | `src/types/observatory.ts` | Direct export from domain |
| 11 | RegulatoryState | `backend/app/domain/models/regulatory_state.py` | `src/types/observatory.ts` | Direct export + GCC extension |
| 12 | ExplanationPack | `backend/app/domain/models/explanation.py` | `src/types/observatory.ts` | Direct export from domain |
| 13 | BusinessImpactSummary | `backend/app/domain/models/business_impact.py` | `src/types/observatory.ts` | Direct export from domain |
| 14 | LossTrajectoryPoint | `backend/app/domain/models/business_impact.py` | `src/types/observatory.ts` | Direct export from domain |
| 15 | TimeToFailure | `backend/app/domain/models/business_impact.py` | `src/types/observatory.ts` | Direct export from domain |
| 16 | RegulatoryBreachEvent | `backend/app/domain/models/business_impact.py` | `src/types/observatory.ts` | Direct export from domain |

---

## 7. Bonus Models in V4 Canonical (Not in Target List but Present)

These exist in `backend/app/domain/models/` and should be kept:

| Model | File | Role |
|-------|------|------|
| `RegulatoryProfile` | `scenario.py` | Jurisdiction-specific regulatory thresholds (sub-model of Scenario) |
| `ScenarioTimeConfig` | `scenario.py` | Temporal engine parameters |
| `ScenarioDna` | `scenario.py` | Business identity + causal chain |
| `TriggerEvent` | `scenario.py` | Scenario trigger event |
| `SectorImpactLink` | `scenario.py` | Ordered sector impact chain link |
| `BankingBreachFlags` | `banking_stress.py` | Per-entity breach indicators |
| `InsuranceBreachFlags` | `insurance_stress.py` | Per-entity breach indicators |
| `FintechBreachFlags` | `fintech_stress.py` | Per-entity breach indicators |
| `ExplanationDriver` | `explanation.py` | Key outcome driver |
| `StageTrace` | `explanation.py` | Per-stage execution trace |
| `ActionExplanation` | `explanation.py` | Per-action explanation |
| `Equations` | `explanation.py` | Mandatory formula strings |
| `CauseEffectLink` | `business_impact.py` | Cause → effect → consequence chain |
| `LossTranslation` | `business_impact.py` | Business-language loss translation |
| `ExecutiveActionExplanation` | `business_impact.py` | Business-language action explanation |
| `ExecutiveDecisionExplanation` | `business_impact.py` | Full executive explanation package |
| `TimeStepState` | `time_engine.py` | System state at single timestep |
| `EntityTemporalImpact` | `time_engine.py` | Per-entity impact at single timestep |
| `VersionedModel` | `base.py` | Base model with frozen schema version |

---

## 8. Decision Gate

This alignment plan is **LOCKED**. Before implementing:

1. **Phase 1 prerequisite:** Confirm `backend/src/` is truly unreachable — `grep -r "from src\." backend/app/` must return zero results
2. **Phase 2 prerequisite:** Full list of files importing from `app.schemas.observatory` must be enumerated before changing imports
3. **Phase 3 prerequisite:** V2 `frontend/app/` dead code must be removed first (Step 3, Phase 1) to avoid type conflicts
4. **Phase 4 prerequisite:** `npx tsc --noEmit` must pass on current codebase before any type deletions

Awaiting your command to begin execution.
