# Backend Alignment Plan — Step 6 (LOCKED)

**Date:** 2026-04-02
**Scope:** 15 target modules × 4 code locations
**Pipeline:** 9 stages + 2 post-pipeline + 3 infrastructure services
**Goal:** One module per pipeline stage, zero duplicates, clean import graph

---

## 1. Current Backend Module Inventory

The backend has **4 competing code locations** for engine/service logic:

| # | Location | Role | Module Count | Status |
|---|----------|------|-------------|--------|
| A | `app/services/` | **V4 service engines** — one subdirectory per concern | 12 subdirs (banking, insurance, fintech, financial, decision, explainability, regulatory, reporting, business_impact, time_engine, audit, physics + propagation + scenario = empty) | **AUTHORITY** |
| B | `app/intelligence/engines/` | **V2 intelligence engines** — monolithic files | 5 files (scenario_engines.py ~875L, propagation_engine.py ~700L, decision_engine.py ~900L, monte_carlo.py, gcc_constants.py) | **REFACTOR** — absorb into A |
| C | `app/intelligence/` (sub-packages) | **V1-V2 specialized modules** | physics/ (2 files), physics_core/ (7 files), math_core/ (10 files), math/ (1 file), insurance/ (1 file), insurance_intelligence/ (4 files), scenario_engine/ (5 files) | **REFACTOR** — consolidate into A |
| D | `app/scenarios/` | **V1 scenario orchestration** | 3 files (engine.py ~250L, runner.py ~497L, templates.py) | **REFACTOR** — merge into A's scenario service |

### Orchestration Layer

| File | Lines | Role | Status |
|------|-------|------|--------|
| `app/orchestration/pipeline.py` | ~200 | V1 10-stage lifecycle: INGEST→NORMALIZE→ENRICH→STORE→GRAPH_BUILD→SCORE→PHYSICS_UPDATE→INSURANCE_UPDATE→SCENARIO_RUN→API_OUTPUT | **REMOVE** — replaced by pipeline_v4 |
| `app/orchestration/pipeline_v4.py` | ~300 | V4 9-stage pipeline with graceful degradation | **AUTHORITY** |
| `app/services/orchestrator.py` | ~150 | V1 service orchestrator wrapping pipeline.py | **REMOVE** — replaced by pipeline_v4 |

### Empty Service Directories (stubs, no engine code)

| Directory | Status |
|-----------|--------|
| `app/services/physics/` | **Empty** — logic in `intelligence/physics_core/` |
| `app/services/propagation/` | **Empty** — logic in `intelligence/engines/propagation_engine.py` |
| `app/services/scenario/` | **Empty** — logic in `intelligence/scenario_engine/` + `scenarios/` |

---

## 2. Target Module Cross-Reference (15 Modules)

### ✅ MATCH — Exists in `app/services/` (Location A), functional

