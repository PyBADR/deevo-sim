"""Data Reality Foundation — Pydantic v2 request/response schemas.

Six schemas mapping 1:1 to the reality_tables ORM models.
Inherits from FoundationModel for provenance, tenant_id, timestamps.
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import Field

from src.data_foundation.schemas.base import FoundationModel


# ═══════════════════════════════════════════════════════════════════════════════
# Source Truth Registry
# ═══════════════════════════════════════════════════════════════════════════════

class SourceTruthRegistryEntry(FoundationModel):
    """A registered real-world data source."""

    source_id: str = Field(..., max_length=128, description="Unique source identifier")
    source_name: str = Field(..., max_length=256, description="Human-readable source name")
    source_name_ar: Optional[str] = Field(default=None, max_length=256)
    source_type: str = Field(..., max_length=64, description="API, CSV_UPLOAD, SCRAPER, GOVERNMENT, etc.")
    provider_org: str = Field(..., max_length=256, description="Organization providing data")
    provider_country: Optional[str] = Field(default=None, max_length=4)

    base_url: Optional[str] = Field(default=None, max_length=1024)
    api_docs_url: Optional[str] = Field(default=None, max_length=1024)
    auth_method: Optional[str] = Field(default=None, max_length=64)

    reliability: str = Field(default="HIGH", max_length=32)
    coverage_countries: Optional[list[str]] = Field(default=None)
    coverage_sectors: Optional[list[str]] = Field(default=None)
    update_frequency: str = Field(..., max_length=32)
    expected_lag_hours: Optional[int] = Field(default=None, ge=0)

    is_active: bool = Field(default=True)
    requires_license: bool = Field(default=False)
    license_expiry: Optional[str] = Field(default=None, description="ISO date")
    last_successful_fetch: Optional[datetime] = Field(default=None)
    consecutive_failures: int = Field(default=0, ge=0)

    feeds_datasets: Optional[list[str]] = Field(default=None)
    feeds_indicators: Optional[list[str]] = Field(default=None)

    description: Optional[str] = Field(default=None)
    tags: Optional[list[str]] = Field(default=None)
    metadata_json: Optional[dict] = Field(default=None)


# ═══════════════════════════════════════════════════════════════════════════════
# Raw Source Records
# ═══════════════════════════════════════════════════════════════════════════════

class RawSourceRecord(FoundationModel):
    """An immutable raw payload fetched from a source."""

    record_id: str = Field(..., max_length=128)
    source_id: str = Field(..., max_length=128)
    fetch_run_id: str = Field(..., max_length=128)

    source_url: str = Field(..., max_length=1024, description="URL from which data was fetched")
    fetch_timestamp: datetime = Field(..., description="When fetch occurred (UTC)")
    content_hash: str = Field(..., max_length=128, description="SHA-256 of raw payload")

    period_start: str = Field(..., description="Period coverage start (ISO date)")
    period_end: str = Field(..., description="Period coverage end (ISO date)")

    raw_payload: dict = Field(..., description="Immutable raw JSON payload")
    content_type: str = Field(default="application/json", max_length=64)
    payload_size_bytes: Optional[int] = Field(default=None, ge=0)

    is_duplicate: bool = Field(default=False)
    duplicate_of_record_id: Optional[str] = Field(default=None, max_length=128)
    normalization_status: str = Field(default="PENDING", max_length=32)


# ═══════════════════════════════════════════════════════════════════════════════
# Indicator Catalog
# ═══════════════════════════════════════════════════════════════════════════════

class IndicatorCatalogEntry(FoundationModel):
    """A canonical indicator definition — what we measure and how."""

    indicator_id: str = Field(..., max_length=128)
    indicator_code: str = Field(..., max_length=64, description="Unique code (e.g., 'GDP_GROWTH_KW')")
    indicator_name: str = Field(..., max_length=256)
    indicator_name_ar: Optional[str] = Field(default=None, max_length=256)
    description: Optional[str] = Field(default=None)

    category: str = Field(..., max_length=64, description="MACRO, INTEREST_RATE, FX, OIL_ENERGY, etc.")
    subcategory: Optional[str] = Field(default=None, max_length=64)
    sector: Optional[str] = Field(default=None, max_length=64)
    country_scope: Optional[str] = Field(default=None, max_length=4)

    unit: str = Field(..., max_length=64, description="percent, USD_bn, bps, etc.")
    value_type: str = Field(default="NUMERIC", max_length=32)
    precision_digits: int = Field(default=2, ge=0)
    frequency: str = Field(..., max_length=32)

    normal_range_min: Optional[float] = Field(default=None)
    normal_range_max: Optional[float] = Field(default=None)
    alert_threshold_low: Optional[float] = Field(default=None)
    alert_threshold_high: Optional[float] = Field(default=None)

    primary_source_id: Optional[str] = Field(default=None, max_length=128)
    secondary_source_ids: Optional[list[str]] = Field(default=None)

    is_active: bool = Field(default=True)
    is_composite: bool = Field(default=False)
    composite_formula: Optional[str] = Field(default=None)

    tags: Optional[list[str]] = Field(default=None)
    metadata_json: Optional[dict] = Field(default=None)


# ═══════════════════════════════════════════════════════════════════════════════
# Canonical Observations
# ═══════════════════════════════════════════════════════════════════════════════

class CanonicalObservation(FoundationModel):
    """A normalized indicator observation in canonical form."""

    observation_id: str = Field(..., max_length=128)
    indicator_id: str = Field(..., max_length=128)
    indicator_code: str = Field(..., max_length=64)

    value: float = Field(...)
    unit: str = Field(..., max_length=64)
    country: str = Field(..., max_length=4)
    entity_id: Optional[str] = Field(default=None, max_length=64)

    period_start: str = Field(..., description="ISO date")
    period_end: str = Field(..., description="ISO date")
    frequency: str = Field(..., max_length=32)
    observation_date: str = Field(..., description="ISO date")

    source_id: str = Field(..., max_length=128)
    source_url: str = Field(..., max_length=1024)
    fetch_timestamp: datetime = Field(...)
    content_hash: str = Field(..., max_length=128)
    raw_record_id: Optional[str] = Field(default=None, max_length=128)
    normalization_run_id: Optional[str] = Field(default=None, max_length=128)

    confidence_score: float = Field(default=0.8, ge=0.0, le=1.0)
    confidence_method: str = Field(default="SOURCE_DECLARED", max_length=64)
    is_provisional: bool = Field(default=False)
    revision_number: int = Field(default=0, ge=0)

    previous_value: Optional[float] = Field(default=None)
    change_absolute: Optional[float] = Field(default=None)
    change_pct: Optional[float] = Field(default=None)


# ═══════════════════════════════════════════════════════════════════════════════
# Source Fetch Runs
# ═══════════════════════════════════════════════════════════════════════════════

class SourceFetchRun(FoundationModel):
    """A fetch execution run log."""

    run_id: str = Field(..., max_length=128)
    source_id: str = Field(..., max_length=128)

    source_url: str = Field(..., max_length=1024)
    fetch_timestamp: datetime = Field(...)
    content_hash: Optional[str] = Field(default=None, max_length=128)

    period_start: str = Field(..., description="ISO date")
    period_end: str = Field(..., description="ISO date")

    status: str = Field(default="PENDING", max_length=32)
    started_at: Optional[datetime] = Field(default=None)
    completed_at: Optional[datetime] = Field(default=None)
    duration_seconds: Optional[float] = Field(default=None, ge=0)

    records_fetched: int = Field(default=0, ge=0)
    records_new: int = Field(default=0, ge=0)
    records_duplicate: int = Field(default=0, ge=0)
    records_failed: int = Field(default=0, ge=0)
    payload_size_bytes: Optional[int] = Field(default=None, ge=0)

    error_message: Optional[str] = Field(default=None)
    error_code: Optional[str] = Field(default=None, max_length=64)
    retry_count: int = Field(default=0, ge=0)

    trigger_type: str = Field(default="SCHEDULED", max_length=32)
    triggered_by: Optional[str] = Field(default=None, max_length=128)


# ═══════════════════════════════════════════════════════════════════════════════
# Normalization Runs
# ═══════════════════════════════════════════════════════════════════════════════

class NormalizationRun(FoundationModel):
    """A normalization execution run log (raw → canonical)."""

    run_id: str = Field(..., max_length=128)
    fetch_run_id: str = Field(..., max_length=128)
    source_id: str = Field(..., max_length=128)
    indicator_id: Optional[str] = Field(default=None, max_length=128)

    started_at: Optional[datetime] = Field(default=None)
    completed_at: Optional[datetime] = Field(default=None)
    duration_seconds: Optional[float] = Field(default=None, ge=0)

    status: str = Field(default="PENDING", max_length=32)

    raw_records_input: int = Field(default=0, ge=0)
    observations_created: int = Field(default=0, ge=0)
    observations_updated: int = Field(default=0, ge=0)
    observations_skipped: int = Field(default=0, ge=0)
    validation_errors: int = Field(default=0, ge=0)

    normalization_version: str = Field(default="1.0.0", max_length=16)
    field_mappings_used: Optional[dict] = Field(default=None)
    quality_gates_applied: Optional[dict] = Field(default=None)

    error_message: Optional[str] = Field(default=None)
    error_details: Optional[dict] = Field(default=None)
