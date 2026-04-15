# Signal Intelligence & Decision Engine — Classification & Clustering Design Brief

**Date:** 2026-04-15
**Branch:** `feature/signal-intelligence-classification-brief`
**Base:** `contract/unified-demo-operating-contract`
**Type:** Design brief — documentation only, no code changes
**Status:** Classifies the proposed system into implementation clusters with phased roadmap

---

## Purpose

This document classifies the proposed Signal Intelligence & Decision Engine into clear implementation clusters, maps each cluster against the current platform state, assigns risk controls, and defines a phased rollout that protects the existing governed simulation platform.

No code is implemented. No scenarios are changed. No UI is modified. No live feeds are connected. No production deployment is triggered.

---

## C1 — Signal Ingestion

### Sources

| Source Category | Examples | Protocol | Refresh Model |
|----------------|----------|----------|---------------|
| Market data feeds | Brent crude, GCC equity indices, FX rates, CDS spreads | REST/WebSocket | Real-time (≤15 min) |
| News & wire services | Reuters, Bloomberg, Al Jazeera, MEED | RSS/Atom, API | Near real-time (≤60 min) |
| Government statistics | GCC central bank releases, OPEC reports, sovereign filings | API, scrape | Periodic (7–35 day windows) |
| Maritime/shipping | AIS data (AISSTREAM), port throughput, Suez/Hormuz transit | WebSocket, REST | Real-time (≤30 min) |
| Aviation/logistics | OpenSky, IATA capacity, freight indices | REST | Near real-time (≤60 min) |
| Regulatory filings | SAMA, CBUAE, CBB, CBK, CBO, QCB circulars | API, scrape | Periodic (days–weeks) |
| Analyst/manual input | Internal analyst entries, scenario overrides | Manual form | On-demand (UNKNOWN freshness) |

### Schemas

Each ingested signal must conform to the existing `SignalSnapshot` schema (`backend/src/signal_ingestion/models.py`):

| Field | Type | Purpose |
|-------|------|---------|
| `snapshot_id` | `str` | Unique identifier |
| `source_id` | `str` | Links to `SignalSource` registry |
| `timestamp` | `datetime` | Ingestion time (UTC) |
| `raw_value` | `Any` | Source-native payload |
| `normalized_value` | `float` | 0.0–1.0 normalized signal strength |
| `unit` | `str` | Original unit (%, USD, bps, etc.) |
| `freshness` | `SnapshotFreshness` | FRESH / RECENT / STALE / EXPIRED / UNKNOWN |
| `confidence_score` | `float` | Computed from source weight × freshness multiplier |
| `tags` | `list[str]` | Scenario/sector association tags |
| `metadata` | `dict` | Source-specific context |

### Validation Rules

| Rule | Enforcement | Status |
|------|-------------|--------|
| Source must exist in `SignalSource` registry | Registry lookup on `source_id` | **Exists** (models.py) |
| `confidence_weight` ≥ `MIN_SOURCE_CONFIDENCE` (0.60) | Governance gate check | **Exists** (governance.py) |
| `normalized_value` in [0.0, 1.0] | Pydantic validator | **Exists** (simulation_schemas.py pattern) |
| `freshness` computed from source type × elapsed time | Freshness window lookup | **Exists** (governance.py `FRESHNESS_WINDOWS`) |
| Expired snapshots cannot enter scoring pipeline | Governance gate 2 | **Exists** (governance.py) |
| Duplicate snapshot suppression (same source + same raw value within window) | Deduplication filter | **Missing** |

### Freshness Model

Already defined in `governance.py`:

| Source Type | Fresh | Recent | Stale | Expired |
|-------------|-------|--------|-------|---------|
| RSS | ≤60 min | ≤120 min | ≤300 min | >300 min |
| API | ≤30 min | ≤60 min | ≤150 min | >150 min |
| Market | ≤15 min | ≤30 min | ≤75 min | >75 min |
| Government | ≤7 days | ≤14 days | ≤35 days | >35 days |
| Manual | N/A | N/A | N/A | Always UNKNOWN |

### Source Confidence

