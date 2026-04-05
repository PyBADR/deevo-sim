"""decisions.engine — Operator Layer decision lifecycle.

This is the authoritative engine for creating, executing, and closing
OperatorDecisions.  It does NOT bypass signal/seed/run layers.

State machine:
    CREATED → IN_REVIEW → EXECUTED → CLOSED
    CREATED → IN_REVIEW → FAILED   → CLOSED
    CREATED → EXECUTED  (direct execution without explicit review step)

Transition guard matrix:
    CREATED   → IN_REVIEW  ✓  (review_decision)
    CREATED   → EXECUTED   ✓  (execute_decision — skips IN_REVIEW)
    IN_REVIEW → EXECUTED   ✓  (execute_decision)
    IN_REVIEW → FAILED     ✓  (execute_decision on error)
    EXECUTED  → CLOSED     ✓  (close_decision)
    FAILED    → CLOSED     ✓  (close_decision)
    CLOSED    → any        ✗  DecisionError

Execution dispatch by DecisionType:
    TRIGGER_RUN         → run_unified_pipeline() → persists via store + runs cache
    APPROVE_ACTION      → record approval in audit log
    REJECT_ACTION       → record rejection in audit log
    ESCALATE            → record escalation in audit log
    IGNORE              → record ignore in audit log
    OVERRIDE_RUN_RESULT → persist override payload; record in audit log

Linkage requirement:
    At least one of source_signal_id, source_seed_id, source_run_id must be
    provided.  The engine rejects orphan decisions before they are persisted.
"""

from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone
from typing import Any

from app.domain.models.operator_decision import (
    DecisionStatus,
    DecisionType,
    OperatorDecision,
    OutcomeStatus,
)

logger = logging.getLogger("observatory.decisions")


# ── Exception ─────────────────────────────────────────────────────────────────

class DecisionError(ValueError):
    """Raised for invalid decision operations."""


# ── Transition guard ──────────────────────────────────────────────────────────

_VALID_TRANSITIONS: dict[DecisionStatus, set[DecisionStatus]] = {
    DecisionStatus.CREATED:   {DecisionStatus.IN_REVIEW, DecisionStatus.EXECUTED, DecisionStatus.FAILED},
    DecisionStatus.IN_REVIEW: {DecisionStatus.EXECUTED, DecisionStatus.FAILED},
    DecisionStatus.EXECUTED:  {DecisionStatus.CLOSED},
    DecisionStatus.FAILED:    {DecisionStatus.CLOSED},
    DecisionStatus.CLOSED:    set(),  # terminal
}


def _assert_transition(decision: OperatorDecision, target: DecisionStatus) -> None:
    allowed = _VALID_TRANSITIONS.get(decision.decision_status, set())
    if target not in allowed:
        raise DecisionError(
            f"Decision {decision.decision_id}: transition "
            f"{decision.decision_status.value} → {target.value} is not allowed. "
            f"Current status: {decision.decision_status.value}."
        )


# ── Public API ────────────────────────────────────────────────────────────────

def create_decision(
    decision_type:     DecisionType,
    created_by:        str,
    source_signal_id:  str | None      = None,
    source_seed_id:    str | None      = None,
    source_run_id:     str | None      = None,
    decision_payload:  dict[str, Any]  | None = None,
    rationale:         str | None      = None,
    confidence_score:  float | None    = None,
) -> OperatorDecision:
    """Create a new OperatorDecision and persist it.

    Linkage validation: at least one source reference is required.

    Args:
        decision_type:    classification of the decision.
        created_by:       identity of the creating operator.
        source_signal_id: (optional) signal that prompted this decision.
        source_seed_id:   (optional) seed that prompted this decision.
        source_run_id:    (optional) run that prompted this decision.
        decision_payload: structured context for this decision type.
        rationale:        human-readable justification.
        confidence_score: operator confidence in the decision (0-1).

    Returns:
        Persisted OperatorDecision in CREATED status.

    Raises:
        DecisionError: if no source linkage provided.
    """
    if not any([source_signal_id, source_seed_id, source_run_id]):
        raise DecisionError(
            "OperatorDecision must reference at least one of: "
            "source_signal_id, source_seed_id, source_run_id"
        )

    decision = OperatorDecision(
        decision_type    = decision_type,
        created_by       = created_by,
        source_signal_id = source_signal_id,
        source_seed_id   = source_seed_id,
        source_run_id    = source_run_id,
        decision_payload = decision_payload or {},
        rationale        = rationale,
        confidence_score = confidence_score,
    )

    from app.signals import store
    store.save_decision(_decision_to_dict(decision))

    logger.info(
        "decision.create decision_id=%s type=%s actor=%s source_signal=%s source_seed=%s source_run=%s",
        decision.decision_id, decision.decision_type.value, created_by,
        source_signal_id, source_seed_id, source_run_id,
    )
    return decision


