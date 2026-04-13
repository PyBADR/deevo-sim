"""Enforcement Integration — minimal hooks into evaluation and replay flows.

Provides pure functions that can be called from existing services without
modifying their architecture. Each function takes data already available in
the calling context and returns enforcement results.

No I/O. No redesign. Deterministic only.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple

from src.data_foundation.enforcement.enforcement_engine import (
    evaluate_decision_for_enforcement,
)
from src.data_foundation.enforcement.schemas import (
    EnforcementDecision,
    EnforcementPolicy,
    ExecutionGateResult,
)

__all__ = [
    "evaluate_replay_enforcement",
    "evaluate_decision_enforcement",
    "build_enforcement_summary",
]


def evaluate_replay_enforcement(
    *,
    decision_log_id: str,
    decision_rule_id: Optional[str] = None,
    policies: List[EnforcementPolicy],
    rule_lifecycle_status: Optional[str] = None,
    has_unresolved_calibration: Optional[bool] = None,
    data_freshness_passed: Optional[bool] = None,
    explainability_score: Optional[float] = None,
    original_confidence: Optional[float] = None,
    context: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Evaluate enforcement for a replayed decision.

    Called after replay matching to determine whether a replayed decision
    would be executable under current enforcement policies.

    Returns a summary dict suitable for inclusion in ReplayReport.
    """
    decision, gates = evaluate_decision_for_enforcement(
        decision_log_id=decision_log_id,
        decision_rule_id=decision_rule_id,
        policies=policies,
        context=context or {},
        rule_lifecycle_status=rule_lifecycle_status,
        has_unresolved_calibration=has_unresolved_calibration,
        data_freshness_passed=data_freshness_passed,
        explainability_score=explainability_score,
        original_confidence=original_confidence,
    )
    return build_enforcement_summary(decision, gates)


def evaluate_decision_enforcement(
    *,
    decision_log_id: str,
    decision_rule_id: Optional[str] = None,
    policies: List[EnforcementPolicy],
    correctness_score: Optional[float] = None,
    explainability_score: Optional[float] = None,
    truth_validation_passed: Optional[bool] = None,
    truth_critical_failure: bool = False,
    has_unresolved_calibration: Optional[bool] = None,
    data_freshness_passed: Optional[bool] = None,
    financial_exposure_usd: Optional[float] = None,
    has_conflicting_actions: Optional[bool] = None,
    rule_lifecycle_status: Optional[str] = None,
    original_confidence: Optional[float] = None,
    context: Optional[Dict[str, Any]] = None,
) -> Tuple[EnforcementDecision, List[ExecutionGateResult]]:
    """Evaluate enforcement for a decision post-evaluation.

    Called after decision evaluation scoring to determine execution eligibility.
    """
    return evaluate_decision_for_enforcement(
        decision_log_id=decision_log_id,
        decision_rule_id=decision_rule_id,
        policies=policies,
        context=context or {},
        rule_lifecycle_status=rule_lifecycle_status,
        truth_validation_passed=truth_validation_passed,
        truth_critical_failure=truth_critical_failure,
        has_unresolved_calibration=has_unresolved_calibration,
        data_freshness_passed=data_freshness_passed,
        explainability_score=explainability_score,
        financial_exposure_usd=financial_exposure_usd,
        has_conflicting_actions=has_conflicting_actions,
        original_confidence=original_confidence,
    )


def build_enforcement_summary(
    decision: EnforcementDecision,
    gates: List[ExecutionGateResult],
) -> Dict[str, Any]:
    """Build a summary dict from enforcement results.

    Suitable for embedding in replay reports or evaluation outputs.
    """
    return {
        "enforcement_id": decision.enforcement_id,
        "enforcement_action": decision.enforcement_action,
        "is_executable": decision.is_executable,
        "shadow_mode": decision.shadow_mode,
        "effective_confidence": decision.effective_confidence,
        "blocking_reasons": decision.blocking_reasons,
        "triggered_policy_ids": decision.triggered_policy_ids,
        "required_approver": decision.required_approver,
        "fallback_action": decision.fallback_action,
        "gate_summary": {
            "total": len(gates),
            "passed": sum(1 for g in gates if g.gate_result == "PASS"),
            "failed": sum(1 for g in gates if g.gate_result == "FAIL"),
            "warned": sum(1 for g in gates if g.gate_result == "WARN"),
            "skipped": sum(1 for g in gates if g.gate_result == "SKIP"),
        },
        "gates": [
            {
                "gate_type": g.gate_type,
                "gate_result": g.gate_result,
                "reason": g.reason,
            }
            for g in gates
        ],
    }
