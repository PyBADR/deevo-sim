"""outcomes.engine — Outcome Intelligence lifecycle engine.

This engine is the authoritative layer for creating and transitioning Outcome
entities.  It enforces the transition guard matrix, rejects orphan outcomes,
and writes audit events for every lifecycle change.

State machine:
    PENDING_OBSERVATION → OBSERVED  (observe_outcome)
    PENDING_OBSERVATION → FAILED    (fail_outcome)
    OBSERVED            → CONFIRMED (confirm_outcome)
    OBSERVED            → DISPUTED  (dispute_outcome)
    OBSERVED            → FAILED    (fail_outcome)
    CONFIRMED           → CLOSED    (close_outcome)
    DISPUTED            → CONFIRMED (confirm_outcome — dispute resolved)
    DISPUTED            → CLOSED    (close_outcome)
    FAILED              → CLOSED    (close_outcome)
    CLOSED              → any       ✗  OutcomeError (terminal)

Linkage requirement:
    At least one of source_decision_id, source_run_id must be provided.
    source_signal_id and source_seed_id are optional enrichment.

This engine does NOT compute ROI. It records outcome truth.
"""
from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any

from app.domain.models.outcome import (
    Outcome,
    OutcomeClassification,
    OutcomeStatus,
)

logger = logging.getLogger("observatory.outcomes")


# ── Exception ──────────────────────────────────────────────────────────────────

class OutcomeError(ValueError):
    """Raised for invalid outcome operations."""


# ── Transition guard matrix ────────────────────────────────────────────────────

_VALID_TRANSITIONS: dict[OutcomeStatus, set[OutcomeStatus]] = {
    OutcomeStatus.PENDING_OBSERVATION: {OutcomeStatus.OBSERVED, OutcomeStatus.FAILED},
    OutcomeStatus.OBSERVED:            {OutcomeStatus.CONFIRMED, OutcomeStatus.DISPUTED, OutcomeStatus.FAILED},
    OutcomeStatus.CONFIRMED:           {OutcomeStatus.CLOSED},
    OutcomeStatus.DISPUTED:            {OutcomeStatus.CONFIRMED, OutcomeStatus.CLOSED},
    OutcomeStatus.FAILED:              {OutcomeStatus.CLOSED},
    OutcomeStatus.CLOSED:              set(),  # terminal — no transitions out
}


def _assert_transition(outcome: Outcome, target: OutcomeStatus) -> None:
    allowed = _VALID_TRANSITIONS.get(outcome.outcome_status, set())
    if target not in allowed:
        raise OutcomeError(
            f"Outcome {outcome.outcome_id}: transition "
            f"{outcome.outcome_status.value} → {target.value} is not allowed. "
            f"Allowed from {outcome.outcome_status.value}: "
            f"{[s.value for s in allowed] or 'none (terminal)'}."
        )


# ── Public API ─────────────────────────────────────────────────────────────────

def create_outcome(
    recorded_by:          str,
    source_decision_id:   str | None              = None,
    source_run_id:        str | None              = None,
    source_signal_id:     str | None              = None,
    source_seed_id:       str | None              = None,
    outcome_classification: OutcomeClassification | None = None,
    expected_value:       float | None            = None,
    realized_value:       float | None            = None,
    evidence_payload:     dict[str, Any] | None   = None,
    notes:                str | None              = None,
) -> Outcome:
    """Create a new Outcome entity and persist it.

    Linkage: at least one of source_decision_id or source_run_id is required.
    Starts in PENDING_OBSERVATION status.

    Args:
        recorded_by:           actor recording this outcome.
        source_decision_id:    linked OperatorDecision (preferred linkage).
        source_run_id:         linked pipeline run.
        source_signal_id:      optional upstream signal reference.
        source_seed_id:        optional upstream seed reference.
        outcome_classification: initial classification if known immediately.
        expected_value:        expected numeric value (units defined by evidence).
        realized_value:        realized numeric value if already known.
        evidence_payload:      structured JSON evidence.
        notes:                 human notes.

    Returns:
        Persisted Outcome in PENDING_OBSERVATION status.

    Raises:
        OutcomeError: if no linkage provided.
    """
    if not any([source_decision_id, source_run_id]):
        raise OutcomeError(
            "Outcome must reference at least one of: source_decision_id, source_run_id"
        )

    outcome = Outcome(
        recorded_by            = recorded_by,
        source_decision_id     = source_decision_id,
        source_run_id          = source_run_id,
        source_signal_id       = source_signal_id,
        source_seed_id         = source_seed_id,
        outcome_classification = outcome_classification,
        expected_value         = expected_value,
        realized_value         = realized_value,
        evidence_payload       = evidence_payload or {},
        notes                  = notes,
    )

    from app.signals import store
    store.save_outcome(_outcome_to_dict(outcome))

    logger.info(
        "outcome.create outcome_id=%s actor=%s source_decision=%s source_run=%s",
        outcome.outcome_id, recorded_by, source_decision_id, source_run_id,
    )
    return outcome


