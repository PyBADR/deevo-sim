"""
Impact Observatory | مرصد الأثر — FlowState (v4 §3.4)
Single entity flow snapshot from the physics stage.
Flow = Capacity × Availability × RouteEfficiency
"""

from pydantic import BaseModel, Field
from typing import Literal


class FlowState(BaseModel):
    """v4 canonical flow state — entity-level physics snapshot."""

    timestamp: str = Field(..., description="ISO-8601 UTC timestamp")
    entity_id: str = Field(..., description="UUIDv7 entity reference")
    inbound_flow: float = Field(..., ge=0.0, description="Inbound flow units")
    outbound_flow: float = Field(..., ge=0.0, description="Outbound flow units")
    net_flow: float = Field(..., description="Net flow (may be negative)")
    capacity: float = Field(..., ge=0.0, description="Throughput capacity")
    availability: float = Field(..., ge=0.0, le=1.0, description="Availability ratio")
    route_efficiency: float = Field(..., ge=0.0, le=1.0, description="Route efficiency ratio")
    computed_flow: float = Field(..., ge=0.0, description="capacity × availability × route_efficiency")
    flow_status: Literal["nominal", "degraded", "interrupted"] = Field(
        ..., description="Flow health status"
    )

    model_config = {"extra": "ignore"}
