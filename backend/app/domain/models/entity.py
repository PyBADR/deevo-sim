"""
Impact Observatory | مرصد الأثر — Entity (v4 §3.2)
Stress participant node. UUIDv7 identity, typed, with physical + financial attributes.
"""

from pydantic import BaseModel, Field
from typing import Literal


class Entity(BaseModel):
    """v4 canonical entity — a stress participant node in the scenario graph."""

    entity_id: str = Field(..., description="UUIDv7 unique within scenario")
    entity_type: Literal["bank", "insurer", "fintech", "market_infrastructure"] = Field(
        ..., description="Sector classification"
    )
    name: str = Field(..., min_length=1, max_length=160, description="Entity name")
    jurisdiction: str = Field(..., min_length=2, max_length=32, description="Regulatory jurisdiction")
    exposure: float = Field(..., ge=0.0, description="Total exposure in base currency")
    capital_buffer: float = Field(..., ge=0.0, description="Available capital buffer")
    liquidity_buffer: float = Field(..., ge=0.0, description="Available liquidity buffer")
    capacity: float = Field(..., ge=0.0, description="Flow throughput capacity")
    availability: float = Field(..., ge=0.0, le=1.0, description="Operational availability ratio")
    route_efficiency: float = Field(..., ge=0.0, le=1.0, description="Route efficiency ratio")
    criticality: float = Field(..., ge=0.0, le=1.0, description="Systemic criticality score")
    regulatory_classification: Literal["systemic", "material", "standard"] = Field(
        ..., description="Regulatory classification tier"
    )
    active: bool = Field(..., description="Whether entity participates in simulation")

    model_config = {"extra": "ignore"}