def observe_outcome(
    outcome_id:       str,
    actor:            str,
    evidence_payload: dict[str, Any] | None = None,
    realized_value:   float | None          = None,
    notes:            str | None            = None,
) -> Outcome:
    """Transition PENDING_OBSERVATION → OBSERVED.

    Records evidence and optional realized value at the moment of observation.

    Args:
        outcome_id:       ID of the outcome to observe.
        actor:            observer identity.
        evidence_payload: structured evidence gathered at observation time.
        realized_value:   numeric realized value if observable.
        notes:            human notes.

    Returns:
        Updated Outcome in OBSERVED status.
    """
    outcome = _resolve_outcome(outcome_id)
    _assert_transition(outcome, OutcomeStatus.OBSERVED)

    observed = outcome.to_observed(
        evidence_payload = evidence_payload,
        realized_value   = realized_value,
        notes            = notes,
    )

    from app.signals import store
    store.update_outcome(_outcome_to_dict(observed), "outcome.observed")

    logger.info("outcome.observe outcome_id=%s actor=%s", outcome_id, actor)
    return observed


def confirm_outcome(
    outcome_id:      str,
    actor:           str,
    classification:  OutcomeClassification,
    realized_value:  float | None = None,
    notes:           str | None   = None,
) -> Outcome:
    """Transition OBSERVED or DISPUTED → CONFIRMED.

    Classification is required at confirmation time.

    Args:
        outcome_id:     ID of the outcome to confirm.
        actor:          confirming actor.
        classification: OutcomeClassification (required).
        realized_value: final realized value if updated at confirmation.
        notes:          human notes.

    Returns:
        Updated Outcome in CONFIRMED status with classification.
    """
    outcome = _resolve_outcome(outcome_id)
    _assert_transition(outcome, OutcomeStatus.CONFIRMED)

    confirmed = outcome.to_confirmed(
        classification = classification,
        realized_value = realized_value,
        notes          = notes,
    )

    from app.signals import store
    store.update_outcome(_outcome_to_dict(confirmed), "outcome.confirmed")

    logger.info(
        "outcome.confirm outcome_id=%s actor=%s classification=%s",
        outcome_id, actor, classification.value,
    )
    return confirmed


def dispute_outcome(
    outcome_id: str,
    actor:      str,
    reason:     str,
    notes:      str | None = None,
) -> Outcome:
    """Transition OBSERVED → DISPUTED.

    Marks the outcome as contested. Sets error_flag=True.

    Args:
        outcome_id: ID of the outcome to dispute.
        actor:      disputing actor.
        reason:     reason for dispute (required).
        notes:      additional notes.

    Returns:
        Updated Outcome in DISPUTED status.
    """
    outcome = _resolve_outcome(outcome_id)
    _assert_transition(outcome, OutcomeStatus.DISPUTED)

    disputed = outcome.to_disputed(reason=reason, notes=notes)

    from app.signals import store
    store.update_outcome(_outcome_to_dict(disputed), "outcome.disputed")

    logger.info("outcome.dispute outcome_id=%s actor=%s reason=%s", outcome_id, actor, reason)
    return disputed


def fail_outcome(
    outcome_id: str,
    actor:      str,
    reason:     str,
) -> Outcome:
    """Transition PENDING_OBSERVATION or OBSERVED → FAILED.

    Use when observation or confirmation process itself fails.

    Args:
        outcome_id: ID of the outcome to mark failed.
        actor:      actor marking the failure.
        reason:     failure reason.

    Returns:
        Updated Outcome in FAILED status.
    """
    outcome = _resolve_outcome(outcome_id)
    _assert_transition(outcome, OutcomeStatus.FAILED)

    failed = outcome.to_failed(reason=reason)

    from app.signals import store
    store.update_outcome(_outcome_to_dict(failed), "outcome.failed")

    logger.info("outcome.fail outcome_id=%s actor=%s reason=%s", outcome_id, actor, reason)
    return failed


