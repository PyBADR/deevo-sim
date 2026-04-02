"""
Impact Observatory | مرصد الأثر — Base Model
Versioned Pydantic v2 base for all domain objects.
"""

from pydantic import BaseModel, Field


class VersionedModel(BaseModel):
    """Base model with frozen schema version for audit traceability."""
    schema_version: str = Field(default="4.0.0", frozen=True)
    model_config = {"extra": "ignore", "populate_by_name": True}