| # | Target Module | Existing File | Lines | Pipeline Stage | Domain Models Used | Status |
|---|--------------|---------------|-------|---------------|-------------------|--------|
| 1 | **financial_engine** | `services/financial/engine.py` | ~200 | Stage 5: Financial | `FinancialImpact` | ✅ **MATCH** — sector GDP bases, loss = exposure × shock × propagation, currency impact |
| 2 | **banking_risk_engine** | `services/banking/engine.py` | ~150 | Stage 6a: Banking Risk | `BankingStress`, `BankingBreachFlags` | ✅ **MATCH** — deposit outflow, LCR/NSFR/CET1/CAR computation, breach flag detection |
| 3 | **insurance_risk_engine** | `services/insurance/engine.py` | ~150 | Stage 6b: Insurance Risk | `InsuranceStress`, `InsuranceBreachFlags` | ✅ **MATCH** — claims spike, reserve ratio, solvency ratio, combined ratio, breach flags |
| 4 | **fintech_engine** | `services/fintech/engine.py` | ~110 | Stage 6c: Fintech Risk | `FintechStress`, `FintechBreachFlags` | ✅ **MATCH** — transaction failure rate, settlement delay, service availability, breach flags |
| 5 | **regulatory_service** | `services/regulatory/engine.py` | ~100 | Stage 7: Regulatory | `RegulatoryState` | ✅ **MATCH** — Basel III compliance (LCR ≥1.0, NSFR ≥1.0, CET1 ≥4.5%, CAR ≥8%), breach level, mandatory actions |
| 6 | **decision_engine** | `services/decision/engine.py` | ~350 | Stage 8: Decision | `DecisionAction`, `DecisionPlan` | ✅ **MATCH** — 20 action templates, 5-factor priority formula (0.25U + 0.30V + 0.20R + 0.15F + 0.10T), RBAC, HITL approval |
| 7 | **explainability_engine** | `services/explainability/engine.py` | ~200 | Stage 9: Explanation | `ExplanationPack`, `ExplanationDriver`, `StageTrace`, `ActionExplanation`, `Equations` | ✅ **MATCH** — bilingual narrative, confidence scoring, stage traces, mandatory equations |
| 8 | **business_impact_service** | `services/business_impact/engine.py` | ~250 | Post-pipeline: §16 | `BusinessImpactSummary`, `LossTrajectoryPoint`, `TimeToFailure`, `RegulatoryBreachEvent`, `CauseEffectLink`, `LossTranslation`, `ExecutiveDecisionExplanation` | ✅ **MATCH** — cascading impact, sector contagion, loss trajectory, time-to-failure prediction |
| 9 | **timeline_service** | `services/time_engine/engine.py` | ~200 | Post-pipeline: §17 | `TimeStepState`, `EntityTemporalImpact` | ✅ **MATCH** — timestep simulation, shock decay ShockEffective(t) = S × (1-d)^t, per-entity temporal tracking |
| 10 | **reporting_service** | `services/reporting/engine.py` | ~200 | Post-pipeline | `ExplanationPack`, `BusinessImpactSummary` | ✅ **MATCH** — three modes (Executive, Analyst, Regulatory Brief), bilingual output |
| 11 | **audit_service** | `services/audit/engine.py` | ~150 | Cross-cutting | SHA-256 hashing, computation provenance | ✅ **MATCH** — audit trail, decision verification, hash chain integrity |

### ⚠️ SPLIT — Logic exists but split across multiple locations

| # | Target Module | Current Locations | Pipeline Stage | Issue | Resolution |
|---|--------------|-------------------|---------------|-------|------------|
| 12 | **scenario_engine** | `intelligence/scenario_engine/runner.py` (~129L, mock), `scenarios/runner.py` (~497L, production), `scenarios/engine.py` (~250L, orchestrator), `scenarios/templates.py`, `intelligence/engines/scenario_engines.py` (~875L, 17 templates) | Stage 1: Scenario | **5 files across 3 directories.** Mock runner in intelligence/, production runner in scenarios/, 17 templates in intelligence/engines/. | Consolidate into `services/scenario/engine.py`. Keep template definitions as `services/scenario/templates.py`. Delete mock runner. |
| 13 | **physics_engine** | `intelligence/physics_core/` (7 files: flow_field, friction, pressure, shockwave, threat_field, potential_routing, system_stress), `intelligence/physics/` (2 files: flow_field, gcc_physics_config), `services/physics/` (empty) | Stage 2: Physics | **9 files across 2 directories + 1 empty stub.** `physics_core/` is the V4 implementation. `physics/` is the V2 implementation with GCC-specific config. | Consolidate into `services/physics/engine.py` as facade. Keep `intelligence/physics_core/` as computation library (pure functions). Delete `intelligence/physics/`. |
| 14 | **propagation_engine** | `intelligence/engines/propagation_engine.py` (~700L), `intelligence/math/propagation.py`, `intelligence/math_core/propagation.py`, `services/propagation/` (empty) | Stage 4: Propagation | **3 files across 2 directories + 1 empty stub.** `engines/propagation_engine.py` is the main engine. Two math files provide helper functions. | Consolidate into `services/propagation/engine.py`. Import pure math from `intelligence/math_core/`. |

### ❌ MISSING — No dedicated module exists

