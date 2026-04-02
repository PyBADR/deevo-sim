"""
Impact Observatory | مرصد الأثر — DecisionAction + DecisionPlan (v4 §3.9, §3.10)
Ranked decision actions with priority formula:
Priority = 0.25×Urgency + 0.30×Value + 0.20×RegRisk + 0.15×Feasibility + 0.10×TimeEffect
TOP 3 actions only. Deterministic tie-breaking: reg_risk → urgency → execution_window_hours → action_id.
"""

from pydantic import BaseModel, Field
from typing import List, Literal


class DecisionAction(BaseModel):
    """v4 canonical decision action — one ranked response action."""

    action_id: str = Field(..., description="UUIDv7 unique within run")
    run_id: str = Field(..., description="UUIDv7 run reference")
    rank: int = Field(..., ge=1, le=3, description="Action rank (1=highest)")
    action_type: Literal[
        "inject_liquidity", "restrict_exposure", "reroute_flow",
        "raise_capital_buffer", "increase_reserves",
        "trigger_regulatory_escalation", "reduce_counterparty_limit",
        "activate_bcp"
    ] = Field(..., description="Action classification")
    target_level: Literal["entity", "sector", "system"] = Field(
        ..., description="Scope of action target"
    )
    target_ref: str = Field(..., description="Entity UUID, sector name, or 'system'")
    urgency: float = Field(..., ge=0.0, le=1.0, description="Urgency sub-score")
    value: float = Field(..., ge=0.0, le=1.0, description="Value sub-score")
    reg_risk: float = Field(..., ge=0.0, le=1.0, description="Regulatory risk sub-score")
    feasibility: float = Field(..., ge=0.0, le=1.0, description="Feasibility sub-score")
    time_effect: float = Field(..., ge=0.0, le=1.0, description="Time effect sub-score")
    priority_score: float = Field(..., ge=0.0, le=1.0, description="Weighted priority score")
    reason_codes: List[str] = Field(
        ..., min_length=1,
        description="Breach/driver codes triggering this action"
    )
    preconditions: List[str] = Field(default_factory=list, description="Required preconditions")
    expected_loss_reduction: float = Field(..., ge=0.0, description="Expected loss reduction in currency")
    expected_flow_recovery: float = Field(..., ge=0.0, le=1.0, description="Expected flow recovery ratio")
    execution_window_hours: int = Field(..., ge=0, le=168, description="Execution window in hours")
    requires_override: bool = Field(..., description="Whether admin/operator override is needed")

    model_config = {"extra": "ignore"}


class DecisionPlan(BaseModel):
    """v4 canonical decision plan — final decision engine output for a run."""

    run_id: str = Field(..., description="UUIDv7 run reference")
    generated_at: str = Field(..., description="ISO-8601 UTC generation timestamp")
    model_version: str = Field(..., description="Semver model version")
    candidate_count: int = Field(..., ge=0, description="Total candidate actions generated")
    feasible_count: int = Field(..., ge=0, description="Candidates passing feasibility filter")
    actions: List[DecisionAction] = Field(
        default_factory=list, max_length=3, description="Top 3 ranked actions"
    )
    dropped_actions_count: int = Field(..., ge=0, description="Actions dropped by filters")
    constrained_by_rbac: bool = Field(..., description="Whether RBAC filtered any candidates")
    constrained_by_regulation: bool = Field(..., description="Whether regulation filtered candidates")
    plan_status: Literal["complete", "partial", "empty"] = Field(
        ..., description="Decision plan completeness"
    )

    model_config = {"extra": "ignore", "protected_namespaces": ()}
