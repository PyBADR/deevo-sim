"""Decision Enforcement Layer — SQLAlchemy ORM table definitions.

Four tables (df_enf_* prefix):

  df_enf_policies           — enforcement policy rules
  df_enf_decisions          — resolved enforcement outcomes
  df_enf_execution_gates    — individual gate check results
  df_enf_approval_requests  — manual approval requests

Design:
  - Same _FoundationMixin as all df_* tables
  - JSONB for flexible nested data (conditions, triggered_policy_ids, blocking_reasons)
  - VARCHAR enums (no Postgres native ENUMs)
  - String PKs (128-char max)
"""

from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import (
    Boolean,
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
# Table: df_enf_policies
# ═══════════════════════════════════════════════════════════════════════════════

class EnforcementPolicyORM(_FoundationMixin, Base):
    __tablename__ = "df_enf_policies"

    policy_id: Mapped[str] = mapped_column(String(128), primary_key=True)
    policy_name: Mapped[str] = mapped_column(String(256), nullable=False)
    policy_type: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    scope_type: Mapped[str] = mapped_column(String(32), default="GLOBAL", nullable=False, index=True)
    scope_ref: Mapped[str | None] = mapped_column(String(128), nullable=True, index=True)
    conditions: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    action_on_match: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    severity: Mapped[str] = mapped_column(String(16), default="MEDIUM", nullable=False)
    priority: Mapped[int] = mapped_column(Integer, default=100, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False, index=True)
    rationale: Mapped[str] = mapped_column(Text, nullable=False)
    created_by: Mapped[str] = mapped_column(String(256), nullable=False)

    __table_args__ = (
        Index("ix_df_enf_pol_type_active", "policy_type", "is_active"),
        Index("ix_df_enf_pol_scope", "scope_type", "scope_ref"),
        Index("ix_df_enf_pol_priority", "priority", "is_active"),
    )


# ═══════════════════════════════════════════════════════════════════════════════
# Table: df_enf_decisions
# ═══════════════════════════════════════════════════════════════════════════════

class EnforcementDecisionORM(_FoundationMixin, Base):
    __tablename__ = "df_enf_decisions"

    enforcement_id: Mapped[str] = mapped_column(String(128), primary_key=True)
    decision_log_id: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    decision_rule_id: Mapped[str | None] = mapped_column(String(128), nullable=True, index=True)
    enforcement_status: Mapped[str] = mapped_column(String(32), default="PENDING", nullable=False, index=True)
    enforcement_action: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    triggered_policy_ids: Mapped[dict | None] = mapped_column(JSONB, nullable=True)  # List[str]
    blocking_reasons: Mapped[dict | None] = mapped_column(JSONB, nullable=True)  # List[str]
    required_approver: Mapped[str | None] = mapped_column(String(256), nullable=True)
    fallback_action: Mapped[str | None] = mapped_column(String(128), nullable=True)
    effective_confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    is_executable: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    shadow_mode: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    __table_args__ = (
        Index("ix_df_enf_dec_dlog", "decision_log_id"),
        Index("ix_df_enf_dec_status_action", "enforcement_status", "enforcement_action"),
    )


# ═══════════════════════════════════════════════════════════════════════════════
# Table: df_enf_execution_gates
# ═══════════════════════════════════════════════════════════════════════════════

class ExecutionGateResultORM(_FoundationMixin, Base):
    __tablename__ = "df_enf_execution_gates"

    gate_id: Mapped[str] = mapped_column(String(128), primary_key=True)
    decision_log_id: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    enforcement_id: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    gate_type: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    gate_result: Mapped[str] = mapped_column(String(16), nullable=False, index=True)
    reason: Mapped[str] = mapped_column(Text, default="", nullable=False)
    checked_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)

    __table_args__ = (
        Index("ix_df_enf_gate_dlog_type", "decision_log_id", "gate_type"),
    )


# ═══════════════════════════════════════════════════════════════════════════════
# Table: df_enf_approval_requests
# ═══════════════════════════════════════════════════════════════════════════════

class ApprovalRequestORM(_FoundationMixin, Base):
    __tablename__ = "df_enf_approval_requests"

    approval_id: Mapped[str] = mapped_column(String(128), primary_key=True)
    decision_log_id: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    enforcement_id: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    requested_from: Mapped[str] = mapped_column(String(256), nullable=False)
    approval_status: Mapped[str] = mapped_column(String(32), default="PENDING", nullable=False, index=True)
    reason: Mapped[str] = mapped_column(Text, default="", nullable=False)
    requested_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    responded_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    __table_args__ = (
        Index("ix_df_enf_appr_status", "approval_status"),
        Index("ix_df_enf_appr_dlog", "decision_log_id"),
        Index("ix_df_enf_appr_enf", "enforcement_id"),
    )
