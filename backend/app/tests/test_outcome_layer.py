"""Tests for the Outcome Intelligence Layer.

Coverage:
    TestOutcomeModel         — domain model, transitions, immutability
    TestOutcomePersistence   — store CRUD: save/update/load/load-all
    TestOutcomeEngine        — create, observe, confirm, dispute, fail, close
    TestOutcomeTransitions   — full guard matrix: valid + invalid
    TestOutcomeAuditEvents   — every transition writes the correct audit event
    TestOutcomeLinkage       — orphan rejection, linkage variants
"""
from __future__ import annotations

import json
import os
import pytest
from datetime import datetime, timezone

# ── Test helpers ──────────────────────────────────────────────────────────────

def _setup_store(tmp_path):
    """Initialize a clean, isolated SQLite store for each test."""
    from app.signals import store as _store
    _store._engine = None
    _store._DB_PATH = None
    db_path = str(tmp_path / "test_outcomes.db")
    _store.init_db(path=db_path)
    return _store


def _make_decision_id():
    return "dec-test00000001"


def _make_run_id():
    return "run-test00000001"


# ── TestOutcomeModel ──────────────────────────────────────────────────────────

class TestOutcomeModel:
    """Domain model: fields, defaults, immutability, transitions."""

    def test_create_with_decision_linkage(self):
        from app.domain.models.outcome import Outcome, OutcomeStatus
        outcome = Outcome(
            recorded_by        = "test-actor",
            source_decision_id = _make_decision_id(),
        )
        assert outcome.outcome_id.startswith("out-")
        assert outcome.outcome_status == OutcomeStatus.PENDING_OBSERVATION
        assert outcome.error_flag is False
        assert outcome.outcome_classification is None
        assert outcome.observed_at is None
        assert outcome.closed_at is None

    def test_create_with_run_linkage(self):
        from app.domain.models.outcome import Outcome
        outcome = Outcome(recorded_by="test-actor", source_run_id=_make_run_id())
        assert outcome.source_run_id == _make_run_id()
        assert outcome.source_decision_id is None

    def test_frozen_model(self):
        from app.domain.models.outcome import Outcome
        import pydantic
        outcome = Outcome(recorded_by="test-actor", source_run_id=_make_run_id())
        with pytest.raises((pydantic.ValidationError, TypeError)):
            outcome.outcome_status = "OBSERVED"  # type: ignore

    def test_to_observed_merges_evidence(self):
        from app.domain.models.outcome import Outcome, OutcomeStatus
        outcome = Outcome(
            recorded_by        = "test-actor",
            source_decision_id = _make_decision_id(),
            evidence_payload   = {"initial_key": "initial_val"},
        )
        observed = outcome.to_observed(
            evidence_payload = {"new_key": "new_val"},
            realized_value   = 1_000_000.0,
        )
        assert observed.outcome_status == OutcomeStatus.OBSERVED
        assert observed.observed_at is not None
        assert observed.realized_value == 1_000_000.0
        assert "initial_key" in observed.evidence_payload
        assert "new_key" in observed.evidence_payload

    def test_to_confirmed_sets_classification(self):
        from app.domain.models.outcome import Outcome, OutcomeStatus, OutcomeClassification
        outcome = Outcome(
            recorded_by        = "test-actor",
            source_decision_id = _make_decision_id(),
        ).to_observed()
        confirmed = outcome.to_confirmed(OutcomeClassification.TRUE_POSITIVE)
        assert confirmed.outcome_status == OutcomeStatus.CONFIRMED
        assert confirmed.outcome_classification == OutcomeClassification.TRUE_POSITIVE
        assert confirmed.time_to_resolution_seconds is not None

    def test_to_disputed_sets_error_flag(self):
        from app.domain.models.outcome import Outcome, OutcomeStatus
        outcome = Outcome(
            recorded_by        = "test-actor",
            source_decision_id = _make_decision_id(),
        ).to_observed()
        disputed = outcome.to_disputed("Evidence does not support classification")
        assert disputed.outcome_status == OutcomeStatus.DISPUTED
        assert disputed.error_flag is True
        assert "DISPUTED" in (disputed.notes or "")

    def test_to_closed_computes_resolution_time(self):
        from app.domain.models.outcome import Outcome, OutcomeStatus, OutcomeClassification
        outcome = (
            Outcome(recorded_by="test-actor", source_decision_id=_make_decision_id())
            .to_observed()
            .to_confirmed(OutcomeClassification.FALSE_POSITIVE)
        )
        closed = outcome.to_closed()
        assert closed.outcome_status == OutcomeStatus.CLOSED
        assert closed.closed_at is not None
        assert isinstance(closed.time_to_resolution_seconds, int)
        assert closed.time_to_resolution_seconds >= 0