- Base confidence weight assigned per source at registration (0.0–1.0)
- Runtime confidence = `confidence_weight × freshness_multiplier`
- Freshness multipliers: FRESH→1.00, RECENT→0.85, STALE→0.60, EXPIRED→0.30, UNKNOWN→0.50
- Sources with confidence <0.60 are **untrusted** — all snapshots advisory-only
- Auto-kill after `MAX_CONSECUTIVE_FAILURES=3` consecutive failures

### What Already Exists

| Component | File | Status |
|-----------|------|--------|
| `SignalSource` model | `signal_ingestion/models.py` | Implemented |
| `SignalSnapshot` model | `signal_ingestion/models.py` | Implemented |
| `SignalSourceType` enum (RSS, API, MARKET, GOVERNMENT, MANUAL) | `signal_ingestion/models.py` | Implemented |
| `SnapshotFreshness` enum | `signal_ingestion/models.py` | Implemented |
| Freshness windows per source type | `signal_ingestion/governance.py` | Implemented |
| Confidence thresholds (MIN_SOURCE=0.60, MIN_SNAPSHOT=0.40, MIN_SCORING=0.50) | `signal_ingestion/governance.py` | Implemented |
| `SignalAuditLog` (append-only) | `signal_ingestion/audit_log.py` | Implemented |
| Feature flags (`ENABLE_DEV_SIGNAL_PREVIEW`, `ENABLE_SIGNAL_SCORING_V5`) | `signal_ingestion/feature_flags.py` | Implemented |
| RSS connector (fixture) | `signal_ingestion/connectors/rss_connector.py` | Implemented |
| Base connector interface | `signal_ingestion/connectors/base.py` | Implemented |
| `IngestionService` orchestrator | `signal_ingestion/ingestion_service.py` | Implemented |
| `PreviewService` (dev snapshot preview) | `signal_ingestion/preview_service.py` | Implemented |
| Governance decision gate (8-gate evaluator) | `signal_ingestion/governance.py` | Implemented |

### What Is Missing

| Component | Description | Priority |
|-----------|-------------|----------|
| Market data connector | Real-time commodity, FX, equity feed connector | v5 |
| API connector | REST/GraphQL external API connector | v5 |
| Government data connector | GCC central bank / statistical agency connector | v6 |
| Maritime connector | AIS / port throughput feed connector | v6 |
| Snapshot deduplication | Suppress duplicate snapshots within freshness window | v5 |
| Source health dashboard | Monitoring UI for connector status, failure rates | v6 |
| Batch ingestion pipeline | Bulk historical signal import for backtesting | v7 |
| Cross-source corroboration | Confidence boost when multiple sources agree | v7 |

---

## C2 — Signal Interpretation Engine

### Signal Types

#### Explicit Signals
Direct, quantifiable market or institutional data:

| Signal | Example | Source Type |
|--------|---------|-------------|
| Commodity price move | Brent crude +3.2% on Hormuz tensions | MARKET |
| Equity index shift | ADX banking sector index −1.8% | MARKET |
| Credit spread widening | Saudi CDS 5Y spread +12bps | MARKET |
| FX rate pressure | USD/AED forward points inverted | MARKET |
| Shipping rate spike | Suez transit insurance surcharge +25% | API |
| Official rate decision | SAMA repo rate hold at 6.00% | GOVERNMENT |

#### Implicit Signals
Derived from patterns rather than direct observation:

| Signal | Detection Method | Confidence Modifier |
|--------|------------------|---------------------|
| Hidden tightening | Central bank repo volume ↓ without rate change | ×0.75 (inferred) |
| Regulatory tone shift | Circular language analysis: "encourage" → "require" | ×0.70 (textual) |
| Capital allocation shift | Sector fund flow reversal (3-month trend break) | ×0.80 (statistical) |
| Liquidity pressure | Interbank rate − policy rate spread widening | ×0.85 (derived) |
| Earnings sentiment shift | Consensus revision breadth across GCC banks | ×0.75 (aggregate) |

### Weighting Logic

Interpretation weight combines source confidence, signal type, and scenario relevance:

```
interpretation_weight =
    source_confidence           # 0.0–1.0 from governance gate
  × signal_type_modifier        # 1.0 explicit, 0.70–0.85 implicit
  × scenario_relevance          # 0.0–1.0 tag-based match to active scenario
  × freshness_multiplier        # 1.0 FRESH → 0.30 EXPIRED

final_advisory_score = clamp(interpretation_weight, 0.0, 1.0)
```

### Confidence Logic