| # | Target Module | Pipeline Stage | What Exists | What's Missing | Build Priority |
|---|--------------|---------------|-------------|----------------|---------------|
| 15 | **entity_graph_service** | Stage 3: Graph | `app/graph/` directory (contents unclear — likely Neo4j connectors), `app/db/neo4j.py` (Neo4j connection), `scenarios/engine.py` has graph-build logic inline | **No dedicated graph service.** Graph building is scattered across scenario engine (inline entity/edge construction) and Neo4j connector (raw Cypher queries). | **HIGH** — Stage 3 is the bridge between physics and propagation. Must extract graph-build logic from scenarios/engine.py into `services/graph/engine.py`. |

---

## 3. Duplicate Module Analysis

### 3.1 Scenario Engine (5 duplicates → 1 target)

| File | Purpose | Keep/Remove |
|------|---------|-------------|
| `intelligence/engines/scenario_engines.py` (~875L) | 17 GCC scenario templates with stress mappings | **KEEP** — extract templates into `services/scenario/templates.py` |
| `intelligence/scenario_engine/runner.py` (~129L) | Mock runner: baseline→shock→propagate→quantify→decide | **REMOVE** — mock, superseded by production runner |
| `intelligence/scenario_engine/baseline.py` | Baseline state computation | **EVALUATE** — merge into `services/scenario/engine.py` if useful |
| `intelligence/scenario_engine/delta.py` | Shock delta computation | **EVALUATE** — merge if useful |
| `intelligence/scenario_engine/inject.py` | Shock injection | **EVALUATE** — merge if useful |
| `intelligence/scenario_engine/explanation.py` | Scenario-level explanation | **REMOVE** — superseded by `services/explainability/engine.py` |
| `scenarios/runner.py` (~497L) | Production runner: 14 event types, cascade propagation, regression validation | **KEEP** — this becomes the core of `services/scenario/engine.py` |
| `scenarios/engine.py` (~250L) | Orchestrator: normalize→graph→score | **REFACTOR** — extract graph-build into `services/graph/engine.py`, rest into scenario service |
| `scenarios/templates.py` | Template definitions | **MERGE** — combine with intelligence/engines/scenario_engines.py templates |

### 3.2 Decision Engine (2 duplicates → 1 target)

| File | Purpose | Keep/Remove |
|------|---------|-------------|
| `services/decision/engine.py` (~350L) | V4 decision engine with 20 templates, RBAC, HITL | **KEEP** — this is canonical |
| `intelligence/engines/decision_engine.py` (~900L) | V2 decision intelligence with 20 templates, cost/impact matrices | **MERGE** — contains richer template definitions and DPS formula. Merge unique content into services/decision. Then delete. |

### 3.3 Propagation Engine (3 duplicates → 1 target)

| File | Purpose | Keep/Remove |
|------|---------|-------------|
| `intelligence/engines/propagation_engine.py` (~700L) | Graph-based discrete dynamics: x_i(t+1) = s_i × Σ(w_ji × p_ji × x_j(t)) - d_i × x_i(t) + shock_i | **KEEP** — this is the core algorithm |
| `intelligence/math/propagation.py` | Math helpers for propagation | **MERGE** — fold into propagation engine or keep as utility |
| `intelligence/math_core/propagation.py` | Math helpers (different file) | **MERGE** — fold into propagation engine or keep as utility |

### 3.4 Physics (9 files → 1 facade + library)

| Location | Files | Keep/Remove |
|----------|-------|-------------|
| `intelligence/physics_core/` | flow_field, friction, pressure, shockwave, threat_field, potential_routing, system_stress (7 files) | **KEEP** — pure computation library. These are stateless math functions. |
| `intelligence/physics/` | flow_field, gcc_physics_config (2 files) | **MERGE** — gcc_physics_config into `services/physics/config.py`. Delete duplicate flow_field. |

### 3.5 Insurance (3 locations → 1 target)

| Location | Files | Keep/Remove |
|----------|-------|-------------|
| `services/insurance/engine.py` (~150L) | V4 insurance stress engine | **KEEP** — canonical |
| `intelligence/insurance/claims_uplift.py` | Claims uplift calculator | **MERGE** — fold into services/insurance if needed |
| `intelligence/insurance_intelligence/` (4 files) | claims_surge, portfolio_exposure, severity_projection, underwriting_watch | **MERGE** — these are sub-computations. Import from services/insurance/engine.py as needed. |

