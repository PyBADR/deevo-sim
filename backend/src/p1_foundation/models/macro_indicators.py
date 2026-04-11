"""P1 Data Foundation — Macroeconomic Indicators.

GDP, inflation, unemployment, trade balance, and other macro-level
indicators tracked across GCC member states.
"""

from __future__ import annotations

from pydantic import Field

from p1_foundation.models.base import ConfidenceMixin, GeoMixin, P1BaseModel, ProvenanceMixin
from p1_foundation.models.enums import FrequencyType, SignalDirection


class MacroIndicatorRecord(P1BaseModel, GeoMixin, ConfidenceMixin, ProvenanceMixin):
    """A single macroeconomic indicator observation."""

    indicator_name: str = Field(..., description="Indicator identifier (e.g., 'gdp_growth_pct')")
    display_name: str = Field(..., description="Human-readable indicator name")
    value: float = Field(..., description="Observed numeric value")
    unit: str = Field(..., description="Unit of measurement (%, USD bn, index)")
    period: str = Field(..., description="Time period (e.g., '2024-Q3', '2024-01')")
    frequency: FrequencyType = Field(..., description="Reporting frequency")
    direction: SignalDirection = Field(default=SignalDirection.STABLE, description="Trend direction")
    previous_value: float | None = Field(default=None, description="Prior period value")
    yoy_change_pct: float | None = Field(default=None, description="Year-over-year change %")
    entity_id: str | None = Field(default=None, description="FK to EntityRegistryEntry.id if entity-specific")
    dataset_id: str | None = Field(default=None, description="FK to DatasetRegistryEntry.id")
