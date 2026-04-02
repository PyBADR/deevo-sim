"""
Impact Observatory | مرصد الأثر — Business Impact Layer (v4 §16) + Executive Explanation (v4 §19)
Loss trajectory, time-to-failure, regulatory breach events, and executive narrative.
"""

from pydantic import BaseModel, Field
from typing import List, Optional, Literal


# ============================================================================
# §16.2.1 LossTrajectoryPoint
# ============================================================================

class LossTrajectoryPoint(BaseModel):
    """Per-timestep loss trajectory point with velocity and acceleration."""

    run_id: str = Field(..., description="UUIDv7 run reference")
    scope_level: Literal["entity", "sector", "system"] = Field(...)
    scope_ref: str = Field(..., description="Entity UUID, sector name, or 'system'")
    timestep_index: int = Field(..., ge=0)
    timestamp: str = Field(..., description="ISO-8601 UTC")
    direct_loss: float = Field(..., ge=0.0, description="Direct loss at timestep")
    propagated_loss: float = Field(..., ge=0.0, description="Propagated loss at timestep")
    cumulative_loss: float = Field(..., ge=0.0, description="Sum of all losses to date")
    revenue_at_risk: float = Field(..., ge=0.0)
    loss_velocity: float = Field(..., description="Loss rate of change per step")
    loss_acceleration: float = Field(..., description="Loss acceleration per step²")
    status: Literal["stable", "deteriorating", "critical", "failed"] = Field(...)

    model_config = {"extra": "ignore"}


# ============================================================================
# §16.2.2 TimeToFailure
# ============================================================================

class TimeToFailure(BaseModel):
    """Time-to-failure prediction for a specific failure type and scope."""

    run_id: str = Field(..., description="UUIDv7 run reference")
    scope_level: Literal["entity", "sector", "system"] = Field(...)
    scope_ref: str = Field(...)
    failure_type: Literal[
        "liquidity_failure", "capital_failure", "solvency_failure",
        "availability_failure", "regulatory_failure"
    ] = Field(...)
    failure_threshold_value: float = Field(...)
    current_value_at_t0: float = Field(...)
    predicted_failure_timestep: Optional[int] = Field(default=None, description="null if no failure")
    predicted_failure_timestamp: Optional[str] = Field(default=None)
    time_to_failure_hours: Optional[float] = Field(default=None)
    confidence_score: float = Field(..., ge=0.0, le=1.0)
    failure_reached_within_horizon: bool = Field(...)

    model_config = {"extra": "ignore"}


# ============================================================================
# §16.2.3 RegulatoryBreachEvent
# ============================================================================

class RegulatoryBreachEvent(BaseModel):
    """Timestamped regulatory breach event."""

    run_id: str = Field(...)
    timestep_index: int = Field(..., ge=0)
    timestamp: str = Field(...)
    scope_level: Literal["entity", "sector", "system"] = Field(...)
    scope_ref: str = Field(...)
    metric_name: Literal[
        "lcr", "nsfr", "cet1_ratio", "capital_adequacy_ratio",
        "solvency_ratio", "reserve_ratio", "service_availability",
        "settlement_delay_minutes"
    ] = Field(...)
    metric_value: float = Field(...)
    threshold_value: float = Field(...)
    breach_direction: Literal["below_minimum", "above_maximum"] = Field(...)
    breach_level: Literal["minor", "major", "critical"] = Field(...)
    first_breach: bool = Field(...)
    reportable: bool = Field(...)

    model_config = {"extra": "ignore"}


# ============================================================================
# §16.3.1 BusinessImpactSummary
# ============================================================================

class BusinessImpactSummary(BaseModel):
    """Aggregate business impact summary for a run."""

    run_id: str = Field(...)
    currency: str = Field(..., pattern=r"^[A-Z]{3}$")
    peak_cumulative_loss: float = Field(..., ge=0.0)
    peak_loss_timestep: int = Field(..., ge=0)
    peak_loss_timestamp: str = Field(...)
    system_time_to_first_failure_hours: Optional[float] = Field(default=None)
    first_failure_type: Optional[str] = Field(default=None)
    first_failure_scope_ref: Optional[str] = Field(default=None)
    critical_breach_count: int = Field(..., ge=0)
    reportable_breach_count: int = Field(..., ge=0)
    business_severity: Literal["low", "medium", "high", "severe"] = Field(...)
    executive_status: Literal["monitor", "intervene", "escalate", "crisis"] = Field(...)

    model_config = {"extra": "ignore"}


# ============================================================================
# §19 Executive Decision Explanation
# ============================================================================

class CauseEffectLink(BaseModel):
    """One step in the cause → effect → consequence chain."""
    step: int = Field(..., ge=1)
    cause: str = Field(..., min_length=1, max_length=500)
    effect: str = Field(..., min_length=1, max_length=500)
    business_consequence: str = Field(..., min_length=1, max_length=500)
    evidence_metric: Literal[
        "loss", "flow", "lcr", "solvency_ratio", "service_availability",
        "settlement_delay_minutes", "criticality"
    ] = Field(...)
    evidence_value: float = Field(...)

    model_config = {"extra": "ignore"}


class LossTranslation(BaseModel):
    """Business-language loss translation for executives."""
    peak_loss_value: float = Field(..., ge=0.0)
    peak_loss_time: str = Field(...)
    affected_revenue_value: float = Field(..., ge=0.0)
    entities_at_risk_count: int = Field(..., ge=0)
    first_failed_scope_ref: Optional[str] = Field(default=None)
    business_materiality_band: Literal["immaterial", "moderate", "material", "critical"] = Field(...)

    model_config = {"extra": "ignore"}


class ExecutiveActionExplanation(BaseModel):
    """Business-language explanation of a recommended action."""
    rank: int = Field(..., ge=1, le=3)
    action_id: str = Field(...)
    action_title: str = Field(..., min_length=1, max_length=200)
    why_now: str = Field(..., min_length=1, max_length=1000)
    expected_business_benefit: str = Field(..., min_length=1, max_length=1000)
    expected_regulatory_effect: str = Field(..., min_length=1, max_length=1000)
    if_not_executed: str = Field(..., min_length=1, max_length=1000)

    model_config = {"extra": "ignore"}


class ExecutiveDecisionExplanation(BaseModel):
    """v4 §19.1.1 — Business-facing executive explanation."""

    run_id: str = Field(...)
    generated_at: str = Field(...)
    executive_summary: str = Field(..., min_length=1, max_length=3000)
    cause_effect_chain: List[CauseEffectLink] = Field(..., min_length=1, max_length=20)
    loss_translation: LossTranslation = Field(...)
    recommended_actions: List[ExecutiveActionExplanation] = Field(..., max_length=3)
    board_message: str = Field(..., min_length=1, max_length=3000)
    regulator_message: str = Field(..., min_length=1, max_length=3000)

    model_config = {"extra": "ignore"}