# ── TestOutcomePersistence ────────────────────────────────────────────────────

class TestOutcomePersistence:
    """Store functions: save_outcome, update_outcome, load_outcome_by_id, load_outcomes."""

    def test_save_and_load_by_id(self, tmp_path):
        store = _setup_store(tmp_path)
        from app.domain.models.outcome import Outcome, OutcomeStatus
        outcome = Outcome(
            recorded_by        = "test-actor",
            source_decision_id = _make_decision_id(),
            expected_value     = 500_000.0,
            evidence_payload   = {"context": "stress_test"},
            notes              = "Initial recording",
        )
        from app.outcomes.engine import _outcome_to_dict
        store.save_outcome(_outcome_to_dict(outcome))

        row = store.load_outcome_by_id(outcome.outcome_id)
        assert row is not None
        assert row["outcome_id"] == outcome.outcome_id
        assert row["outcome_status"] == OutcomeStatus.PENDING_OBSERVATION.value
        assert row["recorded_by"] == "test-actor"
        assert row["expected_value"] == 500_000.0
        assert row["evidence_payload"]["context"] == "stress_test"
        assert row["notes"] == "Initial recording"
        assert row["error_flag"] is False

    def test_save_idempotent(self, tmp_path):
        store = _setup_store(tmp_path)
        from app.domain.models.outcome import Outcome
        from app.outcomes.engine import _outcome_to_dict
        outcome = Outcome(recorded_by="test-actor", source_run_id=_make_run_id())
        d = _outcome_to_dict(outcome)
        store.save_outcome(d)
        store.save_outcome(d)  # second call must not raise or duplicate
        rows = store.load_outcomes()
        assert sum(1 for r in rows if r["outcome_id"] == outcome.outcome_id) == 1

    def test_update_outcome_and_reload(self, tmp_path):
        store = _setup_store(tmp_path)
        from app.domain.models.outcome import Outcome, OutcomeStatus
        from app.outcomes.engine import _outcome_to_dict
        outcome = Outcome(recorded_by="test-actor", source_run_id=_make_run_id())
        store.save_outcome(_outcome_to_dict(outcome))

        observed = outcome.to_observed(realized_value=1_234.0)
        store.update_outcome(_outcome_to_dict(observed), "outcome.observed")

        row = store.load_outcome_by_id(outcome.outcome_id)
        assert row["outcome_status"] == OutcomeStatus.OBSERVED.value
        assert row["realized_value"] == 1_234.0
        assert row["observed_at"] is not None

    def test_load_outcomes_filter_by_decision(self, tmp_path):
        store = _setup_store(tmp_path)
        from app.domain.models.outcome import Outcome
        from app.outcomes.engine import _outcome_to_dict
        dec_id = "dec-filter-test00"
        o1 = Outcome(recorded_by="actor", source_decision_id=dec_id)
        o2 = Outcome(recorded_by="actor", source_decision_id=dec_id)
        o3 = Outcome(recorded_by="actor", source_run_id=_make_run_id())
        for o in [o1, o2, o3]:
            store.save_outcome(_outcome_to_dict(o))

        rows = store.load_outcomes(decision_id=dec_id)
        assert len(rows) == 2
        assert all(r["source_decision_id"] == dec_id for r in rows)

    def test_audit_event_written_on_save(self, tmp_path):
        store = _setup_store(tmp_path)
        from app.domain.models.outcome import Outcome
        from app.outcomes.engine import _outcome_to_dict
        outcome = Outcome(recorded_by="test-actor", source_decision_id=_make_decision_id())
        store.save_outcome(_outcome_to_dict(outcome))

        audit = store.get_audit_log(entity_id=outcome.outcome_id, event_type="outcome.created")
        assert len(audit) == 1
        assert audit[0]["entity_kind"] == "outcome"

    def test_load_nonexistent_returns_none(self, tmp_path):
        store = _setup_store(tmp_path)
        row = store.load_outcome_by_id("out-does-not-exist")
        assert row is None


