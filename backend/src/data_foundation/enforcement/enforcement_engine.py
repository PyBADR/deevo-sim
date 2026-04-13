"""Decision Enforcement Engine — deterministic enforcement evaluation.

Evaluates a decision candidate against governance state and enforcement policies.
Produces a single EnforcementDecision with one of 7 enforcement actions:
  ALLOW, BLOCK, ESCALATE, REQUIRE_APPROVAL, FALLBACK, SHADOW_ONLY, DEGRADE_CONFIDENCE

All functions are pure — no I/O, fully testable.
Policy priority is respected: lower number = higher priority.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple
from uuid import uuid4

from src.data_foundation.enforcement.schemas import (
    EnforcementDecision,
    EnforcementPolicy,
    ExecutionGateResult,
    VALID_ENFORCEMENT_ACTIONS,
)

__all__ = [
    "evaluate_decision_for_enforcement",
    "apply_enforcement_policies",
    "resolve_policy_matches",
    "compute_effective_execution_state",
    "determine_fallback_action",
    "determine_required_approver",
    "degrade_confidence",
]


def _gen_enf_id() -> str:
    return f"ENFD-{str(uuid4())[:12]}"


def _gen_gate_id() -> str:
    return f"GATE-{str(uuid4())[:12]}"


# ═══════════════════════════════════════════════════════════════════════════════
# Gate Checks — each returns (gate_type, result, reason)
# ═══════════════════════════════════════════════════════════════════════════════

def _check_rule_lifecycle(
    rule_lifecycle_status: Optional[str],
) -> Tuple[str, str, str]:
    """If rule lifecycle status is not ACTIVE -> BLOCK."""
    if rule_lifecycle_status is None:
        return ("RULE_LIFECYCLE", "SKIP", "No rule lifecycle status provided")
    if rule_lifecycle_status != "ACTIVE":
        return ("RULE_LIFECYCLE", "FAIL", f"Rule lifecycle status is '{rule_lifecycle_status}', not ACTIVE")
    return ("RULE_LIFECYCLE", "PASS", "Rule is ACTIVE")


def _check_truth_validation(
    truth_validation_passed: Optional[bool],
    truth_critical_failure: bool = False,
) -> Tuple[str, str, str]:
    """If critical truth validation fails -> FAIL."""
    if truth_validation_passed is None:
        return ("TRUTH_VALIDATION", "SKIP", "No truth validation result provided")
    if truth_critical_failure:
        return ("TRUTH_VALIDATION", "FAIL", "Critical truth validation failure")
    if not truth_validation_passed:
        return ("TRUTH_VALIDATION", "WARN", "Truth validation failed (non-critical)")
    return ("TRUTH_VALIDATION", "PASS", "Truth validation passed")


def _check_calibration_status(
    has_unresolved_calibration: Optional[bool],
) -> Tuple[str, str, str]:
    """If unresolved calibration trigger exists -> WARN."""
    if has_unresolved_calibration is None:
        return ("CALIBRATION_STATUS", "SKIP", "No calibration status provided")
    if has_unresolved_calibration:
        return ("CALIBRATION_STATUS", "WARN", "Unresolved calibration trigger exists")
    return ("CALIBRATION_STATUS", "PASS", "No unresolved calibration triggers")


def _check_data_freshness(
    data_freshness_passed: Optional[bool],
) -> Tuple[str, str, str]:
    """If data freshness fails -> FAIL."""
    if data_freshness_passed is None:
        return ("DATA_FRESHNESS", "SKIP", "No data freshness check provided")
    if not data_freshness_passed:
        return ("DATA_FRESHNESS", "FAIL", "Data freshness check failed")
    return ("DATA_FRESHNESS", "PASS", "Data is fresh")


def _check_explainability(
    explainability_score: Optional[float],
    threshold: float = 0.5,
) -> Tuple[str, str, str]:
    """If explainability completeness below threshold -> WARN."""
    if explainability_score is None:
        return ("EXPLAINABILITY", "SKIP", "No explainability score provided")
    if explainability_score < threshold:
        return ("EXPLAINABILITY", "WARN", f"Explainability score {explainability_score:.3f} below threshold {threshold}")
    return ("EXPLAINABILITY", "PASS", f"Explainability score {explainability_score:.3f} meets threshold")


def _check_financial_exposure(
    financial_exposure_usd: Optional[float],
    threshold_usd: float = 1_000_000_000.0,
) -> Tuple[str, str, str]:
    """If financial exposure exceeds policy threshold -> WARN."""
    if financial_exposure_usd is None:
        return ("FINANCIAL_EXPOSURE", "SKIP", "No financial exposure provided")
    if financial_exposure_usd > threshold_usd:
        return ("FINANCIAL_EXPOSURE", "WARN", f"Financial exposure ${financial_exposure_usd:,.0f} exceeds ${threshold_usd:,.0f}")
    return ("FINANCIAL_EXPOSURE", "PASS", f"Financial exposure within threshold")


def _check_conflict(
    has_conflicting_actions: Optional[bool],
) -> Tuple[str, str, str]:
    """If conflicting decision actions exist -> WARN."""
    if has_conflicting_actions is None:
        return ("CONFLICT_CHECK", "SKIP", "No conflict check provided")
    if has_conflicting_actions:
        return ("CONFLICT_CHECK", "WARN", "Conflicting decision actions detected")
    return ("CONFLICT_CHECK", "PASS", "No conflicting actions")


# ═══════════════════════════════════════════════════════════════════════════════
# Policy Matching
# ═══════════════════════════════════════════════════════════════════════════════

def _condition_matches(
    condition_key: str,
    condition_value: Any,
    context: Dict[str, Any],
) -> bool:
    """Check if a single policy condition matches the context."""
    actual = context.get(condition_key)
    if actual is None:
        return False

    # Threshold conditions: {"operator": "gt", "value": 100}
    if isinstance(condition_value, dict):
        op = condition_value.get("operator", "eq")
        threshold = condition_value.get("value")
        if threshold is None:
            return False
        try:
            actual_num = float(actual)
            threshold_num = float(threshold)
        except (TypeError, ValueError):
            return False
        if op == "gt":
            return actual_num > threshold_num
        if op == "lt":
            return actual_num < threshold_num
        if op == "gte":
            return actual_num >= threshold_num
        if op == "lte":
            return actual_num <= threshold_num
        if op == "eq":
            return actual_num == threshold_num
        return False

    # List membership: condition_value is a list, actual must be in it
    if isinstance(condition_value, list):
        return actual in condition_value

    # Direct equality
    return actual == condition_value


def resolve_policy_matches(
    policies: List[EnforcementPolicy],
    context: Dict[str, Any],
) -> List[EnforcementPolicy]:
    """Filter policies whose conditions all match the given context.

    Only active policies are considered.
    Returns policies sorted by priority (ascending = highest priority first).
    """
    matched: List[EnforcementPolicy] = []
    for pol in policies:
        if not pol.is_active:
            continue
        # Empty conditions = always matches
        if not pol.conditions:
            matched.append(pol)
            continue
        all_match = all(
            _condition_matches(k, v, context)
            for k, v in pol.conditions.items()
        )
        if all_match:
            matched.append(pol)
    # Sort by priority ascending (lower number = higher priority)
    matched.sort(key=lambda p: p.priority)
    return matched


def apply_enforcement_policies(
    matched_policies: List[EnforcementPolicy],
) -> Tuple[str, List[str], List[str], Optional[str]]:
    """Apply matched policies in priority order to determine final action.

    Priority escalation rules (deterministic):
      BLOCK > REQUIRE_APPROVAL > ESCALATE > SHADOW_ONLY > DEGRADE_CONFIDENCE > FALLBACK > ALLOW

    Returns: (action, triggered_policy_ids, blocking_reasons, fallback_action)
    """
    ACTION_PRIORITY = {
        "BLOCK": 0,
        "REQUIRE_APPROVAL": 1,
        "ESCALATE": 2,
        "SHADOW_ONLY": 3,
        "DEGRADE_CONFIDENCE": 4,
        "FALLBACK": 5,
        "ALLOW": 6,
    }

    if not matched_policies:
        return ("ALLOW", [], [], None)

    triggered_ids: List[str] = []
    blocking_reasons: List[str] = []
    fallback_action: Optional[str] = None

    # Find the highest-severity action across all matched policies
    best_action = "ALLOW"
    best_priority = ACTION_PRIORITY["ALLOW"]

    for pol in matched_policies:
        triggered_ids.append(pol.policy_id)
        action = pol.action_on_match
        action_rank = ACTION_PRIORITY.get(action, 6)

        if action_rank < best_priority:
            best_action = action
            best_priority = action_rank

        if action in ("BLOCK", "REQUIRE_APPROVAL", "ESCALATE"):
            blocking_reasons.append(f"[{pol.policy_id}] {pol.rationale}")

        if action == "FALLBACK" and pol.conditions.get("fallback_action"):
            fallback_action = str(pol.conditions["fallback_action"])

    return (best_action, triggered_ids, blocking_reasons, fallback_action)


# ═══════════════════════════════════════════════════════════════════════════════
# Confidence Degradation
# ═══════════════════════════════════════════════════════════════════════════════

def degrade_confidence(
    original_confidence: float,
    degradation_factor: float = 0.5,
) -> float:
    """Apply deterministic confidence degradation.

    Clamps result to [0.0, 1.0].
    """
    degraded = original_confidence * degradation_factor
    return max(0.0, min(1.0, degraded))


# ═══════════════════════════════════════════════════════════════════════════════
# Approver / Fallback Determination
# ═══════════════════════════════════════════════════════════════════════════════

def determine_required_approver(
    matched_policies: List[EnforcementPolicy],
    context: Dict[str, Any],
) -> Optional[str]:
    """Determine who must approve based on matched policies.

    Checks policy conditions for 'required_approver' field,
    falls back to context 'default_approver'.
    """
    for pol in matched_policies:
        approver = pol.conditions.get("required_approver")
        if approver:
            return str(approver)
    return context.get("default_approver")


def determine_fallback_action(
    matched_policies: List[EnforcementPolicy],
    context: Dict[str, Any],
) -> Optional[str]:
    """Determine fallback action from matched policies or context."""
    for pol in matched_policies:
        fb = pol.conditions.get("fallback_action")
        if fb:
            return str(fb)
    return context.get("default_fallback_action")


# ═══════════════════════════════════════════════════════════════════════════════
# Execution State Computation
# ═══════════════════════════════════════════════════════════════════════════════

def compute_effective_execution_state(
    gate_results: List[Tuple[str, str, str]],
    policy_action: str,
    original_confidence: Optional[float] = None,
    matched_policies: Optional[List[EnforcementPolicy]] = None,
    context: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Compute final execution state from gate results + policy outcome.

    Gate-level escalation (deterministic):
      - Any FAIL gate -> at minimum BLOCK (unless policy overrides to REQUIRE_APPROVAL)
      - WARN gates may escalate to ESCALATE or SHADOW_ONLY depending on policy

    Returns dict with: action, is_executable, shadow_mode, effective_confidence,
                       blocking_reasons, required_approver, fallback_action
    """
    _ctx = context or {}
    _policies = matched_policies or []

    fail_gates = [g for g in gate_results if g[1] == "FAIL"]
    warn_gates = [g for g in gate_results if g[1] == "WARN"]

    blocking_reasons: List[str] = []
    action = policy_action

    # Gate-level overrides (gates are stronger than policy ALLOW)
    if fail_gates:
        for gt, _, reason in fail_gates:
            blocking_reasons.append(f"[{gt}] {reason}")
        # BLOCK unless policy explicitly says REQUIRE_APPROVAL for this type
        if action in ("ALLOW", "FALLBACK", "DEGRADE_CONFIDENCE", "SHADOW_ONLY"):
            action = "BLOCK"

    if warn_gates and action == "ALLOW":
        # Warn gates with no policy match -> ESCALATE
        for gt, _, reason in warn_gates:
            blocking_reasons.append(f"[{gt}] {reason}")
        if any(g[0] == "CALIBRATION_STATUS" for g in warn_gates):
            action = "SHADOW_ONLY"
        elif any(g[0] == "EXPLAINABILITY" for g in warn_gates):
            action = "DEGRADE_CONFIDENCE"
        elif any(g[0] in ("FINANCIAL_EXPOSURE", "CONFLICT_CHECK") for g in warn_gates):
            action = "ESCALATE"

    # Compute derived fields
    is_executable = action == "ALLOW"
    shadow_mode = action == "SHADOW_ONLY"
    effective_confidence = original_confidence

    if action == "DEGRADE_CONFIDENCE" and original_confidence is not None:
        effective_confidence = degrade_confidence(original_confidence)

    required_approver = None
    if action == "REQUIRE_APPROVAL":
        required_approver = determine_required_approver(_policies, _ctx)

    fallback_action = None
    if action == "FALLBACK":
        fallback_action = determine_fallback_action(_policies, _ctx)

    return {
        "action": action,
        "is_executable": is_executable,
        "shadow_mode": shadow_mode,
        "effective_confidence": effective_confidence,
        "blocking_reasons": blocking_reasons,
        "required_approver": required_approver,
        "fallback_action": fallback_action,
    }


