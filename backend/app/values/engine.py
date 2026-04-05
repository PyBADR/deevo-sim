"""values.engine — ROI / Decision Value computation engine.

This engine is the authoritative layer for computing, recomputing, and
querying DecisionValue entities.

Architecture:
    - Reads from the Outcome layer (read-only).  Never modifies outcomes.
    - Produces DecisionValue entities derived from confirmed or observed Outcomes.
    - Persists via store.save_value — every computation is durable and restart-safe.
    - All inputs are stored in calculation_trace.  Recomputation from trace is exact.

Computation Formula:
    net_value  = avoided_loss - total_cost
    total_cost = operational_cost + decision_cost + latency_cost

    avoided_loss resolution (priority order):
        1. Explicitly provided avoided_loss parameter
        2. outcome.expected_value (if available and avoided_loss not given)
        3. 0.0  (neither source available)

Value Classification Thresholds (fixed, stored in trace):
    net_value ≥  1_000_000  →  HIGH_VALUE
    net_value >          0  →  POSITIVE_VALUE
    net_value ==         0  →  NEUTRAL        (within ±1.0 tolerance)
    net_value <          0  →  NEGATIVE_VALUE
    net_value ≤ -1_000_000  →  LOSS_INDUCING

Confidence Score (0.0–1.0):
    Base weight from outcome status:
        CONFIRMED           → 1.00
        DISPUTED            → 0.50
        OBSERVED            → 0.75
        PENDING_OBSERVATION → 0.40
        FAILED              → 0.20
        CLOSED              → 1.00  (final state — confidence preserved)
    Penalties:
        error_flag = True   → −0.25
        classification = FALSE_POSITIVE → −0.30
        classification = FALSE_NEGATIVE → −0.20
        classification = NO_MATERIAL_IMPACT → −0.10

Restrictions:
    - compute_value_from_outcome: no restriction on outcome status — caller decides
      whether to compute on OBSERVED vs CONFIRMED outcomes.  Both are valid.
    - recompute_value: loads existing value, finds original outcome, recomputes
      with new cost inputs.  Writes a NEW row (new value_id).  Old row preserved.
    - list_values: no filter = all values; filters by outcome_id, decision_id, run_id.
"""
from __future__ import annotations

import logging
from datetime import timezone
from typing import Any

from app.domain.models.decision_value import DecisionValue, ValueClassification
from app.domain.models.outcome import Outcome, OutcomeClassification, OutcomeStatus

logger = logging.getLogger("observatory.values")


# ── Exception ──────────────────────────────────────────────────────────────────

class ValueError_(ValueError):
    """Raised for invalid value computation operations."""


# ── Confidence weights ─────────────────────────────────────────────────────────

_STATUS_CONFIDENCE: dict[OutcomeStatus, float] = {
    OutcomeStatus.CONFIRMED:           1.00,
    OutcomeStatus.CLOSED:              1.00,
    OutcomeStatus.OBSERVED:            0.75,
    OutcomeStatus.DISPUTED:            0.50,
    OutcomeStatus.PENDING_OBSERVATION: 0.40,
    OutcomeStatus.FAILED:              0.20,
}

_CLASS_CONFIDENCE_DELTA: dict[OutcomeClassification, float] = {
    OutcomeClassification.TRUE_POSITIVE:            0.00,
    OutcomeClassification.OPERATIONALLY_SUCCESSFUL: 0.00,
    OutcomeClassification.PARTIALLY_REALIZED:      -0.10,
    OutcomeClassification.NO_MATERIAL_IMPACT:      -0.10,
    OutcomeClassification.TRUE_NEGATIVE:            0.00,
    OutcomeClassification.FALSE_NEGATIVE:          -0.20,
    OutcomeClassification.FALSE_POSITIVE:          -0.30,
    OutcomeClassification.OPERATIONALLY_FAILED:    -0.25,
}

# Classification thresholds — stored in trace so they are auditable
_THRESHOLDS = {
    "HIGH_VALUE":     1_000_000.0,
    "LOSS_INDUCING": -1_000_000.0,
    "NEUTRAL_BAND":         1.0,   # |net_value| < 1.0 → NEUTRAL
}


# ── Public API ─────────────────────────────────────────────────────────────────

