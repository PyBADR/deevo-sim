"""
Operator Layer decision tests.

Covers:
  - Domain model: enums, state transitions, immutability
  - Persistence: save/load/update decision_records + audit events
  - Engine: create, execute, close, transition guards, linkage enforcement
  - Transition guard matrix: all valid + invalid transitions
  - Execution dispatch: TRIGGER_RUN mocked, non-pipeline types
  - API validation: route input/output shapes via Pydantic models

Uses the same isolated temp-DB pattern as test_signal_layer_hardening.py.
"""
from __future__ import annotations

import os
import tempfile
import unittest
from datetime import datetime, timezone
from unittest.mock import MagicMock, patch


# ── Helpers ────────────────────────────────────────────────────────────────────

def _setup_store(tmp_path: str):
    import app.signals.store as store_mod
    from sqlalchemy import create_engine, event as sa_event

    engine = create_engine(
        f"sqlite:///{tmp_path}",
        connect_args={"check_same_thread": False},
        echo=False,
    )

    @sa_event.listens_for(engine, "connect")
    def _pragma(conn, _):
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA foreign_keys=ON")

    store_mod._engine = engine
    store_mod.Base.metadata.create_all(engine)
    return engine


# ── Domain model tests ─────────────────────────────────────────────────────────

class TestOperatorDecisionModel(unittest.TestCase):

    def _make(self, decision_type="APPROVE_ACTION"):
        from app.domain.models.operator_decision import (
            OperatorDecision, DecisionType, DecisionStatus, OutcomeStatus
        )
        return OperatorDecision(
            decision_type    = DecisionType(decision_type),
            created_by       = "analyst@io",
            source_signal_id = "sig-abc123",
        )

    def test_default_status_is_created(self):
        from app.domain.models.operator_decision import DecisionStatus
        d = self._make()
        self.assertEqual(d.decision_status, DecisionStatus.CREATED)

    def test_decision_id_has_dec_prefix(self):
        d = self._make()
        self.assertTrue(d.decision_id.startswith("dec-"))

    def test_to_executed_sets_outcome_success(self):
        from app.domain.models.operator_decision import DecisionStatus, OutcomeStatus
        d = self._make()
        executed = d.to_executed({"run_id": "run-xyz"})
        self.assertEqual(executed.decision_status, DecisionStatus.EXECUTED)
        self.assertEqual(executed.outcome_status, OutcomeStatus.SUCCESS)
        self.assertEqual(executed.outcome_payload["run_id"], "run-xyz")

    def test_to_failed_sets_outcome_failure(self):
        from app.domain.models.operator_decision import DecisionStatus, OutcomeStatus
        d = self._make()
        failed = d.to_failed("pipeline error")
        self.assertEqual(failed.decision_status, DecisionStatus.FAILED)
        self.assertEqual(failed.outcome_status, OutcomeStatus.FAILURE)
        self.assertIn("pipeline error", failed.outcome_payload.get("error", ""))

    def test_to_closed_sets_closed_at(self):
        from app.domain.models.operator_decision import DecisionStatus
        d = self._make()
        executed = d.to_executed({})
        closed = executed.to_closed()
        self.assertEqual(closed.decision_status, DecisionStatus.CLOSED)
        self.assertIsNotNone(closed.closed_at)

    def test_immutability_preserved(self):
        """Original decision is unchanged after transition."""
        d = self._make()
        d.to_executed({"result": "done"})
        from app.domain.models.operator_decision import DecisionStatus
        self.assertEqual(d.decision_status, DecisionStatus.CREATED)


# ── Persistence tests ─────────────────────────────────────────────────────────

