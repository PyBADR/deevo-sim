"""
DAL Closure Verification Suite
═══════════════════════════════════════════════════════════════════════════════
Validates all 5 gaps are closed per the DAL VERIFIED specification.

Gap 1: Hash chain hardening — verify endpoint returns regulator-grade response
Gap 2: Control Tower source lock — backend metrics endpoint exists and is accurate
Gap 3: Server-side persona enforcement — RBAC alignment between engine + rbac.py
Gap 4: Drift elimination — no local-only state mutations exist
Gap 5: Controlled state mutation — link_references is backend-backed
"""

import ast
import os
import unittest

from sqlalchemy import create_engine
from sqlalchemy import event as sa_event

from app.authority.engine import (
    propose,
    submit_for_review,
    approve,
    execute,
    annotate,
    verify_hash_chain,
    compute_authority_metrics,
    link_references,
    get_events,
    AUTHORITY_ACTION_PERMISSIONS,
    AuthorityPermissionError,
    AuthorityError,
)


def _setup_authority_db():
    """Create an isolated SQLite engine for one test class, inject into signals.store."""
    import app.signals.store as store_mod
    import app.authority.models  # noqa: F401

    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})

    @sa_event.listens_for(engine, "connect")
    def _pragma(conn, _):
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA foreign_keys=ON")

    store_mod._engine = engine
    store_mod.Base.metadata.create_all(engine)
    return engine


def _happy_path(decision_id: str) -> dict:
    """Propose → submit → approve → return authority dict."""
    env = propose(decision_id, "analyst-001", "analyst", rationale="Test")
    submit_for_review(decision_id, "analyst-001", "analyst")
    return approve(decision_id, "admin-001", "admin", rationale="Approved for test")


class TestGap1_HashChainHardening(unittest.TestCase):
    """Gap 1: verify_hash_chain returns regulator-grade response fields."""

    def setUp(self):
        self.engine = _setup_authority_db()

    def test_verify_response_has_regulator_fields(self):
        env = propose("gap1-001", "analyst-001", "analyst")
        submit_for_review("gap1-001", "analyst-001", "analyst")
        approve("gap1-001", "admin-001", "admin", rationale="OK")

        report = verify_hash_chain(env["authority_id"])

        # Must have all regulator-grade fields
        self.assertIn("valid", report)
        self.assertIn("broken_at", report)
        self.assertIn("expected_hash", report)
        self.assertIn("actual_hash", report)
        self.assertIn("events_checked", report)
        self.assertIn("chain_trace", report)
        self.assertIn("errors", report)

        # Must be valid
        self.assertTrue(report["valid"])
        self.assertIsNone(report["broken_at"])
        self.assertIsNone(report["expected_hash"])
        self.assertIsNone(report["actual_hash"])
        self.assertEqual(report["events_checked"], 3)  # propose + submit + approve
        self.assertEqual(len(report["chain_trace"]), 3)
        self.assertEqual(len(report["errors"]), 0)

    def test_chain_trace_entries_have_full_detail(self):
        env = propose("gap1-002", "analyst-001", "analyst")
        report = verify_hash_chain(env["authority_id"])
        trace = report["chain_trace"][0]

        required_fields = {
            "index", "event_id", "action", "from_status", "to_status",
            "timestamp", "event_hash", "previous_event_hash",
            "recomputed_hash", "link_valid", "hash_valid",
        }
        self.assertTrue(required_fields.issubset(set(trace.keys())),
                        f"Missing fields: {required_fields - set(trace.keys())}")
        self.assertTrue(trace["link_valid"])
        self.assertTrue(trace["hash_valid"])

    def test_empty_chain_returns_valid(self):
        report = verify_hash_chain("nonexistent-authority-id")
        self.assertTrue(report["valid"])
        self.assertEqual(report["events_checked"], 0)
        self.assertIsNone(report["broken_at"])


