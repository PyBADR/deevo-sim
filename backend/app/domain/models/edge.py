"""
Impact Observatory | مرصد الأثر — Edge (v4 §3.3)
Directional dependency between entities.
"""

from pydantic import BaseModel, Field
from typing import Literal


class Edge(BaseModel):
    """v4 canonical edge — directional dependency link."""

    edge_id: str = Field(..., description="UUIDv7 unique within scenario")
    source_entity_id: str = Field(..., description="Source entity UUIDv7")
    target_entity_id: str = Field(..., description="Target entity UUIDv7")
    relation_type: Literal["funding", "payment", "insurance", "technology", "market"] = Field(
        ..., description="Dependency type"
    )
    exposure: float = Field(..., ge=0.0, description="Edge exposure in base currency")
    transmission_coefficient: float = Field(..., ge=0.0, le=1.0, description="Propagation strength")
    capacity: float = Field(..., ge=0.0, description="Edge throughput capacity")
    availability: float = Field(..., ge=0.0, le=1.0, description="Edge availability ratio")
    route_efficiency: float = Field(..., ge=0.0, le=1.0, description="Route efficiency ratio")
    latency_ms: int = Field(..., ge=0, description="Edge latency in milliseconds")
    active: bool = Field(..., description="Whether edge is active in simulation")

    model_config = {"extra": "ignore"}
