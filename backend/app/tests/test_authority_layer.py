"""
Backend Decision Authority Layer tests.

Covers:
  1.  Create authority envelope (propose)
  2.  Valid transitions pass (full happy-path lifecycle)
  3.  Invalid transitions fail (AuthorityError)
  4.  Approval required before execution enforcement
  5.  Resubmission increments revision_number and resets fields
  6.  Append-only event creation (events never modified)
  7.  Hash chain continuity (previous_event_hash links)
  8.  Hash recomputation matches stored hash (integrity)
  9.  Actor attribution preserved in envelope + events
  10. RBAC enforcement (AuthorityPermissionError on wrong role)
  11. Linked outcome/value references stored but not copied
  12. List / query API returns correct results
  13. Override bypasses FSM guard and is audited
  14. Annotate appends event without changing status
  15. Duplicate propose rejected (409-equivalent AuthorityError)

Uses an isolated in-memory SQLite database — no shared state between tests.
"""

from __future__ import annotations

import unittest
import tempfile
import os

from sqlalchemy import create_engine
from sqlalchemy import event as sa_event


# ── Isolated store setup ───────────────────────────────────────────────────────

def _setup_authority_db():
    """Create an isolated SQLite engine for one test, inject into signals.store."""
    import app.signals.store as store_mod
    import app.authority.models  # noqa: F401 — registers DecisionAuthorityRecord on Base

    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})

    @sa_event.listens_for(engine, "connect")
    def _pragma(conn, _):
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA foreign_keys=ON")

    store_mod._engine = engine
    store_mod.Base.metadata.create_all(engine)
    return engine


# ── Test: Authority creation ───────────────────────────────────────────────────

class TestAuthorityPropose(unittest.TestCase):

    def setUp(self):
        self.engine = _setup_authority_db()

    def test_propose_creates_envelope(self):
        from app.authority.engine import propose
        result = propose(
            decision_id="dec-aaa111",
            actor_id="analyst-001",
            actor_role="analyst",
            rationale="Test proposal",
            priority=2,
        )
        self.assertEqual(result["decision_id"], "dec-aaa111")
        self.assertEqual(result["authority_status"], "PROPOSED")
        self.assertEqual(result["revision_number"], 1)
        self.assertEqual(result["proposed_by"], "analyst-001")
        self.assertEqual(result["priority"], 2)
        self.assertIsNotNone(result["authority_id"])

    def test_propose_creates_initial_event(self):
        from app.authority.engine import propose, get_events_by_decision
        result = propose("dec-bbb222", "analyst-001", "analyst")
        events = get_events_by_decision("dec-bbb222")
        self.assertEqual(len(events), 1)
        ev = events[0]
        self.assertEqual(ev["action"], "PROPOSE")
        self.assertEqual(ev["to_status"], "PROPOSED")
        self.assertIsNone(ev["from_status"])
        self.assertIsNone(ev["previous_event_hash"])  # first event
        self.assertIsNotNone(ev["event_hash"])

    def test_duplicate_propose_raises_error(self):
        from app.authority.engine import propose, AuthorityError
        propose("dec-ccc333", "analyst-001", "analyst")
        with self.assertRaises(AuthorityError) as ctx:
            propose("dec-ccc333", "analyst-002", "analyst")
        self.assertIn("already has an authority envelope", str(ctx.exception))

    def test_propose_priority_clamped(self):
        from app.authority.engine import propose
        r = propose("dec-ddd444", "analyst-001", "analyst", priority=99)
        self.assertEqual(r["priority"], 5)
        r2 = propose("dec-ddd555", "analyst-001", "analyst", priority=-1)
        self.assertEqual(r2["priority"], 1)


# ── Test: Valid transitions ────────────────────────────────────────────────────

