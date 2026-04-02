"""
Impact Observatory | مرصد الأثر — FinancialImpact (v4 §3.5)
Per-entity financial loss computed by: Loss = Exposure × ShockIntensity × PropagationFactor
"""

from pydantic import BaseModel, Field
from typing import Literal


class FinancialImpact(BaseModel):
    """v4 canonical financial impact — entity-level loss quantification."""

    entity_id: str = Field(..., description="UUIDv7 entity reference")
    timestamp: str = Field(..., description="ISO-8601 UTC timestamp")
    exposure: float = Field(..., ge=0.0, description="Entity exposure in base currency")
    shock_intensity: float = Field(..., ge=0.0, le=5.0, description="Scenario shock scalar")
    propagation_factor: float = Field(..., ge=0.0, le=5.0, description="Derived propagation multiplier")
    loss: float = Field(..., ge=0.0, description="Computed loss = exposure × shock × propagation")
    revenue_at_risk: float = Field(..., ge=0.0, description="Revenue at risk in base currency")
    capital_after_loss: float = Field(..., description="Capital remaining after loss (may be negative)")
    liquidity_after_loss: float = Field(..., description="Liquidity remaining after loss (may be negative)")
    impact_status: Literal["stable", "watch", "breach", "default"] = Field(
        ..., description="Entity impact classification"
    )

    model_config = {"extra": "ignore"}