### 3.6 Orchestration (3 files → 1 target)

| File | Purpose | Keep/Remove |
|------|---------|-------------|
| `orchestration/pipeline_v4.py` (~300L) | V4 9-stage pipeline with graceful degradation | **KEEP** — canonical orchestrator |
| `orchestration/pipeline.py` (~200L) | V1 10-stage lifecycle | **REMOVE** — superseded by pipeline_v4 |
| `services/orchestrator.py` (~150L) | V1 service orchestrator | **REMOVE** — superseded by pipeline_v4 |

---

## 4. Target Architecture (Final State)

### 4.1 Canonical Module Map

```
backend/app/
├── orchestration/
│   └── pipeline.py              ← RENAMED from pipeline_v4.py (delete old pipeline.py)
│
├── services/
│   ├── scenario/
│   │   ├── engine.py            ← CONSOLIDATED from scenarios/runner.py + scenarios/engine.py
│   │   └── templates.py         ← CONSOLIDATED from scenarios/templates.py + intelligence/engines/scenario_engines.py
│   │
│   ├── physics/
│   │   ├── engine.py            ← NEW facade calling intelligence/physics_core/ functions
│   │   └── config.py            ← MOVED from intelligence/physics/gcc_physics_config.py
│   │
│   ├── graph/
│   │   └── engine.py            ← NEW — extracted from scenarios/engine.py graph-build logic
│   │
│   ├── propagation/
│   │   └── engine.py            ← MOVED from intelligence/engines/propagation_engine.py
│   │
│   ├── financial/
│   │   └── engine.py            ← KEEP as-is (Stage 5)
│   │
│   ├── banking/
│   │   └── engine.py            ← KEEP as-is (Stage 6a)
│   │
│   ├── insurance/
│   │   └── engine.py            ← KEEP + merge intelligence/insurance* sub-computations
│   │
│   ├── fintech/
│   │   └── engine.py            ← KEEP as-is (Stage 6c)
│   │
│   ├── regulatory/
│   │   └── engine.py            ← KEEP as-is (Stage 7)
│   │
│   ├── decision/
│   │   └── engine.py            ← KEEP + merge intelligence/engines/decision_engine.py templates
│   │
│   ├── explainability/
│   │   └── engine.py            ← KEEP as-is (Stage 9)
│   │
│   ├── business_impact/
│   │   └── engine.py            ← KEEP as-is (§16)
│   │
│   ├── time_engine/
│   │   └── engine.py            ← KEEP as-is (§17, mapped to target "timeline_service")
│   │
│   ├── reporting/
│   │   └── engine.py            ← KEEP as-is
│   │
│   └── audit/
│       └── engine.py            ← KEEP as-is
│
├── intelligence/
│   ├── physics_core/            ← KEEP as pure math library (7 files, stateless functions)
│   └── math_core/               ← KEEP as pure math library (10 files, stateless functions)
│
└── domain/
    └── models/                  ← KEEP as-is (canonical Pydantic v2 domain models)
```

### 4.2 Directories to Delete After Consolidation

| Directory | Files | Reason |
|-----------|-------|--------|
| `intelligence/engines/` | scenario_engines.py, propagation_engine.py, decision_engine.py, monte_carlo.py, gcc_constants.py | Content merged into services/ |
| `intelligence/physics/` | flow_field.py, gcc_physics_config.py | Duplicate of physics_core, config moved |
| `intelligence/math/` | propagation.py | Merged into services/propagation/ |
| `intelligence/insurance/` | claims_uplift.py | Merged into services/insurance/ |
| `intelligence/insurance_intelligence/` | 4 files | Merged into services/insurance/ |
| `intelligence/scenario_engine/` | 5 files | Merged into services/scenario/ |
| `scenarios/` | engine.py, runner.py, templates.py | Merged into services/scenario/ |
| `orchestration/pipeline.py` | V1 pipeline | Superseded by pipeline_v4 |
| `services/orchestrator.py` | V1 orchestrator | Superseded by pipeline_v4 |