def compute_value_from_outcome(
    outcome_id:       str,
    computed_by:      str,
    avoided_loss:     float | None = None,
    operational_cost: float        = 0.0,
    decision_cost:    float        = 0.0,
    latency_cost:     float        = 0.0,
    notes:            str | None   = None,
) -> DecisionValue:
    """Compute ROI from an existing Outcome.

    Deterministic formula: net_value = avoided_loss - total_cost.
    All inputs and context stored in calculation_trace for full recomputability.

    Args:
        outcome_id:       ID of the source Outcome (required).
        computed_by:      actor or system identity performing the computation.
        avoided_loss:     monetary value of loss avoided.  If None, falls back to
                          outcome.expected_value, then 0.0.
        operational_cost: cost of running the underlying pipeline (default 0.0).
        decision_cost:    cost of the decision action itself (default 0.0).
        latency_cost:     cost from response time delay (default 0.0).
        notes:            optional human notes attached to this computation.

    Returns:
        Persisted DecisionValue entity.

    Raises:
        ValueError_: if outcome not found.
    """
    outcome = _resolve_outcome(outcome_id)
    value = _compute(
        outcome          = outcome,
        computed_by      = computed_by,
        avoided_loss     = avoided_loss,
        operational_cost = operational_cost,
        decision_cost    = decision_cost,
        latency_cost     = latency_cost,
        notes            = notes,
        audit_event_type = "value.computed",
    )
    logger.info(
        "value.computed value_id=%s outcome_id=%s net_value=%s classification=%s actor=%s",
        value.value_id, outcome_id, value.net_value, value.value_classification.value, computed_by,
    )
    return value


def recompute_value(
    value_id:         str,
    computed_by:      str,
    avoided_loss:     float | None = None,
    operational_cost: float | None = None,
    decision_cost:    float | None = None,
    latency_cost:     float | None = None,
    notes:            str | None   = None,
) -> DecisionValue:
    """Recompute ROI with updated cost inputs.

    Loads the existing DecisionValue to find its source_outcome_id, then
    re-runs the computation with updated inputs.  The original row is
    preserved — a NEW row is written with a new value_id.

    If a cost input is None, the original value from the existing record is reused.

    Args:
        value_id:    ID of the DecisionValue to recompute from.
        computed_by: actor or system identity.
        avoided_loss, operational_cost, decision_cost, latency_cost:
                     new cost inputs.  If None, original values are kept.
        notes:       optional notes on why this recomputation was done.

    Returns:
        New persisted DecisionValue entity (new value_id).

    Raises:
        ValueError_: if value or source outcome not found.
    """
    existing_row = _resolve_value_row(value_id)
    outcome = _resolve_outcome(existing_row["source_outcome_id"])

    # Use existing values as defaults for any None inputs
    _avoided_loss     = avoided_loss     if avoided_loss     is not None else existing_row.get("avoided_loss",     None)
    _operational_cost = operational_cost if operational_cost is not None else existing_row.get("operational_cost", 0.0)
    _decision_cost    = decision_cost    if decision_cost    is not None else existing_row.get("decision_cost",    0.0)
    _latency_cost     = latency_cost     if latency_cost     is not None else existing_row.get("latency_cost",     0.0)

    value = _compute(
        outcome          = outcome,
        computed_by      = computed_by,
        avoided_loss     = _avoided_loss,
        operational_cost = _operational_cost,
        decision_cost    = _decision_cost,
        latency_cost     = _latency_cost,
        notes            = notes,
        audit_event_type = "value.recomputed",
        prior_value_id   = value_id,
    )
    logger.info(
        "value.recomputed new_value_id=%s prior_value_id=%s outcome_id=%s net_value=%s actor=%s",
        value.value_id, value_id, outcome.outcome_id, value.net_value, computed_by,
    )
    return value


def get_value(value_id: str) -> DecisionValue | None:
    """Load a DecisionValue from persistent store by ID."""
    from app.signals import store
    row = store.load_value_by_id(value_id)
    if row is None:
        return None
    return _row_to_value(row)


def list_values(
    outcome_id:  str | None = None,
    decision_id: str | None = None,
    run_id:      str | None = None,
    limit:       int        = 100,
) -> list[DecisionValue]:
    """List DecisionValues from persistent store, optionally filtered."""
    from app.signals import store
    rows = store.load_values(
        outcome_id  = outcome_id,
        decision_id = decision_id,
        run_id      = run_id,
        limit       = limit,
    )
    result: list[DecisionValue] = []
    for row in rows:
        try:
            result.append(_row_to_value(row))
        except Exception as exc:
            logger.error("values.list_values: could not reconstruct value_id=%s: %s",
                         row.get("value_id"), exc)
    return result


