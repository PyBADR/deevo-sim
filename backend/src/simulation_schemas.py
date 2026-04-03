"""
Impact Observatory | مرصد الأثر
Pydantic v2 schemas for all API request/response models.

FIX: Replaced all dict[str, Any] sub-models with fully-typed Pydantic models.
     Added model_validator(mode='after') to enforce structural contracts.
     Numeric fields are never Optional — they default to 0.0 so .toFixed() cannot crash.
     List fields default to [] so .map()/.reduce() cannot crash.
     sector_losses is List[SectorLoss] (list), NOT dict — fixes frontend reduce() crash.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


# ---------------------------------------------------------------------------
# Request Models
# ---------------------------------------------------------------------------

class SimulateRequest(BaseModel):
    """Request body for POST /simulate."""

    scenario_id: str = Field(
        ...,
        description="Scenario identifier from the scenario catalog.",
        examples=["hormuz_chokepoint_disruption"],
    )
    severity: float = Field(
        ...,
        ge=0.01,
        le=1.0,
        description="Base severity of the event [0.01–1.0].",
        examples=[0.75],
    )
    horizon_hours: int = Field(
        default=336,
        ge=24,
        le=2160,
        description="Simulation horizon in hours (24h–2160h / 14 days–90 days).",
    )
    label: Optional[str] = Field(
        default=None,
        max_length=128,
        description="Optional human-readable run label.",
    )

    @field_validator("scenario_id")
    @classmethod
    def scenario_id_not_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("scenario_id must not be empty")
        return v.strip()


# Keep backward-compat alias
SimulateRequest.__doc__ = SimulateRequest.__doc__


# ---------------------------------------------------------------------------
# Typed sub-models (replaces dict[str, Any] everywhere)
# ---------------------------------------------------------------------------

class EntityImpact(BaseModel):
    """Entity-level financial impact — all fields have safe defaults."""
    entity_id: str = ""
    entity_label: str = ""
    loss_usd: float = 0.0
    direct_loss_usd: float = 0.0
    indirect_loss_usd: float = 0.0
    systemic_loss_usd: float = 0.0
    stress_score: float = 0.0
    classification: str = "NOMINAL"
    peak_day: int = 1
    sector: str = "unknown"
    propagation_factor: float = 1.0


class SectorLoss(BaseModel):
    """Sector-level loss row — a LIST item, not a dict key.
    Frontend iterates this with .map() / .reduce() — must be a list.
    """
    sector: str = "unknown"
    loss_usd: float = 0.0
    pct: float = 0.0


class DecisionAction(BaseModel):
    """A single ranked decision action."""
    action_id: str = ""
    rank: int = 0
    sector: str = "cross-sector"
    owner: str = ""
    action: str = ""
    action_ar: str = ""
    priority_score: float = 0.0
    urgency: float = 0.0
    loss_avoided_usd: float = 0.0
    loss_avoided_formatted: str = "$0"
    cost_usd: float = 0.0
    cost_formatted: str = "$0"
    regulatory_risk: float = 0.0
    feasibility: float = 0.0
    time_to_act_hours: int = 24
    status: str = "PENDING_REVIEW"
    escalation_trigger: str = ""


class BottleneckNode(BaseModel):
    """Network bottleneck node — used in physical_system_status.bottlenecks and top-level."""
    node_id: str = ""
    node_label: str = Field(default="", alias="label")
    bottleneck_score: float = 0.0
    is_critical_bottleneck: bool = False
    utilization: float = 0.0
    criticality: float = 0.0
    redundancy: float = 0.0
    degree: int = 0
    rank: int = 0
    sector: str = "unknown"
    lat: float = 0.0
    lng: float = 0.0

    model_config = ConfigDict(populate_by_name=True)


class FinancialImpact(BaseModel):
    """Full financial impact block — guaranteed list fields, no None numerics."""
    total_loss_usd: float = 0.0
    total_loss_formatted: str = "$0"
    direct_loss_usd: float = 0.0
    indirect_loss_usd: float = 0.0
    systemic_loss_usd: float = 0.0
    systemic_multiplier: float = 1.0
    affected_entities: int = 0
    critical_entities: int = 0
    top_entities: List[Dict[str, Any]] = Field(default_factory=list)
    gdp_impact_pct: float = 0.0             # NOT Optional — always a number
    sector_losses: List[Dict[str, Any]] = Field(default_factory=list)  # LIST not dict
    confidence_interval: Dict[str, float] = Field(
        default_factory=lambda: {"lower": 0.0, "upper": 0.0, "confidence": 0.0}
    )


class SectorAnalysisRow(BaseModel):
    sector: str = "unknown"
    exposure: float = 0.0
    stress: float = 0.0
    classification: str = "NOMINAL"
    risk_level: str = "NOMINAL"


class PropagationStep(BaseModel):
    step: int = 0
    entity_id: str = ""
    entity_label: str = ""
    impact: float = 0.0
    propagation_score: float = 0.0
    mechanism: str = ""


class UnifiedRiskScore(BaseModel):
    score: float = 0.0
    components: Dict[str, float] = Field(default_factory=dict)
    risk_level: str = "NOMINAL"
    classification: str = "NOMINAL"


class PhysicalSystemStatus(BaseModel):
    """Physical system status — congestion_score and recovery_score are NEVER None."""
    nodes_assessed: int = 0
    saturated_nodes: int = 0
    flow_balance_status: str = "NOMINAL"
    system_utilization: float = 0.0
    congestion_score: float = 0.0       # NOT Optional — .toFixed() safe
    recovery_score: float = 0.0         # NOT Optional — .toFixed() safe
    bottlenecks: List[Any] = Field(default_factory=list)  # NOT Optional — .map() safe
    node_states: Dict[str, Any] = Field(default_factory=dict)


class RecoveryPoint(BaseModel):
    day: int = 0
    recovery_fraction: float = 0.0
    damage_remaining: float = 0.0
    residual_stress: float = 0.0


class LiquidityStress(BaseModel):
    aggregate_stress: float = 0.0
    liquidity_stress: float = 0.0
    car_ratio: float = 0.12
    lcr_ratio: float = 1.0
    outflow_rate: float = 0.0
    time_to_breach_hours: float = 9999.0
    classification: str = "NOMINAL"
    sector: str = "banking"


class InsuranceStress(BaseModel):
    """Insurance stress — time_to_insolvency_hours uses 9999.0 to mean 'no imminent risk'."""
    sector: str = "insurance"
    aggregate_stress: float = 0.0
    severity_index: float = 0.0
    combined_ratio: float = 1.0
    claims_surge_multiplier: float = 1.0
    reserve_adequacy: float = 1.0          # kept for backward compat (old field name)
    reserve_adequacy_ratio: float = 1.0
    tiv_exposure: float = 0.0             # backward compat alias
    tiv_exposure_usd: float = 0.0
    solvency_score: float = 1.0
    loss_ratio: float = 0.0
    reinsurance_trigger: bool = False
    time_to_insolvency_hours: float = 9999.0  # 9999 = no imminent insolvency
    ifrs17_risk_adjustment_pct: float = 0.0
    portfolio_exposure_usd: float = 0.0
    underwriting_status: str = "STABLE"
    affected_lines: List[Any] = Field(default_factory=list)
    run_id: str = ""
    classification: str = "NOMINAL"


class FintechStress(BaseModel):
    aggregate_stress: float = 0.0
    digital_stress: float = 0.0
    digital_banking_stress: float = 0.0
    liquidity_stress: float = 0.0        # backward-compat alias
    payment_disruption_score: float = 0.0
    cross_border_disruption: float = 0.0
    settlement_delay_hours: float = 0.0
    payment_volume_impact_pct: float = 0.0
    api_availability_pct: float = 100.0
    time_to_payment_failure_hours: float = 9999.0
    affected_platforms: List[Any] = Field(default_factory=list)
    run_id: str = ""
    sector: str = "fintech"
    classification: str = "NOMINAL"


class FlowResult(BaseModel):
    flow_type: str = ""
    base_volume_usd: float = 0.0
    disrupted_volume_usd: float = 0.0
    disruption_factor: float = 0.0
    congestion: float = 0.0
    delay_days: float = 0.0
    backlog_usd: float = 0.0
    rerouting_cost_usd: float = 0.0
    saturation_pct: float = 0.0
    stress_score: float = 0.0
    classification: str = "NOMINAL"
    volume_loss_usd: float = 0.0


class FlowAnalysis(BaseModel):
    money: Dict[str, Any] = Field(default_factory=dict)
    logistics: Dict[str, Any] = Field(default_factory=dict)
    energy: Dict[str, Any] = Field(default_factory=dict)
    payments: Dict[str, Any] = Field(default_factory=dict)
    claims: Dict[str, Any] = Field(default_factory=dict)
    aggregate_disruption_usd: float = 0.0
    most_disrupted_flow: str = "money"
    flow_recovery_days: int = 0


class CausalChainStep(BaseModel):
    step: int = 0
    entity_id: str = ""
    entity_label: str = ""
    entity_label_ar: str = ""
    impact_usd: float = 0.0
    impact_usd_formatted: str = "$0"
    stress_delta: float = 0.0
    mechanism_en: str = ""
    mechanism_ar: str = ""
    sector: str = "unknown"
    hop: int = 0
    confidence: float = 0.0


class SensitivityPerturbation(BaseModel):
    delta_severity_pct: float = 0.0
    perturbed_severity: float = 0.0
    resulting_loss_usd: float = 0.0
    resulting_risk_score: float = 0.0
    loss_change_pct: float = 0.0
    risk_change_pct: float = 0.0


class Sensitivity(BaseModel):
    perturbations: List[SensitivityPerturbation] = Field(default_factory=list)
    most_sensitive_parameter: str = ""
    linearity_score: float = 0.0
    base_severity: float = 0.0
    base_loss_usd: float = 0.0
    base_risk_score: float = 0.0


class UncertaintyBands(BaseModel):
    lower_bound: float = 0.0
    upper_bound: float = 0.0
    band_width: float = 0.0
    interpretation: str = ""
    confidence: float = 0.0


class ExplainabilityBlock(BaseModel):
    causal_chain: List[Dict[str, Any]] = Field(default_factory=list)
    narrative_en: str = ""
    narrative_ar: str = ""
    sensitivity: Dict[str, Any] = Field(default_factory=dict)
    uncertainty_bands: Dict[str, Any] = Field(default_factory=dict)
    model_equation: str = ""
    confidence_score: float = 0.0        # NOT Optional — .toFixed() safe
    methodology: str = "deterministic_propagation"
    source: str = ""


class ActionItem(BaseModel):
    action_id: str = ""
    rank: int = 0
    sector: str = "cross-sector"
    owner: str = ""
    action: str = ""
    action_ar: str = ""
    priority_score: float = 0.0
    urgency: float = 0.0
    loss_avoided_usd: float = 0.0
    loss_avoided_formatted: str = "$0"
    cost_usd: float = 0.0
    cost_formatted: str = "$0"
    regulatory_risk: float = 0.0
    feasibility: float = 0.0
    time_to_act_hours: int = 24
    status: str = "PENDING_REVIEW"
    escalation_trigger: str = ""


class DecisionPlan(BaseModel):
    """Decision plan — all action lists default to [], priority_matrix defaults to {}."""
    business_severity: str = "LOW"
    time_to_first_failure_hours: float = 999.0
    actions: List[Dict[str, Any]] = Field(default_factory=list)
    escalation_triggers: List[str] = Field(default_factory=list)
    monitoring_priorities: List[str] = Field(default_factory=list)
    five_questions: Dict[str, Any] = Field(default_factory=dict)
    # Derived partitions — NOT Optional, default to empty list
    immediate_actions: List[Dict[str, Any]] = Field(default_factory=list)
    short_term_actions: List[Dict[str, Any]] = Field(default_factory=list)
    long_term_actions: List[Dict[str, Any]] = Field(default_factory=list)
    priority_matrix: Dict[str, List[str]] = Field(
        default_factory=lambda: {"IMMEDIATE": [], "URGENT": [], "MONITOR": [], "WATCH": []}
    )


class Headline(BaseModel):
    total_loss_usd: float = 0.0
    total_loss_formatted: str = "$0"
    peak_day: int = 0
    affected_entities: int = 0
    critical_count: int = 0
    elevated_count: int = 0
    max_recovery_days: int = 0
    severity_code: str = "NOMINAL"
    average_stress: float = 0.0


# ---------------------------------------------------------------------------
# Primary response model
# ---------------------------------------------------------------------------

class SimulateResponse(BaseModel):
    """Full simulation output — 16 top-level fields.

    CONTRACT: Every list field defaults to []. Every numeric field defaults to 0.0.
    Frontend can safely call .map(), .reduce(), .toFixed() on all fields.
    """

    # Metadata
    run_id: str = ""
    scenario_id: str = ""
    model_version: str = "2.1.0"
    severity: float = 0.0
    horizon_hours: int = 336
    time_horizon_days: int = 14
    generated_at: str = ""
    duration_ms: int = 0

    # Core outputs — NEVER None
    event_severity: float = 0.0
    peak_day: int = 0
    confidence_score: float = 0.0
    propagation_score: float = 0.0
    unified_risk_score: float = 0.0
    risk_level: str = "NOMINAL"
    congestion_score: float = 0.0       # top-level alias
    recovery_score: float = 0.0         # top-level alias

    # Structured sub-objects — all have safe defaults
    financial_impact: FinancialImpact = Field(default_factory=FinancialImpact)
    sector_analysis: List[SectorAnalysisRow] = Field(default_factory=list)
    propagation_chain: List[Dict[str, Any]] = Field(default_factory=list)
    physical_system_status: PhysicalSystemStatus = Field(default_factory=PhysicalSystemStatus)
    bottlenecks: List[Dict[str, Any]] = Field(default_factory=list)
    recovery_trajectory: List[Dict[str, Any]] = Field(default_factory=list)
    banking_stress: Dict[str, Any] = Field(default_factory=dict)
    insurance_stress: Dict[str, Any] = Field(default_factory=dict)
    fintech_stress: Dict[str, Any] = Field(default_factory=dict)
    flow_analysis: Dict[str, Any] = Field(default_factory=dict)
    explainability: ExplainabilityBlock = Field(default_factory=ExplainabilityBlock)
    decision_plan: DecisionPlan = Field(default_factory=DecisionPlan)
    headline: Headline = Field(default_factory=Headline)

    model_config = ConfigDict(arbitrary_types_allowed=True, populate_by_name=True)

    @model_validator(mode="after")
    def ensure_top_level_aliases(self) -> "SimulateResponse":
        """Mirror nested values into top-level aliases if they're still at default."""
        if self.congestion_score == 0.0:
            self.congestion_score = self.physical_system_status.congestion_score
        if self.recovery_score == 0.0:
            self.recovery_score = self.physical_system_status.recovery_score
        return self