---

## 5. Runtime Flow Alignment

### V4 Pipeline Stages → Service Mapping

```
Stage 1: Scenario Setup
  └── services/scenario/engine.py
      Input:  ScenarioCreateRequest (API schema)
      Output: Scenario (domain model) with entities[], edges[], scenario_dna

Stage 2: Physics
  └── services/physics/engine.py → intelligence/physics_core/*
      Input:  Scenario.entities, Scenario.edges
      Output: FlowState[] (per-entity flow snapshots)

Stage 3: Graph Snapshot
  └── services/graph/engine.py → db/neo4j.py
      Input:  Scenario.entities, Scenario.edges
      Output: Graph materialized in Neo4j, entity/edge IDs indexed

Stage 4: Propagation
  └── services/propagation/engine.py → intelligence/math_core/*
      Input:  FlowState[], Graph edges, shock_intensity
      Output: Updated FlowState[] with propagated impacts

Stage 5: Financial Impact
  └── services/financial/engine.py
      Input:  Scenario, FlowState[] (propagated)
      Output: FinancialImpact[] (per-entity loss)

Stage 6: Sector Risk (parallel)
  ├── services/banking/engine.py
  │   Input:  FinancialImpact[] (entity_type=bank), RegulatoryProfile
  │   Output: BankingStress[] + BankingBreachFlags[]
  ├── services/insurance/engine.py
  │   Input:  FinancialImpact[] (entity_type=insurer), RegulatoryProfile
  │   Output: InsuranceStress[] + InsuranceBreachFlags[]
  └── services/fintech/engine.py
      Input:  FinancialImpact[] (entity_type=fintech), RegulatoryProfile
      Output: FintechStress[] + FintechBreachFlags[]

Stage 7: Regulatory
  └── services/regulatory/engine.py
      Input:  BankingStress[], InsuranceStress[], FintechStress[], RegulatoryProfile
      Output: RegulatoryState (aggregate compliance)

Stage 8: Decision
  └── services/decision/engine.py
      Input:  FinancialImpact[], BankingStress[], InsuranceStress[], FintechStress[], RegulatoryState
      Output: DecisionPlan with DecisionAction[] (top 3)

Stage 9: Explanation
  └── services/explainability/engine.py
      Input:  All stage outputs + Scenario
      Output: ExplanationPack (narrative, drivers, stage traces, equations)

Post-Pipeline: Business Impact (§16)
  └── services/business_impact/engine.py
      Input:  FinancialImpact[], BankingStress[], InsuranceStress[], FintechStress[], RegulatoryState
      Output: BusinessImpactSummary, LossTrajectoryPoint[], TimeToFailure[], RegulatoryBreachEvent[]

Post-Pipeline: Timeline (§17)
  └── services/time_engine/engine.py
      Input:  Scenario, FlowState[], FinancialImpact[]
      Output: TimeStepState[] with EntityTemporalImpact[]

Post-Pipeline: Reporting
  └── services/reporting/engine.py
      Input:  ExplanationPack, BusinessImpactSummary, DecisionPlan
      Output: ExecutiveReport, AnalystReport, RegulatoryBrief

Cross-Cutting: Audit
  └── services/audit/engine.py
      Input:  All stage inputs/outputs
      Output: SHA-256 audit trail, computation provenance
```

### Pipeline Orchestrator Contract

`orchestration/pipeline.py` (renamed from pipeline_v4.py) calls services in order:

