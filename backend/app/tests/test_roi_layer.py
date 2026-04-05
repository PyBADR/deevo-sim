"""Tests for the ROI / Decision Value Layer.

Coverage:
    TestROIDeterminism       — same inputs produce identical outputs
    TestROIValidation        — negative avoided_loss rejected at engine level
    TestROILinkage           — non-existent outcome raises ValueError_
    TestROITraceCompleteness — calculation_trace contains all required fields
    TestROIRecomputation     — recompute writes new row, preserves lineage
"""
from __future__ import annotations

import json
import pytest


# ── Test helpers ──────────────────────────────────────────────────────────────

def _setup_store(tmp_path):
    """Initialize a clean, isolated SQLite store for each test."""
    from app.signals import store as _store
    _store._engine = None
    _store._DB_PATH = None
    db_path = str(tmp_path / "test_roi.db")
    _store.init_db(path=db_path)
    return _store


def _make_outcome(store, *, source_decision_id="dec-roi-test0001", expected_value=500_000.0):
    """Persist a minimal confirmed Outcome and return its outcome_id."""
    from app.domain.models.outcome import Outcome, OutcomeStatus, OutcomeClassification
    outcome = Outcome(
        recorded_by        = "test-actor",
        source_decision_id = source_decision_id,
        expected_value     = expected_value,
    )
    # Transition to CONFIRMED so confidence base = 1.0
    outcome = outcome.model_copy(update={
        "outcome_status":         OutcomeStatus.CONFIRMED,
        "outcome_classification": OutcomeClassification.TRUE_POSITIVE,
    })
    d = outcome.model_dump()
    d["time_to_resolution_seconds"] = d.pop("time_to_resolution_seconds", None)
    store.save_outcome(d)
    return outcome.outcome_id


# ── TestROIDeterminism ────────────────────────────────────────────────────────

class TestROIDeterminism:
    """Same inputs must always produce the same outputs."""

    def test_identical_inputs_produce_identical_net_value(self, tmp_path):
        store = _setup_store(tmp_path)
        outcome_id = _make_outcome(store)

        from app.values.engine import compute_value_from_outcome
        v1 = compute_value_from_outcome(
            outcome_id       = outcome_id,
            computed_by      = "test-actor",
            avoided_loss     = 1_000_000.0,
            operational_cost = 100_000.0,
            decision_cost    = 50_000.0,
            latency_cost     = 25_000.0,
        )
        v2 = compute_value_from_outcome(
            outcome_id       = outcome_id,
            computed_by      = "test-actor",
            avoided_loss     = 1_000_000.0,
            operational_cost = 100_000.0,
            decision_cost    = 50_000.0,
            latency_cost     = 25_000.0,
        )

        assert v1.net_value == v2.net_value, "net_value is not deterministic"
        assert v1.value_classification == v2.value_classification
        assert v1.value_confidence_score == v2.value_confidence_score

    def test_formula_correctness(self, tmp_path):
        store = _setup_store(tmp_path)
        outcome_id = _make_outcome(store)

        from app.values.engine import compute_value_from_outcome
        v = compute_value_from_outcome(
            outcome_id       = outcome_id,
            computed_by      = "test-actor",
            avoided_loss     = 800_000.0,
            operational_cost = 100_000.0,
            decision_cost    = 50_000.0,
            latency_cost     = 25_000.0,
        )

        expected_total_cost = 100_000.0 + 50_000.0 + 25_000.0
        expected_net_value  = 800_000.0 - expected_total_cost

        assert v.total_cost == expected_total_cost
        assert v.net_value  == expected_net_value

    def test_trace_inputs_match_computation(self, tmp_path):
        store = _setup_store(tmp_path)
        outcome_id = _make_outcome(store)

        from app.values.engine import compute_value_from_outcome
        v = compute_value_from_outcome(
            outcome_id       = outcome_id,
            computed_by      = "test-actor",
            avoided_loss     = 300_000.0,
            operational_cost = 10_000.0,
            decision_cost    = 5_000.0,
            latency_cost     = 2_000.0,
        )

        trace = v.calculation_trace
        assert trace["inputs"]["avoided_loss"]     == 300_000.0
        assert trace["inputs"]["operational_cost"] == 10_000.0
        assert trace["inputs"]["decision_cost"]    == 5_000.0
        assert trace["inputs"]["latency_cost"]     == 2_000.0
        assert trace["outputs"]["net_value"]       == v.net_value


# ── TestROIValidation ─────────────────────────────────────────────────────────

