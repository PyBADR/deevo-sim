"""P1 Data Foundation — Source Registry.

Tracks every data source: API endpoints, CSV uploads, manual entry points,
and derived computation sources.
"""

from __future__ import annotations

from pydantic import Field

from p1_foundation.models.base import ConfidenceMixin, P1BaseModel
from p1_foundation.models.enums import FrequencyType, SourceType


class SourceRegistryEntry(P1BaseModel, ConfidenceMixin):
    """A registered data source feeding the observatory."""

    source_id: str = Field(..., description="Unique source identifier (e.g., 'cbk_api')")
    display_name: str = Field(..., description="Human-readable source name")
    description: str = Field(..., description="What this source provides")
    provider: str = Field(..., description="Organization providing the data")
    endpoint_url: str | None = Field(default=None, description="API endpoint or file path")
    update_frequency: FrequencyType = Field(..., description="How often source updates")
    datasets_fed: list[str] = Field(default_factory=list, description="Dataset IDs this source feeds")
    requires_auth: bool = Field(default=False, description="Whether auth is needed")
    is_active: bool = Field(default=True, description="Whether source is operational")
    last_successful_pull: str | None = Field(default=None, description="ISO timestamp of last successful ingestion")
