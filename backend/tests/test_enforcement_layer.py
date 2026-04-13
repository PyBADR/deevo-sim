"""Decision Enforcement Layer — comprehensive tests.

Covers:
  - Schema validation (Phase 1)
  - Converter round-trips (Phase 3)
  - Enforcement engine: policy matching, priority resolution, gate checks (Phase 5)
  - Execution gate service: can_execute, approval, fallback, shadow (Phase 6)
  - Audit integration: enforcement audit entries, chain compatibility (Phase 7)
  - API routes: full endpoint tests (Phase 8)
  - Integration: replay/evaluation enforcement hooks (Phase 10)

All tests are deterministic. No flaky timing. No real external services.
"""

from __future__ import annotations

from datetime import datetime, timezone

import pytest

# ═══════════════════════════════════════════════════════════════════════════════
# Schema Validation Tests
# ═══════════════════════════════════════════════════════════════════════════════


class TestEnforcementPolicySchema:
    def test_valid_policy(self):
        from src.data_foundation.enforcement.schemas import EnforcementPolicy
        p = EnforcementPolicy(
            policy_id="EPOL-BLOCK-001",
            policy_name="Block Inactive Rules",
            policy_type="BLOCK_RULE",
            scope_type="GLOBAL",
            conditions={},
            action_on_match="BLOCK",
            severity="HIGH",
            priority=10,
            rationale="Inactive rules must not execute",
            created_by="system",
        )
        assert p.policy_id == "EPOL-BLOCK-001"
        assert p.is_active is True
        assert p.provenance_hash is not None

    def test_all_policy_types_valid(self):
        from src.data_foundation.enforcement.schemas import EnforcementPolicy, VALID_POLICY_TYPES
        for pt in VALID_POLICY_TYPES:
            p = EnforcementPolicy(
                policy_id=f"EPOL-{pt}",
                policy_name=f"Test {pt}",
                policy_type=pt,
                action_on_match="ALLOW",
                rationale="test",
                created_by="test",
            )
            assert p.policy_type == pt

    def test_invalid_policy_type(self):
        from src.data_foundation.enforcement.schemas import EnforcementPolicy
        with pytest.raises(ValueError, match="policy_type"):
            EnforcementPolicy(
                policy_id="X", policy_name="X", policy_type="INVALID",
                action_on_match="ALLOW", rationale="x", created_by="x",
            )

    def test_invalid_action_on_match(self):
        from src.data_foundation.enforcement.schemas import EnforcementPolicy
        with pytest.raises(ValueError, match="action_on_match"):
            EnforcementPolicy(
                policy_id="X", policy_name="X", policy_type="BLOCK_RULE",
                action_on_match="DESTROY", rationale="x", created_by="x",
            )

    def test_invalid_scope_type(self):
        from src.data_foundation.enforcement.schemas import EnforcementPolicy
        with pytest.raises(ValueError, match="scope_type"):
            EnforcementPolicy(
                policy_id="X", policy_name="X", policy_type="BLOCK_RULE",
                scope_type="NONEXISTENT", action_on_match="ALLOW",
                rationale="x", created_by="x",
            )

    def test_invalid_severity(self):
        from src.data_foundation.enforcement.schemas import EnforcementPolicy
        with pytest.raises(ValueError, match="severity"):
            EnforcementPolicy(
                policy_id="X", policy_name="X", policy_type="BLOCK_RULE",
                severity="EXTREME", action_on_match="ALLOW",
                rationale="x", created_by="x",
            )

    def test_unique_hashes(self):
        from src.data_foundation.enforcement.schemas import EnforcementPolicy
        p1 = EnforcementPolicy(
            policy_id="A", policy_name="A", policy_type="BLOCK_RULE",
            action_on_match="BLOCK", rationale="a", created_by="a",
        )
        p2 = EnforcementPolicy(
            policy_id="B", policy_name="B", policy_type="BLOCK_RULE",
            action_on_match="BLOCK", rationale="b", created_by="b",
        )
        assert p1.provenance_hash != p2.provenance_hash


class TestEnforcementDecisionSchema:
    def test_valid_decision(self):
        from src.data_foundation.enforcement.schemas import EnforcementDecision
        d = EnforcementDecision(
            enforcement_id="ENFD-test123",
            decision_log_id="DLOG-001",
            enforcement_action="BLOCK",
            blocking_reasons=["Rule inactive"],
        )
        assert d.enforcement_status == "PENDING"
        assert d.is_executable is False
        assert d.shadow_mode is False

    def test_all_actions_valid(self):
        from src.data_foundation.enforcement.schemas import EnforcementDecision, VALID_ENFORCEMENT_ACTIONS
        for action in VALID_ENFORCEMENT_ACTIONS:
            d = EnforcementDecision(
                enforcement_id=f"ENFD-{action}",
                decision_log_id="DLOG-001",
                enforcement_action=action,
            )
            assert d.enforcement_action == action

    def test_invalid_status(self):
        from src.data_foundation.enforcement.schemas import EnforcementDecision
        with pytest.raises(ValueError, match="enforcement_status"):
            EnforcementDecision(
                enforcement_id="X", decision_log_id="Y",
                enforcement_status="INVALID", enforcement_action="ALLOW",
            )

    def test_invalid_action(self):
        from src.data_foundation.enforcement.schemas import EnforcementDecision
        with pytest.raises(ValueError, match="enforcement_action"):
            EnforcementDecision(
                enforcement_id="X", decision_log_id="Y",
                enforcement_action="DESTROY",
            )