# ═══════════════════════════════════════════════════════════════════════════════
# Main Entry Point
# ═══════════════════════════════════════════════════════════════════════════════

def evaluate_decision_for_enforcement(
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
    """Evaluate a decision candidate against all enforcement gates and policies.

    Returns: (EnforcementDecision, list of ExecutionGateResult)
    """
    now = datetime.now(timezone.utc)
    enforcement_id = _gen_enf_id()

    # 1. Run all gate checks
    raw_gates: List[Tuple[str, str, str]] = [
        _check_rule_lifecycle(rule_lifecycle_status),
        _check_truth_validation(truth_validation_passed, truth_critical_failure),
        _check_calibration_status(has_unresolved_calibration),
        _check_data_freshness(data_freshness_passed),
        _check_explainability(explainability_score, explainability_threshold),
        _check_financial_exposure(financial_exposure_usd, financial_threshold_usd),
        _check_conflict(has_conflicting_actions),
    ]

    # 2. Build gate result schemas
    gate_results: List[ExecutionGateResult] = []
    for gate_type, result, reason in raw_gates:
        gate_results.append(ExecutionGateResult(
            gate_id=_gen_gate_id(),
            decision_log_id=decision_log_id,
            enforcement_id=enforcement_id,
            gate_type=gate_type,
            gate_result=result,
            reason=reason,
            checked_at=now,
        ))

    # 3. Match policies against context
    matched = resolve_policy_matches(policies, context)
    policy_action, triggered_ids, policy_reasons, policy_fallback = \
        apply_enforcement_policies(matched)

    # 4. Compute final execution state
    state = compute_effective_execution_state(
        gate_results=raw_gates,
        policy_action=policy_action,
        original_confidence=original_confidence,
        matched_policies=matched,
        context=context,
    )

    # Merge policy reasons into blocking reasons
    all_reasons = state["blocking_reasons"] + policy_reasons
    # Deduplicate while preserving order
    seen = set()
    unique_reasons = []
    for r in all_reasons:
        if r not in seen:
            seen.add(r)
            unique_reasons.append(r)

    fallback = state["fallback_action"] or policy_fallback

    # 5. Build enforcement decision
    decision = EnforcementDecision(
        enforcement_id=enforcement_id,
        decision_log_id=decision_log_id,
        decision_rule_id=decision_rule_id,
        enforcement_status="EVALUATED",
        enforcement_action=state["action"],
        triggered_policy_ids=triggered_ids,
        blocking_reasons=unique_reasons,
        required_approver=state["required_approver"],
        fallback_action=fallback,
        effective_confidence=state["effective_confidence"],
        is_executable=state["is_executable"],
        shadow_mode=state["shadow_mode"],
    )

    return (decision, gate_results)