class TestValidTransitions(unittest.TestCase):

    def setUp(self):
        self.engine = _setup_authority_db()

    def _propose(self, decision_id="dec-valid-001"):
        from app.authority.engine import propose
        return propose(decision_id, "analyst-001", "analyst", rationale="test")

    def test_propose_to_under_review(self):
        from app.authority.engine import submit_for_review
        self._propose()
        r = submit_for_review("dec-valid-001", "analyst-001", "analyst")
        self.assertEqual(r["authority_status"], "UNDER_REVIEW")
        self.assertIsNotNone(r["review_started_at"])

    def test_under_review_to_approved(self):
        from app.authority.engine import submit_for_review, approve
        self._propose()
        submit_for_review("dec-valid-001", "analyst-001", "analyst")
        r = approve("dec-valid-001", "exec-001", "admin", rationale="Looks good")
        self.assertEqual(r["authority_status"], "APPROVED")
        self.assertEqual(r["authority_actor_id"], "exec-001")
        self.assertIsNotNone(r["authority_decided_at"])

    def test_approved_to_executed(self):
        from app.authority.engine import submit_for_review, approve, execute
        self._propose()
        submit_for_review("dec-valid-001", "analyst-001", "analyst")
        approve("dec-valid-001", "exec-001", "admin")
        r = execute("dec-valid-001", "operator-001", "operator", execution_result="Action completed")
        self.assertEqual(r["authority_status"], "EXECUTED")
        self.assertEqual(r["executed_by"], "operator-001")
        self.assertIsNotNone(r["executed_at"])

    def test_full_happy_path(self):
        from app.authority.engine import (
            propose, submit_for_review, approve, queue_execution,
            execute, get_events_by_decision
        )
        propose("dec-full-001", "analyst-001", "analyst")
        submit_for_review("dec-full-001", "analyst-001", "analyst")
        approve("dec-full-001", "exec-001", "admin")
        queue_execution("dec-full-001", "operator-001", "operator")
        execute("dec-full-001", "operator-001", "operator",
                linked_outcome_id="out-abc", linked_value_id="val-xyz")
        events = get_events_by_decision("dec-full-001")
        actions = [e["action"] for e in events]
        self.assertEqual(actions, [
            "PROPOSE", "SUBMIT_FOR_REVIEW", "APPROVE", "QUEUE_EXECUTION", "EXECUTE"
        ])

    def test_rejected_to_proposed_via_resubmit(self):
        from app.authority.engine import propose, submit_for_review, reject, resubmit
        propose("dec-rejsub-001", "analyst-001", "analyst")
        submit_for_review("dec-rejsub-001", "analyst-001", "analyst")
        reject("dec-rejsub-001", "exec-001", "admin", rationale="Insufficient detail")
        r = resubmit("dec-rejsub-001", "analyst-001", "analyst", rationale="Added more detail")
        self.assertEqual(r["authority_status"], "PROPOSED")
        self.assertEqual(r["revision_number"], 2)
        # Approval fields reset
        self.assertIsNone(r["authority_actor_id"])
        self.assertIsNone(r["authority_decided_at"])

    def test_escalate_increments_level(self):
        from app.authority.engine import propose, submit_for_review, escalate
        propose("dec-esc-001", "analyst-001", "analyst")
        submit_for_review("dec-esc-001", "analyst-001", "analyst")
        r = escalate("dec-esc-001", "operator-001", "operator")
        self.assertEqual(r["authority_status"], "ESCALATED")
        self.assertEqual(r["escalation_level"], 1)

    def test_withdraw_from_proposed(self):
        from app.authority.engine import propose, withdraw
        propose("dec-wd-001", "analyst-001", "analyst")
        r = withdraw("dec-wd-001", "analyst-001", "analyst")
        self.assertEqual(r["authority_status"], "WITHDRAWN")

    def test_revoke_from_approved(self):
        from app.authority.engine import propose, submit_for_review, approve, revoke
        propose("dec-rev-001", "analyst-001", "analyst")
        submit_for_review("dec-rev-001", "analyst-001", "analyst")
        approve("dec-rev-001", "exec-001", "admin")
        r = revoke("dec-rev-001", "exec-001", "admin", rationale="Policy change")
        self.assertEqual(r["authority_status"], "REVOKED")