Confidence scoring layers:

| Layer | Input | Output |
|-------|-------|--------|
| Source confidence | `SignalSource.confidence_weight` | Base trust in the source |
| Freshness confidence | Time since ingestion vs. `FRESHNESS_WINDOWS` | Temporal reliability |
| Corroboration confidence | Number of independent sources confirming signal | Agreement strength (future) |
| Interpretation confidence | Signal type modifier × scenario relevance | How well signal maps to risk |
| Combined confidence | Product of above layers | Final advisory display score |

### Advisory-Only First

**v5 constraint (non-negotiable):** The interpretation engine operates in ADVISORY mode only.

- Interpretation results are displayed alongside scenario outputs
- They explain context ("Brent crude rose 3% — aligns with energy disruption scenario")
- They do **NOT** modify any metric: `base_loss_usd`, `unified_risk_score`, `confidence_score`, sector rankings, or decision recommendations
- The existing `ImpactMode.ADVISORY` governance gate enforces this
- The existing `MAX_ADJUSTMENT_FACTOR=0.15` (±15%) bound is not invoked in advisory mode — adjustment is always 0.0

### Interpretation Output Schema (Proposed)

```
SignalInterpretation:
  snapshot_id: str              # links to source snapshot
  scenario_id: str              # which scenario this interpretation applies to
  interpretation_text: str      # English narrative
  interpretation_text_ar: str   # Arabic narrative
  signal_type: "explicit" | "implicit"
  advisory_score: float         # 0.0–1.0 interpretation strength
  confidence: float             # 0.0–1.0 combined confidence
  mechanism_ids: list[int]      # indexes into _MECHANISMS (explainability.py)
  impact_mode: ImpactMode       # always ADVISORY in v5
  adjustment_applied: float     # always 0.0 in v5
  governance_verdict: dict      # full GovernanceVerdict serialization
```

---

## C3 — Transmission Graph

### Macro → Banking → Insurance → Real Economy Model

The transmission graph models how a shock propagates through the GCC financial system:

```
Layer 1: Macro Trigger
  ├── Oil price shock / Geopolitical event / Trade disruption
  │
Layer 2: Banking Sector
  ├── Credit exposure (counter-party risk)
  ├── Liquidity stress (interbank market)
  ├── Capital adequacy pressure (pillar-2 add-ons)
  │
Layer 3: Insurance Sector
  ├── Claims surge (reinsurance cession)
  ├── Investment portfolio mark-to-market
  ├── Regulatory solvency stress
  │
Layer 4: Real Economy
  ├── Trade finance availability
  ├── Corporate credit conditions
  ├── Consumer/SME access to capital
  ├── Infrastructure project delays
  └── Employment & spending effects
```

### Entities

| Entity Type | Count | Examples | Current Status |
|-------------|-------|----------|----------------|
| Energy nodes | 6 | Saudi Aramco, ADNOC, QatarEnergy, KPC, PDO, BAPCO | **In GCC_NODES** |
| Maritime nodes | 5 | Jebel Ali, King Abdullah Port, Hamad Port, Salalah, Mina Sulman | **In GCC_NODES** |
| Banking nodes | 8 | SNB, FAB, QNB, NBK, BankMuscat, NBB, KFH, Emirates NBD | **In GCC_NODES** |
| Insurance nodes | 4 | Tawuniya, ADNIC, QIC, Gulf Insurance | **In GCC_NODES** |
| Fintech nodes | 4 | STC Pay, Mashreq Neo, QPay, Bayan | **In GCC_NODES** |
| Logistics nodes | 5 | DP World, SAL Logistics, Qatar Cargo, Agility, Oman Logistics | **In GCC_NODES** |
| Infrastructure nodes | 4 | NEOM, Lusail, DEWA, Duqm SEZ | **In GCC_NODES** |
| Government nodes | 4 | PIF, ADIA, QIA, KIA | **In GCC_NODES** |
| Healthcare nodes | 2 | Seha, HMC | **In GCC_NODES** |
| **Total** | **42** | | **All in registry** |

### Relationships (Cross-Sector Dependency Map)

Already defined in `risk_models.py` as `_CROSS_SECTOR_DEPS`:

