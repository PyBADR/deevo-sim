"""Decision Enforcement Layer — package root.

Exports all schemas, engine functions, and key services.
"""

from src.data_foundation.enforcement.schemas import (
    EnforcementPolicy,
    EnforcementDecision,
    ExecutionGateResult,
    ApprovalRequest,
    VALID_ENFORCEMENT_ACTIONS,
    VALID_ENFORCEMENT_STATUSES,
    VALID_GATE_TYPES,
    VALID_GATE_RESULTS,
    VALID_APPROVAL_STATUSES,
)
from src.data_foundation.enforcement.enforcement_engine import (
    evaluate_decision_for_enforcement,
    apply_enforcement_policies,
    resolve_policy_matches,
    compute_effective_execution_state,
    determine_fallback_action,
    determine_required_approver,
    degrade_confidence,
)
from src.data_foundation.enforcement.execution_gate_service import (
    can_execute_decision,
    create_gate_result,
    require_manual_approval,
    convert_to_fallback,
    mark_shadow_only,
    persist_enforcement_outcome,
)
from src.data_foundation.enforcement.enforcement_audit import (
    audit_enforcement_policy_created,
    audit_enforcement_policy_updated,
    audit_enforcement_evaluated,
    audit_decision_blocked,
    audit_approval_required,
    audit_fallback_applied,
    audit_shadow_mode_activated,
)

__all__ = [
    # Schemas
    "EnforcementPolicy",
    "EnforcementDecision",
    "ExecutionGateResult",
    "ApprovalRequest",
    "VALID_ENFORCEMENT_ACTIONS",
    "VALID_ENFORCEMENT_STATUSES",
    "VALID_GATE_TYPES",
    "VALID_GATE_RESULTS",
    "VALID_APPROVAL_STATUSES",
    # Engine
    "evaluate_decision_for_enforcement",
    "apply_enforcement_policies",
    "resolve_policy_matches",
    "compute_effective_execution_state",
    "determine_fallback_action",
    "determine_required_approver",
    "degrade_confidence",
    # Gate Service
    "can_execute_decision",
    "create_gate_result",
    "require_manual_approval",
    "convert_to_fallback",
    "mark_shadow_only",
    "persist_enforcement_outcome",
    # Audit
    "audit_enforcement_policy_created",
    "audit_enforcement_policy_updated",
    "audit_enforcement_evaluated",
    "audit_decision_blocked",
    "audit_approval_required",
    "audit_fallback_applied",
    "audit_shadow_mode_activated",
]
