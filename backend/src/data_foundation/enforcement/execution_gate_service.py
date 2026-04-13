"""Execution Gate Service — translates enforcement into execution eligibility.

Stateless service layer that wraps the enforcement engine with:
  - execution eligibility determination
  - approval request creation
  - fallback conversion
  - shadow mode marking
  - enforcement outcome persistence (in-memory for stateless operation)

All functions are pure or use in-memory stores — no external I/O required.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple
from uuid import uuid4

from src.data_foundation.enforcement.enforcement_engine import (
    evaluate_decision_for_enforcement,
)
from src.data_foundation.enforcement.schemas import (
    ApprovalRequest,
    EnforcementDecision,
    EnforcementPolicy,
    ExecutionGateResult,
)

__all__ = [
    "can_execute_decision",
    "create_gate_result",
    "require_manual_approval",
    "convert_to_fallback",
    "mark_shadow_only",
    "persist_enforcement_outcome",
]


def _gen_approval_id() -> str:
    return f"APPR-{str(uuid4())[:12]}"


def _gen_gate_id() -> str:
    return f"GATE-{str(uuid4())[:12]}"


# In-memory stores for stateless operation (same pattern as evaluation API)
_enforcement_store: Dict[str, EnforcementDecision] = {}
_gate_store: Dict[str, List[ExecutionGateResult]] = {}
_approval_store: Dict[str, ApprovalRequest] = {}


def can_execute_decision(
    *,
    decision_log_id: str,
    decision_rule_id: Optional[str] = None,
    policies: List[EnforcementPolicy],
    context: Dict[str, Any],
    rule_lifecycle_status: Optional[str] = None,
    truth_validation_passed: Optional[bool] = None,
    truth_critical_failure: bool = False,
    has_unresolved_calibration: Optional[bool] = None,
    data_freshness_passed: Optional[bool] = None,
    explainability_score: Optional[float] = None,
    explainability_threshold: float = 0.5,
    financial_exposure_usd: Optional[float] = None,
    financial_threshold_usd: float = 1_000_000_000.0,
    has_conflicting_actions: Optional[bool] = None,
    original_confidence: Optional[float] = None,
) -> Tuple[EnforcementDecision, List[ExecutionGateResult]]:
    """Full enforcement evaluation — returns (decision, gates).

    This is the primary entry point for execution eligibility checks.
    Wraps evaluate_decision_for_enforcement and handles approval/fallback creation.
    """
    decision, gates = evaluate_decision_for_enforcement(
        decision_log_id=decision_log_id,
        decision_rule_id=decision_rule_id,
        policies=policies,
        context=context,
        rule_lifecycle_status=rule_lifecycle_status,
        truth_validation_passed=truth_validation_passed,
        truth_critical_failure=truth_critical_failure,
        has_unresolved_calibration=has_unresolved_calibration,
        data_freshness_passed=data_freshness_passed,
        explainability_score=explainability_score,
        explainability_threshold=explainability_threshold,
        financial_exposure_usd=financial_exposure_usd,
        financial_threshold_usd=financial_threshold_usd,
        has_conflicting_actions=has_conflicting_actions,
        original_confidence=original_confidence,
    )

    # Auto-create approval request if needed
    if decision.enforcement_action == "REQUIRE_APPROVAL" and decision.required_approver:
        approval = require_manual_approval(
            decision_log_id=decision_log_id,
            enforcement_id=decision.enforcement_id,
            requested_from=decision.required_approver,
            reason="; ".join(decision.blocking_reasons) if decision.blocking_reasons else "Approval required by policy",
        )
        _approval_store[approval.approval_id] = approval

    return (decision, gates)


def create_gate_result(
    *,
    decision_log_id: str,
    enforcement_id: str,
    gate_type: str,
    gate_result: str,
    reason: str = "",
) -> ExecutionGateResult:
    """Create a standalone gate result."""
    return ExecutionGateResult(
        gate_id=_gen_gate_id(),
        decision_log_id=decision_log_id,
        enforcement_id=enforcement_id,
        gate_type=gate_type,
        gate_result=gate_result,
        reason=reason,
        checked_at=datetime.now(timezone.utc),
    )


def require_manual_approval(
    *,
    decision_log_id: str,
    enforcement_id: str,
    requested_from: str,
    reason: str = "",
) -> ApprovalRequest:
    """Create a manual approval request."""
    return ApprovalRequest(
        approval_id=_gen_approval_id(),
        decision_log_id=decision_log_id,
        enforcement_id=enforcement_id,
        requested_from=requested_from,
        approval_status="PENDING",
        reason=reason,
        requested_at=datetime.now(timezone.utc),
    )


def convert_to_fallback(
    decision: EnforcementDecision,
    fallback_action: str,
) -> EnforcementDecision:
    """Convert an enforcement decision to use a fallback action.

    Returns a new EnforcementDecision with FALLBACK action.
    """
    return EnforcementDecision(
        enforcement_id=decision.enforcement_id,
        decision_log_id=decision.decision_log_id,
        decision_rule_id=decision.decision_rule_id,
        enforcement_status="EVALUATED",
        enforcement_action="FALLBACK",
        triggered_policy_ids=decision.triggered_policy_ids,
        blocking_reasons=decision.blocking_reasons,
        required_approver=None,
        fallback_action=fallback_action,
        effective_confidence=decision.effective_confidence,
        is_executable=False,
        shadow_mode=False,
    )


def mark_shadow_only(
    decision: EnforcementDecision,
) -> EnforcementDecision:
    """Mark an enforcement decision as shadow-only (non-executable, logged).

    Returns a new EnforcementDecision with SHADOW_ONLY action.
    """
    return EnforcementDecision(
        enforcement_id=decision.enforcement_id,
        decision_log_id=decision.decision_log_id,
        decision_rule_id=decision.decision_rule_id,
        enforcement_status="EVALUATED",
        enforcement_action="SHADOW_ONLY",
        triggered_policy_ids=decision.triggered_policy_ids,
        blocking_reasons=decision.blocking_reasons,
        required_approver=None,
        fallback_action=None,
        effective_confidence=decision.effective_confidence,
        is_executable=False,
        shadow_mode=True,
    )


def persist_enforcement_outcome(
    decision: EnforcementDecision,
    gates: List[ExecutionGateResult],
) -> None:
    """Persist enforcement outcome to in-memory stores."""
    _enforcement_store[decision.enforcement_id] = decision
    _gate_store[decision.enforcement_id] = gates


def get_enforcement_decision(enforcement_id: str) -> Optional[EnforcementDecision]:
    """Retrieve a persisted enforcement decision."""
    return _enforcement_store.get(enforcement_id)


def get_enforcement_gates(enforcement_id: str) -> List[ExecutionGateResult]:
    """Retrieve persisted gate results for an enforcement decision."""
    return _gate_store.get(enforcement_id, [])


def get_enforcement_by_decision_log(decision_log_id: str) -> Optional[EnforcementDecision]:
    """Find enforcement decision by decision_log_id."""
    for d in _enforcement_store.values():
        if d.decision_log_id == decision_log_id:
            return d
    return None


def get_pending_approvals() -> List[ApprovalRequest]:
    """Get all pending approval requests."""
    return [a for a in _approval_store.values() if a.approval_status == "PENDING"]


def get_approval(approval_id: str) -> Optional[ApprovalRequest]:
    """Get a specific approval request."""
    return _approval_store.get(approval_id)