| Source Sector | Dependent Sectors |
|---------------|-------------------|
| Energy | Banking, Maritime, Logistics, Fintech |
| Maritime | Energy, Logistics, Banking |
| Banking | Fintech, Insurance, Government |
| Insurance | Banking, Fintech |
| Fintech | Banking, Insurance |
| Logistics | Maritime, Energy |
| Infrastructure | Energy, Banking |
| Government | Banking, Fintech |

### Propagation Rules

Existing propagation model (`risk_models.py`):

```
X_(t+1) = β·P·X_t + (1-β)·X_t + S_t

β = 0.65 (coupling coefficient)
λ = 0.05 (shock decay rate)
cutoff = 0.005 (early-exit threshold)

P = row-normalized adjacency matrix derived from _CROSS_SECTOR_DEPS
S_t = external shock injection, decaying as S_0 × e^(-λ·t)
```

### Neo4j-Ready Model (Proposed)

Node labels and relationship types for graph database materialization:

```cypher
// Node labels
(:Entity {id, label, label_ar, sector, capacity, current_load,
          criticality, redundancy, lat, lng})

// Relationship types
[:DEPENDS_ON {weight, transmission_type}]         // sector dependency
[:COUNTER_PARTY {exposure_usd, confidence}]       // bilateral credit
[:REINSURES {cession_pct, treaty_type}]           // insurance cession
[:SUPPLIES {commodity, volume_pct}]               // supply chain
[:FUNDS {instrument, amount_usd}]                 // sovereign investment
[:REGULATES {authority, jurisdiction}]             // regulatory oversight

// Transmission path query (example)
MATCH path = (trigger:Entity {sector:'energy'})
  -[:DEPENDS_ON*1..3]->(impact:Entity {sector:'banking'})
RETURN path, reduce(w=1.0, r IN relationships(path) | w * r.weight) AS attenuation
```

### Sandbox First, Not Production Scoring

- The transmission graph is built and queried in a **sandbox environment only**
- Graph traversals produce explanatory outputs ("Shock at Aramco → SNB via DEPENDS_ON [0.65] → Tawuniya via COUNTER_PARTY [0.42]")
- Graph outputs do **NOT** modify URS, base_loss_usd, confidence_score, or any simulation metric
- Production scoring pipeline continues using the existing `_CROSS_SECTOR_DEPS` dictionary
- Migration from dictionary to graph-backed propagation requires governance approval (v8)

---

## C4 — Decision Engine

### Decision Recommendation Model

The decision engine synthesizes signal interpretations and transmission paths into actionable recommendations:

| Component | Description | Output |
|-----------|-------------|--------|
| Signal synthesis | Aggregate interpretations across active signals for a scenario | Weighted advisory score |
| Transmission analysis | Trace propagation paths through the graph | Affected entity list + attenuation |
| Outcome projection | Estimate delta in scenario metrics if signal is accurate | Expected loss delta (USD), URS delta |
| Recommendation | Act vs. Do Nothing decision with explanation | Structured recommendation |

### Act vs. Do Nothing

| Decision | Criteria | Output |
|----------|----------|--------|
| **Act** | Advisory score ≥ 0.65 AND confidence ≥ 0.50 AND ≥2 corroborating sources | Specific action recommendation |
| **Monitor** | Advisory score 0.35–0.65 OR confidence 0.35–0.50 OR single source | Watch brief — re-evaluate on next signal |
| **Do Nothing** | Advisory score < 0.35 OR confidence < 0.35 OR signal expired | No action — log rationale |

### Expected Outcome Delta

```
expected_delta = {
  "base_loss_usd_delta":    projected change in scenario loss estimate,
  "urs_delta":              projected change in unified risk score,
  "confidence_delta":       projected change in confidence score,
  "affected_sectors":       list of sectors in transmission path,
  "affected_entities":      list of entity IDs in blast radius,
  "time_horizon_hours":     expected duration of impact,
}
```

### Explanation

Every recommendation includes a structured explanation:

```
DecisionExplanation:
  summary: str               # "Energy price spike suggests Hormuz scenario
                              #  loss estimate may be conservative by $420M"
  summary_ar: str             # Arabic translation
  causal_chain: list[str]     # ["Brent +3.2%", "→ Aramco revenue risk",
                              #  "→ SNB credit exposure", "→ Tawuniya claims"]
  mechanism_ids: list[int]    # indexes into explainability._MECHANISMS
  signal_sources: list[str]   # source_ids that contributed
  confidence_breakdown: dict  # per-layer confidence scores
```

