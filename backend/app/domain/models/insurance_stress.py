"""
Impact Observatory | مرصد الأثر — InsuranceStress (v4 §3.7)
Per-entity insurance claims, reserves, and solvency stress.
"""

from pydantic import BaseModel, Field


class InsuranceBreachFlags(BaseModel):
    """v4 breach flags for insurance regulatory thresholds."""
    solvency_breach: bool = Field(..., description="Solvency ratio below minimum")
    reserve_breach: bool = Field(..., description="Reserve ratio below minimum")
    liquidity_breach: bool = Field(..., description="Liquidity gap beyond tolerance")

    model_config = {"extra": "ignore"}


class InsuranceStress(BaseModel):
    """v4 canonical insurance stress — per-entity claims, reserves, solvency."""

    entity_id: str = Field(..., description="UUIDv7 entity reference (entity_type=insurer)")
    timestamp: str = Field(..., description="ISO-8601 UTC timestamp")
    premium_drop: float = Field(..., ge=0.0, description="Premium revenue loss in base currency")
    claims_spike: float = Field(..., ge=0.0, description="Claims surge in base currency")
    reserve_ratio: float = Field(..., ge=0.0, description="Reserve ratio (reserves / obligations)")
    solvency_ratio: float = Field(..., ge=0.0, description="Solvency ratio (assets / liabilities)")
    combined_ratio: float = Field(..., ge=0.0, description="Combined loss and expense ratio")
    liquidity_gap: float = Field(..., description="Liquidity gap (may be negative = deficit)")
    breach_flags: InsuranceBreachFlags = Field(..., description="Regulatory breach indicators")

    model_config = {"extra": "ignore"}