# ── TestOutcomeEngine ─────────────────────────────────────────────────────────

class TestOutcomeEngine:
    """Engine public API: create, observe, confirm, dispute, fail, close."""

    def test_create_outcome_persists(self, tmp_path):
        _setup_store(tmp_path)
        from app.outcomes import engine
        outcome = engine.create_outcome(
            recorded_by        = "operator-1",
            source_decision_id = _make_decision_id(),
            expected_value     = 10_000_000.0,
        )
        assert outcome.outcome_id.startswith("out-")

        reloaded = engine.get_outcome(outcome.outcome_id)
        assert reloaded is not None
        assert reloaded.outcome_id == outcome.outcome_id
        assert reloaded.expected_value == 10_000_000.0

    def test_observe_transitions_status(self, tmp_path):
        _setup_store(tmp_path)
        from app.outcomes import engine
        from app.domain.models.outcome import OutcomeStatus
        outcome = engine.create_outcome(
            recorded_by = "operator-1",
            source_run_id = _make_run_id(),
        )
        observed = engine.observe_outcome(
            outcome_id       = outcome.outcome_id,
            actor            = "operator-1",
            evidence_payload = {"observation": "stress indicators rising"},
            realized_value   = 2_500_000.0,
        )
        assert observed.outcome_status == OutcomeStatus.OBSERVED
        assert observed.realized_value == 2_500_000.0

        # Verify persisted
        reloaded = engine.get_outcome(outcome.outcome_id)
        assert reloaded.outcome_status == OutcomeStatus.OBSERVED

    def test_confirm_outcome_requires_observation_first(self, tmp_path):
        _setup_store(tmp_path)
        from app.outcomes import engine
        from app.outcomes.engine import OutcomeError
        from app.domain.models.outcome import OutcomeClassification
        outcome = engine.create_outcome(
            recorded_by        = "operator-1",
            source_decision_id = _make_decision_id(),
        )
        with pytest.raises(OutcomeError, match="transition"):
            engine.confirm_outcome(
                outcome_id     = outcome.outcome_id,
                actor          = "operator-1",
                classification = OutcomeClassification.TRUE_POSITIVE,
            )

    def test_full_lifecycle_pending_observed_confirmed_closed(self, tmp_path):
        _setup_store(tmp_path)
        from app.outcomes import engine
        from app.domain.models.outcome import OutcomeStatus, OutcomeClassification
        outcome = engine.create_outcome(
            recorded_by        = "operator-1",
            source_decision_id = _make_decision_id(),
        )
        observed  = engine.observe_outcome(outcome.outcome_id, "operator-1")
        confirmed = engine.confirm_outcome(
            outcome.outcome_id, "operator-1",
            OutcomeClassification.OPERATIONALLY_SUCCESSFUL,
        )
        closed = engine.close_outcome(outcome.outcome_id, "operator-1", notes="All done")

        assert closed.outcome_status == OutcomeStatus.CLOSED
        assert closed.closed_at is not None
        assert closed.time_to_resolution_seconds is not None

    def test_dispute_then_confirm_then_close(self, tmp_path):
        _setup_store(tmp_path)
        from app.outcomes import engine
        from app.domain.models.outcome import OutcomeStatus, OutcomeClassification
        outcome = engine.create_outcome(
            recorded_by = "operator-1",
            source_run_id = _make_run_id(),
        )
        engine.observe_outcome(outcome.outcome_id, "operator-1")
        engine.dispute_outcome(outcome.outcome_id, "operator-2", reason="Measurement error suspected")
        engine.confirm_outcome(
            outcome.outcome_id, "operator-1",
            OutcomeClassification.PARTIALLY_REALIZED,
        )
        closed = engine.close_outcome(outcome.outcome_id, "operator-1")
        assert closed.outcome_status == OutcomeStatus.CLOSED

    def test_fail_and_close(self, tmp_path):
        _setup_store(tmp_path)
        from app.outcomes import engine
        from app.domain.models.outcome import OutcomeStatus
        outcome = engine.create_outcome(
            recorded_by = "operator-1",
            source_run_id = _make_run_id(),
        )
        failed = engine.fail_outcome(outcome.outcome_id, "operator-1", "Data source unavailable")
        assert failed.outcome_status == OutcomeStatus.FAILED
        assert failed.error_flag is True

        closed = engine.close_outcome(outcome.outcome_id, "operator-1")
        assert closed.outcome_status == OutcomeStatus.CLOSED

    def test_list_outcomes_returns_all(self, tmp_path):
        _setup_store(tmp_path)
        from app.outcomes import engine
        for i in range(3):
            engine.create_outcome(
                recorded_by = f"operator-{i}",
                source_run_id = f"run-list-test-{i:04d}",
            )
        outcomes = engine.list_outcomes()
        assert len(outcomes) >= 3


