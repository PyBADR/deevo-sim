"""P1 Data Foundation — Entity Registry.

Canonical registry of every tracked entity: banks, insurers, sovereign funds,
logistics nodes, regulators, and corporations across the GCC.
"""

from __future__ import annotations

from pydantic import Field

from p1_foundation.models.base import GeoMixin, P1BaseModel, SectorMixin
from p1_foundation.models.enums import SourceType


class EntityRegistryEntry(P1BaseModel, GeoMixin, SectorMixin):
    """A tracked entity in the observatory."""

    entity_id: str = Field(..., description="Unique entity code (e.g., 'NBK', 'ADNOC')")
    display_name: str = Field(..., description="Full official name")
    display_name_ar: str | None = Field(default=None, description="Arabic name")
    entity_type: str = Field(..., description="Entity classification (bank, insurer, port, etc.)")
    parent_entity_id: str | None = Field(default=None, description="FK to parent entity")
    market_cap_usd: float | None = Field(default=None, ge=0, description="Market cap in USD")
    employee_count: int | None = Field(default=None, ge=0, description="Number of employees")
    swift_code: str | None = Field(default=None, description="SWIFT/BIC code for financial entities")
    is_active: bool = Field(default=True, description="Whether entity is currently tracked")
    tags: list[str] = Field(default_factory=list, description="Searchable tags")