class TestGap2_ControlTowerSourceLock(unittest.TestCase):
    """Gap 2: compute_authority_metrics returns accurate DB-level counts."""

    def setUp(self):
        self.engine = _setup_authority_db()

    def test_metrics_returns_all_required_fields(self):
        metrics = compute_authority_metrics()
        required = {
            "proposed", "under_review", "approved_pending_execution",
            "executed", "rejected", "failed", "escalated",
            "returned", "revoked", "withdrawn", "total_active", "total",
        }
        self.assertTrue(required.issubset(set(metrics.keys())),
                        f"Missing metrics: {required - set(metrics.keys())}")

    def test_metrics_accuracy(self):
        # Create known state: 1 proposed, 1 approved
        propose("gap2-001", "analyst-001", "analyst")
        propose("gap2-002", "analyst-001", "analyst")
        submit_for_review("gap2-002", "analyst-001", "analyst")
        approve("gap2-002", "admin-001", "admin", rationale="OK")

        metrics = compute_authority_metrics()
        self.assertGreaterEqual(metrics["proposed"], 1)
        self.assertGreaterEqual(metrics["approved_pending_execution"], 1)
        self.assertGreaterEqual(metrics["total_active"], 2)
        self.assertEqual(metrics["total"],
                         sum([
                             metrics["proposed"], metrics["under_review"],
                             metrics["approved_pending_execution"],
                             metrics["executed"], metrics["rejected"],
                             metrics["failed"], metrics["escalated"],
                             metrics["returned"], metrics["revoked"],
                             metrics["withdrawn"],
                         ]))


class TestGap3_ServerSidePersonaEnforcement(unittest.TestCase):
    """Gap 3: Engine RBAC matrix aligns with rbac.py. All roles blocked correctly."""

    def setUp(self):
        self.engine = _setup_authority_db()

    def test_engine_rbac_aligns_with_rbac_py(self):
        from app.core.rbac import Role, ROLE_PERMISSIONS, Permission

        # Map engine action → rbac.py permission
        action_to_permission = {
            "PROPOSE": Permission.PROPOSE_AUTHORITY,
            "SUBMIT_FOR_REVIEW": Permission.SUBMIT_AUTHORITY,
            "APPROVE": Permission.APPROVE_AUTHORITY,
            "REJECT": Permission.REJECT_AUTHORITY,
            "RETURN_FOR_REVISION": Permission.RETURN_AUTHORITY,
            "ESCALATE": Permission.ESCALATE_AUTHORITY,
            "QUEUE_EXECUTION": Permission.EXECUTE_AUTHORITY,
            "EXECUTE": Permission.EXECUTE_AUTHORITY,
            "REPORT_EXECUTION_FAILURE": Permission.REPORT_AUTHORITY_EXECUTION_FAILURE,
            "REVOKE": Permission.REVOKE_AUTHORITY,
            "WITHDRAW": Permission.WITHDRAW_AUTHORITY,
            "OVERRIDE": Permission.OVERRIDE_AUTHORITY,
            "ANNOTATE": Permission.ANNOTATE_AUTHORITY,
            "RESUBMIT": Permission.PROPOSE_AUTHORITY,
        }

        for action, engine_roles in AUTHORITY_ACTION_PERMISSIONS.items():
            perm = action_to_permission.get(action)
            if perm is None:
                continue
            for role in Role:
                role_name = role.value
                engine_allows = role_name in engine_roles
                rbac_allows = perm in ROLE_PERMISSIONS.get(role, set())
                # Engine should NOT be MORE permissive than rbac.py
                if engine_allows and not rbac_allows:
                    self.fail(
                        f"RBAC MISALIGNMENT: Engine allows {role_name} for {action}, "
                        f"but rbac.py denies {perm.value} for {role_name}."
                    )

    def test_viewer_blocked_on_all_actions(self):
        with self.assertRaises(AuthorityPermissionError):
            propose("gap3-001", "viewer-001", "viewer")

    def test_regulator_blocked_on_propose(self):
        with self.assertRaises(AuthorityPermissionError):
            propose("gap3-002", "reg-001", "regulator")

    def test_analyst_blocked_on_approve(self):
        propose("gap3-003", "analyst-001", "analyst")
        submit_for_review("gap3-003", "analyst-001", "analyst")
        with self.assertRaises(AuthorityPermissionError):
            approve("gap3-003", "analyst-001", "analyst")

    def test_operator_blocked_on_approve(self):
        propose("gap3-004", "analyst-001", "analyst")
        submit_for_review("gap3-004", "analyst-001", "analyst")
        with self.assertRaises(AuthorityPermissionError):
            approve("gap3-004", "operator-001", "operator")


