"""P1 Data Foundation — Event Signals.

Geopolitical, economic, and infrastructure events that
drive scenario activation in the simulation engine.
"""

from __future__ import annotations

from pydantic import Field

from p1_foundation.models.base import ConfidenceMixin, GeoMixin, P1BaseModel, ProvenanceMixin
from p1_foundation.models.enums import Severity


class EventSignalRecord(P1BaseModel, GeoMixin, ConfidenceMixin, ProvenanceMixin):
    """A detected or reported event signal."""

    event_type: str = Field(..., description="Event category (geopolitical, economic, infrastructure, regulatory)")
    headline: str = Field(..., description="Short event headline")
    description: str = Field(..., description="Detailed event description")
    severity: Severity = Field(..., description="Impact severity")
    affected_sectors: list[str] = Field(default_factory=list, description="Sectors impacted")
    affected_entities: list[str] = Field(default_factory=list, description="Entity IDs impacted")
    event_date: str = Field(..., description="When event occurred (ISO date)")
    expiry_date: str | None = Field(default=None, description="When event impact expires (ISO date)")
    scenario_ids: list[str] = Field(default_factory=list, description="Linked simulation scenario IDs")
    is_active: bool = Field(default=True, description="Whether event is still in effect")
    dataset_id: str | None = Field(default=None, description="FK to DatasetRegistryEntry.id")