def execute_decision(
    decision_id: str,
    actor:       str,
    params:      dict[str, Any] | None = None,
) -> OperatorDecision:
    """Execute a decision — dispatch to type-specific handler.

    Valid from CREATED or IN_REVIEW status.

    Execution handlers by type:
        TRIGGER_RUN         → runs run_unified_pipeline() and persists the run
        APPROVE_ACTION      → writes audit approval record
        REJECT_ACTION       → writes audit rejection record
        ESCALATE            → writes escalation audit record
        IGNORE              → writes ignore audit record
        OVERRIDE_RUN_RESULT → persists override payload in outcome

    Args:
        decision_id: ID of the decision to execute.
        actor:       identity of the executing operator.
        params:      optional runtime parameters (e.g. template_id for TRIGGER_RUN).

    Returns:
        Updated OperatorDecision in EXECUTED status.

    Raises:
        DecisionError: decision not found, invalid transition, or execution failure.
    """
    decision = _resolve_decision(decision_id)
    _assert_transition(decision, DecisionStatus.EXECUTED)
    params = params or {}

    try:
        outcome_payload = _dispatch_execution(decision, actor, params)
    except DecisionError:
        raise
    except Exception as exc:
        # Transition to FAILED and persist before raising
        failed = decision.to_failed(str(exc))
        from app.signals import store
        store.update_decision(_decision_to_dict(failed), "decision.failed")
        logger.error("decision.execute FAILED decision_id=%s: %s", decision_id, exc)
        raise DecisionError(f"Decision {decision_id} execution failed: {exc}") from exc

    executed = decision.to_executed(outcome_payload)
    from app.signals import store
    store.update_decision(_decision_to_dict(executed), "decision.executed")

    logger.info(
        "decision.execute decision_id=%s type=%s actor=%s outcome=%s",
        decision_id, decision.decision_type.value, actor,
        executed.outcome_status.value,
    )
    return executed


def close_decision(
    decision_id:    str,
    actor:          str,
    outcome_status: OutcomeStatus = OutcomeStatus.SUCCESS,
) -> OperatorDecision:
    """Close a decision (terminal state).

    Valid from EXECUTED or FAILED status only.

    Args:
        decision_id:    ID of the decision to close.
        actor:          identity of the closing operator.
        outcome_status: final outcome classification.

    Returns:
        Updated OperatorDecision in CLOSED status.

    Raises:
        DecisionError: decision not found or invalid transition.
    """
    decision = _resolve_decision(decision_id)
    _assert_transition(decision, DecisionStatus.CLOSED)

    closed = decision.to_closed(outcome_status)
    from app.signals import store
    store.update_decision(_decision_to_dict(closed), "decision.closed")

    logger.info(
        "decision.close decision_id=%s actor=%s outcome=%s",
        decision_id, actor, outcome_status.value,
    )
    return closed


def get_decision(decision_id: str) -> OperatorDecision | None:
    """Load a decision from the persistent store by ID."""
    from app.signals import store
    row = store.load_decision_by_id(decision_id)
    if row is None:
        return None
    return _row_to_decision(row)


def list_decisions(
    status: str | None        = None,
    decision_type: str | None = None,
    limit: int                = 100,
) -> list[OperatorDecision]:
    """List decisions from persistent store, optionally filtered."""
    from app.signals import store
    rows = store.load_decisions(status=status, decision_type=decision_type, limit=limit)
    result: list[OperatorDecision] = []
    for row in rows:
        try:
            result.append(_row_to_decision(row))
        except Exception as exc:
            logger.error("decisions.list_decisions: could not reconstruct decision_id=%s: %s",
                         row.get("decision_id"), exc)
    return result


# ── Execution handlers ────────────────────────────────────────────────────────

def _dispatch_execution(
    decision: OperatorDecision,
    actor:    str,
    params:   dict[str, Any],
) -> dict[str, Any]:
    """Route to the correct execution handler by decision_type.

    Returns the outcome_payload dict.
    """
    dispatch: dict[DecisionType, Any] = {
        DecisionType.TRIGGER_RUN:         _execute_trigger_run,
        DecisionType.APPROVE_ACTION:      _execute_approve_action,
        DecisionType.REJECT_ACTION:       _execute_reject_action,
        DecisionType.ESCALATE:            _execute_escalate,
        DecisionType.IGNORE:              _execute_ignore,
        DecisionType.OVERRIDE_RUN_RESULT: _execute_override_run_result,
    }
    handler = dispatch.get(decision.decision_type)
    if handler is None:
        raise DecisionError(f"No execution handler for decision_type={decision.decision_type}")
    return handler(decision, actor, params)


