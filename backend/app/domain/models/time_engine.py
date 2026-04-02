"""
Impact Observatory | مرصد الأثر — Time Engine Models (v4 §17.3)
Temporal simulation state objects: TimeStepState, EntityTemporalImpact.
ShockEffective(t) = ShockIntensity × (1 - shock_decay_rate)^t
"""

from pydantic import BaseModel, Field
from typing import List, Literal


class EntityTemporalImpact(BaseModel):
    """v4 §17.3.2 — Per-entity impact at a single timestep."""

    entity_id: str = Field(..., description="UUIDv7 entity reference")
    impact_score: float = Field(..., ge=0.0, le=5.0, description="Entity impact magnitude")
    impact_delta: float = Field(..., description="Change from previous timestep")
    flow_value: float = Field(..., ge=0.0, description="Entity flow at this timestep")
    flow_delta: float = Field(..., description="Flow change from previous timestep")
    loss_value: float = Field(..., ge=0.0, description="Entity loss at this timestep")
    loss_delta: float = Field(..., description="Loss change from previous timestep")
    status: Literal["stable", "watch", "breach", "failed"] = Field(...)

    model_config = {"extra": "ignore"}


class TimeStepState(BaseModel):
    """v4 §17.3.1 — Complete system state at a single timestep."""

    run_id: str = Field(..., description="UUIDv7 run reference")
    timestep_index: int = Field(..., ge=0)
    timestamp: str = Field(..., description="ISO-8601 UTC")
    shock_intensity_effective: float = Field(..., ge=0.0, le=5.0, description="Decayed shock at this step")
    entity_impacts: List[EntityTemporalImpact] = Field(
        default_factory=list, description="Per-entity impacts"
    )
    aggregate_loss: float = Field(..., ge=0.0)
    aggregate_flow: float = Field(..., ge=0.0)
    regulatory_breach_count: int = Field(..., ge=0)
    system_status: Literal["stable", "degrading", "critical", "failed"] = Field(...)

    model_config = {"extra": "ignore"}