class TestExecutionGateResultSchema:
    def test_valid_gate(self):
        from src.data_foundation.enforcement.schemas import ExecutionGateResult
        g = ExecutionGateResult(
            gate_id="GATE-test123",
            decision_log_id="DLOG-001",
            enforcement_id="ENFD-001",
            gate_type="RULE_LIFECYCLE",
            gate_result="PASS",
            reason="Rule is ACTIVE",
            checked_at=datetime.now(timezone.utc),
        )
        assert g.gate_result == "PASS"

    def test_all_gate_types(self):
        from src.data_foundation.enforcement.schemas import ExecutionGateResult, VALID_GATE_TYPES
        now = datetime.now(timezone.utc)
        for gt in VALID_GATE_TYPES:
            g = ExecutionGateResult(
                gate_id=f"GATE-{gt}", decision_log_id="D", enforcement_id="E",
                gate_type=gt, gate_result="PASS", checked_at=now,
            )
            assert g.gate_type == gt

    def test_invalid_gate_type(self):
        from src.data_foundation.enforcement.schemas import ExecutionGateResult
        with pytest.raises(ValueError, match="gate_type"):
            ExecutionGateResult(
                gate_id="X", decision_log_id="D", enforcement_id="E",
                gate_type="INVALID", gate_result="PASS",
                checked_at=datetime.now(timezone.utc),
            )

    def test_invalid_gate_result(self):
        from src.data_foundation.enforcement.schemas import ExecutionGateResult
        with pytest.raises(ValueError, match="gate_result"):
            ExecutionGateResult(
                gate_id="X", decision_log_id="D", enforcement_id="E",
                gate_type="RULE_LIFECYCLE", gate_result="MAYBE",
                checked_at=datetime.now(timezone.utc),
            )


class TestApprovalRequestSchema:
    def test_valid_request(self):
        from src.data_foundation.enforcement.schemas import ApprovalRequest
        a = ApprovalRequest(
            approval_id="APPR-test123",
            decision_log_id="DLOG-001",
            enforcement_id="ENFD-001",
            requested_from="cro@bank.com",
            reason="High exposure",
            requested_at=datetime.now(timezone.utc),
        )
        assert a.approval_status == "PENDING"
        assert a.responded_at is None

    def test_all_statuses(self):
        from src.data_foundation.enforcement.schemas import ApprovalRequest, VALID_APPROVAL_STATUSES
        now = datetime.now(timezone.utc)
        for status in VALID_APPROVAL_STATUSES:
            a = ApprovalRequest(
                approval_id=f"APPR-{status}", decision_log_id="D",
                enforcement_id="E", requested_from="user",
                approval_status=status, requested_at=now,
            )
            assert a.approval_status == status

    def test_invalid_status(self):
        from src.data_foundation.enforcement.schemas import ApprovalRequest
        with pytest.raises(ValueError, match="approval_status"):
            ApprovalRequest(
                approval_id="X", decision_log_id="D", enforcement_id="E",
                requested_from="user", approval_status="INVALID",
                requested_at=datetime.now(timezone.utc),
            )


# ═══════════════════════════════════════════════════════════════════════════════
# Converter Round-Trip Tests
# ═══════════════════════════════════════════════════════════════════════════════


class TestConverters:
    def test_policy_roundtrip(self):
        from src.data_foundation.enforcement.schemas import EnforcementPolicy
        from src.data_foundation.enforcement.converters import (
            enforcement_policy_to_orm, enforcement_policy_from_orm,
        )
        original = EnforcementPolicy(
            policy_id="EPOL-RT-001", policy_name="Round Trip Test",
            policy_type="BLOCK_RULE", scope_type="COUNTRY", scope_ref="SA",
            conditions={"severity": {"operator": "gte", "value": 0.8}},
            action_on_match="BLOCK", severity="CRITICAL", priority=5,
            rationale="Test round trip", created_by="test",
        )
        orm = enforcement_policy_to_orm(original)
        assert orm.policy_id == "EPOL-RT-001"
        assert orm.scope_type == "COUNTRY"
        assert orm.scope_ref == "SA"
        assert orm.conditions == {"severity": {"operator": "gte", "value": 0.8}}

    def test_decision_roundtrip(self):
        from src.data_foundation.enforcement.schemas import EnforcementDecision
        from src.data_foundation.enforcement.converters import (
            enforcement_decision_to_orm,
        )
        original = EnforcementDecision(
            enforcement_id="ENFD-RT-001", decision_log_id="DLOG-001",
            enforcement_action="REQUIRE_APPROVAL",
            triggered_policy_ids=["POL-1", "POL-2"],
            blocking_reasons=["reason 1"],
            required_approver="cro@bank.com",
            effective_confidence=0.75,
        )
        orm = enforcement_decision_to_orm(original)
        assert orm.enforcement_id == "ENFD-RT-001"
        assert orm.triggered_policy_ids == ["POL-1", "POL-2"]
        assert orm.required_approver == "cro@bank.com"

    def test_gate_roundtrip(self):
        from src.data_foundation.enforcement.schemas import ExecutionGateResult
        from src.data_foundation.enforcement.converters import (
            execution_gate_result_to_orm,
        )
        now = datetime.now(timezone.utc)
        original = ExecutionGateResult(
            gate_id="GATE-RT-001", decision_log_id="D",
            enforcement_id="E", gate_type="RULE_LIFECYCLE",
            gate_result="FAIL", reason="Not active", checked_at=now,
        )
        orm = execution_gate_result_to_orm(original)
        assert orm.gate_id == "GATE-RT-001"
        assert orm.gate_result == "FAIL"

    def test_approval_roundtrip(self):
        from src.data_foundation.enforcement.schemas import ApprovalRequest
        from src.data_foundation.enforcement.converters import (
            approval_request_to_orm,
        )
        now = datetime.now(timezone.utc)
        original = ApprovalRequest(
            approval_id="APPR-RT-001", decision_log_id="D",
            enforcement_id="E", requested_from="admin",
            reason="High risk", requested_at=now,
        )
        orm = approval_request_to_orm(original)
        assert orm.approval_id == "APPR-RT-001"
        assert orm.approval_status == "PENDING"