# ── Test: Invalid transitions ──────────────────────────────────────────────────

class TestInvalidTransitions(unittest.TestCase):

    def setUp(self):
        self.engine = _setup_authority_db()

    def _propose(self, did="dec-inv-001"):
        from app.authority.engine import propose
        return propose(did, "analyst-001", "analyst")

    def test_cannot_approve_from_proposed(self):
        from app.authority.engine import approve, AuthorityError
        self._propose()
        with self.assertRaises(AuthorityError):
            approve("dec-inv-001", "exec-001", "admin")

    def test_cannot_execute_from_proposed(self):
        from app.authority.engine import execute, AuthorityError
        self._propose()
        with self.assertRaises(AuthorityError):
            execute("dec-inv-001", "operator-001", "operator")

    def test_cannot_execute_from_under_review(self):
        from app.authority.engine import submit_for_review, execute, AuthorityError
        self._propose()
        submit_for_review("dec-inv-001", "analyst-001", "analyst")
        with self.assertRaises(AuthorityError):
            execute("dec-inv-001", "operator-001", "operator")

    def test_terminal_state_immutable(self):
        from app.authority.engine import (
            propose, submit_for_review, approve, execute,
            submit_for_review as sfr, AuthorityError
        )
        propose("dec-term-001", "analyst-001", "analyst")
        submit_for_review("dec-term-001", "analyst-001", "analyst")
        approve("dec-term-001", "exec-001", "admin")
        execute("dec-term-001", "operator-001", "operator")
        # EXECUTED is terminal — no further transitions
        with self.assertRaises(AuthorityError):
            sfr("dec-term-001", "analyst-001", "analyst")

    def test_cannot_revoke_terminal(self):
        from app.authority.engine import (
            propose, submit_for_review, approve, execute, revoke, AuthorityError
        )
        propose("dec-revterm-001", "analyst-001", "analyst")
        submit_for_review("dec-revterm-001", "analyst-001", "analyst")
        approve("dec-revterm-001", "exec-001", "admin")
        execute("dec-revterm-001", "operator-001", "operator")
        with self.assertRaises(AuthorityError):
            revoke("dec-revterm-001", "exec-001", "admin")

    def test_resubmit_requires_rejected_state(self):
        from app.authority.engine import propose, resubmit, AuthorityError
        propose("dec-resubmit-bad-001", "analyst-001", "analyst")
        # PROPOSED is not a valid from-state for RESUBMIT
        with self.assertRaises(AuthorityError):
            resubmit("dec-resubmit-bad-001", "analyst-001", "analyst")

    def test_get_nonexistent_authority(self):
        from app.authority.engine import get_by_decision
        result = get_by_decision("no-such-decision")
        self.assertIsNone(result)

    def test_transition_nonexistent_raises_not_found(self):
        from app.authority.engine import submit_for_review, AuthorityNotFoundError
        with self.assertRaises(AuthorityNotFoundError):
            submit_for_review("ghost-decision", "analyst-001", "analyst")


# ── Test: Approval enforcement ─────────────────────────────────────────────────

class TestApprovalEnforcement(unittest.TestCase):

    def setUp(self):
        self.engine = _setup_authority_db()

    def test_execute_without_approval_rejected(self):
        """Core invariant: execution requires APPROVED or EXECUTION_PENDING."""
        from app.authority.engine import propose, execute, AuthorityError
        propose("dec-enforce-001", "analyst-001", "analyst")
        with self.assertRaises(AuthorityError) as ctx:
            execute("dec-enforce-001", "operator-001", "operator")
        self.assertIn("PROPOSED", str(ctx.exception))
        self.assertIn("APPROVED or EXECUTION_PENDING", str(ctx.exception))

    def test_execute_after_approval_succeeds(self):
        from app.authority.engine import propose, submit_for_review, approve, execute
        propose("dec-enforce-002", "analyst-001", "analyst")
        submit_for_review("dec-enforce-002", "analyst-001", "analyst")
        approve("dec-enforce-002", "exec-001", "admin")
        r = execute("dec-enforce-002", "operator-001", "operator")
        self.assertEqual(r["authority_status"], "EXECUTED")

    def test_execute_after_queue_succeeds(self):
        from app.authority.engine import (
            propose, submit_for_review, approve, queue_execution, execute
        )
        propose("dec-enforce-003", "analyst-001", "analyst")
        submit_for_review("dec-enforce-003", "analyst-001", "analyst")
        approve("dec-enforce-003", "exec-001", "admin")
        queue_execution("dec-enforce-003", "operator-001", "operator")
        r = execute("dec-enforce-003", "operator-001", "operator")
        self.assertEqual(r["authority_status"], "EXECUTED")


