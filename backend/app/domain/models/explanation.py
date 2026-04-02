"""
Impact Observatory | مرصد الأثر — ExplanationPack (v4 §3.12)
Human-readable and machine-auditable explanation with mandatory equation strings.
"""

from pydantic import BaseModel, Field
from typing import List, Literal


class ExplanationDriver(BaseModel):
    """Key driver contributing to the scenario outcome."""
    driver: str = Field(..., min_length=1, max_length=120)
    magnitude: float = Field(...)
    unit: str = Field(..., min_length=1, max_length=64)
    affected_entities: List[str] = Field(default_factory=list, description="UUIDv7 references")

    model_config = {"extra": "ignore"}


class StageTrace(BaseModel):
    """Per-stage execution trace for auditability."""
    stage: Literal[
        "physics", "graph", "propagation", "financial",
        "risk", "regulatory", "decision", "explanation"
    ] = Field(...)
    status: Literal["completed", "partial", "failed", "skipped"] = Field(...)
    input_ref: str = Field(..., min_length=1, max_length=300)
    output_ref: str = Field(..., min_length=1, max_length=300)
    notes: str = Field(default="", max_length=1000)

    model_config = {"extra": "ignore"}


class ActionExplanation(BaseModel):
    """Explanation for why a specific action was selected."""
    rank: int = Field(..., ge=1, le=3)
    action_id: str = Field(..., description="UUIDv7")
    why_selected: str = Field(..., min_length=1, max_length=2000)
    supporting_metrics: dict = Field(
        ..., description="Keys: urgency, value, reg_risk, feasibility, time_effect, priority_score"
    )

    model_config = {"extra": "ignore"}


class Equations(BaseModel):
    """Mandatory exact equation strings."""
    loss_formula: str = Field(
        default="Loss(t) = Exposure × ShockIntensity × PropagationFactor(t)", frozen=True
    )
    flow_formula: str = Field(
        default="Flow(t) = Capacity × Availability × RouteEfficiency", frozen=True
    )
    propagation_formula: str = Field(
        default="Impact_next = Impact_current × TransmissionCoefficient", frozen=True
    )
    priority_formula: str = Field(
        default="Priority = 0.25 Urgency + 0.30 Value + 0.20 RegRisk + 0.15 Feasibility + 0.10 TimeEffect",
        frozen=True,
    )

    model_config = {"extra": "ignore"}


class ExplanationPack(BaseModel):
    """v4 canonical explanation — audit-grade explanation package."""

    run_id: str = Field(..., description="UUIDv7 run reference")
    generated_at: str = Field(..., description="ISO-8601 UTC timestamp")
    summary: str = Field(..., min_length=1, max_length=5000, description="Executive summary narrative")
    equations: Equations = Field(default_factory=Equations, description="Mandatory formula strings")
    drivers: List[ExplanationDriver] = Field(..., min_length=1, description="Key outcome drivers")
    stage_traces: List[StageTrace] = Field(
        ..., min_length=8, max_length=8, description="Exactly 8 post-scenario stage traces"
    )
    action_explanations: List[ActionExplanation] = Field(
        default_factory=list, max_length=3, description="Explanation per ranked action"
    )
    assumptions: List[str] = Field(default_factory=list, description="Model assumptions")
    limitations: List[str] = Field(default_factory=list, description="Known limitations")

    model_config = {"extra": "ignore"}