# ═══════════════════════════════════════════════════════════════════════════════
# Enforcement Engine Tests
# ═══════════════════════════════════════════════════════════════════════════════


def _make_policy(**kwargs) -> "EnforcementPolicy":
    from src.data_foundation.enforcement.schemas import EnforcementPolicy
    defaults = {
        "policy_id": "EPOL-TEST",
        "policy_name": "Test Policy",
        "policy_type": "BLOCK_RULE",
        "action_on_match": "ALLOW",
        "rationale": "test",
        "created_by": "test",
        "priority": 100,
    }
    defaults.update(kwargs)
    return EnforcementPolicy(**defaults)


class TestPolicyMatching:
    def test_empty_conditions_always_match(self):
        from src.data_foundation.enforcement.enforcement_engine import resolve_policy_matches
        pol = _make_policy(conditions={})
        matched = resolve_policy_matches([pol], {"anything": "goes"})
        assert len(matched) == 1

    def test_exact_match(self):
        from src.data_foundation.enforcement.enforcement_engine import resolve_policy_matches
        pol = _make_policy(conditions={"country": "SA"})
        assert len(resolve_policy_matches([pol], {"country": "SA"})) == 1
        assert len(resolve_policy_matches([pol], {"country": "AE"})) == 0

    def test_list_membership(self):
        from src.data_foundation.enforcement.enforcement_engine import resolve_policy_matches
        pol = _make_policy(conditions={"country": ["SA", "AE", "QA"]})
        assert len(resolve_policy_matches([pol], {"country": "SA"})) == 1
        assert len(resolve_policy_matches([pol], {"country": "KW"})) == 0

    def test_threshold_gt(self):
        from src.data_foundation.enforcement.enforcement_engine import resolve_policy_matches
        pol = _make_policy(conditions={"exposure": {"operator": "gt", "value": 1000}})
        assert len(resolve_policy_matches([pol], {"exposure": 2000})) == 1
        assert len(resolve_policy_matches([pol], {"exposure": 500})) == 0

    def test_threshold_lte(self):
        from src.data_foundation.enforcement.enforcement_engine import resolve_policy_matches
        pol = _make_policy(conditions={"score": {"operator": "lte", "value": 0.5}})
        assert len(resolve_policy_matches([pol], {"score": 0.5})) == 1
        assert len(resolve_policy_matches([pol], {"score": 0.6})) == 0

    def test_multi_condition_all_must_match(self):
        from src.data_foundation.enforcement.enforcement_engine import resolve_policy_matches
        pol = _make_policy(conditions={"country": "SA", "sector": "banking"})
        assert len(resolve_policy_matches([pol], {"country": "SA", "sector": "banking"})) == 1
        assert len(resolve_policy_matches([pol], {"country": "SA", "sector": "energy"})) == 0

    def test_inactive_policy_skipped(self):
        from src.data_foundation.enforcement.enforcement_engine import resolve_policy_matches
        pol = _make_policy(is_active=False, conditions={})
        assert len(resolve_policy_matches([pol], {})) == 0

    def test_priority_ordering(self):
        from src.data_foundation.enforcement.enforcement_engine import resolve_policy_matches
        p1 = _make_policy(policy_id="A", priority=50, conditions={})
        p2 = _make_policy(policy_id="B", priority=10, conditions={})
        p3 = _make_policy(policy_id="C", priority=100, conditions={})
        matched = resolve_policy_matches([p1, p2, p3], {})
        assert [m.policy_id for m in matched] == ["B", "A", "C"]

    def test_missing_context_key_no_match(self):
        from src.data_foundation.enforcement.enforcement_engine import resolve_policy_matches
        pol = _make_policy(conditions={"missing_key": "value"})
        assert len(resolve_policy_matches([pol], {})) == 0


class TestPolicyApplication:
    def test_no_policies_allow(self):
        from src.data_foundation.enforcement.enforcement_engine import apply_enforcement_policies
        action, ids, reasons, fb = apply_enforcement_policies([])
        assert action == "ALLOW"
        assert ids == []

    def test_block_wins_over_allow(self):
        from src.data_foundation.enforcement.enforcement_engine import apply_enforcement_policies
        p1 = _make_policy(policy_id="A", action_on_match="ALLOW")
        p2 = _make_policy(policy_id="B", action_on_match="BLOCK")
        action, ids, reasons, _ = apply_enforcement_policies([p1, p2])
        assert action == "BLOCK"
        assert "B" in ids

    def test_require_approval_wins_over_escalate(self):
        from src.data_foundation.enforcement.enforcement_engine import apply_enforcement_policies
        p1 = _make_policy(policy_id="A", action_on_match="ESCALATE")
        p2 = _make_policy(policy_id="B", action_on_match="REQUIRE_APPROVAL")
        action, _, _, _ = apply_enforcement_policies([p1, p2])
        assert action == "REQUIRE_APPROVAL"

    def test_block_wins_over_everything(self):
        from src.data_foundation.enforcement.enforcement_engine import apply_enforcement_policies
        policies = [
            _make_policy(policy_id="A", action_on_match="ALLOW"),
            _make_policy(policy_id="B", action_on_match="REQUIRE_APPROVAL"),
            _make_policy(policy_id="C", action_on_match="BLOCK"),
            _make_policy(policy_id="D", action_on_match="SHADOW_ONLY"),
        ]
        action, _, _, _ = apply_enforcement_policies(policies)
        assert action == "BLOCK"


