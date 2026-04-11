"""Data Reality Foundation — 6 new tables.

source_truth_registry, raw_source_records, indicator_catalog,
canonical_observations, source_fetch_runs, normalization_runs.

Revision ID: 002_data_reality
Revises: 001_p2_foundation
Create Date: 2026-04-11
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "002_data_reality"
down_revision: Union[str, None] = "001_p2_foundation"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _foundation_cols():
    """Columns shared by every df_ table (mirrors FoundationModel)."""
    return [
        sa.Column("schema_version", sa.String(16), nullable=False, server_default="1.0.0"),
        sa.Column("tenant_id", sa.String(64), nullable=True, index=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("provenance_hash", sa.String(128), nullable=True),
    ]


def upgrade() -> None:
    # ── df_source_truth_registry ─────────────────────────────────────────
    op.create_table(
        "df_source_truth_registry",
        sa.Column("source_id", sa.String(128), primary_key=True),
        sa.Column("source_name", sa.String(256), nullable=False),
        sa.Column("source_name_ar", sa.String(256), nullable=True),
        sa.Column("source_type", sa.String(64), nullable=False, index=True),
        sa.Column("provider_org", sa.String(256), nullable=False),
        sa.Column("provider_country", sa.String(4), nullable=True, index=True),
        sa.Column("base_url", sa.String(1024), nullable=True),
        sa.Column("api_docs_url", sa.String(1024), nullable=True),
        sa.Column("auth_method", sa.String(64), nullable=True),
        sa.Column("reliability", sa.String(32), nullable=False, server_default="HIGH"),
        sa.Column("coverage_countries", postgresql.JSONB(), nullable=True),
        sa.Column("coverage_sectors", postgresql.JSONB(), nullable=True),
        sa.Column("update_frequency", sa.String(32), nullable=False),
        sa.Column("expected_lag_hours", sa.Integer(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("requires_license", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("license_expiry", sa.Date(), nullable=True),
        sa.Column("last_successful_fetch", sa.DateTime(timezone=True), nullable=True),
        sa.Column("consecutive_failures", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("feeds_datasets", postgresql.JSONB(), nullable=True),
        sa.Column("feeds_indicators", postgresql.JSONB(), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("tags", postgresql.JSONB(), nullable=True),
        sa.Column("metadata_json", postgresql.JSONB(), nullable=True),
        *_foundation_cols(),
    )
    op.create_index("ix_df_str_type_reliability", "df_source_truth_registry", ["source_type", "reliability"])
    op.create_index("ix_df_str_active_freq", "df_source_truth_registry", ["is_active", "update_frequency"])

    # ── df_raw_source_records ────────────────────────────────────────────
    op.create_table(
        "df_raw_source_records",
        sa.Column("record_id", sa.String(128), primary_key=True),
        sa.Column("source_id", sa.String(128), nullable=False, index=True),
        sa.Column("fetch_run_id", sa.String(128), nullable=False, index=True),
        sa.Column("source_url", sa.String(1024), nullable=False),
        sa.Column("fetch_timestamp", sa.DateTime(timezone=True), nullable=False, index=True),
        sa.Column("content_hash", sa.String(128), nullable=False, index=True),
        sa.Column("period_start", sa.Date(), nullable=False),
        sa.Column("period_end", sa.Date(), nullable=False),
        sa.Column("raw_payload", postgresql.JSONB(), nullable=False),
        sa.Column("content_type", sa.String(64), nullable=False, server_default="application/json"),
        sa.Column("payload_size_bytes", sa.Integer(), nullable=True),
        sa.Column("is_duplicate", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("duplicate_of_record_id", sa.String(128), nullable=True),
        sa.Column("normalization_status", sa.String(32), nullable=False, server_default="PENDING"),
        *_foundation_cols(),
    )
    op.create_index("ix_df_raw_source_fetch", "df_raw_source_records", ["source_id", "fetch_timestamp"])
    op.create_index("ix_df_raw_content_hash", "df_raw_source_records", ["content_hash"])
    op.create_index("ix_df_raw_norm_status", "df_raw_source_records", ["normalization_status"])

    # ── df_indicator_catalog ─────────────────────────────────────────────
    op.create_table(
        "df_indicator_catalog",
        sa.Column("indicator_id", sa.String(128), primary_key=True),
        sa.Column("indicator_code", sa.String(64), nullable=False, unique=True, index=True),
        sa.Column("indicator_name", sa.String(256), nullable=False),
        sa.Column("indicator_name_ar", sa.String(256), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("category", sa.String(64), nullable=False, index=True),
        sa.Column("subcategory", sa.String(64), nullable=True),
        sa.Column("sector", sa.String(64), nullable=True, index=True),
        sa.Column("country_scope", sa.String(4), nullable=True),
        sa.Column("unit", sa.String(64), nullable=False),
        sa.Column("value_type", sa.String(32), nullable=False, server_default="NUMERIC"),
        sa.Column("precision_digits", sa.Integer(), nullable=False, server_default="2"),
        sa.Column("frequency", sa.String(32), nullable=False),
        sa.Column("normal_range_min", sa.Float(), nullable=True),
        sa.Column("normal_range_max", sa.Float(), nullable=True),
        sa.Column("alert_threshold_low", sa.Float(), nullable=True),
        sa.Column("alert_threshold_high", sa.Float(), nullable=True),
        sa.Column("primary_source_id", sa.String(128), nullable=True),
        sa.Column("secondary_source_ids", postgresql.JSONB(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("is_composite", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("composite_formula", sa.Text(), nullable=True),
        sa.Column("tags", postgresql.JSONB(), nullable=True),
        sa.Column("metadata_json", postgresql.JSONB(), nullable=True),
        *_foundation_cols(),
    )
    op.create_index("ix_df_ic_category_sector", "df_indicator_catalog", ["category", "sector"])
    op.create_index("ix_df_ic_active_freq", "df_indicator_catalog", ["is_active", "frequency"])

    # ── df_canonical_observations ────────────────────────────────────────
    op.create_table(
        "df_canonical_observations",
        sa.Column("observation_id", sa.String(128), primary_key=True),
        sa.Column("indicator_id", sa.String(128), nullable=False, index=True),
        sa.Column("indicator_code", sa.String(64), nullable=False, index=True),
        sa.Column("value", sa.Float(), nullable=False),
        sa.Column("unit", sa.String(64), nullable=False),
        sa.Column("country", sa.String(4), nullable=False, index=True),
        sa.Column("entity_id", sa.String(64), nullable=True, index=True),
        sa.Column("period_start", sa.Date(), nullable=False, index=True),
        sa.Column("period_end", sa.Date(), nullable=False),
        sa.Column("frequency", sa.String(32), nullable=False),
        sa.Column("observation_date", sa.Date(), nullable=False),
        sa.Column("source_id", sa.String(128), nullable=False, index=True),
        sa.Column("source_url", sa.String(1024), nullable=False),
        sa.Column("fetch_timestamp", sa.DateTime(timezone=True), nullable=False),
        sa.Column("content_hash", sa.String(128), nullable=False),
        sa.Column("raw_record_id", sa.String(128), nullable=True),
        sa.Column("normalization_run_id", sa.String(128), nullable=True),
        sa.Column("confidence_score", sa.Float(), nullable=False, server_default="0.8"),
        sa.Column("confidence_method", sa.String(64), nullable=False, server_default="SOURCE_DECLARED"),
        sa.Column("is_provisional", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("revision_number", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("previous_value", sa.Float(), nullable=True),
        sa.Column("change_absolute", sa.Float(), nullable=True),
        sa.Column("change_pct", sa.Float(), nullable=True),
        *_foundation_cols(),
    )
    op.create_index("ix_df_co_indicator_period", "df_canonical_observations", ["indicator_code", "period_start", "country"])
    op.create_index("ix_df_co_source_fetch", "df_canonical_observations", ["source_id", "fetch_timestamp"])
    op.create_index("ix_df_co_country_date", "df_canonical_observations", ["country", "observation_date"])

    # ── df_source_fetch_runs ─────────────────────────────────────────────
    op.create_table(
        "df_source_fetch_runs",
        sa.Column("run_id", sa.String(128), primary_key=True),
        sa.Column("source_id", sa.String(128), nullable=False, index=True),
        sa.Column("source_url", sa.String(1024), nullable=False),
        sa.Column("fetch_timestamp", sa.DateTime(timezone=True), nullable=False, index=True),
        sa.Column("content_hash", sa.String(128), nullable=True),
        sa.Column("period_start", sa.Date(), nullable=False),
        sa.Column("period_end", sa.Date(), nullable=False),
        sa.Column("status", sa.String(32), nullable=False, server_default="PENDING", index=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("duration_seconds", sa.Float(), nullable=True),
        sa.Column("records_fetched", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("records_new", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("records_duplicate", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("records_failed", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("payload_size_bytes", sa.Integer(), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("error_code", sa.String(64), nullable=True),
        sa.Column("retry_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("trigger_type", sa.String(32), nullable=False, server_default="SCHEDULED"),
        sa.Column("triggered_by", sa.String(128), nullable=True),
        *_foundation_cols(),
    )
    op.create_index("ix_df_sfr_source_status", "df_source_fetch_runs", ["source_id", "status"])
    op.create_index("ix_df_sfr_fetch_ts", "df_source_fetch_runs", ["fetch_timestamp"])

    # ── df_normalization_runs ────────────────────────────────────────────
    op.create_table(
        "df_normalization_runs",
        sa.Column("run_id", sa.String(128), primary_key=True),
        sa.Column("fetch_run_id", sa.String(128), nullable=False, index=True),
        sa.Column("source_id", sa.String(128), nullable=False, index=True),
        sa.Column("indicator_id", sa.String(128), nullable=True, index=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("duration_seconds", sa.Float(), nullable=True),
        sa.Column("status", sa.String(32), nullable=False, server_default="PENDING", index=True),
        sa.Column("raw_records_input", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("observations_created", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("observations_updated", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("observations_skipped", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("validation_errors", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("normalization_version", sa.String(16), nullable=False, server_default="1.0.0"),
        sa.Column("field_mappings_used", postgresql.JSONB(), nullable=True),
        sa.Column("quality_gates_applied", postgresql.JSONB(), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("error_details", postgresql.JSONB(), nullable=True),
        *_foundation_cols(),
    )
    op.create_index("ix_df_nr_fetch_run", "df_normalization_runs", ["fetch_run_id"])
    op.create_index("ix_df_nr_source_status", "df_normalization_runs", ["source_id", "status"])


def downgrade() -> None:
    op.drop_table("df_normalization_runs")
    op.drop_table("df_source_fetch_runs")
    op.drop_table("df_canonical_observations")
    op.drop_table("df_indicator_catalog")
    op.drop_table("df_raw_source_records")
    op.drop_table("df_source_truth_registry")
