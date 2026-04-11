"""P1 Data Foundation — Signal Models.

Domain-specific signal records: interest rates, oil/energy prices,
FX rates, and Kuwait CBK indicators.
"""

from __future__ import annotations

from pydantic import Field

from p1_foundation.models.base import ConfidenceMixin, GeoMixin, P1BaseModel, ProvenanceMixin
from p1_foundation.models.enums import Currency, SignalDirection


class InterestRateSignalRecord(P1BaseModel, GeoMixin, ConfidenceMixin, ProvenanceMixin):
    """Central bank interest rate observation."""

    rate_name: str = Field(..., description="Rate identifier (e.g., 'cbk_discount_rate')")
    display_name: str = Field(..., description="Human-readable rate name")
    rate_value_pct: float = Field(..., description="Rate as percentage (e.g., 4.25)")
    previous_rate_pct: float | None = Field(default=None, description="Prior rate value")
    change_bps: int | None = Field(default=None, description="Change in basis points")
    direction: SignalDirection = Field(default=SignalDirection.STABLE)
    effective_date: str = Field(..., description="When rate takes effect (ISO date)")
    central_bank: str = Field(..., description="Issuing central bank")
    currency: Currency = Field(..., description="Currency this rate governs")
    entity_id: str | None = Field(default=None, description="FK to EntityRegistryEntry.id")
    dataset_id: str | None = Field(default=None, description="FK to DatasetRegistryEntry.id")


class OilEnergySignalRecord(P1BaseModel, ConfidenceMixin, ProvenanceMixin):
    """Oil and energy price/production signal."""

    signal_name: str = Field(..., description="Signal identifier (e.g., 'brent_crude_spot')")
    display_name: str = Field(..., description="Human-readable signal name")
    price_usd: float | None = Field(default=None, ge=0, description="Price in USD per unit")
    volume_mbpd: float | None = Field(default=None, ge=0, description="Volume in million barrels/day")
    unit: str = Field(default="USD/bbl", description="Unit of measurement")
    direction: SignalDirection = Field(default=SignalDirection.STABLE)
    change_pct: float | None = Field(default=None, description="Period-over-period change %")
    observation_date: str = Field(..., description="Observation date (ISO)")
    benchmark: str = Field(default="Brent", description="Price benchmark (Brent, WTI, OPEC Basket)")
    dataset_id: str | None = Field(default=None, description="FK to DatasetRegistryEntry.id")


class FXSignalRecord(P1BaseModel, ConfidenceMixin, ProvenanceMixin):
    """Foreign exchange rate signal."""

    pair: str = Field(..., description="Currency pair (e.g., 'KWD/USD')")
    base_currency: Currency = Field(..., description="Base currency")
    quote_currency: Currency = Field(..., description="Quote currency")
    rate: float = Field(..., gt=0, description="Exchange rate")
    bid: float | None = Field(default=None, gt=0, description="Bid price")
    ask: float | None = Field(default=None, gt=0, description="Ask price")
    spread_bps: float | None = Field(default=None, ge=0, description="Spread in basis points")
    direction: SignalDirection = Field(default=SignalDirection.STABLE)
    change_pct: float | None = Field(default=None, description="Daily change %")
    observation_date: str = Field(..., description="Observation date (ISO)")
    is_peg: bool = Field(default=False, description="Whether this is a pegged rate")
    dataset_id: str | None = Field(default=None, description="FK to DatasetRegistryEntry.id")


class KuwaitCBKIndicatorRecord(P1BaseModel, ConfidenceMixin, ProvenanceMixin):
    """Kuwait Central Bank specific indicator (CBK bulletin data)."""

    indicator_code: str = Field(..., description="CBK indicator code")
    indicator_name: str = Field(..., description="Indicator name")
    value: float = Field(..., description="Observed value")
    unit: str = Field(..., description="Unit of measurement")
    period: str = Field(..., description="Reporting period (e.g., '2024-Q3')")
    category: str = Field(..., description="CBK category (monetary, banking, external)")
    direction: SignalDirection = Field(default=SignalDirection.STABLE)
    previous_value: float | None = Field(default=None, description="Prior period value")
    country: str = Field(default="KW", description="Always Kuwait")
    entity_id: str | None = Field(default=None, description="FK to CBK entity in registry")
    dataset_id: str | None = Field(default=None, description="FK to DatasetRegistryEntry.id")