class TestGateChecks:
    def test_rule_lifecycle_active_pass(self):
        from src.data_foundation.enforcement.enforcement_engine import _check_rule_lifecycle
        gt, result, _ = _check_rule_lifecycle("ACTIVE")
        assert result == "PASS"

    def test_rule_lifecycle_inactive_fail(self):
        from src.data_foundation.enforcement.enforcement_engine import _check_rule_lifecycle
        gt, result, _ = _check_rule_lifecycle("DRAFT")
        assert result == "FAIL"

    def test_rule_lifecycle_none_skip(self):
        from src.data_foundation.enforcement.enforcement_engine import _check_rule_lifecycle
        _, result, _ = _check_rule_lifecycle(None)
        assert result == "SKIP"

    def test_truth_validation_critical_fail(self):
        from src.data_foundation.enforcement.enforcement_engine import _check_truth_validation
        _, result, _ = _check_truth_validation(False, truth_critical_failure=True)
        assert result == "FAIL"

    def test_truth_validation_noncritical_warn(self):
        from src.data_foundation.enforcement.enforcement_engine import _check_truth_validation
        _, result, _ = _check_truth_validation(False, truth_critical_failure=False)
        assert result == "WARN"

    def test_truth_validation_pass(self):
        from src.data_foundation.enforcement.enforcement_engine import _check_truth_validation
        _, result, _ = _check_truth_validation(True)
        assert result == "PASS"

    def test_calibration_unresolved_warn(self):
        from src.data_foundation.enforcement.enforcement_engine import _check_calibration_status
        _, result, _ = _check_calibration_status(True)
        assert result == "WARN"

    def test_calibration_resolved_pass(self):
        from src.data_foundation.enforcement.enforcement_engine import _check_calibration_status
        _, result, _ = _check_calibration_status(False)
        assert result == "PASS"

    def test_data_freshness_fail(self):
        from src.data_foundation.enforcement.enforcement_engine import _check_data_freshness
        _, result, _ = _check_data_freshness(False)
        assert result == "FAIL"

    def test_explainability_below_threshold_warn(self):
        from src.data_foundation.enforcement.enforcement_engine import _check_explainability
        _, result, _ = _check_explainability(0.3, threshold=0.5)
        assert result == "WARN"

    def test_explainability_above_threshold_pass(self):
        from src.data_foundation.enforcement.enforcement_engine import _check_explainability
        _, result, _ = _check_explainability(0.8, threshold=0.5)
        assert result == "PASS"

    def test_financial_exposure_exceeds_warn(self):
        from src.data_foundation.enforcement.enforcement_engine import _check_financial_exposure
        _, result, _ = _check_financial_exposure(2e9, threshold_usd=1e9)
        assert result == "WARN"

    def test_conflict_detected_warn(self):
        from src.data_foundation.enforcement.enforcement_engine import _check_conflict
        _, result, _ = _check_conflict(True)
        assert result == "WARN"


class TestConfidenceDegradation:
    def test_default_degradation(self):
        from src.data_foundation.enforcement.enforcement_engine import degrade_confidence
        assert degrade_confidence(1.0) == 0.5

    def test_custom_factor(self):
        from src.data_foundation.enforcement.enforcement_engine import degrade_confidence
        assert degrade_confidence(0.8, 0.25) == pytest.approx(0.2)

    def test_clamp_to_zero(self):
        from src.data_foundation.enforcement.enforcement_engine import degrade_confidence
        assert degrade_confidence(0.0) == 0.0