# ── Test: Resubmission ─────────────────────────────────────────────────────────

class TestResubmission(unittest.TestCase):

    def setUp(self):
        self.engine = _setup_authority_db()

    def test_resubmit_increments_revision(self):
        from app.authority.engine import propose, submit_for_review, reject, resubmit
        propose("dec-resub-001", "analyst-001", "analyst")
        submit_for_review("dec-resub-001", "analyst-001", "analyst")
        reject("dec-resub-001", "exec-001", "admin")
        r = resubmit("dec-resub-001", "analyst-001", "analyst")
        self.assertEqual(r["revision_number"], 2)

    def test_resubmit_resets_reviewer(self):
        from app.authority.engine import propose, submit_for_review, reject, resubmit
        propose("dec-resub-002", "analyst-001", "analyst")
        submit_for_review("dec-resub-002", "analyst-001", "analyst",
                          reviewer_id="rev-001", reviewer_role="admin")
        reject("dec-resub-002", "exec-001", "admin")
        r = resubmit("dec-resub-002", "analyst-001", "analyst")
        self.assertIsNone(r["reviewer_id"])
        self.assertIsNone(r["reviewer_role"])

    def test_double_resubmit_increments_to_3(self):
        from app.authority.engine import (
            propose, submit_for_review, reject, resubmit, return_for_revision
        )
        propose("dec-resub-003", "analyst-001", "analyst")
        submit_for_review("dec-resub-003", "analyst-001", "analyst")
        reject("dec-resub-003", "exec-001", "admin")
        resubmit("dec-resub-003", "analyst-001", "analyst")
        submit_for_review("dec-resub-003", "analyst-001", "analyst")
        return_for_revision("dec-resub-003", "exec-001", "admin")
        r = resubmit("dec-resub-003", "analyst-001", "analyst")
        self.assertEqual(r["revision_number"], 3)


# ── Test: Append-only event log ────────────────────────────────────────────────

class TestAppendOnlyEvents(unittest.TestCase):

    def setUp(self):
        self.engine = _setup_authority_db()

    def test_events_accumulate_correctly(self):
        from app.authority.engine import (
            propose, submit_for_review, approve, get_events_by_decision
        )
        propose("dec-evlog-001", "analyst-001", "analyst")
        self.assertEqual(len(get_events_by_decision("dec-evlog-001")), 1)
        submit_for_review("dec-evlog-001", "analyst-001", "analyst")
        self.assertEqual(len(get_events_by_decision("dec-evlog-001")), 2)
        approve("dec-evlog-001", "exec-001", "admin")
        self.assertEqual(len(get_events_by_decision("dec-evlog-001")), 3)

    def test_events_ordered_chronologically(self):
        from app.authority.engine import propose, submit_for_review, get_events_by_decision
        propose("dec-evord-001", "analyst-001", "analyst")
        submit_for_review("dec-evord-001", "analyst-001", "analyst")
        events = get_events_by_decision("dec-evord-001")
        self.assertEqual(events[0]["action"], "PROPOSE")
        self.assertEqual(events[1]["action"], "SUBMIT_FOR_REVIEW")

    def test_annotate_appends_event_without_status_change(self):
        from app.authority.engine import propose, annotate, get_events_by_decision, get_by_decision
        propose("dec-ann-001", "analyst-001", "analyst")
        annotate("dec-ann-001", "analyst-001", "analyst", notes="Reviewing context")
        envelope = get_by_decision("dec-ann-001")
        self.assertEqual(envelope["authority_status"], "PROPOSED")  # no change
        events = get_events_by_decision("dec-ann-001")
        self.assertEqual(len(events), 2)
        self.assertEqual(events[1]["action"], "ANNOTATE")
        self.assertEqual(events[1]["from_status"], "PROPOSED")
        self.assertEqual(events[1]["to_status"], "PROPOSED")


