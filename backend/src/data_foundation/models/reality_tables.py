"""Data Reality Foundation — SQLAlchemy ORM table definitions.

Six new tables that track *where data actually comes from* and *how it gets
normalized into canonical form*.  These sit between raw external sources and
the existing df_* indicator/signal tables.

Tables:
  df_source_truth_registry   — master list of every real-world data source
  df_raw_source_records      — immutable raw payloads fetched from sources
  df_indicator_catalog       — canonical indicator definitions (the "what")
  df_canonical_observations  — normalized indicator values (the "measured")
  df_source_fetch_runs       — fetch execution log (the "when + status")
  df_normalization_runs      — normalization execution log (raw → canonical)

Design:
  - Same _FoundationMixin as existing tables (schema_version, tenant_id, timestamps, provenance_hash)
  - source_url, fetch_timestamp, content_hash, period coverage mandatory where applicable
  - JSONB for semi-structured payloads and metadata
  - VARCHAR enums (no Postgres native ENUMs)
  - String PKs (UUID-based, 128-char max)
"""

from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    Float,
    Index,
    Integer,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from src.db.postgres import Base


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class _FoundationMixin:
    """Columns present on every data_foundation table."""
    schema_version: Mapped[str] = mapped_column(String(16), default="1.0.0", nullable=False)
    tenant_id: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow, onupdate=_utcnow, nullable=False)
    provenance_hash: Mapped[str | None] = mapped_column(String(128), nullable=True)


# ═══════════════════════════════════════════════════════════════════════════════
# Table: df_source_truth_registry
# The master list of every real-world data source the observatory consumes.
# ═══════════════════════════════════════════════════════════════════════════════

class SourceTruthRegistryORM(_FoundationMixin, Base):
    __tablename__ = "df_source_truth_registry"

    source_id: Mapped[str] = mapped_column(String(128), primary_key=True)
    source_name: Mapped[str] = mapped_column(String(256), nullable=False)
    source_name_ar: Mapped[str | None] = mapped_column(String(256), nullable=True)
    source_type: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    # e.g. API, CSV_UPLOAD, SCRAPER, GOVERNMENT, RSS, FEED, MANUAL
    provider_org: Mapped[str] = mapped_column(String(256), nullable=False)
    provider_country: Mapped[str | None] = mapped_column(String(4), nullable=True, index=True)

    # Connectivity
    base_url: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    api_docs_url: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    auth_method: Mapped[str | None] = mapped_column(String(64), nullable=True)
    # e.g. API_KEY, OAUTH2, BASIC, NONE

    # Reliability & coverage
    reliability: Mapped[str] = mapped_column(String(32), default="HIGH", nullable=False)
    # AUTHORITATIVE, HIGH, MODERATE, LOW, EXPERIMENTAL
    coverage_countries: Mapped[dict | None] = mapped_column(JSONB, nullable=True)  # List[str]
    coverage_sectors: Mapped[dict | None] = mapped_column(JSONB, nullable=True)  # List[str]
    update_frequency: Mapped[str] = mapped_column(String(32), nullable=False)
    # REAL_TIME, DAILY, WEEKLY, MONTHLY, QUARTERLY, ON_DEMAND, STATIC
    expected_lag_hours: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # Operational
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    requires_license: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    license_expiry: Mapped[datetime | None] = mapped_column(Date, nullable=True)
    last_successful_fetch: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    consecutive_failures: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    # Datasets fed
    feeds_datasets: Mapped[dict | None] = mapped_column(JSONB, nullable=True)  # List[str]
    feeds_indicators: Mapped[dict | None] = mapped_column(JSONB, nullable=True)  # List[str]

    # Metadata
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    tags: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    metadata_json: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    __table_args__ = (
        Index("ix_df_str_type_reliability", "source_type", "reliability"),
        Index("ix_df_str_active_freq", "is_active", "update_frequency"),
    )


# ═══════════════════════════════════════════════════════════════════════════════
# Table: df_raw_source_records
# Immutable raw payloads fetched from sources, before any normalization.
# ═══════════════════════════════════════════════════════════════════════════════