class TestFullEvaluation:
    def test_all_pass_allow(self):
        from src.data_foundation.enforcement.enforcement_engine import evaluate_decision_for_enforcement
        decision, gates = evaluate_decision_for_enforcement(
            decision_log_id="DLOG-001",
            policies=[],
            context={},
            rule_lifecycle_status="ACTIVE",
            truth_validation_passed=True,
            data_freshness_passed=True,
            has_unresolved_calibration=False,
            explainability_score=0.9,
            has_conflicting_actions=False,
        )
        assert decision.enforcement_action == "ALLOW"
        assert decision.is_executable is True
        assert decision.shadow_mode is False

    def test_inactive_rule_blocks(self):
        from src.data_foundation.enforcement.enforcement_engine import evaluate_decision_for_enforcement
        decision, gates = evaluate_decision_for_enforcement(
            decision_log_id="DLOG-002",
            policies=[],
            context={},
            rule_lifecycle_status="DRAFT",
        )
        assert decision.enforcement_action == "BLOCK"
        assert decision.is_executable is False

    def test_data_freshness_fail_blocks(self):
        from src.data_foundation.enforcement.enforcement_engine import evaluate_decision_for_enforcement
        decision, _ = evaluate_decision_for_enforcement(
            decision_log_id="DLOG-003",
            policies=[],
            context={},
            data_freshness_passed=False,
        )
        assert decision.enforcement_action == "BLOCK"

    def test_critical_truth_failure_blocks(self):
        from src.data_foundation.enforcement.enforcement_engine import evaluate_decision_for_enforcement
        decision, _ = evaluate_decision_for_enforcement(
            decision_log_id="DLOG-004",
            policies=[],
            context={},
            truth_validation_passed=False,
            truth_critical_failure=True,
        )
        assert decision.enforcement_action == "BLOCK"

    def test_unresolved_calibration_shadow(self):
        from src.data_foundation.enforcement.enforcement_engine import evaluate_decision_for_enforcement
        decision, _ = evaluate_decision_for_enforcement(
            decision_log_id="DLOG-005",
            policies=[],
            context={},
            has_unresolved_calibration=True,
        )
        assert decision.enforcement_action == "SHADOW_ONLY"
        assert decision.shadow_mode is True

    def test_low_explainability_degrades(self):
        from src.data_foundation.enforcement.enforcement_engine import evaluate_decision_for_enforcement
        decision, _ = evaluate_decision_for_enforcement(
            decision_log_id="DLOG-006",
            policies=[],
            context={},
            explainability_score=0.2,
            original_confidence=0.9,
        )
        assert decision.enforcement_action == "DEGRADE_CONFIDENCE"
        assert decision.effective_confidence == pytest.approx(0.45)

    def test_financial_exposure_escalates(self):
        from src.data_foundation.enforcement.enforcement_engine import evaluate_decision_for_enforcement
        decision, _ = evaluate_decision_for_enforcement(
            decision_log_id="DLOG-007",
            policies=[],
            context={},
            financial_exposure_usd=5e9,
            financial_threshold_usd=1e9,
        )
        assert decision.enforcement_action == "ESCALATE"

    def test_conflicting_actions_escalate(self):
        from src.data_foundation.enforcement.enforcement_engine import evaluate_decision_for_enforcement
        decision, _ = evaluate_decision_for_enforcement(
            decision_log_id="DLOG-008",
            policies=[],
            context={},
            has_conflicting_actions=True,
        )
        assert decision.enforcement_action == "ESCALATE"

    def test_policy_block_overrides_gate_pass(self):
        from src.data_foundation.enforcement.enforcement_engine import evaluate_decision_for_enforcement
        pol = _make_policy(action_on_match="BLOCK", conditions={})
        decision, _ = evaluate_decision_for_enforcement(
            decision_log_id="DLOG-009",
            policies=[pol],
            context={},
            rule_lifecycle_status="ACTIVE",
            truth_validation_passed=True,
        )
        assert decision.enforcement_action == "BLOCK"
        assert pol.policy_id in decision.triggered_policy_ids

    def test_gate_fail_blocks_despite_allow_policy(self):
        from src.data_foundation.enforcement.enforcement_engine import evaluate_decision_for_enforcement
        pol = _make_policy(action_on_match="ALLOW", conditions={})
        decision, _ = evaluate_decision_for_enforcement(
            decision_log_id="DLOG-010",
            policies=[pol],
            context={},
            rule_lifecycle_status="RETIRED",
        )
        assert decision.enforcement_action == "BLOCK"

    def test_require_approval_with_approver(self):
        from src.data_foundation.enforcement.enforcement_engine import evaluate_decision_for_enforcement
        pol = _make_policy(
            action_on_match="REQUIRE_APPROVAL",
            conditions={"required_approver": "cro@bank.com"},
        )
        decision, _ = evaluate_decision_for_enforcement(
            decision_log_id="DLOG-011",
            policies=[pol],
            context={"required_approver": "cro@bank.com"},
        )
        assert decision.enforcement_action == "REQUIRE_APPROVAL"
        assert decision.required_approver == "cro@bank.com"

    def test_gates_produce_correct_count(self):
        from src.data_foundation.enforcement.enforcement_engine import evaluate_decision_for_enforcement
        _, gates = evaluate_decision_for_enforcement(
            decision_log_id="DLOG-012",
            policies=[],
            context={},
            rule_lifecycle_status="ACTIVE",
            truth_validation_passed=True,
            has_unresolved_calibration=False,
            data_freshness_passed=True,
            explainability_score=0.9,
            financial_exposure_usd=100.0,
            has_conflicting_actions=False,
        )
        assert len(gates) == 7  # One per gate type


# ═══════════════════════════════════════════════════════════════════════════════
# Execution Gate Service Tests
# ═══════════════════════════════════════════════════════════════════════════════