class TestROIValidation:
    """Negative avoided_loss must be rejected."""

    def test_negative_avoided_loss_rejected_by_api_schema(self):
        """Pydantic validation on ComputeValueBody must reject negative avoided_loss."""
        from pydantic import ValidationError
        from app.api.v1.routes.values import ComputeValueBody

        with pytest.raises(ValidationError) as exc_info:
            ComputeValueBody(
                source_outcome_id = "out-test",
                avoided_loss      = -1.0,
            )

        errors = exc_info.value.errors()
        avoided_loss_errors = [e for e in errors if "avoided_loss" in str(e.get("loc", ""))]
        assert len(avoided_loss_errors) > 0, "No validation error raised for negative avoided_loss"

    def test_negative_avoided_loss_recompute_schema_rejected(self):
        """RecomputeValueBody must also reject negative avoided_loss."""
        from pydantic import ValidationError
        from app.api.v1.routes.values import RecomputeValueBody

        with pytest.raises(ValidationError) as exc_info:
            RecomputeValueBody(avoided_loss=-500.0)

        errors = exc_info.value.errors()
        avoided_loss_errors = [e for e in errors if "avoided_loss" in str(e.get("loc", ""))]
        assert len(avoided_loss_errors) > 0

    def test_zero_avoided_loss_accepted(self):
        """Zero avoided_loss is a valid boundary case."""
        from app.api.v1.routes.values import ComputeValueBody

        body = ComputeValueBody(
            source_outcome_id = "out-test",
            avoided_loss      = 0.0,
        )
        assert body.avoided_loss == 0.0

    def test_positive_avoided_loss_accepted(self):
        """Positive avoided_loss must pass validation."""
        from app.api.v1.routes.values import ComputeValueBody

        body = ComputeValueBody(
            source_outcome_id = "out-test",
            avoided_loss      = 1_000_000.0,
        )
        assert body.avoided_loss == 1_000_000.0


# ── TestROILinkage ────────────────────────────────────────────────────────────

class TestROILinkage:
    """Value computation must fail for non-existent outcomes."""

    def test_compute_for_nonexistent_outcome_raises(self, tmp_path):
        _setup_store(tmp_path)

        from app.values.engine import compute_value_from_outcome, ValueError_

        with pytest.raises(ValueError_) as exc_info:
            compute_value_from_outcome(
                outcome_id       = "out-does-not-exist",
                computed_by      = "test-actor",
                avoided_loss     = 500_000.0,
            )

        assert "not found" in str(exc_info.value).lower()

    def test_save_value_rejects_orphan_row(self, tmp_path):
        """store.save_value must raise if source_outcome_id does not exist."""
        from app.signals import store

        _setup_store(tmp_path)

        with pytest.raises(Exception) as exc_info:
            store.save_value({
                "value_id":         "val-orphan000001",
                "source_outcome_id": "out-nonexistent",
                "computed_by":      "test-actor",
                "net_value":        100_000.0,
                "value_classification": "POSITIVE_VALUE",
                "calculation_trace": {},
            })

        assert "referential integrity" in str(exc_info.value).lower() or \
               "does not exist" in str(exc_info.value).lower()

    def test_recompute_for_nonexistent_value_raises(self, tmp_path):
        _setup_store(tmp_path)

        from app.values.engine import recompute_value, ValueError_

        with pytest.raises(ValueError_) as exc_info:
            recompute_value(
                value_id    = "val-does-not-exist",
                computed_by = "test-actor",
            )

        assert "not found" in str(exc_info.value).lower()


# ── TestROITraceCompleteness ──────────────────────────────────────────────────

