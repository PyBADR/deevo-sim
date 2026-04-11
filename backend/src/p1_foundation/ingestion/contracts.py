"""P1 Data Foundation — Ingestion Contracts.

Declarative contracts that define how raw data maps into P1 models:
field mappings, quality gates, and transformation rules.
"""

from __future__ import annotations

from pydantic import BaseModel, Field

from p1_foundation.models.enums import DataQuality, FrequencyType, SourceType


class FieldMapping(BaseModel):
    """Maps a source field to a target model field."""

    source_field: str = Field(..., description="Field name in raw source data")
    target_field: str = Field(..., description="Field name in P1 model")
    transform: str | None = Field(default=None, description="Transform function name (e.g., 'to_float', 'strip')")
    default: str | float | int | bool | None = Field(default=None, description="Default if source field is missing")
    required: bool = Field(default=True, description="Whether source field must be present")


class QualityGate(BaseModel):
    """A validation rule applied during ingestion."""

    field: str = Field(..., description="Target field to validate")
    check: str = Field(..., description="Check type: not_null, range, regex, in_set, unique")
    params: dict = Field(default_factory=dict, description="Check parameters (e.g., {'min': 0, 'max': 100})")
    severity: str = Field(default="error", description="'error' = reject record, 'warning' = flag but accept")


class IngestionContract(BaseModel):
    """Defines how a data source maps into a P1 model."""

    contract_id: str = Field(..., description="Unique contract identifier")
    source_id: str = Field(..., description="FK to SourceRegistryEntry.source_id")
    target_model: str = Field(..., description="Python import path to target Pydantic model")
    target_dataset: str = Field(..., description="FK to DatasetRegistryEntry.dataset_name")
    source_type: SourceType = Field(..., description="Ingestion method")
    update_frequency: FrequencyType = Field(..., description="Expected update cadence")
    field_mappings: list[FieldMapping] = Field(default_factory=list, description="Source→target field maps")
    quality_gates: list[QualityGate] = Field(default_factory=list, description="Validation rules")
    output_quality: DataQuality = Field(default=DataQuality.BRONZE, description="Quality tier of output")
    description: str = Field(default="", description="Contract description")
    is_active: bool = Field(default=True, description="Whether contract is enabled")