class TestDecisionPersistence(unittest.TestCase):

    def setUp(self):
        self.tmp = tempfile.mktemp(suffix=".db")
        _setup_store(self.tmp)
        import app.signals.store as s
        self.store = s

    def tearDown(self):
        try:
            os.unlink(self.tmp)
        except FileNotFoundError:
            pass

    def _decision_dict(self, decision_type="APPROVE_ACTION", signal_id="sig-test"):
        from app.domain.models.operator_decision import OperatorDecision, DecisionType
        d = OperatorDecision(
            decision_type    = DecisionType(decision_type),
            created_by       = "operator@io",
            source_signal_id = signal_id,
        )
        from app.decisions.engine import _decision_to_dict
        return _decision_to_dict(d), d.decision_id

    def test_save_and_load_decision(self):
        d_dict, d_id = self._decision_dict()
        self.store.save_decision(d_dict)

        loaded = self.store.load_decision_by_id(d_id)
        self.assertIsNotNone(loaded)
        self.assertEqual(loaded["decision_status"], "CREATED")
        self.assertEqual(loaded["source_signal_id"], "sig-test")

    def test_save_decision_writes_audit_event(self):
        d_dict, d_id = self._decision_dict()
        self.store.save_decision(d_dict)

        events = self.store.get_audit_log(entity_id=d_id)
        self.assertTrue(any(e["event_type"] == "decision.created" for e in events))

    def test_save_decision_idempotent(self):
        """Duplicate save_decision must not raise or create duplicate audit events."""
        d_dict, d_id = self._decision_dict()
        self.store.save_decision(d_dict)
        self.store.save_decision(d_dict)  # second call

        events = self.store.get_audit_log(entity_id=d_id, event_type="decision.created")
        self.assertEqual(len(events), 1)

    def test_update_decision_writes_audit(self):
        d_dict, d_id = self._decision_dict()
        self.store.save_decision(d_dict)

        d_dict_updated = {**d_dict, "decision_status": "EXECUTED", "outcome_status": "SUCCESS"}
        self.store.update_decision(d_dict_updated, "decision.executed")

        events = self.store.get_audit_log(entity_id=d_id, event_type="decision.executed")
        self.assertEqual(len(events), 1)

    def test_load_decisions_filter_by_status(self):
        for i in range(3):
            d_dict, _ = self._decision_dict(signal_id=f"sig-{i:03d}")
            self.store.save_decision(d_dict)

        rows = self.store.load_decisions(status="CREATED")
        self.assertGreaterEqual(len(rows), 3)
        for r in rows:
            self.assertEqual(r["decision_status"], "CREATED")

    def test_load_decision_not_found_returns_none(self):
        self.assertIsNone(self.store.load_decision_by_id("dec-nonexistent"))

    def test_decision_payload_roundtrip(self):
        """JSON payload must survive store round-trip."""
        from app.domain.models.operator_decision import OperatorDecision, DecisionType
        from app.decisions.engine import _decision_to_dict
        d = OperatorDecision(
            decision_type    = DecisionType.TRIGGER_RUN,
            created_by       = "operator@io",
            source_run_id    = "run-abc",
            decision_payload = {"template_id": "hormuz_closure", "severity": 0.9},
        )
        d_dict = _decision_to_dict(d)
        self.store.save_decision(d_dict)
        loaded = self.store.load_decision_by_id(d.decision_id)
        self.assertEqual(loaded["decision_payload"]["template_id"], "hormuz_closure")
        self.assertAlmostEqual(loaded["decision_payload"]["severity"], 0.9)


# ── Engine transition guard tests ─────────────────────────────────────────────