# ── Internal helpers ───────────────────────────────────────────────────────────

def _compute(
    outcome:          Outcome,
    computed_by:      str,
    avoided_loss:     float | None,
    operational_cost: float,
    decision_cost:    float,
    latency_cost:     float,
    notes:            str | None,
    audit_event_type: str,
    prior_value_id:   str | None = None,
) -> DecisionValue:
    """Core deterministic computation.  Used by both compute and recompute."""

    # ── Resolve avoided_loss ──────────────────────────────────────────────────
    if avoided_loss is not None:
        _avoided_loss = float(avoided_loss)
        avoided_loss_source = "explicit"
        value_quality = "REAL_VALUE"
    elif outcome.expected_value is not None:
        _avoided_loss = float(outcome.expected_value)
        avoided_loss_source = "outcome.expected_value"
        value_quality = "INFERRED_FROM_OUTCOME"
    else:
        _avoided_loss = 0.0
        avoided_loss_source = "default_zero"
        value_quality = "COST_ONLY_NO_EXPECTED_VALUE"

    # ── Compute ───────────────────────────────────────────────────────────────
    _operational_cost = float(operational_cost)
    _decision_cost    = float(decision_cost)
    _latency_cost     = float(latency_cost)
    total_cost        = _operational_cost + _decision_cost + _latency_cost
    net_value         = _avoided_loss - total_cost

    # ── Confidence score ──────────────────────────────────────────────────────
    base_confidence = _STATUS_CONFIDENCE.get(outcome.outcome_status, 0.5)
    error_penalty   = 0.25 if outcome.error_flag else 0.0
    class_delta     = _CLASS_CONFIDENCE_DELTA.get(outcome.outcome_classification, 0.0) \
                      if outcome.outcome_classification else 0.0
    confidence = max(0.0, min(1.0, base_confidence - error_penalty + class_delta))

    # ── Value classification ──────────────────────────────────────────────────
    classification = _classify(net_value)

    # ── Calculation trace — every input, step, and context preserved ─────────
    trace: dict[str, Any] = {
        "formula": "avoided_loss - (operational_cost + decision_cost + latency_cost)",
        # value_quality distinguishes real ROI from cost-only computations.
        # REAL_VALUE:                  avoided_loss was explicitly provided.
        # INFERRED_FROM_OUTCOME:       avoided_loss taken from outcome.expected_value.
        # COST_ONLY_NO_EXPECTED_VALUE: no avoided_loss available; net_value is purely negative cost.
        "value_quality": value_quality,
        "inputs": {
            "avoided_loss":          _avoided_loss,
            "avoided_loss_source":   avoided_loss_source,
            "operational_cost":      _operational_cost,
            "decision_cost":         _decision_cost,
            "latency_cost":          _latency_cost,
        },
        "intermediate": {
            "total_cost": total_cost,
        },
        "outputs": {
            "net_value": net_value,
        },
        "classification_thresholds": _THRESHOLDS,
        "confidence_factors": {
            "outcome_status_base":   base_confidence,
            "error_flag_penalty":    error_penalty,
            "classification_delta":  class_delta,
            "final_confidence":      confidence,
        },
        "outcome_context": {
            "outcome_id":              outcome.outcome_id,
            "outcome_status":          outcome.outcome_status.value,
            "outcome_classification":  outcome.outcome_classification.value
                                       if outcome.outcome_classification else None,
            "realized_value":          outcome.realized_value,
            "expected_value":          outcome.expected_value,
            "error_flag":              outcome.error_flag,
            "time_to_resolution_seconds": outcome.time_to_resolution_seconds,
            "source_decision_id":     outcome.source_decision_id,
            "source_run_id":          outcome.source_run_id,
        },
        "computed_by": computed_by,
        "computed_at": _now_utc_iso(),
    }
    if prior_value_id:
        trace["recomputed_from_value_id"] = prior_value_id

    value = DecisionValue(
        source_outcome_id      = outcome.outcome_id,
        source_decision_id     = outcome.source_decision_id,
        source_run_id          = outcome.source_run_id,
        computed_by            = computed_by,
        expected_value         = outcome.expected_value,
        realized_value         = outcome.realized_value,
        avoided_loss           = _avoided_loss,
        operational_cost       = _operational_cost,
        decision_cost          = _decision_cost,
        latency_cost           = _latency_cost,
        total_cost             = total_cost,
        net_value              = net_value,
        value_confidence_score = confidence,
        value_classification   = classification,
        calculation_trace      = trace,
        notes                  = notes,
    )

    # ── Persist ───────────────────────────────────────────────────────────────
    row = _value_to_dict(value)
    row["_audit_event_type"] = audit_event_type
    from app.signals import store
    store.save_value(row)

    return value


