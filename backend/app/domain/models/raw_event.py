"""
Impact Observatory | مرصد الأثر — Raw Event Models

Data contracts for the Ingestion → Quality pipeline stages.
RawEvent → ValidatedEvent → NormalizedEvent → EnrichedEvent
"""

from datetime import datetime
from typing import Optional
from pydantic import Field
from .base import VersionedModel


class RawEvent(VersionedModel):
    """Stage 1 output: unvalidated event from any source."""
    source: str = Field(..., description="scenario_catalog | crucix | manual")
    source_id: str = Field(..., description="Original ID from source system")
    event_type: str = Field(..., description="geopolitical | economic | natural | cyber")
    payload: dict = Field(default_factory=dict, description="Raw unvalidated payload")
    received_at: datetime = Field(default_factory=datetime.utcnow)
    provenance: dict = Field(default_factory=dict, description="Source metadata")


class ValidatedEvent(VersionedModel):
    """Stage 2 output: business-rule validated event."""
    raw_event_id: str
    template_id: Optional[str] = None
    severity: float = Field(..., ge=0.0, le=1.0, description="Validated 0-1 severity")
    horizon_hours: int = Field(..., gt=0, le=8760, description="Time horizon in hours")
    sectors_affected: list[str] = Field(default_factory=list)
    validation_score: float = Field(default=1.0, ge=0.0, le=1.0)
    warnings: list[str] = Field(default_factory=list)


class NormalizedEvent(VersionedModel):
    """Stage 3-4 output: normalized + deduplicated event."""
    event_id: str
    canonical_type: str = Field(..., description="Normalized to taxonomy")
    severity: float = Field(..., ge=0.0, le=1.0)
    shock_vector: list[dict] = Field(default_factory=list, description="[{node_id, impact}]")
    geographic_scope: list[str] = Field(default_factory=list, description="GCC country codes")
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)
    provenance_chain: list[str] = Field(default_factory=list)


class EnrichedEvent(VersionedModel):
    """Stage 5 output: enriched with graph context."""
    event_id: str
    canonical_type: str
    severity: float = Field(..., ge=0.0, le=1.0)
    shock_vector: list[dict] = Field(default_factory=list)
    geographic_scope: list[str] = Field(default_factory=list)
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)
    provenance_chain: list[str] = Field(default_factory=list)
    graph_node_ids: list[str] = Field(default_factory=list, description="Matched node IDs from graph registry")
    regional_multipliers: dict[str, float] = Field(default_factory=dict)
    enrichment_completeness: float = Field(default=1.0, ge=0.0, le=1.0)
