"""
Impact Observatory | مرصد الأثر — BankingStress (v4 §3.6)
Per-entity banking liquidity and capital stress with regulatory breach flags.
"""

from pydantic import BaseModel, Field


class BankingBreachFlags(BaseModel):
    """v4 breach flags for banking regulatory thresholds."""
    lcr_breach: bool = Field(..., description="LCR below regulatory minimum")
    nsfr_breach: bool = Field(..., description="NSFR below regulatory minimum")
    cet1_breach: bool = Field(..., description="CET1 ratio below regulatory minimum")
    car_breach: bool = Field(..., description="Capital adequacy ratio below minimum")

    model_config = {"extra": "ignore"}


class BankingStress(BaseModel):
    """v4 canonical banking stress — per-entity liquidity and capital metrics."""

    entity_id: str = Field(..., description="UUIDv7 entity reference (entity_type=bank)")
    timestamp: str = Field(..., description="ISO-8601 UTC timestamp")
    deposit_outflow: float = Field(..., ge=0.0, description="Deposit outflow in base currency")
    wholesale_funding_outflow: float = Field(..., ge=0.0, description="Wholesale funding outflow")
    hqla: float = Field(..., ge=0.0, description="High-quality liquid assets")
    projected_cash_outflows_30d: float = Field(..., ge=0.0, description="Projected 30-day cash outflows")
    projected_cash_inflows_30d: float = Field(..., ge=0.0, description="Projected 30-day cash inflows")
    lcr: float = Field(..., ge=0.0, description="Liquidity Coverage Ratio = HQLA / net_cash_outflows_30d")
    nsfr: float = Field(..., ge=0.0, description="Net Stable Funding Ratio")
    cet1_ratio: float = Field(..., ge=0.0, description="Common Equity Tier 1 ratio")
    capital_adequacy_ratio: float = Field(..., ge=0.0, description="Capital adequacy ratio (Basel III)")
    breach_flags: BankingBreachFlags = Field(..., description="Regulatory breach indicators")

    model_config = {"extra": "ignore"}
