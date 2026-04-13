"""Decision Enforcement — ORM ↔ Pydantic converter functions.

8 converter functions (to_orm + from_orm for each of 4 models).
"""

from __future__ import annotations

from src.data_foundation.enforcement.orm_models import (
    ApprovalRequestORM,
    EnforcementDecisionORM,
    EnforcementPolicyORM,
    ExecutionGateResultORM,
)
from src.data_foundation.enforcement.schemas import (
    ApprovalRequest,
    EnforcementDecision,
    EnforcementPolicy,
    ExecutionGateResult,
)

__all__ = [
    "enforcement_policy_to_orm", "enforcement_policy_from_orm",
    "enforcement_decision_to_orm", "enforcement_decision_from_orm",
    "execution_gate_result_to_orm", "execution_gate_result_from_orm",
    "approval_request_to_orm", "approval_request_from_orm",
]


# ── EnforcementPolicy ─────────────────────────────────────────────────────

def enforcement_policy_to_orm(schema: EnforcementPolicy) -> EnforcementPolicyORM:
    return EnforcementPolicyORM(
        policy_id=schema.policy_id,
        policy_name=schema.policy_name,
        policy_type=schema.policy_type,
        scope_type=schema.scope_type,
        scope_ref=schema.scope_ref,
        conditions=schema.conditions or None,
        action_on_match=schema.action_on_match,
        severity=schema.severity,
        priority=schema.priority,
        is_active=schema.is_active,
        rationale=schema.rationale,
        created_by=schema.created_by,
        provenance_hash=schema.provenance_hash,
    )


def enforcement_policy_from_orm(orm: EnforcementPolicyORM) -> EnforcementPolicy:
    return EnforcementPolicy.model_validate(orm)


# ── EnforcementDecision ────────────────────────────────────────────────────

def enforcement_decision_to_orm(schema: EnforcementDecision) -> EnforcementDecisionORM:
    return EnforcementDecisionORM(
        enforcement_id=schema.enforcement_id,
        decision_log_id=schema.decision_log_id,
        decision_rule_id=schema.decision_rule_id,
        enforcement_status=schema.enforcement_status,
        enforcement_action=schema.enforcement_action,
        triggered_policy_ids=schema.triggered_policy_ids or None,
        blocking_reasons=schema.blocking_reasons or None,
        required_approver=schema.required_approver,
        fallback_action=schema.fallback_action,
        effective_confidence=schema.effective_confidence,
        is_executable=schema.is_executable,
        shadow_mode=schema.shadow_mode,
        provenance_hash=schema.provenance_hash,
    )


def enforcement_decision_from_orm(orm: EnforcementDecisionORM) -> EnforcementDecision:
    return EnforcementDecision.model_validate(orm)


# ── ExecutionGateResult ────────────────────────────────────────────────────

def execution_gate_result_to_orm(schema: ExecutionGateResult) -> ExecutionGateResultORM:
    return ExecutionGateResultORM(
        gate_id=schema.gate_id,
        decision_log_id=schema.decision_log_id,
        enforcement_id=schema.enforcement_id,
        gate_type=schema.gate_type,
        gate_result=schema.gate_result,
        reason=schema.reason,
        checked_at=schema.checked_at,
        provenance_hash=schema.provenance_hash,
    )


def execution_gate_result_from_orm(orm: ExecutionGateResultORM) -> ExecutionGateResult:
    return ExecutionGateResult.model_validate(orm)


# ── ApprovalRequest ────────────────────────────────────────────────────────

def approval_request_to_orm(schema: ApprovalRequest) -> ApprovalRequestORM:
    return ApprovalRequestORM(
        approval_id=schema.approval_id,
        decision_log_id=schema.decision_log_id,
        enforcement_id=schema.enforcement_id,
        requested_from=schema.requested_from,
        approval_status=schema.approval_status,
        reason=schema.reason,
        requested_at=schema.requested_at,
        responded_at=schema.responded_at,
        provenance_hash=schema.provenance_hash,
    )


def approval_request_from_orm(orm: ApprovalRequestORM) -> ApprovalRequest:
    return ApprovalRequest.model_validate(orm)