def _classify(net_value: float) -> ValueClassification:
    """Deterministic classification from net_value using fixed thresholds."""
    if net_value >= _THRESHOLDS["HIGH_VALUE"]:
        return ValueClassification.HIGH_VALUE
    if net_value <= _THRESHOLDS["LOSS_INDUCING"]:
        return ValueClassification.LOSS_INDUCING
    if abs(net_value) < _THRESHOLDS["NEUTRAL_BAND"]:
        return ValueClassification.NEUTRAL
    if net_value > 0:
        return ValueClassification.POSITIVE_VALUE
    return ValueClassification.NEGATIVE_VALUE


def _resolve_outcome(outcome_id: str) -> Outcome:
    """Load Outcome from the persistence layer, raising ValueError_ if not found."""
    from app.outcomes.engine import get_outcome
    outcome = get_outcome(outcome_id)
    if outcome is None:
        raise ValueError_(f"Outcome {outcome_id!r} not found.")
    return outcome


def _resolve_value_row(value_id: str) -> dict:
    """Load raw value row from store, raising ValueError_ if not found."""
    from app.signals import store
    row = store.load_value_by_id(value_id)
    if row is None:
        raise ValueError_(f"DecisionValue {value_id!r} not found.")
    return row


def _value_to_dict(value: DecisionValue) -> dict:
    """Convert DecisionValue to a plain dict suitable for store.save_value."""
    return {
        "value_id":               value.value_id,
        "source_outcome_id":      value.source_outcome_id,
        "source_decision_id":     value.source_decision_id,
        "source_run_id":          value.source_run_id,
        "computed_at":            value.computed_at,
        "computed_by":            value.computed_by,
        "expected_value":         value.expected_value,
        "realized_value":         value.realized_value,
        "avoided_loss":           value.avoided_loss,
        "operational_cost":       value.operational_cost,
        "decision_cost":          value.decision_cost,
        "latency_cost":           value.latency_cost,
        "total_cost":             value.total_cost,
        "net_value":              value.net_value,
        "value_confidence_score": value.value_confidence_score,
        "value_classification":   value.value_classification.value,
        "calculation_trace":      value.calculation_trace,
        "notes":                  value.notes,
    }


def _row_to_value(row: dict) -> DecisionValue:
    """Reconstruct a DecisionValue from a DB row dict."""
    from datetime import datetime
    from app.outcomes.engine import _coerce_dt

    return DecisionValue(
        value_id               = row["value_id"],
        source_outcome_id      = row["source_outcome_id"],
        source_decision_id     = row.get("source_decision_id"),
        source_run_id          = row.get("source_run_id"),
        computed_at            = _coerce_dt(row["computed_at"]),
        computed_by            = row["computed_by"],
        expected_value         = row.get("expected_value"),
        realized_value         = row.get("realized_value"),
        avoided_loss           = float(row.get("avoided_loss", 0.0)),
        operational_cost       = float(row.get("operational_cost", 0.0)),
        decision_cost          = float(row.get("decision_cost", 0.0)),
        latency_cost           = float(row.get("latency_cost", 0.0)),
        total_cost             = float(row.get("total_cost", 0.0)),
        net_value              = float(row["net_value"]),
        value_confidence_score = float(row.get("value_confidence_score", 0.0)),
        value_classification   = ValueClassification(row["value_classification"]),
        calculation_trace      = row.get("calculation_trace") or {},
        notes                  = row.get("notes"),
    )


def _now_utc_iso() -> str:
    from datetime import datetime, timezone
    return datetime.now(timezone.utc).isoformat()