class RawSourceRecordORM(_FoundationMixin, Base):
    __tablename__ = "df_raw_source_records"

    record_id: Mapped[str] = mapped_column(String(128), primary_key=True)
    source_id: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    fetch_run_id: Mapped[str] = mapped_column(String(128), nullable=False, index=True)

    # Source provenance (mandatory)
    source_url: Mapped[str] = mapped_column(String(1024), nullable=False)
    fetch_timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    content_hash: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    # SHA-256 of the raw payload — dedup key

    # Period coverage (mandatory)
    period_start: Mapped[datetime] = mapped_column(Date, nullable=False)
    period_end: Mapped[datetime] = mapped_column(Date, nullable=False)

    # Raw payload
    raw_payload: Mapped[dict] = mapped_column(JSONB, nullable=False)
    content_type: Mapped[str] = mapped_column(String(64), default="application/json", nullable=False)
    payload_size_bytes: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # Lineage
    is_duplicate: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    duplicate_of_record_id: Mapped[str | None] = mapped_column(String(128), nullable=True)
    normalization_status: Mapped[str] = mapped_column(String(32), default="PENDING", nullable=False)
    # PENDING, IN_PROGRESS, COMPLETED, FAILED, SKIPPED

    __table_args__ = (
        Index("ix_df_raw_source_fetch", "source_id", "fetch_timestamp"),
        Index("ix_df_raw_content_hash", "content_hash"),
        Index("ix_df_raw_norm_status", "normalization_status"),
    )


# ═══════════════════════════════════════════════════════════════════════════════
# Table: df_indicator_catalog
# Canonical indicator definitions — what we measure and how.
# ═══════════════════════════════════════════════════════════════════════════════

class IndicatorCatalogORM(_FoundationMixin, Base):
    __tablename__ = "df_indicator_catalog"

    indicator_id: Mapped[str] = mapped_column(String(128), primary_key=True)
    indicator_code: Mapped[str] = mapped_column(String(64), nullable=False, unique=True, index=True)
    indicator_name: Mapped[str] = mapped_column(String(256), nullable=False)
    indicator_name_ar: Mapped[str | None] = mapped_column(String(256), nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Classification
    category: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    # MACRO, INTEREST_RATE, FX, OIL_ENERGY, BANKING, INSURANCE, LOGISTICS, CBK, COMPOSITE
    subcategory: Mapped[str | None] = mapped_column(String(64), nullable=True)
    sector: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    country_scope: Mapped[str | None] = mapped_column(String(4), nullable=True)
    # NULL = all GCC, or specific country code

    # Measurement
    unit: Mapped[str] = mapped_column(String(64), nullable=False)
    # e.g. "percent", "USD_bn", "bps", "USD_per_bbl", "index", "KWD_mn"
    value_type: Mapped[str] = mapped_column(String(32), default="NUMERIC", nullable=False)
    # NUMERIC, RATE, INDEX, RATIO, COUNT
    precision_digits: Mapped[int] = mapped_column(Integer, default=2, nullable=False)
    frequency: Mapped[str] = mapped_column(String(32), nullable=False)
    # DAILY, WEEKLY, MONTHLY, QUARTERLY, ANNUAL

    # Thresholds
    normal_range_min: Mapped[float | None] = mapped_column(Float, nullable=True)
    normal_range_max: Mapped[float | None] = mapped_column(Float, nullable=True)
    alert_threshold_low: Mapped[float | None] = mapped_column(Float, nullable=True)
    alert_threshold_high: Mapped[float | None] = mapped_column(Float, nullable=True)

    # Sources
    primary_source_id: Mapped[str | None] = mapped_column(String(128), nullable=True)
    secondary_source_ids: Mapped[dict | None] = mapped_column(JSONB, nullable=True)  # List[str]

    # Operational
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_composite: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    composite_formula: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Metadata
    tags: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    metadata_json: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    __table_args__ = (
        Index("ix_df_ic_category_sector", "category", "sector"),
        Index("ix_df_ic_active_freq", "is_active", "frequency"),
    )


# ═══════════════════════════════════════════════════════════════════════════════
# Table: df_canonical_observations
# Normalized indicator values — the measured data in canonical form.
# ═══════════════════════════════════════════════════════════════════════════════

class CanonicalObservationORM(_FoundationMixin, Base):
    __tablename__ = "df_canonical_observations"

    observation_id: Mapped[str] = mapped_column(String(128), primary_key=True)
    indicator_id: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    indicator_code: Mapped[str] = mapped_column(String(64), nullable=False, index=True)

    # Value
    value: Mapped[float] = mapped_column(Float, nullable=False)
    unit: Mapped[str] = mapped_column(String(64), nullable=False)
    country: Mapped[str] = mapped_column(String(4), nullable=False, index=True)
    entity_id: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)

    # Period coverage (mandatory)
    period_start: Mapped[datetime] = mapped_column(Date, nullable=False, index=True)
    period_end: Mapped[datetime] = mapped_column(Date, nullable=False)
    frequency: Mapped[str] = mapped_column(String(32), nullable=False)
    observation_date: Mapped[datetime] = mapped_column(Date, nullable=False)

    # Provenance (mandatory)
    source_id: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    source_url: Mapped[str] = mapped_column(String(1024), nullable=False)
    fetch_timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    content_hash: Mapped[str] = mapped_column(String(128), nullable=False)
    raw_record_id: Mapped[str | None] = mapped_column(String(128), nullable=True)
    normalization_run_id: Mapped[str | None] = mapped_column(String(128), nullable=True)

    # Quality
    confidence_score: Mapped[float] = mapped_column(Float, default=0.8, nullable=False)
    confidence_method: Mapped[str] = mapped_column(String(64), default="SOURCE_DECLARED", nullable=False)
    is_provisional: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    revision_number: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    # Delta
    previous_value: Mapped[float | None] = mapped_column(Float, nullable=True)
    change_absolute: Mapped[float | None] = mapped_column(Float, nullable=True)
    change_pct: Mapped[float | None] = mapped_column(Float, nullable=True)

    __table_args__ = (
        Index("ix_df_co_indicator_period", "indicator_code", "period_start", "country"),
        Index("ix_df_co_source_fetch", "source_id", "fetch_timestamp"),
        Index("ix_df_co_country_date", "country", "observation_date"),
    )