class TestDecisionEngineTransitions(unittest.TestCase):

    def setUp(self):
        self.tmp = tempfile.mktemp(suffix=".db")
        _setup_store(self.tmp)

    def tearDown(self):
        try:
            os.unlink(self.tmp)
        except FileNotFoundError:
            pass

    def test_create_decision_requires_linkage(self):
        from app.decisions.engine import create_decision, DecisionError
        from app.domain.models.operator_decision import DecisionType
        with self.assertRaises(DecisionError) as ctx:
            create_decision(
                decision_type = DecisionType.IGNORE,
                created_by    = "operator@io",
                # No source_* provided
            )
        self.assertIn("reference at least one", str(ctx.exception))

    def test_create_decision_with_signal_id(self):
        from app.decisions.engine import create_decision
        from app.domain.models.operator_decision import DecisionType, DecisionStatus
        d = create_decision(
            decision_type    = DecisionType.IGNORE,
            created_by       = "analyst@io",
            source_signal_id = "sig-test001",
            rationale        = "Low confidence signal",
        )
        self.assertEqual(d.decision_status, DecisionStatus.CREATED)
        self.assertEqual(d.source_signal_id, "sig-test001")

    def test_close_requires_executed_or_failed(self):
        """Cannot close a CREATED decision directly."""
        from app.decisions.engine import create_decision, close_decision, DecisionError
        from app.domain.models.operator_decision import DecisionType
        d = create_decision(
            decision_type    = DecisionType.IGNORE,
            created_by       = "operator@io",
            source_signal_id = "sig-x",
        )
        with self.assertRaises(DecisionError) as ctx:
            close_decision(d.decision_id, actor="operator@io")
        self.assertIn("CREATED", str(ctx.exception))

    def test_close_executed_decision(self):
        from app.decisions.engine import (
            create_decision, get_decision, DecisionError
        )
        from app.decisions import engine as eng
        from app.domain.models.operator_decision import DecisionType, DecisionStatus
        d = create_decision(
            decision_type    = DecisionType.ESCALATE,
            created_by       = "operator@io",
            source_seed_id   = "seed-abc",
        )
        # Manually transition to EXECUTED (bypass execute for simplicity)
        executed = d.to_executed({"escalated": True})
        import app.signals.store as store_mod
        store_mod.update_decision(eng._decision_to_dict(executed), "decision.executed")

        from app.decisions.engine import close_decision
        closed = close_decision(d.decision_id, actor="admin@io")
        self.assertEqual(closed.decision_status, DecisionStatus.CLOSED)
        self.assertIsNotNone(closed.closed_at)

    def test_cannot_execute_closed_decision(self):
        from app.decisions.engine import (
            create_decision, close_decision, execute_decision, DecisionError
        )
        from app.decisions import engine as eng
        from app.domain.models.operator_decision import DecisionType
        d = create_decision(
            decision_type    = DecisionType.IGNORE,
            created_by       = "operator@io",
            source_run_id    = "run-zzz",
        )
        executed = d.to_executed({})
        import app.signals.store as store_mod
        store_mod.update_decision(eng._decision_to_dict(executed), "decision.executed")
        close_decision(d.decision_id, actor="admin@io")

        with self.assertRaises(DecisionError):
            execute_decision(d.decision_id, actor="admin@io")

    def test_execute_not_found_raises(self):
        from app.decisions.engine import execute_decision, DecisionError
        with self.assertRaises(DecisionError) as ctx:
            execute_decision("dec-nonexistent", actor="op@io")
        self.assertIn("not found", str(ctx.exception).lower())


# ── Execution dispatch tests ──────────────────────────────────────────────────