# ── Test: Hash chain ───────────────────────────────────────────────────────────

class TestHashChain(unittest.TestCase):

    def setUp(self):
        self.engine = _setup_authority_db()

    def test_first_event_has_no_prev_hash(self):
        from app.authority.engine import propose, get_events_by_decision
        propose("dec-hash-001", "analyst-001", "analyst")
        events = get_events_by_decision("dec-hash-001")
        self.assertIsNone(events[0]["previous_event_hash"])

    def test_chain_links_consecutive_events(self):
        from app.authority.engine import propose, submit_for_review, get_events_by_decision
        propose("dec-hash-002", "analyst-001", "analyst")
        submit_for_review("dec-hash-002", "analyst-001", "analyst")
        events = get_events_by_decision("dec-hash-002")
        self.assertEqual(events[1]["previous_event_hash"], events[0]["event_hash"])

    def test_hash_recomputes_correctly(self):
        """Recompute each stored event's hash — must match stored value."""
        from app.authority.engine import (
            propose, submit_for_review, approve,
            get_events_by_decision, _compute_event_hash
        )
        propose("dec-hash-003", "analyst-001", "analyst")
        submit_for_review("dec-hash-003", "analyst-001", "analyst")
        approve("dec-hash-003", "exec-001", "admin")

        events = get_events_by_decision("dec-hash-003")
        for ev in events:
            recomputed = _compute_event_hash(
                event_id=ev["event_id"],
                authority_id=ev["authority_id"],
                action=ev["action"],
                from_status=ev["from_status"],
                to_status=ev["to_status"],
                actor_id=ev["actor_id"],
                timestamp_iso=ev["timestamp"],
                previous_event_hash=ev["previous_event_hash"],
            )
            self.assertEqual(
                recomputed, ev["event_hash"],
                f"Hash mismatch for event {ev['event_id']} (action={ev['action']})"
            )

    def test_verify_chain_passes(self):
        from app.authority.engine import propose, submit_for_review, verify_hash_chain, get_by_decision
        propose("dec-hash-004", "analyst-001", "analyst")
        submit_for_review("dec-hash-004", "analyst-001", "analyst")
        auth = get_by_decision("dec-hash-004")
        report = verify_hash_chain(auth["authority_id"])
        self.assertTrue(report["valid"])
        self.assertEqual(report["events_checked"], 2)
        self.assertEqual(len(report["errors"]), 0)


# ── Test: Actor attribution ────────────────────────────────────────────────────

class TestActorAttribution(unittest.TestCase):

    def setUp(self):
        self.engine = _setup_authority_db()

    def test_proposer_recorded(self):
        from app.authority.engine import propose
        r = propose("dec-actor-001", "analyst-jane", "analyst", rationale="My proposal")
        self.assertEqual(r["proposed_by"], "analyst-jane")
        self.assertEqual(r["proposed_by_role"], "analyst")

    def test_approver_recorded(self):
        from app.authority.engine import propose, submit_for_review, approve
        propose("dec-actor-002", "analyst-jane", "analyst")
        submit_for_review("dec-actor-002", "analyst-jane", "analyst")
        r = approve("dec-actor-002", "exec-john", "admin", rationale="Approved")
        self.assertEqual(r["authority_actor_id"], "exec-john")
        self.assertEqual(r["authority_actor_role"], "admin")
        self.assertEqual(r["authority_rationale"], "Approved")

    def test_executor_recorded(self):
        from app.authority.engine import propose, submit_for_review, approve, execute
        propose("dec-actor-003", "analyst-jane", "analyst")
        submit_for_review("dec-actor-003", "analyst-jane", "analyst")
        approve("dec-actor-003", "exec-john", "admin")
        r = execute("dec-actor-003", "operator-kim", "operator")
        self.assertEqual(r["executed_by"], "operator-kim")
        self.assertEqual(r["executed_by_role"], "operator")

    def test_actor_in_events(self):
        from app.authority.engine import propose, get_events_by_decision
        propose("dec-actor-004", "analyst-jane", "analyst")
        events = get_events_by_decision("dec-actor-004")
        self.assertEqual(events[0]["actor_id"], "analyst-jane")
        self.assertEqual(events[0]["actor_role"], "analyst")