### Confidence

Decision confidence is distinct from signal confidence:

| Level | Range | Meaning |
|-------|-------|---------|
| High | ≥0.70 | Multiple corroborating signals, fresh data, clear transmission path |
| Medium | 0.50–0.70 | Some corroboration, mostly fresh, plausible transmission |
| Low | 0.35–0.50 | Single source or stale data, weak transmission evidence |
| Insufficient | <0.35 | Do not recommend — insufficient basis |

### Governance Approval

- All recommendations are **advisory-only** until governance approval
- Recommendations that would change scenario metrics require explicit sign-off
- The existing `GovernanceVerdict` model captures approval decisions
- `approved_by` field tracks who authorized the action
- Full audit trail via `SignalAuditLog`

---

## C5 — Implementation Roadmap

### Phase Definitions

| Phase | Name | Scope | Prerequisite |
|-------|------|-------|--------------|
| **v5** | Advisory Signal Interpretation | Signal display + interpretation, ADVISORY mode only | Current platform stable |
| **v6** | Transmission Graph Sandbox | Neo4j graph build + exploratory queries, sandbox only | v5 stable for 7+ days |
| **v7** | Decision Engine Prototype | Recommendation engine in dev/staging, no production scoring | v6 graph validated |
| **v8** | Governance-Approved Scoring Impact | Signals may influence metrics under governance control | v7 prototype reviewed + governance sign-off |

### v5 — Advisory Signal Interpretation Only

**Goal:** Analysts see signal context alongside scenario outputs. No metrics change.

| Deliverable | Description |
|-------------|-------------|
| Market data connector | Commodity prices, FX rates, equity indices |
| API connector | External REST/GraphQL signal sources |
| Snapshot deduplication | Suppress duplicates within freshness window |
| Interpretation engine | Map signals to scenarios with advisory score |
| Advisory display | Signal context panel in command center |
| Feature flag | `ENABLE_SIGNAL_ADVISORY_V5=false` (default off) |

**Constraints:**
- `ImpactMode.ADVISORY` — signals explain but never score
- No `base_loss_usd`, `unified_risk_score`, or `confidence_score` modification
- No scenario ranking changes
- No decision recommendations displayed
- All signal activity logged via `SignalAuditLog`

### v6 — Transmission Graph Sandbox

**Goal:** Build and explore the transmission graph in a sandbox. Validate entity relationships.

| Deliverable | Description |
|-------------|-------------|
| Neo4j schema | Node labels, relationship types, constraints, indexes |
| Graph construction | Materialize `GCC_NODES` + `_CROSS_SECTOR_DEPS` into Neo4j |
| Graph explorer | Dev-only UI for traversing transmission paths |
| Government/maritime connectors | Expand signal source coverage |
| Source health dashboard | Connector monitoring and failure rate tracking |
| Sandbox isolation | Graph queries run in isolated environment, no production writes |

**Constraints:**
- Graph is read-only from the simulation pipeline's perspective
- Propagation still uses `_CROSS_SECTOR_DEPS` dictionary in production
- Graph outputs are explanatory only — no metric influence
- Sandbox data does not persist to production database

### v7 — Decision Engine Prototype

**Goal:** Prototype recommendation engine in dev/staging. Test Act/Monitor/Do-Nothing logic.

| Deliverable | Description |
|-------------|-------------|
| Recommendation engine | Signal synthesis + transmission analysis + outcome projection |
| Decision explanation | Structured causal chain + bilingual narrative |
| Batch ingestion pipeline | Historical signal import for backtesting |
| Cross-source corroboration | Confidence boost from multiple agreeing sources |
| Backtesting framework | Compare recommendations against historical outcomes |
| Staging deployment | Full pipeline running in staging, isolated from production |

**Constraints:**
- Runs in staging only — zero production impact
- Recommendations are internal, not shown to end users
- No governance approval workflow active
- Backtesting results reviewed before any promotion

### v8 — Governance-Approved Scoring Impact

**Goal:** Allow approved signals to influence scenario metrics under strict governance control.