class TestDecisionExecution(unittest.TestCase):

    def setUp(self):
        self.tmp = tempfile.mktemp(suffix=".db")
        _setup_store(self.tmp)

    def tearDown(self):
        try:
            os.unlink(self.tmp)
        except FileNotFoundError:
            pass

    def test_execute_ignore_writes_audit(self):
        from app.decisions.engine import create_decision, execute_decision
        from app.domain.models.operator_decision import DecisionType, DecisionStatus
        import app.signals.store as store_mod

        d = create_decision(
            decision_type    = DecisionType.IGNORE,
            created_by       = "operator@io",
            source_signal_id = "sig-ignore-test",
            rationale        = "False positive",
        )
        executed = execute_decision(d.decision_id, actor="operator@io")

        self.assertEqual(executed.decision_status, DecisionStatus.EXECUTED)
        events = store_mod.get_audit_log(entity_id=d.decision_id, event_type="decision.ignored")
        self.assertEqual(len(events), 1)

    def test_execute_escalate_writes_audit(self):
        from app.decisions.engine import create_decision, execute_decision
        from app.domain.models.operator_decision import DecisionType
        import app.signals.store as store_mod

        d = create_decision(
            decision_type    = DecisionType.ESCALATE,
            created_by       = "analyst@io",
            source_seed_id   = "seed-escalate",
            decision_payload = {"escalation_target": "CRO"},
        )
        execute_decision(d.decision_id, actor="analyst@io")

        events = store_mod.get_audit_log(entity_id=d.decision_id, event_type="decision.escalated")
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0]["metadata"].get("escalation_target"), "CRO")

    def test_execute_approve_action_writes_audit(self):
        from app.decisions.engine import create_decision, execute_decision
        from app.domain.models.operator_decision import DecisionType
        import app.signals.store as store_mod

        d = create_decision(
            decision_type    = DecisionType.APPROVE_ACTION,
            created_by       = "operator@io",
            source_run_id    = "run-approve-test",
            decision_payload = {"action_id": "act-001"},
        )
        execute_decision(d.decision_id, actor="operator@io")

        events = store_mod.get_audit_log(entity_id=d.decision_id, event_type="action.approved")
        self.assertEqual(len(events), 1)

    def test_execute_trigger_run_calls_pipeline(self):
        """TRIGGER_RUN must call run_unified_pipeline() and persist the run."""
        from app.decisions.engine import create_decision, execute_decision
        from app.domain.models.operator_decision import DecisionType, DecisionStatus
        import app.signals.store as store_mod

        d = create_decision(
            decision_type    = DecisionType.TRIGGER_RUN,
            created_by       = "operator@io",
            source_signal_id = "sig-trigger-test",
            decision_payload = {"template_id": "regional_liquidity_stress_event", "severity": 0.7},
        )

        fake_run_result = {
            "status":           "completed",
            "stages_completed": 13,
            "duration_ms":      150.0,
        }

        with patch("app.simulation.runner.run_unified_pipeline", return_value=fake_run_result), \
             patch("app.api.v1.routes.runs.get_run_store", return_value={}), \
             patch("app.api.v1.routes.runs.get_result_store", return_value={}):
            executed = execute_decision(d.decision_id, actor="operator@io")

        self.assertEqual(executed.decision_status, DecisionStatus.EXECUTED)
        run_id = executed.outcome_payload.get("run_id")
        self.assertIsNotNone(run_id)

        # Run must be persisted in DB
        run_row = store_mod.load_run_by_id(run_id)
        self.assertIsNotNone(run_row)
        self.assertEqual(run_row["status"], "completed")

    def test_execute_trigger_run_without_template_raises(self):
        """TRIGGER_RUN without template_id must raise DecisionError."""
        from app.decisions.engine import create_decision, execute_decision, DecisionError
        from app.domain.models.operator_decision import DecisionType

        d = create_decision(
            decision_type    = DecisionType.TRIGGER_RUN,
            created_by       = "operator@io",
            source_signal_id = "sig-no-template",
            # No template_id in payload
        )

        with self.assertRaises(DecisionError) as ctx:
            execute_decision(d.decision_id, actor="operator@io")
        self.assertIn("template_id", str(ctx.exception))

    def test_execute_override_run_result_requires_run_id(self):
        from app.decisions.engine import create_decision, execute_decision, DecisionError
        from app.domain.models.operator_decision import DecisionType

        d = create_decision(
            decision_type    = DecisionType.OVERRIDE_RUN_RESULT,
            created_by       = "admin@io",
            source_signal_id = "sig-override",
            # No source_run_id and no run_id in payload
        )

        with self.assertRaises(DecisionError) as ctx:
            execute_decision(d.decision_id, actor="admin@io")
        self.assertIn("run_id", str(ctx.exception))


# ── Transition guard matrix ───────────────────────────────────────────────────