# ── Test: RBAC enforcement ─────────────────────────────────────────────────────

class TestRBACEnforcement(unittest.TestCase):

    def setUp(self):
        self.engine = _setup_authority_db()

    def test_viewer_cannot_propose(self):
        from app.authority.engine import propose, AuthorityPermissionError
        with self.assertRaises(AuthorityPermissionError):
            propose("dec-rbac-001", "viewer-001", "viewer")

    def test_analyst_cannot_approve(self):
        from app.authority.engine import propose, submit_for_review, approve, AuthorityPermissionError
        propose("dec-rbac-002", "analyst-001", "analyst")
        submit_for_review("dec-rbac-002", "analyst-001", "analyst")
        with self.assertRaises(AuthorityPermissionError):
            approve("dec-rbac-002", "analyst-001", "analyst")

    def test_analyst_cannot_revoke(self):
        from app.authority.engine import propose, revoke, AuthorityPermissionError
        propose("dec-rbac-003", "analyst-001", "analyst")
        with self.assertRaises(AuthorityPermissionError):
            revoke("dec-rbac-003", "analyst-001", "analyst")

    def test_operator_cannot_approve(self):
        from app.authority.engine import propose, submit_for_review, approve, AuthorityPermissionError
        propose("dec-rbac-004", "analyst-001", "analyst")
        submit_for_review("dec-rbac-004", "analyst-001", "analyst")
        with self.assertRaises(AuthorityPermissionError):
            approve("dec-rbac-004", "operator-001", "operator")

    def test_admin_can_approve(self):
        from app.authority.engine import propose, submit_for_review, approve
        propose("dec-rbac-005", "analyst-001", "analyst")
        submit_for_review("dec-rbac-005", "analyst-001", "analyst")
        r = approve("dec-rbac-005", "admin-001", "admin")
        self.assertEqual(r["authority_status"], "APPROVED")

    def test_regulator_cannot_propose(self):
        from app.authority.engine import propose, AuthorityPermissionError
        # Regulator can only READ + ANNOTATE — both rbac.py and engine agree.
        # PROPOSE requires PROPOSE_AUTHORITY which regulator lacks — must be blocked.
        with self.assertRaises(AuthorityPermissionError):
            propose("dec-rbac-006", "reg-001", "regulator")

    def test_override_requires_admin(self):
        from app.authority.engine import propose, override, AuthorityPermissionError
        propose("dec-rbac-007", "analyst-001", "analyst")
        with self.assertRaises(AuthorityPermissionError):
            override("dec-rbac-007", "analyst-001", "analyst",
                     target_status="APPROVED", rationale="Bypass")


# ── Test: Linked references ────────────────────────────────────────────────────

