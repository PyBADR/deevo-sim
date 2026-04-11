"""P1 Data Foundation — Dataset Registry.

Tracks every dataset in the system: what it contains, where it comes from,
how often it updates, and who owns it.
"""

from __future__ import annotations

from pydantic import Field

from p1_foundation.models.base import P1BaseModel
from p1_foundation.models.enums import DataQuality, FrequencyType, SourceType


class DatasetRegistryEntry(P1BaseModel):
    """A registered dataset in the observatory."""

    dataset_name: str = Field(..., description="Unique dataset identifier (snake_case)")
    display_name: str = Field(..., description="Human-readable name")
    description: str = Field(..., description="What this dataset contains")
    owner: str = Field(..., description="Team or person responsible")
    update_frequency: FrequencyType = Field(..., description="How often data refreshes")
    record_count: int = Field(default=0, ge=0, description="Current number of records")
    quality_tier: DataQuality = Field(default=DataQuality.BRONZE, description="Current quality tier")
    schema_ref: str = Field(..., description="Python import path to the Pydantic model")
    tags: list[str] = Field(default_factory=list, description="Searchable tags")
    is_active: bool = Field(default=True, description="Whether dataset is actively maintained")
