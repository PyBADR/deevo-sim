"""Decision Enforcement Layer — Pydantic v2 schemas.

Four domain models:

  EnforcementPolicy       — rules governing execution eligibility
  EnforcementDecision     — resolved enforcement outcome per decision candidate
  ExecutionGateResult     — individual gate check within enforcement
  ApprovalRequest         — manual approval request when REQUIRE_APPROVAL

All inherit FoundationModel.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import Field, field_validator

from src.data_foundation.schemas.base import FoundationModel

__all__ = [
    "EnforcementPolicy",
    "EnforcementDecision",
    "ExecutionGateResult",
    "ApprovalRequest",
    # Constants
    "VALID_ENFORCEMENT_ACTIONS",
    "VALID_ENFORCEMENT_STATUSES",
    "VALID_GATE_TYPES",
    "VALID_GATE_RESULTS",
    "VALID_APPROVAL_STATUSES",
    "VALID_POLICY_TYPES",
    "VALID_SCOPE_TYPES",
    "VALID_SEVERITY_LEVELS",
]

# ═══════════════════════════════════════════════════════════════════════════════
# Constants
# ═══════════════════════════════════════════════════════════════════════════════

VALID_ENFORCEMENT_ACTIONS = {
    "ALLOW", "BLOCK", "ESCALATE", "REQUIRE_APPROVAL",
    "FALLBACK", "SHADOW_ONLY", "DEGRADE_CONFIDENCE",
}

VALID_ENFORCEMENT_STATUSES = {
    "PENDING", "EVALUATED", "APPROVED", "REJECTED",
    "OVERRIDDEN", "EXPIRED",
}

VALID_GATE_TYPES = {
    "RULE_LIFECYCLE", "TRUTH_VALIDATION", "CALIBRATION_STATUS",
    "POLICY_MATCH", "DATA_FRESHNESS", "EXPLAINABILITY",
    "FINANCIAL_EXPOSURE", "CONFLICT_CHECK",
}

VALID_GATE_RESULTS = {"PASS", "FAIL", "WARN", "SKIP"}

VALID_APPROVAL_STATUSES = {
    "PENDING", "APPROVED", "REJECTED", "EXPIRED", "WITHDRAWN",
}

VALID_POLICY_TYPES = {
    "BLOCK_RULE", "APPROVAL_GATE", "ESCALATION_RULE",
    "SHADOW_RULE", "CONFIDENCE_DEGRADATION", "FALLBACK_RULE",
    "FINANCIAL_THRESHOLD",
}

VALID_SCOPE_TYPES = {
    "GLOBAL", "COUNTRY", "SECTOR", "SCENARIO", "RULE", "ENTITY",
}

VALID_SEVERITY_LEVELS = {
    "LOW", "MEDIUM", "HIGH", "CRITICAL",
}


# ═══════════════════════════════════════════════════════════════════════════════
# Domain Models
# ═══════════════════════════════════════════════════════════════════════════════

class EnforcementPolicy(FoundationModel):
    """Rules governing execution eligibility for decision candidates."""

    policy_id: str = Field(..., description="Format: EPOL-{TYPE}-{VARIANT}")
    policy_name: str = Field(..., min_length=1)
    policy_type: str = Field(...)
    scope_type: str = Field(default="GLOBAL")
    scope_ref: Optional[str] = Field(default=None, description="Ref ID for scoped policies.")
    conditions: Dict[str, Any] = Field(
        default_factory=dict,
        description="Deterministic condition map (field → threshold/match).",
    )
    action_on_match: str = Field(...)
    severity: str = Field(default="MEDIUM")
    priority: int = Field(default=100, ge=0, description="Lower = higher priority.")
    is_active: bool = Field(default=True)
    rationale: str = Field(..., min_length=1)
    created_by: str = Field(..., min_length=1)

    @field_validator("policy_type")
    @classmethod
    def _check_policy_type(cls, v: str) -> str:
        if v not in VALID_POLICY_TYPES:
            raise ValueError(f"policy_type must be one of {VALID_POLICY_TYPES}, got '{v}'")
        return v

    @field_validator("scope_type")
    @classmethod
    def _check_scope_type(cls, v: str) -> str:
        if v not in VALID_SCOPE_TYPES:
            raise ValueError(f"scope_type must be one of {VALID_SCOPE_TYPES}, got '{v}'")
        return v

    @field_validator("action_on_match")
    @classmethod
    def _check_action(cls, v: str) -> str:
        if v not in VALID_ENFORCEMENT_ACTIONS:
            raise ValueError(f"action_on_match must be one of {VALID_ENFORCEMENT_ACTIONS}, got '{v}'")
        return v

    @field_validator("severity")
    @classmethod
    def _check_severity(cls, v: str) -> str:
        if v not in VALID_SEVERITY_LEVELS:
            raise ValueError(f"severity must be one of {VALID_SEVERITY_LEVELS}, got '{v}'")
        return v


class EnforcementDecision(FoundationModel):
    """Resolved enforcement outcome for a decision candidate."""

    enforcement_id: str = Field(..., description="Format: ENFD-{uuid12}")
    decision_log_id: str = Field(...)
    decision_rule_id: Optional[str] = Field(default=None)
    enforcement_status: str = Field(default="PENDING")
    enforcement_action: str = Field(...)
    triggered_policy_ids: List[str] = Field(default_factory=list)
    blocking_reasons: List[str] = Field(default_factory=list)
    required_approver: Optional[str] = Field(default=None)
    fallback_action: Optional[str] = Field(default=None)
    effective_confidence: Optional[float] = Field(default=None, ge=0.0, le=1.0)
    is_executable: bool = Field(default=False)
    shadow_mode: bool = Field(default=False)

    @field_validator("enforcement_status")
    @classmethod
    def _check_status(cls, v: str) -> str:
        if v not in VALID_ENFORCEMENT_STATUSES:
            raise ValueError(f"enforcement_status must be one of {VALID_ENFORCEMENT_STATUSES}, got '{v}'")
        return v

    @field_validator("enforcement_action")
    @classmethod
    def _check_action(cls, v: str) -> str:
        if v not in VALID_ENFORCEMENT_ACTIONS:
            raise ValueError(f"enforcement_action must be one of {VALID_ENFORCEMENT_ACTIONS}, got '{v}'")
        return v


class ExecutionGateResult(FoundationModel):
    """Individual gate check within enforcement evaluation."""

    gate_id: str = Field(..., description="Format: GATE-{uuid12}")
    decision_log_id: str = Field(...)
    enforcement_id: str = Field(...)
    gate_type: str = Field(...)
    gate_result: str = Field(...)
    reason: str = Field(default="")
    checked_at: datetime = Field(...)

    @field_validator("gate_type")
    @classmethod
    def _check_gate_type(cls, v: str) -> str:
        if v not in VALID_GATE_TYPES:
            raise ValueError(f"gate_type must be one of {VALID_GATE_TYPES}, got '{v}'")
        return v

    @field_validator("gate_result")
    @classmethod
    def _check_gate_result(cls, v: str) -> str:
        if v not in VALID_GATE_RESULTS:
            raise ValueError(f"gate_result must be one of {VALID_GATE_RESULTS}, got '{v}'")
        return v


class ApprovalRequest(FoundationModel):
    """Manual approval request when enforcement resolves to REQUIRE_APPROVAL."""

    approval_id: str = Field(..., description="Format: APPR-{uuid12}")
    decision_log_id: str = Field(...)
    enforcement_id: str = Field(...)
    requested_from: str = Field(..., min_length=1)
    approval_status: str = Field(default="PENDING")
    reason: str = Field(default="")
    requested_at: datetime = Field(...)
    responded_at: Optional[datetime] = Field(default=None)

    @field_validator("approval_status")
    @classmethod
    def _check_status(cls, v: str) -> str:
        if v not in VALID_APPROVAL_STATUSES:
            raise ValueError(f"approval_status must be one of {VALID_APPROVAL_STATUSES}, got '{v}'")
        return v