class TestLinkedReferences(unittest.TestCase):

    def setUp(self):
        self.engine = _setup_authority_db()

    def test_linked_ids_stored_on_execute(self):
        from app.authority.engine import propose, submit_for_review, approve, execute
        propose("dec-link-001", "analyst-001", "analyst")
        submit_for_review("dec-link-001", "analyst-001", "analyst")
        approve("dec-link-001", "exec-001", "admin")
        r = execute(
            "dec-link-001", "operator-001", "operator",
            linked_outcome_id="out-abc123",
            linked_value_id="val-xyz789",
        )
        self.assertEqual(r["linked_outcome_id"], "out-abc123")
        self.assertEqual(r["linked_value_id"], "val-xyz789")

    def test_linked_ids_in_event_metadata(self):
        from app.authority.engine import (
            propose, submit_for_review, approve, execute, get_events_by_decision
        )
        propose("dec-link-002", "analyst-001", "analyst")
        submit_for_review("dec-link-002", "analyst-001", "analyst")
        approve("dec-link-002", "exec-001", "admin")
        execute("dec-link-002", "operator-001", "operator",
                linked_outcome_id="out-ref-001")
        events = get_events_by_decision("dec-link-002")
        exec_event = next(e for e in events if e["action"] == "EXECUTE")
        self.assertEqual(exec_event["metadata"]["linked_outcome_id"], "out-ref-001")

    def test_linked_ids_null_by_default(self):
        from app.authority.engine import propose
        r = propose("dec-link-003", "analyst-001", "analyst")
        self.assertIsNone(r["linked_outcome_id"])
        self.assertIsNone(r["linked_value_id"])


# ── Test: Override action ──────────────────────────────────────────────────────

class TestOverride(unittest.TestCase):

    def setUp(self):
        self.engine = _setup_authority_db()

    def test_override_bypasses_fsm(self):
        """OVERRIDE can skip states that normal FSM would block."""
        from app.authority.engine import propose, override
        propose("dec-ov-001", "analyst-001", "analyst")
        # PROPOSED → APPROVED directly (normally requires UNDER_REVIEW first)
        r = override("dec-ov-001", "admin-001", "admin",
                     target_status="APPROVED", rationale="Emergency override")
        self.assertEqual(r["authority_status"], "APPROVED")

    def test_override_audited_with_prior_status(self):
        from app.authority.engine import propose, override, get_events_by_decision
        propose("dec-ov-002", "analyst-001", "analyst")
        override("dec-ov-002", "admin-001", "admin",
                 target_status="EXECUTED", rationale="Admin force-complete")
        events = get_events_by_decision("dec-ov-002")
        ov_event = next(e for e in events if e["action"] == "OVERRIDE")
        self.assertEqual(ov_event["metadata"]["override_from"], "PROPOSED")
        self.assertEqual(ov_event["to_status"], "EXECUTED")

    def test_override_invalid_target_raises(self):
        from app.authority.engine import propose, override, AuthorityError
        propose("dec-ov-003", "analyst-001", "analyst")
        with self.assertRaises(AuthorityError):
            override("dec-ov-003", "admin-001", "admin",
                     target_status="NOT_A_REAL_STATUS", rationale="bad")


# ── Test: List / query ─────────────────────────────────────────────────────────

class TestListQuery(unittest.TestCase):

    def setUp(self):
        self.engine = _setup_authority_db()

    def test_list_all(self):
        from app.authority.engine import propose, list_authorities
        propose("dec-list-001", "analyst-001", "analyst")
        propose("dec-list-002", "analyst-001", "analyst")
        results = list_authorities()
        ids = [r["decision_id"] for r in results]
        self.assertIn("dec-list-001", ids)
        self.assertIn("dec-list-002", ids)

    def test_list_by_status(self):
        from app.authority.engine import propose, submit_for_review, list_authorities
        propose("dec-list-003", "analyst-001", "analyst")
        propose("dec-list-004", "analyst-001", "analyst")
        submit_for_review("dec-list-004", "analyst-001", "analyst")
        results = list_authorities(status="UNDER_REVIEW")
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["decision_id"], "dec-list-004")

    def test_get_by_decision(self):
        from app.authority.engine import propose, get_by_decision
        propose("dec-get-001", "analyst-001", "analyst", rationale="unique")
        r = get_by_decision("dec-get-001")
        self.assertIsNotNone(r)
        self.assertEqual(r["proposal_rationale"], "unique")


if __name__ == "__main__":
    unittest.main(verbosity=2)