# ── TestOutcomeTransitions ────────────────────────────────────────────────────

class TestOutcomeTransitions:
    """Guard matrix: all valid and invalid transitions."""

    @pytest.mark.parametrize("invalid_target", [
        "CONFIRMED", "DISPUTED", "CLOSED",
    ])
    def test_pending_cannot_skip_observed(self, tmp_path, invalid_target):
        _setup_store(tmp_path)
        from app.outcomes import engine
        from app.outcomes.engine import OutcomeError
        from app.domain.models.outcome import OutcomeClassification
        outcome = engine.create_outcome(
            recorded_by = "operator-1",
            source_run_id = _make_run_id(),
        )
        with pytest.raises(OutcomeError, match="transition"):
            if invalid_target == "CONFIRMED":
                engine.confirm_outcome(outcome.outcome_id, "op", OutcomeClassification.TRUE_POSITIVE)
            elif invalid_target == "DISPUTED":
                engine.dispute_outcome(outcome.outcome_id, "op", "bad")
            elif invalid_target == "CLOSED":
                engine.close_outcome(outcome.outcome_id, "op")

    def test_confirmed_cannot_go_to_disputed(self, tmp_path):
        _setup_store(tmp_path)
        from app.outcomes import engine
        from app.outcomes.engine import OutcomeError
        from app.domain.models.outcome import OutcomeClassification
        outcome = engine.create_outcome(
            recorded_by = "operator-1",
            source_run_id = _make_run_id(),
        )
        engine.observe_outcome(outcome.outcome_id, "op")
        engine.confirm_outcome(outcome.outcome_id, "op", OutcomeClassification.TRUE_POSITIVE)
        with pytest.raises(OutcomeError, match="transition"):
            engine.dispute_outcome(outcome.outcome_id, "op", "late dispute")

    def test_closed_is_terminal(self, tmp_path):
        _setup_store(tmp_path)
        from app.outcomes import engine
        from app.outcomes.engine import OutcomeError
        from app.domain.models.outcome import OutcomeClassification
        outcome = engine.create_outcome(
            recorded_by = "operator-1",
            source_run_id = _make_run_id(),
        )
        engine.observe_outcome(outcome.outcome_id, "op")
        engine.confirm_outcome(outcome.outcome_id, "op", OutcomeClassification.NO_MATERIAL_IMPACT)
        engine.close_outcome(outcome.outcome_id, "op")

        with pytest.raises(OutcomeError, match="transition"):
            engine.close_outcome(outcome.outcome_id, "op")  # double-close

    def test_double_close_rejected(self, tmp_path):
        _setup_store(tmp_path)
        from app.outcomes import engine
        from app.outcomes.engine import OutcomeError
        from app.domain.models.outcome import OutcomeClassification
        outcome = engine.create_outcome(
            recorded_by = "operator-1",
            source_run_id = _make_run_id(),
        )
        engine.observe_outcome(outcome.outcome_id, "op")
        engine.confirm_outcome(outcome.outcome_id, "op", OutcomeClassification.TRUE_POSITIVE)
        engine.close_outcome(outcome.outcome_id, "op")
        with pytest.raises(OutcomeError):
            engine.close_outcome(outcome.outcome_id, "op")