# ---------------------------------------------------------------------------
# Standalone response models
# ---------------------------------------------------------------------------

class DecisionPlanResponse(BaseModel):
    """Standalone decision plan endpoint response."""
    run_id: str = ""
    scenario_id: str = ""
    risk_level: str = "NOMINAL"
    decision_plan: DecisionPlan = Field(default_factory=DecisionPlan)


class ExplainabilityResponse(BaseModel):
    """Standalone explainability endpoint response."""
    run_id: str = ""
    scenario_id: str = ""
    confidence_score: float = 0.0
    explainability: ExplainabilityBlock = Field(default_factory=ExplainabilityBlock)


class HealthResponse(BaseModel):
    """Health check response."""
    status: str = "ok"
    model_version: str = "2.1.0"
    scenarios_available: int = 0
    nodes_in_registry: int = 0
    timestamp: str = ""


class ScenarioListItem(BaseModel):
    """Scenario catalog entry for listing."""
    id: str = ""
    name: str = ""
    name_ar: str = ""
    shock_nodes: List[str] = Field(default_factory=list)
    base_loss_usd: float = 0.0
    sectors_affected: List[str] = Field(default_factory=list)
    cross_sector: bool = False


class ErrorResponse(BaseModel):
    """Standard error envelope."""
    error: str = ""
    detail: Optional[str] = None
    status_code: int = 400