```python
async def run_pipeline(scenario_input: ScenarioCreateRequest) -> RunResult:
    # Stage 1
    scenario = await scenario_service.create(scenario_input)

    # Stage 2 (optional — graceful degradation)
    flow_states = await physics_service.compute(scenario) or []

    # Stage 3 (optional)
    await graph_service.materialize(scenario)

    # Stage 4 (optional)
    flow_states = await propagation_service.propagate(flow_states, scenario) or flow_states

    # Stage 5 (mandatory — financial-first path)
    financial = await financial_service.compute(scenario, flow_states)

    # Stage 6 (parallel)
    banking, insurance, fintech = await asyncio.gather(
        banking_service.compute(financial, scenario.regulatory_profile),
        insurance_service.compute(financial, scenario.regulatory_profile),
        fintech_service.compute(financial, scenario.regulatory_profile),
    )

    # Stage 7
    regulatory = await regulatory_service.evaluate(banking, insurance, fintech, scenario.regulatory_profile)

    # Stage 8
    decisions = await decision_service.generate(financial, banking, insurance, fintech, regulatory)

    # Stage 9
    explanation = await explainability_service.explain(scenario, financial, banking, insurance, fintech, regulatory, decisions)

    # Post-pipeline (parallel)
    business_impact, timeline = await asyncio.gather(
        business_impact_service.compute(financial, banking, insurance, fintech, regulatory),
        time_engine_service.simulate(scenario, flow_states, financial),
    )

    # Audit
    audit_hash = await audit_service.record(run_id, all_stages)

    # Reporting (on demand, not every run)
    # reporting_service.generate(explanation, business_impact, decisions)

    return RunResult(...)
```

---

## 6. Safe Migration Order

### Phase 1: Delete Dead Orchestration (zero risk)

1. Delete `orchestration/pipeline.py` (V1 pipeline)
2. Rename `orchestration/pipeline_v4.py` → `orchestration/pipeline.py`
3. Delete `services/orchestrator.py` (V1 orchestrator)
4. Update import in `main.py` if it references old pipeline
5. **Verify:** `python -c "from app.orchestration.pipeline import *; print('OK')"`

### Phase 2: Create Missing Service — `services/graph/engine.py` (additive, zero breakage)

1. Create `services/graph/__init__.py`
2. Create `services/graph/engine.py` — extract graph-build logic from `scenarios/engine.py`
3. Wire into pipeline_v4.py as Stage 3
4. **Verify:** Graph materialization works (Neo4j connection test)

### Phase 3: Consolidate Scenario Engine (medium risk — merge 5 sources)

1. Create `services/scenario/engine.py` — merge production logic from `scenarios/runner.py`
2. Create `services/scenario/templates.py` — merge 17 templates from `intelligence/engines/scenario_engines.py` + `scenarios/templates.py`
3. Update pipeline to call `services.scenario.engine` instead of `scenarios.runner`
4. Keep `intelligence/scenario_engine/` temporarily (mark deprecated)
5. **Verify:** Scenario creation + template resolution works end-to-end

### Phase 4: Consolidate Propagation Engine (low risk — single source, just move)

1. Move `intelligence/engines/propagation_engine.py` → `services/propagation/engine.py`
2. Update import in pipeline
3. Keep `intelligence/math_core/propagation.py` as utility (imported by the engine)
4. Delete `intelligence/math/propagation.py` (duplicate of math_core version)
5. **Verify:** Propagation with known graph produces expected output

### Phase 5: Create Physics Facade (low risk — additive)

1. Create `services/physics/engine.py` as thin facade calling `intelligence/physics_core/` functions
2. Move `intelligence/physics/gcc_physics_config.py` → `services/physics/config.py`
3. Delete `intelligence/physics/flow_field.py` (duplicate of physics_core version)
4. **Verify:** Physics stage produces FlowState[] output

### Phase 6: Merge Intelligence Duplicates (low risk — content merge, no API change)

1. Merge unique templates from `intelligence/engines/decision_engine.py` into `services/decision/engine.py`
2. Merge `intelligence/insurance/claims_uplift.py` into `services/insurance/engine.py`
3. Merge useful sub-computations from `intelligence/insurance_intelligence/` into `services/insurance/engine.py`
4. Merge `intelligence/engines/gcc_constants.py` into `app/core/constants.py`
5. **Verify:** All 6a/6b/6c/8 stage outputs unchanged

### Phase 7: Delete Empty Stubs + Deprecated Code (cleanup)