# ── TestOutcomeAuditEvents ────────────────────────────────────────────────────

class TestOutcomeAuditEvents:
    """Every lifecycle transition must write the correct audit event type."""

    def _get_audit(self, store, outcome_id: str) -> list[dict]:
        return store.get_audit_log(entity_id=outcome_id)

    def test_create_writes_audit(self, tmp_path):
        store = _setup_store(tmp_path)
        from app.outcomes import engine
        outcome = engine.create_outcome(
            recorded_by = "operator-1",
            source_run_id = _make_run_id(),
        )
        audit = self._get_audit(store, outcome.outcome_id)
        event_types = [a["event_type"] for a in audit]
        assert "outcome.created" in event_types

    def test_observe_writes_audit(self, tmp_path):
        store = _setup_store(tmp_path)
        from app.outcomes import engine
        outcome = engine.create_outcome(
            recorded_by = "operator-1",
            source_run_id = _make_run_id(),
        )
        engine.observe_outcome(outcome.outcome_id, "op")
        event_types = [a["event_type"] for a in self._get_audit(store, outcome.outcome_id)]
        assert "outcome.observed" in event_types

    def test_confirm_writes_audit(self, tmp_path):
        store = _setup_store(tmp_path)
        from app.outcomes import engine
        from app.domain.models.outcome import OutcomeClassification
        outcome = engine.create_outcome(
            recorded_by = "operator-1",
            source_run_id = _make_run_id(),
        )
        engine.observe_outcome(outcome.outcome_id, "op")
        engine.confirm_outcome(outcome.outcome_id, "op", OutcomeClassification.FALSE_POSITIVE)
        event_types = [a["event_type"] for a in self._get_audit(store, outcome.outcome_id)]
        assert "outcome.confirmed" in event_types

    def test_dispute_writes_audit(self, tmp_path):
        store = _setup_store(tmp_path)
        from app.outcomes import engine
        outcome = engine.create_outcome(
            recorded_by = "operator-1",
            source_run_id = _make_run_id(),
        )
        engine.observe_outcome(outcome.outcome_id, "op")
        engine.dispute_outcome(outcome.outcome_id, "op", reason="Disputed!")
        event_types = [a["event_type"] for a in self._get_audit(store, outcome.outcome_id)]
        assert "outcome.disputed" in event_types

    def test_failed_writes_audit(self, tmp_path):
        store = _setup_store(tmp_path)
        from app.outcomes import engine
        outcome = engine.create_outcome(
            recorded_by = "operator-1",
            source_run_id = _make_run_id(),
        )
        engine.fail_outcome(outcome.outcome_id, "op", "data unavailable")
        event_types = [a["event_type"] for a in self._get_audit(store, outcome.outcome_id)]
        assert "outcome.failed" in event_types

    def test_close_writes_audit(self, tmp_path):
        store = _setup_store(tmp_path)
        from app.outcomes import engine
        from app.domain.models.outcome import OutcomeClassification
        outcome = engine.create_outcome(
            recorded_by = "operator-1",
            source_run_id = _make_run_id(),
        )
        engine.observe_outcome(outcome.outcome_id, "op")
        engine.confirm_outcome(outcome.outcome_id, "op", OutcomeClassification.TRUE_POSITIVE)
        engine.close_outcome(outcome.outcome_id, "op")
        event_types = [a["event_type"] for a in self._get_audit(store, outcome.outcome_id)]
        assert "outcome.closed" in event_types

    def test_full_lifecycle_produces_all_event_types(self, tmp_path):
        store = _setup_store(tmp_path)
        from app.outcomes import engine
        from app.domain.models.outcome import OutcomeClassification
        outcome = engine.create_outcome(
            recorded_by = "operator-1",
            source_run_id = _make_run_id(),
        )
        engine.observe_outcome(outcome.outcome_id, "op")
        engine.confirm_outcome(outcome.outcome_id, "op", OutcomeClassification.TRUE_POSITIVE)
        engine.close_outcome(outcome.outcome_id, "op")

        audit = self._get_audit(store, outcome.outcome_id)
        event_types = {a["event_type"] for a in audit}
        assert {"outcome.created", "outcome.observed", "outcome.confirmed", "outcome.closed"}.issubset(event_types)