def close_outcome(
    outcome_id: str,
    actor:      str,
    notes:      str | None = None,
) -> Outcome:
    """Transition CONFIRMED, DISPUTED, or FAILED → CLOSED (terminal).

    Computes time_to_resolution_seconds from recorded_at.

    Args:
        outcome_id: ID of the outcome to close.
        actor:      closing actor.
        notes:      final notes.

    Returns:
        Updated Outcome in CLOSED status.

    Raises:
        OutcomeError: if already CLOSED or transition not allowed.
    """
    outcome = _resolve_outcome(outcome_id)
    _assert_transition(outcome, OutcomeStatus.CLOSED)

    closed = outcome.to_closed(notes=notes)

    from app.signals import store
    store.update_outcome(_outcome_to_dict(closed), "outcome.closed")

    logger.info(
        "outcome.close outcome_id=%s actor=%s resolution_secs=%s",
        outcome_id, actor, closed.time_to_resolution_seconds,
    )
    return closed


def get_outcome(outcome_id: str) -> Outcome | None:
    """Load an outcome from the persistent store by ID."""
    from app.signals import store
    row = store.load_outcome_by_id(outcome_id)
    if row is None:
        return None
    return _row_to_outcome(row)


def list_outcomes(
    decision_id: str | None = None,
    run_id:      str | None = None,
    status:      str | None = None,
    limit:       int        = 100,
) -> list[Outcome]:
    """List outcomes from persistent store, optionally filtered."""
    from app.signals import store
    rows = store.load_outcomes(decision_id=decision_id, run_id=run_id, status=status, limit=limit)
    result: list[Outcome] = []
    for row in rows:
        try:
            result.append(_row_to_outcome(row))
        except Exception as exc:
            logger.error("outcomes.list_outcomes: could not reconstruct outcome_id=%s: %s",
                         row.get("outcome_id"), exc)
    return result


# ── Internal helpers ───────────────────────────────────────────────────────────

def _resolve_outcome(outcome_id: str) -> Outcome:
    """Load from DB, raising OutcomeError with a clear message if not found."""
    outcome = get_outcome(outcome_id)
    if outcome is None:
        raise OutcomeError(f"Outcome {outcome_id!r} not found.")
    return outcome


def _outcome_to_dict(outcome: Outcome) -> dict:
    """Convert Outcome to a plain dict suitable for store functions."""
    return {
        "outcome_id":                  outcome.outcome_id,
        "source_decision_id":          outcome.source_decision_id,
        "source_run_id":               outcome.source_run_id,
        "source_signal_id":            outcome.source_signal_id,
        "source_seed_id":              outcome.source_seed_id,
        "outcome_status":              outcome.outcome_status.value,
        "outcome_classification":      outcome.outcome_classification.value if outcome.outcome_classification else None,
        "observed_at":                 outcome.observed_at,
        "recorded_at":                 outcome.recorded_at,
        "updated_at":                  outcome.updated_at,
        "closed_at":                   outcome.closed_at,
        "recorded_by":                 outcome.recorded_by,
        "expected_value":              outcome.expected_value,
        "realized_value":              outcome.realized_value,
        "error_flag":                  outcome.error_flag,
        "time_to_resolution_seconds":  outcome.time_to_resolution_seconds,
        "evidence_payload":            outcome.evidence_payload,
        "notes":                       outcome.notes,
    }


def _row_to_outcome(row: dict) -> Outcome:
    """Reconstruct an Outcome from a DB row dict."""
    cls_val = row.get("outcome_classification")
    return Outcome(
        outcome_id                 = row["outcome_id"],
        source_decision_id         = row.get("source_decision_id"),
        source_run_id              = row.get("source_run_id"),
        source_signal_id           = row.get("source_signal_id"),
        source_seed_id             = row.get("source_seed_id"),
        outcome_status             = OutcomeStatus(row["outcome_status"]),
        outcome_classification     = OutcomeClassification(cls_val) if cls_val else None,
        observed_at                = _coerce_dt(row["observed_at"]) if row.get("observed_at") else None,
        recorded_at                = _coerce_dt(row["recorded_at"]),
        updated_at                 = _coerce_dt(row["updated_at"]),
        closed_at                  = _coerce_dt(row["closed_at"]) if row.get("closed_at") else None,
        recorded_by                = row["recorded_by"],
        expected_value             = row.get("expected_value"),
        realized_value             = row.get("realized_value"),
        error_flag                 = bool(row.get("error_flag", False)),
        time_to_resolution_seconds = row.get("time_to_resolution_secs"),
        evidence_payload           = row.get("evidence_payload") or {},
        notes                      = row.get("notes"),
    )


def _coerce_dt(value) -> datetime:
    if isinstance(value, datetime):
        return value if value.tzinfo else value.replace(tzinfo=timezone.utc)
    if isinstance(value, str):
        dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
        return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)
    raise TypeError(f"Cannot coerce {type(value)} to datetime: {value!r}")