def _execute_trigger_run(
    decision: OperatorDecision,
    actor:    str,
    params:   dict[str, Any],
) -> dict[str, Any]:
    """Execute TRIGGER_RUN: run the unified pipeline and persist the result.

    Uses the same run infrastructure as POST /runs and hitl.approve() —
    no parallel pipeline.

    Required: template_id in decision_payload or params.
    """
    payload   = {**decision.decision_payload, **params}
    template_id   = payload.get("template_id") or payload.get("scenario_id", "")
    severity      = float(payload.get("severity", 0.7))
    horizon_hours = int(payload.get("horizon_hours", 168))
    label         = payload.get("label") or f"[Decision] {decision.decision_id}"

    if not template_id:
        raise DecisionError("TRIGGER_RUN requires template_id in decision_payload or params")

    from app.simulation.runner import run_unified_pipeline
    result = run_unified_pipeline(
        template_id   = template_id,
        severity      = severity,
        horizon_hours = horizon_hours,
        label         = label,
    )

    run_id = str(uuid.uuid4())
    result["run_id"]       = run_id
    result["decision_id"]  = decision.decision_id
    result["triggered_by"] = actor

    # Persist via canonical run store — identical to hitl.approve() pattern
    now = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    run_meta = {
        "run_id":          run_id,
        "scenario_id":     template_id,
        "status":          result.get("status", "completed"),
        "severity":        severity,
        "horizon_hours":   horizon_hours,
        "label":           label,
        "reviewed_by":     actor,
        "stages_completed": result.get("stages_completed", 0),
        "stages_total":    13,
        "computed_in_ms":  result.get("duration_ms"),
        "created_at":      now,
        "completed_at":    now,
    }

    from app.signals import store
    store.save_run(run_meta)
    store.save_run_result(run_id, result)

    try:
        from app.api.v1.routes.runs import get_run_store, get_result_store
        get_run_store()[run_id]    = run_meta
        get_result_store()[run_id] = result
    except Exception as exc:
        logger.warning("_execute_trigger_run: could not warm run cache: %s", exc)

    return {
        "run_id":           run_id,
        "status":           result.get("status", "completed"),
        "stages_completed": result.get("stages_completed", 0),
        "template_id":      template_id,
        "severity":         severity,
    }


def _execute_approve_action(
    decision: OperatorDecision,
    actor:    str,
    params:   dict[str, Any],
) -> dict[str, Any]:
    """Execute APPROVE_ACTION: record approval in audit trail."""
    action_id   = decision.decision_payload.get("action_id", "")
    source_run  = decision.source_run_id or params.get("run_id", "")
    _write_decision_audit(
        entity_id = decision.decision_id,
        actor     = actor,
        event_tag = "action.approved",
        meta      = {"action_id": action_id, "run_id": source_run},
    )
    return {"action_id": action_id, "run_id": source_run, "approved_by": actor}


def _execute_reject_action(
    decision: OperatorDecision,
    actor:    str,
    params:   dict[str, Any],
) -> dict[str, Any]:
    """Execute REJECT_ACTION: record rejection in audit trail."""
    action_id  = decision.decision_payload.get("action_id", "")
    source_run = decision.source_run_id or params.get("run_id", "")
    _write_decision_audit(
        entity_id = decision.decision_id,
        actor     = actor,
        event_tag = "action.rejected",
        meta      = {"action_id": action_id, "run_id": source_run,
                     "reason": decision.rationale or params.get("reason", "")},
    )
    return {"action_id": action_id, "run_id": source_run, "rejected_by": actor}


def _execute_escalate(
    decision: OperatorDecision,
    actor:    str,
    params:   dict[str, Any],
) -> dict[str, Any]:
    """Execute ESCALATE: record escalation in audit trail."""
    target    = decision.decision_payload.get("escalation_target", params.get("escalation_target", "ADMIN"))
    rationale = decision.rationale or params.get("rationale", "")
    _write_decision_audit(
        entity_id = decision.decision_id,
        actor     = actor,
        event_tag = "decision.escalated",
        meta      = {
            "escalation_target":  target,
            "rationale":          rationale,
            "source_signal":      decision.source_signal_id,
            "source_seed":        decision.source_seed_id,
            "source_run":         decision.source_run_id,
        },
    )
    return {"escalation_target": target, "escalated_by": actor, "rationale": rationale}