class TestExecutionGateService:
    def test_can_execute_returns_decision_and_gates(self):
        from src.data_foundation.enforcement.execution_gate_service import can_execute_decision
        decision, gates = can_execute_decision(
            decision_log_id="SVC-001",
            policies=[],
            context={},
            rule_lifecycle_status="ACTIVE",
        )
        assert decision.decision_log_id == "SVC-001"
        assert len(gates) > 0

    def test_persist_and_retrieve(self):
        from src.data_foundation.enforcement.execution_gate_service import (
            can_execute_decision, persist_enforcement_outcome,
            get_enforcement_decision, get_enforcement_gates,
        )
        decision, gates = can_execute_decision(
            decision_log_id="SVC-002",
            policies=[],
            context={},
        )
        persist_enforcement_outcome(decision, gates)
        retrieved = get_enforcement_decision(decision.enforcement_id)
        assert retrieved is not None
        assert retrieved.enforcement_id == decision.enforcement_id
        retrieved_gates = get_enforcement_gates(decision.enforcement_id)
        assert len(retrieved_gates) == len(gates)

    def test_lookup_by_decision_log(self):
        from src.data_foundation.enforcement.execution_gate_service import (
            can_execute_decision, persist_enforcement_outcome,
            get_enforcement_by_decision_log,
        )
        decision, gates = can_execute_decision(
            decision_log_id="SVC-003",
            policies=[],
            context={},
        )
        persist_enforcement_outcome(decision, gates)
        found = get_enforcement_by_decision_log("SVC-003")
        assert found is not None
        assert found.enforcement_id == decision.enforcement_id

    def test_create_gate_result(self):
        from src.data_foundation.enforcement.execution_gate_service import create_gate_result
        g = create_gate_result(
            decision_log_id="D", enforcement_id="E",
            gate_type="RULE_LIFECYCLE", gate_result="PASS",
            reason="Active",
        )
        assert g.gate_type == "RULE_LIFECYCLE"
        assert g.gate_result == "PASS"

    def test_require_manual_approval(self):
        from src.data_foundation.enforcement.execution_gate_service import require_manual_approval
        a = require_manual_approval(
            decision_log_id="D", enforcement_id="E",
            requested_from="cro@bank.com", reason="High exposure",
        )
        assert a.approval_status == "PENDING"
        assert a.requested_from == "cro@bank.com"

    def test_convert_to_fallback(self):
        from src.data_foundation.enforcement.schemas import EnforcementDecision
        from src.data_foundation.enforcement.execution_gate_service import convert_to_fallback
        original = EnforcementDecision(
            enforcement_id="E1", decision_log_id="D1",
            enforcement_action="BLOCK",
        )
        fb = convert_to_fallback(original, "NOTIFY_ONLY")
        assert fb.enforcement_action == "FALLBACK"
        assert fb.fallback_action == "NOTIFY_ONLY"
        assert fb.is_executable is False

    def test_mark_shadow_only(self):
        from src.data_foundation.enforcement.schemas import EnforcementDecision
        from src.data_foundation.enforcement.execution_gate_service import mark_shadow_only
        original = EnforcementDecision(
            enforcement_id="E2", decision_log_id="D2",
            enforcement_action="ALLOW",
        )
        shadow = mark_shadow_only(original)
        assert shadow.enforcement_action == "SHADOW_ONLY"
        assert shadow.shadow_mode is True
        assert shadow.is_executable is False

    def test_auto_approval_on_require_approval(self):
        from src.data_foundation.enforcement.execution_gate_service import (
            can_execute_decision, get_pending_approvals,
        )
        pol = _make_policy(
            action_on_match="REQUIRE_APPROVAL",
            conditions={"required_approver": "approver@test.com"},
        )
        decision, _ = can_execute_decision(
            decision_log_id="SVC-APPR-001",
            policies=[pol],
            context={"required_approver": "approver@test.com"},
        )
        assert decision.enforcement_action == "REQUIRE_APPROVAL"
        pending = get_pending_approvals()
        found = [a for a in pending if a.decision_log_id == "SVC-APPR-001"]
        assert len(found) >= 1


# ═══════════════════════════════════════════════════════════════════════════════
# Audit Integration Tests
# ═══════════════════════════════════════════════════════════════════════════════


class TestAuditIntegration:
    def test_enforcement_policy_created_audit(self):
        from src.data_foundation.enforcement.enforcement_audit import (
            audit_enforcement_policy_created,
        )
        entry = audit_enforcement_policy_created("EPOL-001", "admin", {"type": "BLOCK_RULE"})
        assert entry.event_type == "ENFORCEMENT_POLICY_CREATED"
        assert entry.subject_type == "ENFORCEMENT_POLICY"
        assert entry.subject_id == "EPOL-001"
        assert entry.audit_hash is not None

    def test_enforcement_evaluated_audit(self):
        from src.data_foundation.enforcement.enforcement_audit import audit_enforcement_evaluated
        entry = audit_enforcement_evaluated("ENFD-001", "system", {"action": "BLOCK"})
        assert entry.event_type == "ENFORCEMENT_EVALUATED"
        assert entry.subject_type == "ENFORCEMENT_DECISION"

    def test_decision_blocked_audit(self):
        from src.data_foundation.enforcement.enforcement_audit import audit_decision_blocked
        entry = audit_decision_blocked("ENFD-002", "system", {"reasons": ["inactive rule"]})
        assert entry.event_type == "DECISION_BLOCKED"

    def test_approval_required_audit(self):
        from src.data_foundation.enforcement.enforcement_audit import audit_approval_required
        entry = audit_approval_required("ENFD-003", "system", {"approver": "cro"})
        assert entry.event_type == "APPROVAL_REQUIRED"

    def test_fallback_applied_audit(self):
        from src.data_foundation.enforcement.enforcement_audit import audit_fallback_applied
        entry = audit_fallback_applied("ENFD-004", "system")
        assert entry.event_type == "FALLBACK_APPLIED"

    def test_shadow_mode_activated_audit(self):
        from src.data_foundation.enforcement.enforcement_audit import audit_shadow_mode_activated
        entry = audit_shadow_mode_activated("ENFD-005", "system")
        assert entry.event_type == "SHADOW_MODE_ACTIVATED"

    def test_audit_chain_compatibility(self):
        from src.data_foundation.governance.governance_audit import verify_chain
        from src.data_foundation.enforcement.enforcement_audit import (
            audit_enforcement_policy_created,
            audit_enforcement_evaluated,
            audit_decision_blocked,
        )
        e1 = audit_enforcement_policy_created("P1", "admin")
        e2 = audit_enforcement_evaluated("E1", "system", previous_hash=e1.audit_hash)
        e3 = audit_decision_blocked("E2", "system", previous_hash=e2.audit_hash)
        result = verify_chain([e1, e2, e3])
        assert result["valid"] is True
        assert result["verified"] == 3
        assert result["tampered"] == []
        assert result["chain_breaks"] == []

    def test_enforcement_types_registered(self):
        from src.data_foundation.governance.schemas import (
            VALID_AUDIT_EVENT_TYPES, VALID_AUDIT_SUBJECT_TYPES,
        )
        # Import enforcement_audit to trigger registration
        import src.data_foundation.enforcement.enforcement_audit  # noqa: F401
        assert "ENFORCEMENT_POLICY_CREATED" in VALID_AUDIT_EVENT_TYPES
        assert "ENFORCEMENT_EVALUATED" in VALID_AUDIT_EVENT_TYPES
        assert "DECISION_BLOCKED" in VALID_AUDIT_EVENT_TYPES
        assert "ENFORCEMENT_POLICY" in VALID_AUDIT_SUBJECT_TYPES
        assert "ENFORCEMENT_DECISION" in VALID_AUDIT_SUBJECT_TYPES