class TestDecisionTransitionGuardMatrix(unittest.TestCase):

    def setUp(self):
        from app.decisions.engine import _assert_transition
        from app.decisions.engine import DecisionError as DE
        self.guard = _assert_transition
        self.DecisionError = DE

    def _decision(self, status_str: str):
        from app.domain.models.operator_decision import (
            OperatorDecision, DecisionType, DecisionStatus
        )
        return OperatorDecision(
            decision_type    = DecisionType.IGNORE,
            created_by       = "op@io",
            source_signal_id = "sig-guard",
            decision_status  = DecisionStatus(status_str),
        )

    def test_created_can_go_in_review(self):
        from app.domain.models.operator_decision import DecisionStatus
        self.guard(self._decision("CREATED"), DecisionStatus.IN_REVIEW)  # no raise

    def test_created_can_execute(self):
        from app.domain.models.operator_decision import DecisionStatus
        self.guard(self._decision("CREATED"), DecisionStatus.EXECUTED)  # no raise

    def test_in_review_can_execute(self):
        from app.domain.models.operator_decision import DecisionStatus
        self.guard(self._decision("IN_REVIEW"), DecisionStatus.EXECUTED)  # no raise

    def test_executed_can_close(self):
        from app.domain.models.operator_decision import DecisionStatus
        self.guard(self._decision("EXECUTED"), DecisionStatus.CLOSED)  # no raise

    def test_failed_can_close(self):
        from app.domain.models.operator_decision import DecisionStatus
        self.guard(self._decision("FAILED"), DecisionStatus.CLOSED)  # no raise

    def test_closed_cannot_execute(self):
        from app.domain.models.operator_decision import DecisionStatus
        with self.assertRaises(self.DecisionError):
            self.guard(self._decision("CLOSED"), DecisionStatus.EXECUTED)

    def test_closed_cannot_close_again(self):
        from app.domain.models.operator_decision import DecisionStatus
        with self.assertRaises(self.DecisionError):
            self.guard(self._decision("CLOSED"), DecisionStatus.CLOSED)

    def test_created_cannot_close_directly(self):
        from app.domain.models.operator_decision import DecisionStatus
        with self.assertRaises(self.DecisionError):
            self.guard(self._decision("CREATED"), DecisionStatus.CLOSED)

    def test_executed_cannot_execute_again(self):
        from app.domain.models.operator_decision import DecisionStatus
        with self.assertRaises(self.DecisionError):
            self.guard(self._decision("EXECUTED"), DecisionStatus.EXECUTED)


# ── API route body validation ─────────────────────────────────────────────────

class TestDecisionRouteBodyValidation(unittest.TestCase):

    def _body(self, **kwargs):
        from app.api.v1.routes.decisions import CreateDecisionBody
        return CreateDecisionBody(**kwargs)

    def test_valid_body_approve_action(self):
        b = self._body(
            decision_type    = "APPROVE_ACTION",
            source_signal_id = "sig-abc",
        )
        self.assertEqual(b.decision_type.value, "APPROVE_ACTION")

    def test_valid_body_trigger_run(self):
        b = self._body(
            decision_type    = "TRIGGER_RUN",
            source_run_id    = "run-abc",
            decision_payload = {"template_id": "hormuz_chokepoint_disruption"},
        )
        self.assertEqual(b.decision_type.value, "TRIGGER_RUN")

    def test_invalid_decision_type_raises(self):
        from pydantic import ValidationError
        with self.assertRaises(ValidationError):
            self._body(decision_type="UNKNOWN_TYPE", source_run_id="run-abc")

    def test_confidence_out_of_range_raises(self):
        from pydantic import ValidationError
        with self.assertRaises(ValidationError):
            self._body(
                decision_type    = "IGNORE",
                source_signal_id = "sig-x",
                confidence_score = 1.5,
            )

    def test_close_body_invalid_outcome_passes_pydantic(self):
        """CloseDecisionBody accepts any string for outcome_status (validated at route layer)."""
        from app.api.v1.routes.decisions import CloseDecisionBody
        b = CloseDecisionBody(outcome_status="SUCCESS")
        self.assertEqual(b.outcome_status, "SUCCESS")


if __name__ == "__main__":
    unittest.main()
