"""
Intelligence Adapter Foundation — Normalized Intelligence Signal

PHASE 1: Core domain contract.

NormalizedIntelligenceSignal is the ONLY way external intelligence may enter
the platform. No external system may write directly to Signal / Decision /
Outcome / Value layers.

Semantic separation is enforced at the type level:
    OBSERVED    — raw external facts (feed events, operational disruptions)
    INFERRED    — reasoned interpretation (TREK-style liquidity stress, exposure)
    SIMULATED   — modelled projections (Impact Observatory scenario spread)

These three categories are never collapsed into a single undifferentiated blob.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field

# ─── Adapter version ─────────────────────────────────────────────────────────

ADAPTER_VERSION: str = "1.0.0"


# ─── Enums ────────────────────────────────────────────────────────────────────

class SourceFamily(StrEnum):
    """Top-level classification of external intelligence source families.

    Each family maps to exactly one source adapter stub in intelligence/sources/.
    Adding a new family requires a new stub — never an inline branch here.
    """
    JET_NEXUS          = "jet_nexus"           # geospatial / operational feed
    TREK               = "trek"                # analytical reasoning engine
    IMPACT_OBSERVATORY = "impact_observatory"  # simulation / propagation model
    MANUAL_INTELLIGENCE = "manual_intelligence" # operator-authored intelligence note


class NormalizationStatus(StrEnum):
    """Lifecycle state of normalization for a candidate payload."""
    NORMALIZED     = "NORMALIZED"     # fully valid, ready for bridge
    PARTIAL        = "PARTIAL"        # required fields present, optional fields warned
    REJECTED       = "REJECTED"       # required fields missing / invalid — blocked
    PENDING_REVIEW = "PENDING_REVIEW" # normalized but held for human review


class EvidenceType(StrEnum):
    """Semantic category of an evidence item.

    Preserved across the full pipeline to distinguish source epistemology.
    """
    OBSERVED  = "OBSERVED"   # directly observed fact
    INFERRED  = "INFERRED"   # reasoned / interpreted from observations
    SIMULATED = "SIMULATED"  # modelled / projected consequence


class ReasoningType(StrEnum):
    """Sub-classification of inferred reasoning."""
    LIQUIDITY_STRESS     = "LIQUIDITY_STRESS"
    CREDIT_EXPOSURE      = "CREDIT_EXPOSURE"
    COUNTERPARTY_RISK    = "COUNTERPARTY_RISK"
    REGULATORY_SIGNAL    = "REGULATORY_SIGNAL"
    MARKET_DISRUPTION    = "MARKET_DISRUPTION"
    CONTAGION_RISK       = "CONTAGION_RISK"
    GENERIC_INFERENCE    = "GENERIC_INFERENCE"


class SimulationType(StrEnum):
    """Sub-classification of simulated projections."""
    SCENARIO_PROPAGATION  = "SCENARIO_PROPAGATION"
    SECTOR_STRESS         = "SECTOR_STRESS"
    ENTITY_IMPACT         = "ENTITY_IMPACT"
    RECOVERY_TRAJECTORY   = "RECOVERY_TRAJECTORY"
    MONTE_CARLO_RUN       = "MONTE_CARLO_RUN"
    GENERIC_SIMULATION    = "GENERIC_SIMULATION"


# ─── ID factory ──────────────────────────────────────────────────────────────

def _now_utc() -> datetime:
    return datetime.now(timezone.utc)


def _norm_signal_id() -> str:
    return f"nis-{uuid.uuid4().hex[:16]}"


# ─── Semantic separation models ───────────────────────────────────────────────

class ObservedEvidence(BaseModel):
    """A directly observed fact from an external feed.

    Covers: raw feed events, operational disruptions, incident reports.
    All fields are factual — no interpretation applied here.
    """
    evidence_type: EvidenceType = EvidenceType.OBSERVED
    source_system: str          = Field(..., max_length=64)
    source_event_id: str        = Field(..., max_length=128)
    observed_at: datetime
    entity_refs: list[str]      = Field(default_factory=list, description="External entity identifiers")
    raw_value: dict[str, Any]   = Field(default_factory=dict, description="Raw field values from source")
    notes: str                  = Field("", max_length=500)

    model_config = {"frozen": True}


class InferredReasoning(BaseModel):
    """A reasoned interpretation derived from observations.

    Covers: TREK-style stress analysis, implied exposure, interpreted signals.
    NEVER mixed with SimulatedProjection — reasoning is post-hoc, simulation
    is forward-looking.
    """
    evidence_type: EvidenceType = EvidenceType.INFERRED
    reasoning_type: ReasoningType = ReasoningType.GENERIC_INFERENCE
    source_system: str          = Field(..., max_length=64)
    inferred_at: datetime
    confidence: float           = Field(..., ge=0.0, le=1.0)
    summary: str                = Field(..., max_length=1000)
    supporting_event_ids: list[str] = Field(default_factory=list)
    inferred_severity: float    = Field(..., ge=0.0, le=1.0)
    affected_entities: list[str] = Field(default_factory=list)
    reasoning_payload: dict[str, Any] = Field(default_factory=dict)

    model_config = {"frozen": True}


class SimulatedProjection(BaseModel):
    """A modelled or projected consequence from a simulation engine.

    Covers: Impact Observatory scenario spreads, sector stress projections,
    Monte Carlo outputs.
    NEVER presented as observed fact — always marked as model output.
    """
    evidence_type: EvidenceType = EvidenceType.SIMULATED
    simulation_type: SimulationType = SimulationType.GENERIC_SIMULATION
    source_system: str          = Field(..., max_length=64)
    simulated_at: datetime
    model_version: str          = Field(..., max_length=64)
    confidence: float           = Field(..., ge=0.0, le=1.0)
    horizon_hours: int          = Field(..., ge=1, le=8760)
    summary: str                = Field(..., max_length=1000)
    scenario_id: str | None     = None
    run_id: str | None          = None
    projected_severity: float   = Field(..., ge=0.0, le=1.0)
    affected_domains: list[str] = Field(default_factory=list)
    simulation_payload: dict[str, Any] = Field(default_factory=dict)

    model_config = {"frozen": True}


# ─── Normalized Intelligence Signal ──────────────────────────────────────────

class NormalizedIntelligenceSignal(BaseModel):
    """The unified external intelligence contract.

    This is the ONLY way external intelligence may enter the platform.
    Every field is required to be traceable to its source.

    Semantic sections are preserved in their separate typed containers:
        observed_evidence   — list[ObservedEvidence]
        inferred_reasoning  — list[InferredReasoning]
        simulation_context  — list[SimulatedProjection]

    These are NEVER collapsed. An executive reading this knows exactly:
    - what was observed (facts)
    - what was inferred (reasoning)
    - what was simulated (projections)
    """
    normalized_signal_id: str         = Field(default_factory=_norm_signal_id)
    adapter_version: str              = Field(default=ADAPTER_VERSION)
    normalization_status: NormalizationStatus = NormalizationStatus.NORMALIZED

    # ── Source provenance ──────────────────────────────────────────────────────
    source_family: SourceFamily
    source_systems: list[str]         = Field(..., min_length=1, max_length=10,
                                              description="Named external systems that contributed")
    source_event_ids: list[str]       = Field(default_factory=list,
                                              description="External event IDs for traceability")

    # ── Signal classification ──────────────────────────────────────────────────
    signal_type: str                  = Field(..., max_length=64,
                                              description="disruption | escalation | alert | recovery")
    title: str                        = Field(..., max_length=256)
    summary: str                      = Field(..., max_length=2000)

    # ── Scores ────────────────────────────────────────────────────────────────
    severity_score: float             = Field(..., ge=0.0, le=1.0)
    confidence_score: float           = Field(..., ge=0.0, le=1.0)

    # ── Temporal context ──────────────────────────────────────────────────────
    detected_at: datetime
    time_horizon_hours: int           = Field(..., ge=1, le=8760)

    # ── Scope ─────────────────────────────────────────────────────────────────
    affected_domains: list[str]       = Field(default_factory=list,
                                              description="banking | fintech | insurance | etc")
    affected_geographies: list[str]   = Field(default_factory=list,
                                              description="ISO-3166 country codes or region labels")

    # ── Semantic sections (preserved separately — never collapsed) ─────────────
    observed_evidence: list[ObservedEvidence]       = Field(default_factory=list)
    inferred_reasoning: list[InferredReasoning]     = Field(default_factory=list)
    simulation_context: list[SimulatedProjection]   = Field(default_factory=list)

    # ── Narrative ─────────────────────────────────────────────────────────────
    causal_chain: list[str]           = Field(default_factory=list,
                                              description="Ordered causal narrative steps")
    reasoning_summary: str            = Field("", max_length=2000)

    # ── Adapter trace ─────────────────────────────────────────────────────────
    evidence_payload: dict[str, Any]  = Field(default_factory=dict,
                                              description="Raw source payload reference — never interpreted here")
    trace_payload: dict[str, Any]     = Field(default_factory=dict,
                                              description="Normalization trace — warnings, notes, adapter decisions")

    # ── Timestamps ────────────────────────────────────────────────────────────
    normalized_at: datetime           = Field(default_factory=_now_utc)

    model_config = {"frozen": True}

    def has_observed(self) -> bool:
        return len(self.observed_evidence) > 0

    def has_inferred(self) -> bool:
        return len(self.inferred_reasoning) > 0

    def has_simulated(self) -> bool:
        return len(self.simulation_context) > 0

    def semantic_summary(self) -> dict[str, int]:
        """Return counts of each semantic category — for audit/display."""
        return {
            "observed":  len(self.observed_evidence),
            "inferred":  len(self.inferred_reasoning),
            "simulated": len(self.simulation_context),
        }