# ═══════════════════════════════════════════════════════════════════════════════
# API Route Tests
# ═══════════════════════════════════════════════════════════════════════════════


class TestApiRoutes:
    @pytest.fixture(autouse=True)
    def client(self):
        from fastapi.testclient import TestClient
        from src.data_foundation.enforcement.api import router, _policy_store
        from fastapi import FastAPI
        _policy_store.clear()
        app = FastAPI()
        app.include_router(router, prefix="/api/v1")
        self.client = TestClient(app)
        return self.client

    def test_create_policy(self):
        resp = self.client.post("/api/v1/foundation/enforcement/policies", json={
            "policy_id": "EPOL-API-001",
            "policy_name": "API Test Block",
            "policy_type": "BLOCK_RULE",
            "action_on_match": "BLOCK",
            "rationale": "test",
            "created_by": "test",
        })
        assert resp.status_code == 201
        data = resp.json()
        assert data["policy_id"] == "EPOL-API-001"

    def test_list_policies(self):
        # Create first
        self.client.post("/api/v1/foundation/enforcement/policies", json={
            "policy_id": "EPOL-API-LIST",
            "policy_name": "List Test",
            "policy_type": "APPROVAL_GATE",
            "action_on_match": "REQUIRE_APPROVAL",
            "rationale": "test",
            "created_by": "test",
        })
        resp = self.client.get("/api/v1/foundation/enforcement/policies")
        assert resp.status_code == 200
        assert resp.json()["count"] >= 1

    def test_get_policy(self):
        self.client.post("/api/v1/foundation/enforcement/policies", json={
            "policy_id": "EPOL-API-GET",
            "policy_name": "Get Test",
            "policy_type": "BLOCK_RULE",
            "action_on_match": "BLOCK",
            "rationale": "test",
            "created_by": "test",
        })
        resp = self.client.get("/api/v1/foundation/enforcement/policies/EPOL-API-GET")
        assert resp.status_code == 200
        assert resp.json()["policy_id"] == "EPOL-API-GET"

    def test_get_policy_not_found(self):
        resp = self.client.get("/api/v1/foundation/enforcement/policies/NONEXISTENT")
        assert resp.status_code == 404

    def test_evaluate_enforcement(self):
        # Create a policy first
        self.client.post("/api/v1/foundation/enforcement/policies", json={
            "policy_id": "EPOL-API-EVAL",
            "policy_name": "Eval Test",
            "policy_type": "BLOCK_RULE",
            "conditions": {},
            "action_on_match": "ALLOW",
            "rationale": "test",
            "created_by": "test",
        })
        resp = self.client.post("/api/v1/foundation/enforcement/evaluate/DLOG-EVAL-001", json={
            "rule_lifecycle_status": "ACTIVE",
            "truth_validation_passed": True,
            "data_freshness_passed": True,
            "context": {},
        })
        assert resp.status_code == 200
        data = resp.json()
        assert "enforcement" in data
        assert "gates" in data
        assert data["enforcement"]["enforcement_action"] == "ALLOW"

    def test_evaluate_blocked(self):
        self.client.post("/api/v1/foundation/enforcement/policies", json={
            "policy_id": "EPOL-API-BLK",
            "policy_name": "Block Test",
            "policy_type": "BLOCK_RULE",
            "conditions": {},
            "action_on_match": "BLOCK",
            "rationale": "always block",
            "created_by": "test",
        })
        resp = self.client.post("/api/v1/foundation/enforcement/evaluate/DLOG-BLK-001", json={
            "context": {},
        })
        assert resp.status_code == 200
        assert resp.json()["enforcement"]["enforcement_action"] == "BLOCK"

    def test_get_enforcement_decision(self):
        resp = self.client.post("/api/v1/foundation/enforcement/evaluate/DLOG-LOOKUP-001", json={
            "context": {},
        })
        enf_id = resp.json()["enforcement"]["enforcement_id"]
        resp2 = self.client.get(f"/api/v1/foundation/enforcement/decisions/{enf_id}")
        assert resp2.status_code == 200

    def test_get_enforcement_by_decision_log(self):
        self.client.post("/api/v1/foundation/enforcement/evaluate/DLOG-BYDEC-001", json={
            "context": {},
        })
        resp = self.client.get("/api/v1/foundation/enforcement/decisions/by-decision/DLOG-BYDEC-001")
        assert resp.status_code == 200

    def test_get_gates_by_decision(self):
        self.client.post("/api/v1/foundation/enforcement/evaluate/DLOG-GATES-001", json={
            "context": {},
        })
        resp = self.client.get("/api/v1/foundation/enforcement/gates/by-decision/DLOG-GATES-001")
        assert resp.status_code == 200
        assert resp.json()["count"] >= 1

    def test_pending_approvals(self):
        resp = self.client.get("/api/v1/foundation/enforcement/approvals/pending")
        assert resp.status_code == 200

    def test_get_approval_not_found(self):
        resp = self.client.get("/api/v1/foundation/enforcement/approvals/NONEXISTENT")
        assert resp.status_code == 404