class TestROITraceCompleteness:
    """calculation_trace must contain all required fields."""

    REQUIRED_TOP_KEYS = {
        "formula", "value_quality", "inputs", "intermediate", "outputs",
        "classification_thresholds", "confidence_factors", "outcome_context",
        "computed_by", "computed_at",
    }

    REQUIRED_INPUT_KEYS = {
        "avoided_loss", "avoided_loss_source",
        "operational_cost", "decision_cost", "latency_cost",
    }

    def test_trace_contains_required_top_level_keys(self, tmp_path):
        store = _setup_store(tmp_path)
        outcome_id = _make_outcome(store)

        from app.values.engine import compute_value_from_outcome
        v = compute_value_from_outcome(
            outcome_id   = outcome_id,
            computed_by  = "test-actor",
            avoided_loss = 200_000.0,
        )

        missing = self.REQUIRED_TOP_KEYS - set(v.calculation_trace.keys())
        assert not missing, f"Trace missing keys: {missing}"

    def test_trace_inputs_contain_required_fields(self, tmp_path):
        store = _setup_store(tmp_path)
        outcome_id = _make_outcome(store)

        from app.values.engine import compute_value_from_outcome
        v = compute_value_from_outcome(
            outcome_id   = outcome_id,
            computed_by  = "test-actor",
            avoided_loss = 200_000.0,
        )

        missing = self.REQUIRED_INPUT_KEYS - set(v.calculation_trace["inputs"].keys())
        assert not missing, f"Trace inputs missing keys: {missing}"

    def test_value_quality_explicit(self, tmp_path):
        """Explicit avoided_loss → value_quality = REAL_VALUE."""
        store = _setup_store(tmp_path)
        outcome_id = _make_outcome(store)

        from app.values.engine import compute_value_from_outcome
        v = compute_value_from_outcome(
            outcome_id   = outcome_id,
            computed_by  = "test-actor",
            avoided_loss = 500_000.0,
        )

        assert v.calculation_trace["value_quality"] == "REAL_VALUE"
        assert v.calculation_trace["inputs"]["avoided_loss_source"] == "explicit"

    def test_value_quality_inferred(self, tmp_path):
        """No avoided_loss but outcome has expected_value → INFERRED_FROM_OUTCOME."""
        store = _setup_store(tmp_path)
        outcome_id = _make_outcome(store, expected_value=750_000.0)

        from app.values.engine import compute_value_from_outcome
        v = compute_value_from_outcome(
            outcome_id   = outcome_id,
            computed_by  = "test-actor",
            avoided_loss = None,  # not provided — should fall back to expected_value
        )

        assert v.calculation_trace["value_quality"] == "INFERRED_FROM_OUTCOME"
        assert v.calculation_trace["inputs"]["avoided_loss_source"] == "outcome.expected_value"
        assert v.avoided_loss == 750_000.0

    def test_value_quality_cost_only(self, tmp_path):
        """No avoided_loss and no expected_value → COST_ONLY_NO_EXPECTED_VALUE."""
        store = _setup_store(tmp_path)
        outcome_id = _make_outcome(store, expected_value=None)

        from app.values.engine import compute_value_from_outcome
        v = compute_value_from_outcome(
            outcome_id   = outcome_id,
            computed_by  = "test-actor",
            avoided_loss = None,
        )

        assert v.calculation_trace["value_quality"] == "COST_ONLY_NO_EXPECTED_VALUE"
        assert v.calculation_trace["inputs"]["avoided_loss_source"] == "default_zero"
        assert v.avoided_loss == 0.0


# ── TestROIRecomputation ──────────────────────────────────────────────────────

class TestROIRecomputation:
    """Recompute must write a new row and preserve lineage."""

    def test_recompute_produces_new_value_id(self, tmp_path):
        store = _setup_store(tmp_path)
        outcome_id = _make_outcome(store)

        from app.values.engine import compute_value_from_outcome, recompute_value
        v1 = compute_value_from_outcome(
            outcome_id   = outcome_id,
            computed_by  = "test-actor",
            avoided_loss = 500_000.0,
        )
        v2 = recompute_value(
            value_id    = v1.value_id,
            computed_by = "test-actor",
            avoided_loss = 600_000.0,
        )

        assert v2.value_id != v1.value_id, "Recompute must produce a new value_id"

    def test_recompute_preserves_original_row(self, tmp_path):
        store = _setup_store(tmp_path)
        outcome_id = _make_outcome(store)

        from app.values.engine import compute_value_from_outcome, recompute_value, get_value
        v1 = compute_value_from_outcome(
            outcome_id   = outcome_id,
            computed_by  = "test-actor",
            avoided_loss = 500_000.0,
        )
        recompute_value(
            value_id    = v1.value_id,
            computed_by = "test-actor",
            avoided_loss = 600_000.0,
        )

        # Original row must still be loadable
        original = get_value(v1.value_id)
        assert original is not None, "Original value row was deleted — must be preserved"
        assert original.avoided_loss == 500_000.0

    def test_recompute_trace_contains_lineage(self, tmp_path):
        store = _setup_store(tmp_path)
        outcome_id = _make_outcome(store)

        from app.values.engine import compute_value_from_outcome, recompute_value
        v1 = compute_value_from_outcome(
            outcome_id   = outcome_id,
            computed_by  = "test-actor",
            avoided_loss = 500_000.0,
        )
        v2 = recompute_value(
            value_id    = v1.value_id,
            computed_by = "test-actor",
            avoided_loss = 600_000.0,
        )

        assert "recomputed_from_value_id" in v2.calculation_trace, \
            "Recomputed trace must contain recomputed_from_value_id for lineage"
        assert v2.calculation_trace["recomputed_from_value_id"] == v1.value_id

    def test_recompute_with_updated_cost_changes_net_value(self, tmp_path):
        store = _setup_store(tmp_path)
        outcome_id = _make_outcome(store)

        from app.values.engine import compute_value_from_outcome, recompute_value
        v1 = compute_value_from_outcome(
            outcome_id       = outcome_id,
            computed_by      = "test-actor",
            avoided_loss     = 500_000.0,
            operational_cost = 50_000.0,
        )
        v2 = recompute_value(
            value_id         = v1.value_id,
            computed_by      = "test-actor",
            operational_cost = 100_000.0,  # doubled
        )

        assert v2.net_value < v1.net_value, "Increasing cost must reduce net_value"
        assert v2.operational_cost == 100_000.0
        # avoided_loss should be carried forward from original
        assert v2.avoided_loss == v1.avoided_loss
