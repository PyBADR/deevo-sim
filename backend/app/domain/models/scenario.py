"""
Impact Observatory | مرصد الأثر — Scenario + RegulatoryProfile + ScenarioDna (v4 §3.1, §17.2, §18)
Immutable top-level execution definition containing all input conditions for a run.
"""

from pydantic import BaseModel, Field
from typing import List, Literal, Optional
from .entity import Entity
from .edge import Edge


class RegulatoryProfile(BaseModel):
    """v4 inline regulatory profile — jurisdiction-specific thresholds."""
    jurisdiction: str = Field(..., min_length=2, max_length=32)
    regulatory_version: str = Field(..., description="Semver format")
    lcr_min: float = Field(..., ge=0.0, le=10.0)
    nsfr_min: float = Field(..., ge=0.0, le=10.0)
    cet1_min: float = Field(..., ge=0.0, le=1.0)
    capital_adequacy_min: float = Field(..., ge=0.0, le=1.0)
    insurance_solvency_min: float = Field(..., ge=0.0, le=10.0)
    insurance_reserve_min: float = Field(..., ge=0.0, le=10.0)
    fintech_availability_min: float = Field(..., ge=0.0, le=1.0)
    settlement_delay_max_minutes: int = Field(..., ge=0, le=10080)

    model_config = {"extra": "ignore"}


class ScenarioTimeConfig(BaseModel):
    """v4 §17.2 — Temporal engine parameters."""
    time_granularity_minutes: int = Field(..., ge=1, le=1440)
    time_horizon_steps: int = Field(..., ge=1, le=1000)
    shock_decay_rate: float = Field(..., ge=0.0, le=1.0)
    propagation_delay_steps: int = Field(..., ge=0, le=100)
    recovery_rate: float = Field(..., ge=0.0, le=1.0)
    max_temporal_iterations_per_step: int = Field(..., ge=1, le=100)

    model_config = {"extra": "ignore"}


class TriggerEvent(BaseModel):
    """v4 §18.1.2 — Scenario trigger event."""
    event_type: Literal[
        "market_drop", "bank_run", "catastrophic_claims", "cyber_attack",
        "processor_outage", "regulatory_action", "compound_event"
    ] = Field(...)
    event_name: str = Field(..., min_length=1, max_length=160)
    event_time: str = Field(..., description="ISO-8601 UTC")
    origin_scope_level: Literal["entity", "sector", "system"] = Field(...)
    origin_scope_ref: str = Field(...)
    initial_shock_intensity: float = Field(..., ge=0.0, le=5.0)

    model_config = {"extra": "ignore"}


class SectorImpactLink(BaseModel):
    """v4 §18.1.3 — Ordered sector impact chain link."""
    step: int = Field(..., ge=1)
    source_sector: str = Field(...)
    target_sector: str = Field(...)
    impact_channel: Literal[
        "liquidity", "claims", "payment", "technology", "confidence", "fraud", "capital"
    ] = Field(...)
    transmission_strength: float = Field(..., ge=0.0, le=1.0)
    expected_lag_steps: int = Field(..., ge=0, le=100)

    model_config = {"extra": "ignore"}


class ScenarioDna(BaseModel):
    """v4 §18.1.1 — Business identity and causal chain of a scenario."""
    scenario_type: Literal[
        "liquidity_shock", "credit_shock", "claims_shock", "fraud_shock",
        "operational_outage", "payment_disruption", "compound_systemic_event"
    ] = Field(...)
    trigger_event: TriggerEvent = Field(...)
    sector_impact_chain: List[SectorImpactLink] = Field(..., min_length=1, max_length=20)
    primary_sector: Literal["bank", "insurer", "fintech", "cross_sector"] = Field(...)
    secondary_sectors: List[str] = Field(default_factory=list)
    transmission_mode: Literal["funding", "liquidity", "payment", "claims", "technology", "mixed"] = Field(...)
    severity_band: Literal["low", "medium", "high", "extreme"] = Field(...)

    model_config = {"extra": "ignore"}


class Scenario(BaseModel):
    """v4 canonical scenario — immutable top-level execution definition."""

    scenario_id: str = Field(default="", description="UUIDv7 (server-generated on create)")
    scenario_version: str = Field(default="1.0.0", description="Semver format")
    name: str = Field(..., min_length=1, max_length=120, description="Scenario name")
    description: str = Field(..., min_length=1, max_length=2000, description="Detailed description")
    as_of_date: str = Field(..., description="YYYY-MM-DD format")
    horizon_days: int = Field(..., ge=1, le=365, description="Simulation horizon in days")
    currency: str = Field(default="USD", pattern=r"^[A-Z]{3}$", description="ISO 4217 currency")
    shock_intensity: float = Field(..., ge=0.0, le=5.0, description="Scenario shock scalar")
    market_liquidity_haircut: float = Field(..., ge=0.0, le=1.0)
    deposit_run_rate: float = Field(..., ge=0.0, le=1.0)
    claims_spike_rate: float = Field(..., ge=0.0, le=1.0)
    fraud_loss_rate: float = Field(..., ge=0.0, le=1.0)
    regulatory_profile: RegulatoryProfile = Field(...)
    entities: List[Entity] = Field(..., min_length=1, max_length=10000)
    edges: List[Edge] = Field(default_factory=list, max_length=100000)

    # Server-managed fields
    created_by: str = Field(default="", description="Principal ID from auth")
    created_at: str = Field(default="", description="ISO-8601 UTC")
    status: Literal["draft", "active", "archived"] = Field(default="active")

    # Extension layers (optional on create)
    scenario_dna: Optional[ScenarioDna] = Field(default=None, description="v4 §18 Scenario DNA")
    time_config: Optional[ScenarioTimeConfig] = Field(default=None, description="v4 §17.2 Temporal config")

    model_config = {"extra": "ignore"}