# ═══════════════════════════════════════════════════════════════════════════════
# Integration Tests (Replay/Evaluation)
# ═══════════════════════════════════════════════════════════════════════════════


class TestReplayIntegration:
    def test_replay_enforcement_all_clear(self):
        from src.data_foundation.enforcement.integration import evaluate_replay_enforcement
        result = evaluate_replay_enforcement(
            decision_log_id="REPLAY-001",
            policies=[],
            rule_lifecycle_status="ACTIVE",
            data_freshness_passed=True,
            original_confidence=0.85,
        )
        assert result["enforcement_action"] == "ALLOW"
        assert result["is_executable"] is True
        assert result["gate_summary"]["failed"] == 0

    def test_replay_enforcement_blocked(self):
        from src.data_foundation.enforcement.integration import evaluate_replay_enforcement
        result = evaluate_replay_enforcement(
            decision_log_id="REPLAY-002",
            policies=[],
            rule_lifecycle_status="RETIRED",
        )
        assert result["enforcement_action"] == "BLOCK"
        assert result["is_executable"] is False
        assert result["gate_summary"]["failed"] >= 1

    def test_replay_enforcement_with_policy(self):
        from src.data_foundation.enforcement.integration import evaluate_replay_enforcement
        pol = _make_policy(
            action_on_match="SHADOW_ONLY",
            conditions={"country": "SA"},
        )
        result = evaluate_replay_enforcement(
            decision_log_id="REPLAY-003",
            policies=[pol],
            context={"country": "SA"},
        )
        assert result["enforcement_action"] == "SHADOW_ONLY"
        assert result["shadow_mode"] is True
        assert pol.policy_id in result["triggered_policy_ids"]


class TestEvaluationIntegration:
    def test_decision_enforcement_allow(self):
        from src.data_foundation.enforcement.integration import evaluate_decision_enforcement
        decision, gates = evaluate_decision_enforcement(
            decision_log_id="EVAL-001",
            policies=[],
            rule_lifecycle_status="ACTIVE",
            truth_validation_passed=True,
            data_freshness_passed=True,
            explainability_score=0.9,
            original_confidence=0.85,
        )
        assert decision.enforcement_action == "ALLOW"
        assert decision.is_executable is True

    def test_decision_enforcement_block_on_failure(self):
        from src.data_foundation.enforcement.integration import evaluate_decision_enforcement
        decision, _ = evaluate_decision_enforcement(
            decision_log_id="EVAL-002",
            policies=[],
            truth_critical_failure=True,
            truth_validation_passed=False,
        )
        assert decision.enforcement_action == "BLOCK"

    def test_build_enforcement_summary(self):
        from src.data_foundation.enforcement.integration import (
            evaluate_decision_enforcement, build_enforcement_summary,
        )
        decision, gates = evaluate_decision_enforcement(
            decision_log_id="EVAL-003",
            policies=[],
            rule_lifecycle_status="ACTIVE",
        )
        summary = build_enforcement_summary(decision, gates)
        assert "enforcement_id" in summary
        assert "gate_summary" in summary
        assert summary["gate_summary"]["total"] == len(gates)


# ═══════════════════════════════════════════════════════════════════════════════
# Package Import Tests
# ═══════════════════════════════════════════════════════════════════════════════


class TestPackageImports:
    def test_import_schemas(self):
        from src.data_foundation.enforcement.schemas import (
            EnforcementPolicy, EnforcementDecision,
            ExecutionGateResult, ApprovalRequest,
        )
        assert EnforcementPolicy is not None

    def test_import_orm(self):
        from src.data_foundation.enforcement.orm_models import (
            EnforcementPolicyORM, EnforcementDecisionORM,
            ExecutionGateResultORM, ApprovalRequestORM,
        )
        assert EnforcementPolicyORM.__tablename__ == "df_enf_policies"

    def test_import_converters(self):
        from src.data_foundation.enforcement.converters import (
            enforcement_policy_to_orm, enforcement_policy_from_orm,
            enforcement_decision_to_orm, enforcement_decision_from_orm,
            execution_gate_result_to_orm, execution_gate_result_from_orm,
            approval_request_to_orm, approval_request_from_orm,
        )
        assert callable(enforcement_policy_to_orm)

    def test_import_repositories(self):
        from src.data_foundation.enforcement.repositories import (
            EnforcementPolicyRepository, EnforcementDecisionRepository,
            ExecutionGateRepository, ApprovalRequestRepository,
        )
        assert EnforcementPolicyRepository.pk_field == "policy_id"

    def test_import_engine(self):
        from src.data_foundation.enforcement.enforcement_engine import (
            evaluate_decision_for_enforcement,
            resolve_policy_matches,
            apply_enforcement_policies,
            degrade_confidence,
        )
        assert callable(evaluate_decision_for_enforcement)

    def test_import_package_root(self):
        from src.data_foundation.enforcement import (
            EnforcementPolicy, EnforcementDecision,
            evaluate_decision_for_enforcement,
            can_execute_decision,
            audit_enforcement_evaluated,
        )
        assert callable(can_execute_decision)