def _execute_ignore(
    decision: OperatorDecision,
    actor:    str,
    params:   dict[str, Any],
) -> dict[str, Any]:
    """Execute IGNORE: record conscious ignore in audit trail."""
    reason = decision.rationale or params.get("reason", "Operator decision to ignore")
    _write_decision_audit(
        entity_id = decision.decision_id,
        actor     = actor,
        event_tag = "decision.ignored",
        meta      = {
            "reason":        reason,
            "source_signal": decision.source_signal_id,
            "source_seed":   decision.source_seed_id,
            "source_run":    decision.source_run_id,
        },
    )
    return {"ignored_by": actor, "reason": reason}


def _execute_override_run_result(
    decision: OperatorDecision,
    actor:    str,
    params:   dict[str, Any],
) -> dict[str, Any]:
    """Execute OVERRIDE_RUN_RESULT: persist override payload in audit trail."""
    run_id          = decision.source_run_id or params.get("run_id", "")
    override_values = {**decision.decision_payload, **params.get("override_values", {})}
    rationale       = decision.rationale or params.get("rationale", "")

    if not run_id:
        raise DecisionError("OVERRIDE_RUN_RESULT requires source_run_id or run_id in params")

    _write_decision_audit(
        entity_id = decision.decision_id,
        actor     = actor,
        event_tag = "run.result_overridden",
        meta      = {
            "run_id":          run_id,
            "override_values": override_values,
            "rationale":       rationale,
        },
    )
    return {"run_id": run_id, "overridden_by": actor, "override_values": override_values}


# ── Internal helpers ──────────────────────────────────────────────────────────

def _resolve_decision(decision_id: str) -> OperatorDecision:
    """Load from DB, raising DecisionError with a clear message if not found."""
    decision = get_decision(decision_id)
    if decision is None:
        raise DecisionError(f"Decision {decision_id!r} not found.")
    return decision


def _decision_to_dict(decision: OperatorDecision) -> dict:
    """Convert OperatorDecision to a plain dict suitable for store functions."""
    return {
        "decision_id":       decision.decision_id,
        "source_signal_id":  decision.source_signal_id,
        "source_seed_id":    decision.source_seed_id,
        "source_run_id":     decision.source_run_id,
        "decision_type":     decision.decision_type.value,
        "decision_status":   decision.decision_status.value,
        "decision_payload":  decision.decision_payload,
        "rationale":         decision.rationale,
        "confidence_score":  decision.confidence_score,
        "created_by":        decision.created_by,
        "outcome_status":    decision.outcome_status.value,
        "outcome_payload":   decision.outcome_payload,
        "created_at":        decision.created_at,
        "updated_at":        decision.updated_at,
        "closed_at":         decision.closed_at,
    }


def _row_to_decision(row: dict) -> OperatorDecision:
    """Reconstruct an OperatorDecision from a DB row dict."""
    return OperatorDecision(
        decision_id      = row["decision_id"],
        source_signal_id = row.get("source_signal_id"),
        source_seed_id   = row.get("source_seed_id"),
        source_run_id    = row.get("source_run_id"),
        decision_type    = DecisionType(row["decision_type"]),
        decision_status  = DecisionStatus(row["decision_status"]),
        decision_payload = row.get("decision_payload") or {},
        rationale        = row.get("rationale"),
        confidence_score = row.get("confidence_score"),
        created_by       = row["created_by"],
        outcome_status   = OutcomeStatus(row.get("outcome_status", "PENDING")),
        outcome_payload  = row.get("outcome_payload") or {},
        created_at       = _coerce_dt(row["created_at"]),
        updated_at       = _coerce_dt(row["updated_at"]),
        closed_at        = _coerce_dt(row["closed_at"]) if row.get("closed_at") else None,
    )


def _coerce_dt(value) -> datetime:
    if isinstance(value, datetime):
        return value if value.tzinfo else value.replace(tzinfo=timezone.utc)
    if isinstance(value, str):
        dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
        return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)
    raise TypeError(f"Cannot coerce {type(value)} to datetime: {value!r}")


def _write_decision_audit(
    entity_id: str,
    actor:     str,
    event_tag: str,
    meta:      dict[str, Any],
) -> None:
    """Write a sub-event to the signal audit log for a decision action."""
    try:
        from app.signals import store
        store.write_audit(
            event_type  = event_tag,
            entity_id   = entity_id,
            entity_kind = "decision",
            actor       = actor,
            reason      = None,
            metadata    = meta,
        )
    except Exception as exc:
        logger.warning("_write_decision_audit failed event=%s entity=%s: %s",
                       event_tag, entity_id, exc)