| Deliverable | Description |
|-------------|-------------|
| Governance approval workflow | Explicit sign-off required for each scoring activation |
| Bounded scoring | `MAX_ADJUSTMENT_FACTOR=0.15` (±15%) enforced |
| Live kill switch | Instant revert to static scoring on any anomaly |
| Production graph migration | Replace `_CROSS_SECTOR_DEPS` dict with Neo4j-backed propagation |
| Audit dashboard | Full visibility into signal → interpretation → decision → score chain |
| Rollback procedure | Documented recovery path if scoring produces unexpected results |

**Constraints:**
- `ENABLE_SIGNAL_SCORING_V5=true` required (currently blocked)
- All 8 governance gates must pass per signal
- `MAX_ADJUSTMENT_FACTOR` caps influence at ±15%
- Governance owner sign-off recorded in audit trail
- 7+ days of stable advisory operation required before scoring activation

---

## C6 — Risk Controls

### No Live Intelligence Claim

- The system does **NOT** claim to provide live intelligence
- All signal data is presented as "external context" with explicit confidence scores
- UI labels use "Advisory Signal" and "Signal Context" — never "Intelligence Feed" or "Live Alert"
- Disclaimer: "Signal interpretations are advisory only and do not constitute financial advice"

### No Metric Changes Without Governance

- `ImpactMode` enum enforces OFF → ADVISORY → SCORING progression
- SCORING mode requires `ENABLE_SIGNAL_SCORING_V5=true` (default: false)
- Governance gate evaluates 8 sequential checks before any scoring is permitted
- `GovernanceVerdict` records the decision, reason, and approver for every signal

### Feature Flags

| Flag | Default | Gate | Purpose |
|------|---------|------|---------|
| `ENABLE_DEV_SIGNAL_PREVIEW` | `false` | Preview | Dev-only signal snapshot display |
| `ENABLE_SIGNAL_ADVISORY_V5` | `false` | Advisory | Signal interpretation context display |
| `ENABLE_SIGNAL_SCORING_V5` | `false` | Scoring | Signal influence on scenario metrics |
| `ENABLE_TRANSMISSION_GRAPH` | `false` | Graph | Neo4j graph sandbox activation (proposed) |
| `ENABLE_DECISION_ENGINE` | `false` | Decision | Recommendation engine activation (proposed) |

All flags read from environment variables. Production deployments must **NOT** enable scoring or decision flags.

### Audit Trail

- `SignalAuditLog` records every ingestion event: `SOURCE_CHECKED`, `SNAPSHOT_CREATED`, `SOURCE_FAILED`, `FALLBACK_USED`
- `GovernanceVerdict` records every governance decision with mode, decision type, reason, fallback status, and approver
- Proposed extensions for v6+:
  - `INTERPRETATION_CREATED` — signal mapped to scenario
  - `RECOMMENDATION_GENERATED` — decision engine output
  - `GOVERNANCE_APPROVED` — scoring activation approved
  - `SCORING_APPLIED` — signal adjustment applied to metric
  - `KILL_SWITCH_ACTIVATED` — emergency scoring disable

### Fallback Behavior

| Trigger | Fallback Action |
|---------|-----------------|
| Source fails `MAX_CONSECUTIVE_FAILURES` (3) times | Source auto-disabled, audit logged |
| Snapshot confidence < `MIN_SNAPSHOT_CONFIDENCE` (0.40) | Signal advisory-only, cannot score |
| Source confidence < `MIN_SOURCE_CONFIDENCE` (0.60) | All snapshots from source advisory-only |
| Adjustment exceeds `MAX_ADJUSTMENT_FACTOR` (±0.15) | Adjustment blocked, audit logged |
| Scoring flag disabled | All signals advisory-only regardless of confidence |
| Any governance gate fails | Signal blocked or downgraded to advisory |

### Kill Switch

| Mechanism | Scope | Activation |
|-----------|-------|------------|
| `ENABLE_SIGNAL_SCORING_V5=false` | Global — disables all signal scoring | Environment variable change |
| `ENABLE_SIGNAL_ADVISORY_V5=false` | Global — hides all advisory signals | Environment variable change |
| `MAX_CONSECUTIVE_FAILURES` exceeded | Per-source — disables failing source | Automatic (3 failures) |
| `GovernanceDecision.BLOCKED_KILL_SWITCH` | Per-signal — blocks specific signal | Governance evaluator |
| Proposed: `/api/v1/signals/kill-switch` | Emergency endpoint — instantly reverts to static | API call (v7+) |