# ── TestOutcomeLinkage ─────────────────────────────────────────────────────────

class TestOutcomeLinkage:
    """Orphan rejection and linkage variants."""

    def test_orphan_outcome_rejected(self, tmp_path):
        _setup_store(tmp_path)
        from app.outcomes import engine
        from app.outcomes.engine import OutcomeError
        with pytest.raises(OutcomeError, match="at least one of"):
            engine.create_outcome(
                recorded_by = "operator-1",
                # no source_decision_id, no source_run_id
            )

    def test_decision_only_linkage_accepted(self, tmp_path):
        _setup_store(tmp_path)
        from app.outcomes import engine
        outcome = engine.create_outcome(
            recorded_by        = "operator-1",
            source_decision_id = _make_decision_id(),
        )
        assert outcome.source_decision_id == _make_decision_id()
        assert outcome.source_run_id is None

    def test_run_only_linkage_accepted(self, tmp_path):
        _setup_store(tmp_path)
        from app.outcomes import engine
        outcome = engine.create_outcome(
            recorded_by   = "operator-1",
            source_run_id = _make_run_id(),
        )
        assert outcome.source_run_id == _make_run_id()
        assert outcome.source_decision_id is None

    def test_full_chain_linkage(self, tmp_path):
        _setup_store(tmp_path)
        from app.outcomes import engine
        outcome = engine.create_outcome(
            recorded_by        = "operator-1",
            source_decision_id = _make_decision_id(),
            source_run_id      = _make_run_id(),
            source_signal_id   = "sig-test-0001",
            source_seed_id     = "seed-test-0001",
        )
        assert outcome.source_decision_id is not None
        assert outcome.source_run_id is not None
        assert outcome.source_signal_id is not None
        assert outcome.source_seed_id is not None

    def test_outcome_survives_restart(self, tmp_path):
        """Outcome must remain queryable after store re-init (restart simulation)."""
        from app.signals import store as _store
        _store._engine = None
        _store._DB_PATH = None
        db_path = str(tmp_path / "restart_test.db")
        _store.init_db(path=db_path)

        from app.outcomes import engine
        outcome = engine.create_outcome(
            recorded_by        = "operator-1",
            source_decision_id = _make_decision_id(),
            notes              = "pre-restart note",
        )
        oid = outcome.outcome_id

        # Simulate restart: destroy engine, re-init against same file
        _store._engine = None
        _store._DB_PATH = None
        _store.init_db(path=db_path)

        reloaded = engine.get_outcome(oid)
        assert reloaded is not None
        assert reloaded.outcome_id == oid
        assert reloaded.notes == "pre-restart note"