# ═══════════════════════════════════════════════════════════════════════════════
# Table: df_source_fetch_runs
# Execution log for data fetches — when, from where, what happened.
# ═══════════════════════════════════════════════════════════════════════════════

class SourceFetchRunORM(_FoundationMixin, Base):
    __tablename__ = "df_source_fetch_runs"

    run_id: Mapped[str] = mapped_column(String(128), primary_key=True)
    source_id: Mapped[str] = mapped_column(String(128), nullable=False, index=True)

    # Execution (mandatory provenance)
    source_url: Mapped[str] = mapped_column(String(1024), nullable=False)
    fetch_timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    content_hash: Mapped[str | None] = mapped_column(String(128), nullable=True)

    # Period coverage (mandatory)
    period_start: Mapped[datetime] = mapped_column(Date, nullable=False)
    period_end: Mapped[datetime] = mapped_column(Date, nullable=False)

    # Status
    status: Mapped[str] = mapped_column(String(32), default="PENDING", nullable=False, index=True)
    # PENDING, RUNNING, COMPLETED, FAILED, PARTIAL
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    duration_seconds: Mapped[float | None] = mapped_column(Float, nullable=True)

    # Metrics
    records_fetched: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    records_new: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    records_duplicate: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    records_failed: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    payload_size_bytes: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # Error handling
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    error_code: Mapped[str | None] = mapped_column(String(64), nullable=True)
    retry_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    # Trigger
    trigger_type: Mapped[str] = mapped_column(String(32), default="SCHEDULED", nullable=False)
    # SCHEDULED, MANUAL, WEBHOOK, RETRY
    triggered_by: Mapped[str | None] = mapped_column(String(128), nullable=True)

    __table_args__ = (
        Index("ix_df_sfr_source_status", "source_id", "status"),
        Index("ix_df_sfr_fetch_ts", "fetch_timestamp"),
    )


# ═══════════════════════════════════════════════════════════════════════════════
# Table: df_normalization_runs
# Execution log for normalization — raw → canonical transformation.
# ═══════════════════════════════════════════════════════════════════════════════

class NormalizationRunORM(_FoundationMixin, Base):
    __tablename__ = "df_normalization_runs"

    run_id: Mapped[str] = mapped_column(String(128), primary_key=True)
    fetch_run_id: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    source_id: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    indicator_id: Mapped[str | None] = mapped_column(String(128), nullable=True, index=True)

    # Execution
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    duration_seconds: Mapped[float | None] = mapped_column(Float, nullable=True)

    # Status
    status: Mapped[str] = mapped_column(String(32), default="PENDING", nullable=False, index=True)
    # PENDING, RUNNING, COMPLETED, FAILED, PARTIAL

    # Metrics
    raw_records_input: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    observations_created: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    observations_updated: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    observations_skipped: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    validation_errors: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    # Normalization config
    normalization_version: Mapped[str] = mapped_column(String(16), default="1.0.0", nullable=False)
    field_mappings_used: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    quality_gates_applied: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    # Error handling
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    error_details: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    __table_args__ = (
        Index("ix_df_nr_fetch_run", "fetch_run_id"),
        Index("ix_df_nr_source_status", "source_id", "status"),
    )