---

## C7 — Comparison Against Current Platform

| Capability | Current Status | Proposed Upgrade | Risk | Suggested Phase |
|------------|---------------|------------------|------|-----------------|
| **Signal source registry** | `SignalSource` model with 5 source types | Add market, maritime, government connectors | Low — additive, no existing behavior changes | v5 |
| **Signal ingestion** | RSS fixture connector + base interface | Production-grade connectors for 7 source categories | Medium — external API dependencies | v5–v6 |
| **Snapshot freshness** | Freshness windows defined for 5 source types | No change needed — model is complete | None | Already done |
| **Confidence scoring** | 3-tier confidence thresholds (source, snapshot, scoring) | Add corroboration layer (multi-source agreement) | Low — additive confidence modifier | v7 |
| **Governance gate** | 8-gate evaluator (mode, expired, confidence, stale, bounds) | No change for v5–v6; extend audit actions for v7+ | None for advisory; Low for extensions | v5: none, v7: extend |
| **Feature flags** | 2 flags (DEV_PREVIEW, SCORING_V5) | Add ADVISORY_V5, TRANSMISSION_GRAPH, DECISION_ENGINE | Low — all default false | v5–v7 |
| **Audit trail** | 4 action types (checked, created, failed, fallback) | Add interpretation, recommendation, approval, scoring actions | Low — append-only log extension | v6–v7 |
| **Signal interpretation** | Not implemented — signals are raw snapshots only | Interpretation engine maps signals to scenarios with advisory score | Medium — new component, must respect ADVISORY constraint | v5 |
| **Causal mechanisms** | 17 bilingual mechanism descriptions in `explainability.py` | Link interpretations to mechanism IDs for structured explanation | Low — uses existing mechanism library | v5 |
| **Propagation model** | Matrix-based propagation via `_CROSS_SECTOR_DEPS` dict | Neo4j graph-backed propagation in sandbox | Medium — parallel system, must not replace dict in production | v6 |
| **Entity model** | 42 GCC nodes with sector, capacity, criticality, coordinates | Materialize into Neo4j with typed relationships | Low — read-only graph construction from existing data | v6 |
| **Cross-sector dependencies** | 8 source sectors → dependent sector lists in `risk_models.py` | Graph relationships with weights and transmission types | Medium — weight calibration needed | v6 |
| **Decision recommendations** | Not implemented — no recommendation engine exists | Act/Monitor/Do-Nothing engine with structured explanations | High — new capability, requires backtesting validation | v7 |
| **Outcome projection** | Not implemented — scenario metrics are static per run | Delta estimation for loss, URS, confidence | High — must not influence production metrics until v8 | v7 |
| **Scoring impact** | Blocked — `ENABLE_SIGNAL_SCORING_V5=false` | Bounded scoring (±15%) under governance approval | High — requires full governance sign-off + 7-day advisory soak | v8 |
| **Kill switch** | Source auto-disable after 3 failures + flag-based mode control | Add emergency API endpoint + per-signal governance block | Low — extends existing patterns | v7 |
| **Simulation engine** | 17-stage deterministic pipeline (1100+ lines) | No changes — pipeline remains source of truth | None | Protected |
| **15 scenarios** | All scenarios defined with severity, horizon, sector mappings | No changes — scenario catalog is frozen | None | Protected |
| **Risk classification** | URS thresholds (NOMINAL through SEVERE) | No changes — risk levels are frozen | None | Protected |
| **Frontend UI** | Command center, decision room, macro signals, audit trail | No changes — v5 advisory display is additive panel only | None | Protected |

---

## Acceptance Checklist

- [x] Documentation only — no code files created or modified
- [x] No runtime impact — no server, API, or pipeline changes
- [x] No scenario changes — all 15 scenarios remain as defined
- [x] No UI changes — frontend is untouched
- [x] No live feed connections — no external APIs activated
- [x] No production deployment — no deploy commands or CI triggers
- [x] Clear phased roadmap — v5 → v6 → v7 → v8 with explicit prerequisites
- [x] Existing demo protected — all existing functionality is frozen and marked "Protected"
- [x] Risk controls defined — feature flags, governance gates, audit trail, kill switches
- [x] Comparison table maps every capability against current platform state
