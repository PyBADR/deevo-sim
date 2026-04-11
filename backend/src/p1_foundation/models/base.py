"""P1 Data Foundation — Base Model & Mixins.

All P1 models inherit from P1BaseModel. Reusable mixins provide
provenance tracking, geo tagging, confidence scoring, and sector tagging.
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field

from p1_foundation.models.enums import Confidence, Country, DataQuality, Sector, SourceType


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _new_id() -> str:
    return str(uuid4())


class P1BaseModel(BaseModel):
    """Base for every P1 data foundation model.

    Provides:
    - Unique ID
    - Created/updated timestamps (UTC)
    - Source provenance (name + type)
    - Schema version for forward compatibility
    """

    id: str = Field(default_factory=_new_id, description="Unique record identifier")
    created_at: datetime = Field(default_factory=_utc_now, description="Record creation timestamp (UTC)")
    updated_at: datetime = Field(default_factory=_utc_now, description="Last update timestamp (UTC)")
    source_name: str = Field(..., description="Originating data source name")
    source_type: SourceType = Field(..., description="How data was ingested")
    schema_version: str = Field(default="1.0", description="Schema version for migrations")

    model_config = ConfigDict(
        from_attributes=True,
        extra="ignore",
        populate_by_name=True,
        ser_json_timedelta="iso8601",
        json_schema_extra={"$schema": "p1_foundation/v1"},
    )

    def provenance_hash(self) -> str:
        """SHA-256 hash of the record's data fields (excludes timestamps)."""
        data = self.model_dump(exclude={"created_at", "updated_at"})
        raw = json.dumps(data, sort_keys=True, default=str)
        return hashlib.sha256(raw.encode()).hexdigest()

    def touch(self) -> None:
        """Update the updated_at timestamp."""
        self.updated_at = _utc_now()


class ProvenanceMixin(BaseModel):
    """Tracks data lineage: who provided it, when, and quality tier."""

    provenance_source_id: str | None = Field(default=None, description="FK to SourceRegistryEntry.id")
    provenance_hash: str | None = Field(default=None, description="SHA-256 of source payload at ingestion")
    data_quality: DataQuality = Field(default=DataQuality.BRONZE, description="Quality tier")
    ingested_at: datetime | None = Field(default=None, description="When the record was ingested")


class GeoMixin(BaseModel):
    """Geographic tagging for GCC entities."""

    country: Country = Field(..., description="GCC country code")
    city: str | None = Field(default=None, description="City name")
    lat: float | None = Field(default=None, ge=-90, le=90, description="Latitude")
    lng: float | None = Field(default=None, ge=-180, le=180, description="Longitude")


class ConfidenceMixin(BaseModel):
    """Confidence scoring for data records."""

    confidence: Confidence = Field(default=Confidence.MEDIUM, description="Data confidence level")
    confidence_score: float = Field(default=0.5, ge=0.0, le=1.0, description="Numeric confidence [0,1]")


class SectorMixin(BaseModel):
    """Sector classification."""

    sector: Sector = Field(..., description="Economic sector")
    sub_sector: str | None = Field(default=None, description="Sub-sector detail")