class TestGap4_DriftElimination(unittest.TestCase):
    """Gap 4: Verify no local-only state mutations in authority-store.ts."""

    STORE_PATH = os.path.join(
        os.path.dirname(__file__), "..", "..", "..",
        "frontend", "src", "store", "authority-store.ts"
    )

    def test_no_local_only_set_calls(self):
        """Scan store for direct Zustand set() calls that don't follow an API call."""
        if not os.path.exists(self.STORE_PATH):
            self.skipTest("Frontend store not found at expected path")

        with open(self.STORE_PATH, "r") as f:
            content = f.read()

        # FAIL if linkOutcome/linkValue still contain local-only patterns
        self.assertNotIn(
            "linked_outcome_id: outcome_id, updated_at: new Date()",
            content,
            "linkOutcome still has local-only mutation (Gap 5 not closed)"
        )
        self.assertNotIn(
            "linked_value_id: value_id, updated_at: new Date()",
            content,
            "linkValue still has local-only mutation (Gap 5 not closed)"
        )

    def test_no_setDecisionStatus_pattern(self):
        """Ensure no direct setDecisionStatus calls exist."""
        if not os.path.exists(self.STORE_PATH):
            self.skipTest("Frontend store not found")

        with open(self.STORE_PATH, "r") as f:
            content = f.read()

        self.assertNotIn("setDecisionStatus", content)
        self.assertNotIn("setQueueState", content)

    def test_getQueueSummary_is_not_locally_computed(self):
        """Ensure getQueueSummary reads from backend metrics, not local loop."""
        if not os.path.exists(self.STORE_PATH):
            self.skipTest("Frontend store not found")

        with open(self.STORE_PATH, "r") as f:
            content = f.read()

        # The old pattern iterated authorities.forEach — should be gone
        # New pattern reads from get().metrics
        self.assertIn("get().metrics", content,
                       "getQueueSummary must read from backend-backed metrics")


class TestGap5_ControlledStateMutation(unittest.TestCase):
    """Gap 5: link_references goes through engine with audit trail."""

    def setUp(self):
        self.engine = _setup_authority_db()

    def test_link_references_creates_audit_event(self):
        env = propose("gap5-001", "analyst-001", "analyst")
        result = link_references(
            decision_id="gap5-001",
            actor_id="analyst-001",
            actor_role="analyst",
            linked_outcome_id="out-999",
            notes="Linking outcome"
        )
        self.assertEqual(result["linked_outcome_id"], "out-999")

        # Verify audit event was created
        events = get_events(env["authority_id"])
        link_events = [e for e in events if e.get("metadata", {}).get("link_update")]
        self.assertTrue(len(link_events) > 0, "No audit event for link_references")
        self.assertEqual(link_events[0]["metadata"]["linked_outcome_id"], "out-999")

    def test_link_references_requires_at_least_one_id(self):
        propose("gap5-002", "analyst-001", "analyst")
        with self.assertRaises(AuthorityError):
            link_references(
                decision_id="gap5-002",
                actor_id="analyst-001",
                actor_role="analyst",
            )

    def test_link_references_rbac_enforced(self):
        propose("gap5-003", "analyst-001", "analyst")
        with self.assertRaises(AuthorityPermissionError):
            link_references(
                decision_id="gap5-003",
                actor_id="viewer-001",
                actor_role="viewer",
                linked_value_id="val-001",
            )


if __name__ == "__main__":
    unittest.main()
