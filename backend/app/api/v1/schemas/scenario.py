"""
Impact Observatory | مرصد الأثر — Scenario API Schemas (v4 §4.2, §18.2)
Request/response schemas for scenario catalog and run endpoints.
Imports domain models directly — no contract duplication.
"""

from pydantic import BaseModel, Field
from typing import Dict, List, Literal, Optional

from ....domain.models.decision import DecisionPlan


# ── Typed enums aligned with v4 domain ────────────────────────────────────
ScenarioId = Literal[
    "hormuz_chokepoint_disruption",
    "red_sea_trade_corridor_instability",
    "energy_market_volatility_shock",
    "critical_port_operations_disruption",
    "regional_airspace_disruption",
    "cross_border_sanctions_escalation",
    "regional_liquidity_stress_event",
    "financial_infrastructure_cyber_disruption",
]

# Aligned with v4 ScenarioDna.severity_band + catalog's medium_high
SeverityLevel = Literal["low", "medium", "medium_high", "high", "extreme"]

ScenarioDomainType = Literal[
    "trade_logistics",
    "markets_energy",
    "compliance_financial",
    "banking_financial",
    "aviation_logistics",
    "digital_financial",
]

TriggerType = Literal[
    "maritime_disruption",
    "corridor_instability",
    "price_volatility",
    "port_disruption",
    "airspace_constraint",
    "sanctions_escalation",
    "liquidity_stress",
    "cyber_disruption",
]


# ── Request schemas ───────────────────────────────────────────────────────
class ScenarioParameters(BaseModel):
    """Financial channel parameters from catalog. Validated 0-1 range."""
    flow_reduction_ratio: float = Field(ge=0.0, le=1.0)
    rerouting_ratio: float = Field(ge=0.0, le=1.0)
    delay_multiplier: float = Field(ge=1.0, le=10.0)
    claims_spike_ratio: float = Field(ge=0.0, le=1.0)
    deposit_outflow_ratio: float = Field(ge=0.0, le=1.0)
    fraud_risk_ratio: float = Field(ge=0.0, le=1.0)


class RegulatoryContext(BaseModel):
    """Optional override for regulatory thresholds."""
    jurisdiction: str = "GCC"
    lcr_floor: float = Field(default=1.0, ge=0.0)
    solvency_floor: float = Field(default=1.0, ge=0.0)
    availability_floor: float = Field(default=0.995, ge=0.0, le=1.0)


class ScenarioRunRequest(BaseModel):
    """POST /runs request body when launching from catalog."""
    scenario_id: ScenarioId
    time_horizon_days: int = Field(default=14, ge=1, le=365)
    severity_level: SeverityLevel = "high"
    custom_parameters: Optional[ScenarioParameters] = None
    regulatory_context: Optional[RegulatoryContext] = None


class ScenarioRunResponse(BaseModel):
    """202 Accepted response for POST /runs."""
    run_id: str
    status: Literal["queued", "running", "completed", "failed"]
    scenario_id: str


# ── Dashboard response schemas (typed, not Dict) ─────────────────────────
class DashboardSummary(BaseModel):
    """Executive headline KPIs for dashboard top cards."""
    headline_loss_usd: float = Field(ge=0.0, description="Total projected loss in USD")
    peak_day: int = Field(ge=0, description="Day with maximum impact")
    business_severity: SeverityLevel
    executive_status: str = Field(description="Human-readable status line")
    system_time_to_first_failure_hours: Optional[float] = None


class SectorStressAggregate(BaseModel):
    """Aggregate stress data for a sector, wrapping typed entity lists."""
    aggregate: Dict = Field(default_factory=dict, description="Sector-level aggregate metrics")
    entities: List[Dict] = Field(default_factory=list, description="Per-entity stress objects")
    count: int = Field(default=0, ge=0)


class DashboardPayload(BaseModel):
    """
    Full dashboard response combining all pipeline outputs.
    Each sector field wraps the v4 typed models in aggregate form.
    """
    summary: DashboardSummary
    financial: SectorStressAggregate
    banking: SectorStressAggregate
    insurance: SectorStressAggregate
    fintech: SectorStressAggregate
    decisions: Optional[DecisionPlan] = None
    timeline: List[Dict] = Field(default_factory=list)


# ── Catalog response schema ──────────────────────────────────────────────
class ScenarioDefinition(BaseModel):
    """Schema for a single catalog entry returned by GET /scenarios."""
    scenario_id: str
    scenario_name_en: str
    scenario_name_ar: str
    domain: ScenarioDomainType
    trigger_type: TriggerType
    geographic_scope: List[str]
    severity_default: SeverityLevel
    shock_intensity_default: float = Field(ge=0.0, le=1.0)
    primary_channels: List[str]
    affected_sectors: List[str]
    scenario_parameters: ScenarioParameters
