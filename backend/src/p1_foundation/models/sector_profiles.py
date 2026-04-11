"""P1 Data Foundation — Sector Profile Models.

Structured profiles for banking and insurance sector entities
with financial health metrics, stress indicators, and ratings.
"""

from __future__ import annotations

from pydantic import Field

from p1_foundation.models.base import ConfidenceMixin, GeoMixin, P1BaseModel, ProvenanceMixin, SectorMixin
from p1_foundation.models.enums import Sector


class BankingSectorProfile(P1BaseModel, GeoMixin, ConfidenceMixin, ProvenanceMixin):
    """Financial profile of a banking entity."""

    sector: str = Field(default=Sector.BANKING.value, description="Always 'banking'")
    entity_id: str = Field(..., description="FK to EntityRegistryEntry.id")
    entity_name: str = Field(..., description="Bank name")
    total_assets_usd_bn: float = Field(..., ge=0, description="Total assets (USD billion)")
    tier1_capital_ratio_pct: float = Field(..., ge=0, le=100, description="Tier 1 capital ratio %")
    npl_ratio_pct: float = Field(..., ge=0, le=100, description="Non-performing loan ratio %")
    roa_pct: float = Field(..., description="Return on assets %")
    roe_pct: float = Field(..., description="Return on equity %")
    liquidity_coverage_ratio_pct: float | None = Field(default=None, ge=0, description="LCR %")
    cost_to_income_ratio_pct: float | None = Field(default=None, ge=0, le=100, description="Cost/income ratio %")
    credit_rating: str | None = Field(default=None, description="External credit rating (e.g., 'A+')")
    rating_agency: str | None = Field(default=None, description="Rating agency")
    stress_score: float = Field(default=0.0, ge=0.0, le=1.0, description="Internal stress score [0,1]")
    period: str = Field(..., description="Reporting period (e.g., '2024-Q3')")
    dataset_id: str | None = Field(default=None, description="FK to DatasetRegistryEntry.id")


class InsuranceSectorProfile(P1BaseModel, GeoMixin, ConfidenceMixin, ProvenanceMixin):
    """Financial profile of an insurance entity."""

    sector: str = Field(default=Sector.INSURANCE.value, description="Always 'insurance'")
    entity_id: str = Field(..., description="FK to EntityRegistryEntry.id")
    entity_name: str = Field(..., description="Insurer name")
    gross_written_premium_usd_mn: float = Field(..., ge=0, description="GWP (USD million)")
    net_written_premium_usd_mn: float = Field(..., ge=0, description="NWP (USD million)")
    combined_ratio_pct: float = Field(..., ge=0, description="Combined ratio %")
    solvency_ratio_pct: float = Field(..., ge=0, description="Solvency ratio %")
    investment_yield_pct: float = Field(..., description="Investment portfolio yield %")
    claims_ratio_pct: float | None = Field(default=None, ge=0, le=100, description="Claims ratio %")
    retention_ratio_pct: float | None = Field(default=None, ge=0, le=100, description="Retention ratio %")
    credit_rating: str | None = Field(default=None, description="External credit rating")
    rating_agency: str | None = Field(default=None, description="Rating agency")
    stress_score: float = Field(default=0.0, ge=0.0, le=1.0, description="Internal stress score [0,1]")
    period: str = Field(..., description="Reporting period")
    dataset_id: str | None = Field(default=None, description="FK to DatasetRegistryEntry.id")