1. Delete `intelligence/engines/` directory (all content merged)
2. Delete `intelligence/physics/` directory (content moved)
3. Delete `intelligence/math/` directory (merged into math_core)
4. Delete `intelligence/insurance/` directory (merged)
5. Delete `intelligence/insurance_intelligence/` directory (merged)
6. Delete `intelligence/scenario_engine/` directory (merged into services/scenario)
7. Delete `scenarios/` directory (merged into services/scenario)
8. Delete empty `services/physics/__init__.py` (replaced by real engine)
9. Delete empty `services/propagation/__init__.py` (replaced by real engine)
10. Delete empty `services/scenario/__init__.py` (replaced by real engine)
11. **Verify:** `python -c "from app.services import *; print('OK')"` — no import errors

---

## 7. Module Authority Matrix (Final State)

| # | Target Module | Canonical Location | Pipeline Stage | Input Types | Output Types |
|---|--------------|-------------------|---------------|-------------|-------------|
| 1 | scenario_engine | `services/scenario/engine.py` | Stage 1 | `ScenarioCreateRequest` | `Scenario` |
| 2 | physics_engine | `services/physics/engine.py` | Stage 2 | `Entity[]`, `Edge[]` | `FlowState[]` |
| 3 | entity_graph_service | `services/graph/engine.py` | Stage 3 | `Entity[]`, `Edge[]` | Neo4j graph |
| 4 | propagation_engine | `services/propagation/engine.py` | Stage 4 | `FlowState[]`, graph, shock | `FlowState[]` |
| 5 | financial_engine | `services/financial/engine.py` | Stage 5 | `Scenario`, `FlowState[]` | `FinancialImpact[]` |
| 6 | banking_risk_engine | `services/banking/engine.py` | Stage 6a | `FinancialImpact[]`, `RegulatoryProfile` | `BankingStress[]` |
| 7 | insurance_risk_engine | `services/insurance/engine.py` | Stage 6b | `FinancialImpact[]`, `RegulatoryProfile` | `InsuranceStress[]` |
| 8 | fintech_engine | `services/fintech/engine.py` | Stage 6c | `FinancialImpact[]`, `RegulatoryProfile` | `FintechStress[]` |
| 9 | regulatory_service | `services/regulatory/engine.py` | Stage 7 | Sector stresses, `RegulatoryProfile` | `RegulatoryState` |
| 10 | decision_engine | `services/decision/engine.py` | Stage 8 | All impacts + regulatory | `DecisionPlan` |
| 11 | explainability_engine | `services/explainability/engine.py` | Stage 9 | All stage outputs | `ExplanationPack` |
| 12 | business_impact_service | `services/business_impact/engine.py` | Post: §16 | All impacts + regulatory | `BusinessImpactSummary`, `LossTrajectoryPoint[]`, `TimeToFailure[]`, `RegulatoryBreachEvent[]` |
| 13 | timeline_service | `services/time_engine/engine.py` | Post: §17 | `Scenario`, `FlowState[]`, `FinancialImpact[]` | `TimeStepState[]` |
| 14 | reporting_service | `services/reporting/engine.py` | Post | `ExplanationPack`, `BusinessImpactSummary`, `DecisionPlan` | Executive/Analyst/Regulatory reports |
| 15 | audit_service | `services/audit/engine.py` | Cross-cutting | All stage I/O | SHA-256 audit trail |

---

## 8. Decision Gate

This alignment plan is **LOCKED**. Before implementing:

1. **Phase 1 prerequisite:** Confirm `pipeline_v4.py` is the active orchestrator in `main.py` — `grep -r "pipeline" app/main.py` must show v4
2. **Phase 2 prerequisite:** Neo4j connection must be verified — `docker-compose up neo4j` health check must pass
3. **Phase 3 prerequisite:** All 17 scenario templates must be catalogued with exact stress mappings before merging template files
4. **Phase 4 prerequisite:** Propagation engine discrete dynamics formula must be preserved exactly: `x_i(t+1) = s_i × Σ(w_ji × p_ji × x_j(t)) - d_i × x_i(t) + shock_i`
5. **Phase 6 prerequisite:** Decision engine 20 action templates must be diff'd between services/ and intelligence/ versions before merge — any unique templates in either file must be preserved

Awaiting your command to begin execution.
