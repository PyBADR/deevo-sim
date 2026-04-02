"""
Impact Observatory | مرصد الأثر — FintechStress (v4 §3.8)
Per-entity fintech operational and settlement stress.
"""

from pydantic import BaseModel, Field


class FintechBreachFlags(BaseModel):
    """v4 breach flags for fintech operational thresholds."""
    availability_breach: bool = Field(..., description="Service availability below minimum")
    settlement_breach: bool = Field(..., description="Settlement delay exceeds maximum")
    operational_risk_breach: bool = Field(..., description="Operational risk score exceeds threshold")

    model_config = {"extra": "ignore"}


class FintechStress(BaseModel):
    """v4 canonical fintech stress — per-entity operational metrics."""

    entity_id: str = Field(..., description="UUIDv7 entity reference (entity_type=fintech)")
    timestamp: str = Field(..., description="ISO-8601 UTC timestamp")
    transaction_failure_rate: float = Field(..., ge=0.0, le=1.0, description="Fraction of failing transactions")
    fraud_loss: float = Field(..., ge=0.0, description="Fraud loss in base currency")
    service_availability: float = Field(..., ge=0.0, le=1.0, description="Service uptime ratio")
    settlement_delay_minutes: int = Field(..., ge=0, description="Settlement delay in minutes")
    client_churn_rate: float = Field(..., ge=0.0, le=1.0, description="Client churn rate")
    operational_risk_score: float = Field(..., ge=0.0, le=1.0, description="Composite operational risk")
    breach_flags: FintechBreachFlags = Field(..., description="Operational breach indicators")

    model_config = {"extra": "ignore"}
