"""
Impact Observatory | مرصد الأثر — RegulatoryState (v4 §3.11)
Run-level regulatory compliance status with aggregate ratios and breach classification.
"""

from pydantic import BaseModel, Field
from typing import List, Literal


class RegulatoryState(BaseModel):
    """v4 canonical regulatory state — run-level compliance snapshot."""

    run_id: str = Field(..., description="UUIDv7 run reference")
    timestamp: str = Field(..., description="ISO-8601 UTC timestamp")
    jurisdiction: str = Field(..., min_length=2, max_length=32, description="Regulatory jurisdiction")
    regulatory_version: str = Field(..., description="Semver regulatory ruleset version")
    aggregate_lcr: float = Field(..., ge=0.0, description="Exposure-weighted aggregate LCR")
    aggregate_nsfr: float = Field(..., ge=0.0, description="Exposure-weighted aggregate NSFR")
    aggregate_solvency_ratio: float = Field(..., ge=0.0, description="Aggregate solvency ratio")
    aggregate_capital_adequacy_ratio: float = Field(..., ge=0.0, description="Aggregate CAR")
    breach_level: Literal["none", "minor", "major", "critical"] = Field(
        ..., description="System-wide breach severity"
    )
    mandatory_actions: List[str] = Field(default_factory=list, description="Mandatory regulatory actions")
    reporting_required: bool = Field(..., description="Whether regulatory reporting is triggered")

    model_config = {"extra": "ignore"}
