"""
authority.engine — Backend Decision Authority Layer transition engine.

Responsibilities:
  - Strict FSM transition enforcement (no skipping states)
  - RBAC permission checks per action
  - Atomic write: update DecisionAuthorityRecord + append AuthorityEventRecord
  - SHA-256 hash chain (backend-owned, verifiable)
  - RESUBMIT increments revision_number and resets approval/execution fields
  - OVERRIDE is explicit, auditable, and records prior status

Non-negotiable rules enforced here:
  1. Execution requires authority_status == APPROVED or EXECUTION_PENDING
  2. Terminal states (EXECUTED, REVOKED, WITHDRAWN) are immutable except via OVERRIDE
  3. Every transition writes a hash-chained event atomically with the record update
"""

from __future__ import annotations

import hashlib
import json
import logging
import uuid
from datetime import datetime, timezone
from typing import Any

from sqlalchemy.orm import Session

from app.signals.store import _get_engine
from app.authority.models import DecisionAuthorityRecord, AuthorityEventRecord

logger = logging.getLogger("observatory.authority")


# ── Enums ─────────────────────────────────────────────────────────────────────

AUTHORITY_STATUSES = frozenset({
    "PROPOSED", "UNDER_REVIEW", "APPROVED", "REJECTED", "RETURNED",
    "ESCALATED", "EXECUTION_PENDING", "EXECUTED", "EXECUTION_FAILED",
    "REVOKED", "WITHDRAWN",
})

AUTHORITY_ACTIONS = frozenset({
    "PROPOSE", "SUBMIT_FOR_REVIEW", "APPROVE", "REJECT", "RETURN_FOR_REVISION",
    "ESCALATE", "QUEUE_EXECUTION", "EXECUTE", "REPORT_EXECUTION_FAILURE",
    "REVOKE", "WITHDRAW", "OVERRIDE", "ANNOTATE", "RESUBMIT",
})

TERMINAL_STATES = frozenset({"EXECUTED", "REVOKED", "WITHDRAWN"})

# ── Transition guard matrix ────────────────────────────────────────────────────

AUTHORITY_TRANSITIONS: dict[str, frozenset[str]] = {
    "PROPOSED":          frozenset({"UNDER_REVIEW", "WITHDRAWN"}),
    "UNDER_REVIEW":      frozenset({"APPROVED", "REJECTED", "ESCALATED", "RETURNED"}),
    "APPROVED":          frozenset({"EXECUTION_PENDING", "REVOKED"}),
    "REJECTED":          frozenset({"PROPOSED"}),           # via RESUBMIT
    "RETURNED":          frozenset({"PROPOSED"}),           # via RESUBMIT
    "ESCALATED":         frozenset({"UNDER_REVIEW"}),
    "EXECUTION_PENDING": frozenset({"EXECUTED", "EXECUTION_FAILED"}),
    "EXECUTION_FAILED":  frozenset({"PROPOSED", "WITHDRAWN"}),
    "EXECUTED":          frozenset(),                       # terminal
    "REVOKED":           frozenset(),                       # terminal
    "WITHDRAWN":         frozenset(),                       # terminal
}

# Map action → (required from_status set, target_status)
# None from_status means "any non-terminal" (used for OVERRIDE/ANNOTATE)
ACTION_TARGET: dict[str, tuple[frozenset[str] | None, str | None]] = {
    "PROPOSE":                  (frozenset({"PROPOSED"}),   "PROPOSED"),      # initial only
    "SUBMIT_FOR_REVIEW":        (frozenset({"PROPOSED"}),   "UNDER_REVIEW"),
    "APPROVE":                  (frozenset({"UNDER_REVIEW"}),"APPROVED"),
    "REJECT":                   (frozenset({"UNDER_REVIEW"}),"REJECTED"),
    "RETURN_FOR_REVISION":      (frozenset({"UNDER_REVIEW"}),"RETURNED"),
    "ESCALATE":                 (frozenset({"UNDER_REVIEW"}),"ESCALATED"),
    "QUEUE_EXECUTION":          (frozenset({"APPROVED"}),   "EXECUTION_PENDING"),
    "EXECUTE":                  (frozenset({"APPROVED", "EXECUTION_PENDING"}), "EXECUTED"),
    "REPORT_EXECUTION_FAILURE": (frozenset({"EXECUTION_PENDING"}), "EXECUTION_FAILED"),
    "REVOKE":                   (None,                       "REVOKED"),       # any non-terminal
    "WITHDRAW":                 (None,                       "WITHDRAWN"),     # any non-terminal
    "RESUBMIT":                 (frozenset({"REJECTED", "RETURNED", "EXECUTION_FAILED"}), "PROPOSED"),
    "OVERRIDE":                 (None,                       None),            # target explicit in call
    "ANNOTATE":                 (None,                       None),            # no status change
}


# ── RBAC permission matrix ─────────────────────────────────────────────────────

# Maps action → set of roles authorized to perform it
# Roles match app.core.rbac.Role values (lowercase strings)
# IMPORTANT: This matrix MUST align with app.core.rbac.ROLE_PERMISSIONS.
# The route layer enforces rbac.py permissions; this matrix enforces at engine level.
# Both checks must pass — defense in depth.
AUTHORITY_ACTION_PERMISSIONS: dict[str, frozenset[str]] = {
    "PROPOSE":                  frozenset({"analyst", "operator", "admin"}),
    "SUBMIT_FOR_REVIEW":        frozenset({"analyst", "operator", "admin"}),
    "APPROVE":                  frozenset({"admin"}),
    "REJECT":                   frozenset({"admin"}),
    "RETURN_FOR_REVISION":      frozenset({"admin"}),
    "ESCALATE":                 frozenset({"operator", "admin"}),
    "QUEUE_EXECUTION":          frozenset({"operator", "admin"}),
    "EXECUTE":                  frozenset({"operator", "admin"}),
    "REPORT_EXECUTION_FAILURE": frozenset({"operator", "admin"}),
    "REVOKE":                   frozenset({"admin"}),
    "WITHDRAW":                 frozenset({"analyst", "operator", "admin"}),
    "RESUBMIT":                 frozenset({"analyst", "operator", "admin"}),
    "OVERRIDE":                 frozenset({"admin"}),
    "ANNOTATE":                 frozenset({"analyst", "operator", "admin", "regulator"}),
}


# ── Exceptions ────────────────────────────────────────────────────────────────

class AuthorityError(ValueError):
    """Raised for invalid authority operations (bad transition, missing record, etc.)."""


class AuthorityPermissionError(PermissionError):
    """Raised when the actor's role lacks permission for the requested action."""


class AuthorityNotFoundError(LookupError):
    """Raised when a requested authority record does not exist."""


# ── Internal helpers ──────────────────────────────────────────────────────────

def _now() -> datetime:
    return datetime.now(timezone.utc)


def _authority_id() -> str:
    return f"auth-{uuid.uuid4().hex[:12]}"


def _event_id() -> str:
    return f"aev-{uuid.uuid4().hex[:12]}"


def _j(obj: Any) -> str:
    return json.dumps(obj, default=str)


def _normalize_ts(ts: datetime) -> str:
    """Produce a stable, timezone-normalized ISO-8601 string for hash computation.

    Always emits UTC with microseconds: "YYYY-MM-DDTHH:MM:SS.ffffffZ"
    This ensures the hash is identical whether computed at write time or
    re-derived from the value read back from the database (SQLite may strip
    the +00:00 suffix on round-trip).
    """
    if ts.tzinfo is not None:
        ts = ts.astimezone(timezone.utc).replace(tzinfo=None)
    return ts.strftime("%Y-%m-%dT%H:%M:%S.%f") + "Z"


def _compute_event_hash(
    event_id: str,
    authority_id: str,
    action: str,
    from_status: str | None,
    to_status: str,
    actor_id: str,
    timestamp_iso: str,
    previous_event_hash: str | None,
) -> str:
    """SHA-256 hash over deterministic event field serialization.

    timestamp_iso must be produced by _normalize_ts() for reproducibility.
    """
    payload = {
        "event_id": event_id,
        "authority_id": authority_id,
        "action": action,
        "from_status": from_status or "",
        "to_status": to_status,
        "actor_id": actor_id,
        "timestamp": timestamp_iso,
        "previous_event_hash": previous_event_hash or "",
    }
    data = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(data.encode("utf-8")).hexdigest()


def _get_previous_hash(db: Session, authority_id: str) -> str | None:
    """Return the event_hash of the most recent event for this authority (or None)."""
    row = (
        db.query(AuthorityEventRecord.event_hash)
        .filter(AuthorityEventRecord.authority_id == authority_id)
        .order_by(AuthorityEventRecord.timestamp.desc())
        .first()
    )
    return row[0] if row else None


def _append_event(
    db: Session,
    authority_id: str,
    decision_id: str,
    action: str,
    from_status: str | None,
    to_status: str,
    actor_id: str,
    actor_role: str,
    notes: str | None = None,
    metadata: dict[str, Any] | None = None,
) -> AuthorityEventRecord:
    """Append one hash-chained AuthorityEventRecord within the current session."""
    eid = _event_id()
    ts = _now()
    ts_iso = _normalize_ts(ts)
    prev_hash = _get_previous_hash(db, authority_id)

    event_hash = _compute_event_hash(
        event_id=eid,
        authority_id=authority_id,
        action=action,
        from_status=from_status,
        to_status=to_status,
        actor_id=actor_id,
        timestamp_iso=ts_iso,
        previous_event_hash=prev_hash,
    )

    event = AuthorityEventRecord(
        event_id=eid,
        authority_id=authority_id,
        decision_id=decision_id,
        action=action,
        from_status=from_status,
        to_status=to_status,
        actor_id=actor_id,
        actor_role=actor_role,
        timestamp=ts,
        notes=notes,
        metadata_json=_j(metadata or {}),
        event_hash=event_hash,
        previous_event_hash=prev_hash,
    )
    db.add(event)
    return event


def _assert_permission(action: str, actor_role: str) -> None:
    allowed = AUTHORITY_ACTION_PERMISSIONS.get(action, frozenset())
    if actor_role.lower() not in allowed:
        raise AuthorityPermissionError(
            f"Role '{actor_role}' is not authorized to perform action '{action}'. "
            f"Authorized roles: {sorted(allowed)}"
        )


def _assert_transition(record: DecisionAuthorityRecord, action: str, target_status: str | None) -> None:
    current = record.authority_status
    if target_status is None:
        return  # ANNOTATE / OVERRIDE with explicit target validated by caller

    allowed = AUTHORITY_TRANSITIONS.get(current, frozenset())
    if target_status not in allowed:
        raise AuthorityError(
            f"Authority {record.authority_id}: transition {current} → {target_status} "
            f"is not allowed for action '{action}'. "
            f"Valid transitions from {current}: {sorted(allowed) or 'none (terminal)'}"
        )


def _record_to_dict(rec: DecisionAuthorityRecord) -> dict[str, Any]:
    return {
        "authority_id":         rec.authority_id,
        "decision_id":          rec.decision_id,
        "authority_status":     rec.authority_status,
        "revision_number":      rec.revision_number,
        "escalation_level":     rec.escalation_level,
        "priority":             rec.priority,
        "proposed_by":          rec.proposed_by,
        "proposed_by_role":     rec.proposed_by_role,
        "proposal_rationale":   rec.proposal_rationale,
        "reviewer_id":          rec.reviewer_id,
        "reviewer_role":        rec.reviewer_role,
        "review_started_at":    rec.review_started_at.isoformat() if rec.review_started_at else None,
        "authority_actor_id":   rec.authority_actor_id,
        "authority_actor_role": rec.authority_actor_role,
        "authority_decided_at": rec.authority_decided_at.isoformat() if rec.authority_decided_at else None,
        "authority_rationale":  rec.authority_rationale,
        "executed_by":          rec.executed_by,
        "executed_by_role":     rec.executed_by_role,
        "executed_at":          rec.executed_at.isoformat() if rec.executed_at else None,
        "execution_result":     rec.execution_result,
        "linked_outcome_id":    rec.linked_outcome_id,
        "linked_value_id":      rec.linked_value_id,
        "source_run_id":        rec.source_run_id,
        "source_scenario_label":rec.source_scenario_label,
        "tags":                 json.loads(rec.tags_json) if rec.tags_json else [],
        "created_at":           rec.created_at.isoformat() if rec.created_at else None,
        "updated_at":           rec.updated_at.isoformat() if rec.updated_at else None,
    }


def _event_to_dict(ev: AuthorityEventRecord) -> dict[str, Any]:
    return {
        "event_id":            ev.event_id,
        "authority_id":        ev.authority_id,
        "decision_id":         ev.decision_id,
        "action":              ev.action,
        "from_status":         ev.from_status,
        "to_status":           ev.to_status,
        "actor_id":            ev.actor_id,
        "actor_role":          ev.actor_role,
        "timestamp":           _normalize_ts(ev.timestamp) if ev.timestamp else None,
        "notes":               ev.notes,
        "metadata":            json.loads(ev.metadata_json) if ev.metadata_json else {},
        "event_hash":          ev.event_hash,
        "previous_event_hash": ev.previous_event_hash,
    }


# ── Public engine API ─────────────────────────────────────────────────────────

def propose(
    decision_id: str,
    actor_id: str,
    actor_role: str,
    rationale: str | None = None,
    priority: int = 3,
    source_run_id: str | None = None,
    source_scenario_label: str | None = None,
    tags: list[str] | None = None,
    notes: str | None = None,
) -> dict[str, Any]:
    """Create a new DecisionAuthority envelope in PROPOSED state.

    Raises AuthorityError if an active authority already exists for decision_id.
    Raises AuthorityPermissionError if actor_role cannot PROPOSE.
    """
    _assert_permission("PROPOSE", actor_role)

    with Session(_get_engine()) as db:
        existing = db.query(DecisionAuthorityRecord).filter(
            DecisionAuthorityRecord.decision_id == decision_id
        ).one_or_none()
        if existing is not None:
            raise AuthorityError(
                f"Decision '{decision_id}' already has an authority envelope "
                f"(authority_id={existing.authority_id}, status={existing.authority_status}). "
                f"Use RESUBMIT to restart the lifecycle."
            )

        now = _now()
        aid = _authority_id()
        rec = DecisionAuthorityRecord(
            authority_id=aid,
            decision_id=decision_id,
            authority_status="PROPOSED",
            revision_number=1,
            escalation_level=0,
            priority=max(1, min(5, priority)),
            proposed_by=actor_id,
            proposed_by_role=actor_role,
            proposal_rationale=rationale,
            source_run_id=source_run_id,
            source_scenario_label=source_scenario_label,
            tags_json=_j(tags or []),
            created_at=now,
            updated_at=now,
        )
        db.add(rec)
        db.flush()  # assign PK before appending event

        _append_event(
            db, aid, decision_id,
            action="PROPOSE",
            from_status=None,
            to_status="PROPOSED",
            actor_id=actor_id,
            actor_role=actor_role,
            notes=notes,
        )
        db.commit()
        db.refresh(rec)
        return _record_to_dict(rec)


def _transition(
    decision_id: str,
    action: str,
    actor_id: str,
    actor_role: str,
    target_status: str,
    notes: str | None = None,
    update_fields: dict[str, Any] | None = None,
    metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Generic internal helper — asserts permission + transition, applies update, appends event."""
    _assert_permission(action, actor_role)

    with Session(_get_engine()) as db:
        rec = db.query(DecisionAuthorityRecord).filter(
            DecisionAuthorityRecord.decision_id == decision_id
        ).one_or_none()
        if rec is None:
            raise AuthorityNotFoundError(f"No authority envelope for decision '{decision_id}'.")

        _assert_transition(rec, action, target_status)

        from_status = rec.authority_status
        now = _now()
        rec.authority_status = target_status
        rec.updated_at = now
        if update_fields:
            for k, v in update_fields.items():
                setattr(rec, k, v)

        _append_event(
            db, rec.authority_id, decision_id,
            action=action,
            from_status=from_status,
            to_status=target_status,
            actor_id=actor_id,
            actor_role=actor_role,
            notes=notes,
            metadata=metadata,
        )
        db.commit()
        db.refresh(rec)
        return _record_to_dict(rec)


def submit_for_review(
    decision_id: str,
    actor_id: str,
    actor_role: str,
    reviewer_id: str | None = None,
    reviewer_role: str | None = None,
    notes: str | None = None,
) -> dict[str, Any]:
    now = _now()
    return _transition(
        decision_id, "SUBMIT_FOR_REVIEW", actor_id, actor_role,
        target_status="UNDER_REVIEW",
        notes=notes,
        update_fields={
            "reviewer_id": reviewer_id,
            "reviewer_role": reviewer_role,
            "review_started_at": now,
        },
    )


def approve(
    decision_id: str,
    actor_id: str,
    actor_role: str,
    rationale: str | None = None,
    notes: str | None = None,
) -> dict[str, Any]:
    now = _now()
    return _transition(
        decision_id, "APPROVE", actor_id, actor_role,
        target_status="APPROVED",
        notes=notes,
        update_fields={
            "authority_actor_id": actor_id,
            "authority_actor_role": actor_role,
            "authority_decided_at": now,
            "authority_rationale": rationale,
        },
    )


def reject(
    decision_id: str,
    actor_id: str,
    actor_role: str,
    rationale: str | None = None,
    notes: str | None = None,
) -> dict[str, Any]:
    now = _now()
    return _transition(
        decision_id, "REJECT", actor_id, actor_role,
        target_status="REJECTED",
        notes=notes,
        update_fields={
            "authority_actor_id": actor_id,
            "authority_actor_role": actor_role,
            "authority_decided_at": now,
            "authority_rationale": rationale,
        },
    )


def return_for_revision(
    decision_id: str,
    actor_id: str,
    actor_role: str,
    rationale: str | None = None,
    notes: str | None = None,
) -> dict[str, Any]:
    now = _now()
    return _transition(
        decision_id, "RETURN_FOR_REVISION", actor_id, actor_role,
        target_status="RETURNED",
        notes=notes,
        update_fields={
            "authority_actor_id": actor_id,
            "authority_actor_role": actor_role,
            "authority_decided_at": now,
            "authority_rationale": rationale,
        },
    )


def escalate(
    decision_id: str,
    actor_id: str,
    actor_role: str,
    notes: str | None = None,
) -> dict[str, Any]:
    _assert_permission("ESCALATE", actor_role)
    with Session(_get_engine()) as db:
        rec = db.query(DecisionAuthorityRecord).filter(
            DecisionAuthorityRecord.decision_id == decision_id
        ).one_or_none()
        if rec is None:
            raise AuthorityNotFoundError(f"No authority envelope for decision '{decision_id}'.")
        _assert_transition(rec, "ESCALATE", "ESCALATED")
        from_status = rec.authority_status
        now = _now()
        rec.authority_status = "ESCALATED"
        rec.escalation_level = rec.escalation_level + 1
        rec.updated_at = now
        _append_event(
            db, rec.authority_id, decision_id,
            action="ESCALATE",
            from_status=from_status,
            to_status="ESCALATED",
            actor_id=actor_id,
            actor_role=actor_role,
            notes=notes,
            metadata={"escalation_level": rec.escalation_level},
        )
        db.commit()
        db.refresh(rec)
        return _record_to_dict(rec)


def queue_execution(
    decision_id: str,
    actor_id: str,
    actor_role: str,
    notes: str | None = None,
) -> dict[str, Any]:
    return _transition(
        decision_id, "QUEUE_EXECUTION", actor_id, actor_role,
        target_status="EXECUTION_PENDING",
        notes=notes,
    )


def execute(
    decision_id: str,
    actor_id: str,
    actor_role: str,
    execution_result: str | None = None,
    linked_outcome_id: str | None = None,
    linked_value_id: str | None = None,
    notes: str | None = None,
) -> dict[str, Any]:
    """Execute an approved decision.

    ENFORCEMENT: authority_status must be APPROVED or EXECUTION_PENDING.
    If record is APPROVED, this directly executes (combined QUEUE+EXECUTE).
    If record is EXECUTION_PENDING, this completes the queued execution.
    """
    _assert_permission("EXECUTE", actor_role)
    with Session(_get_engine()) as db:
        rec = db.query(DecisionAuthorityRecord).filter(
            DecisionAuthorityRecord.decision_id == decision_id
        ).one_or_none()
        if rec is None:
            raise AuthorityNotFoundError(f"No authority envelope for decision '{decision_id}'.")

        current = rec.authority_status
        if current not in {"APPROVED", "EXECUTION_PENDING"}:
            raise AuthorityError(
                f"Decision '{decision_id}' cannot be executed: "
                f"authority_status is '{current}'. "
                f"Execution requires APPROVED or EXECUTION_PENDING."
            )

        from_status = current
        now = _now()
        rec.authority_status = "EXECUTED"
        rec.executed_by = actor_id
        rec.executed_by_role = actor_role
        rec.executed_at = now
        rec.execution_result = execution_result
        if linked_outcome_id:
            rec.linked_outcome_id = linked_outcome_id
        if linked_value_id:
            rec.linked_value_id = linked_value_id
        rec.updated_at = now

        _append_event(
            db, rec.authority_id, decision_id,
            action="EXECUTE",
            from_status=from_status,
            to_status="EXECUTED",
            actor_id=actor_id,
            actor_role=actor_role,
            notes=notes,
            metadata={
                "execution_result": execution_result,
                "linked_outcome_id": linked_outcome_id,
                "linked_value_id": linked_value_id,
            },
        )
        db.commit()
        db.refresh(rec)
        return _record_to_dict(rec)


def report_execution_failure(
    decision_id: str,
    actor_id: str,
    actor_role: str,
    failure_reason: str | None = None,
    notes: str | None = None,
) -> dict[str, Any]:
    return _transition(
        decision_id, "REPORT_EXECUTION_FAILURE", actor_id, actor_role,
        target_status="EXECUTION_FAILED",
        notes=notes,
        update_fields={"execution_result": failure_reason},
        metadata={"failure_reason": failure_reason},
    )


def revoke(
    decision_id: str,
    actor_id: str,
    actor_role: str,
    rationale: str | None = None,
    notes: str | None = None,
) -> dict[str, Any]:
    """Revoke from any non-terminal state."""
    _assert_permission("REVOKE", actor_role)
    with Session(_get_engine()) as db:
        rec = db.query(DecisionAuthorityRecord).filter(
            DecisionAuthorityRecord.decision_id == decision_id
        ).one_or_none()
        if rec is None:
            raise AuthorityNotFoundError(f"No authority envelope for decision '{decision_id}'.")
        if rec.authority_status in TERMINAL_STATES:
            raise AuthorityError(
                f"Authority {rec.authority_id} is already in terminal state "
                f"'{rec.authority_status}' and cannot be revoked."
            )
        from_status = rec.authority_status
        now = _now()
        rec.authority_status = "REVOKED"
        rec.authority_actor_id = actor_id
        rec.authority_actor_role = actor_role
        rec.authority_decided_at = now
        rec.authority_rationale = rationale
        rec.updated_at = now
        _append_event(
            db, rec.authority_id, decision_id,
            action="REVOKE",
            from_status=from_status,
            to_status="REVOKED",
            actor_id=actor_id,
            actor_role=actor_role,
            notes=notes,
            metadata={"rationale": rationale},
        )
        db.commit()
        db.refresh(rec)
        return _record_to_dict(rec)


def withdraw(
    decision_id: str,
    actor_id: str,
    actor_role: str,
    notes: str | None = None,
) -> dict[str, Any]:
    """Withdraw from any non-terminal state."""
    _assert_permission("WITHDRAW", actor_role)
    with Session(_get_engine()) as db:
        rec = db.query(DecisionAuthorityRecord).filter(
            DecisionAuthorityRecord.decision_id == decision_id
        ).one_or_none()
        if rec is None:
            raise AuthorityNotFoundError(f"No authority envelope for decision '{decision_id}'.")
        if rec.authority_status in TERMINAL_STATES:
            raise AuthorityError(
                f"Authority {rec.authority_id} is already in terminal state "
                f"'{rec.authority_status}' and cannot be withdrawn."
            )
        from_status = rec.authority_status
        now = _now()
        rec.authority_status = "WITHDRAWN"
        rec.updated_at = now
        _append_event(
            db, rec.authority_id, decision_id,
            action="WITHDRAW",
            from_status=from_status,
            to_status="WITHDRAWN",
            actor_id=actor_id,
            actor_role=actor_role,
            notes=notes,
        )
        db.commit()
        db.refresh(rec)
        return _record_to_dict(rec)


def resubmit(
    decision_id: str,
    actor_id: str,
    actor_role: str,
    rationale: str | None = None,
    notes: str | None = None,
) -> dict[str, Any]:
    """Resubmit after REJECTED / RETURNED / EXECUTION_FAILED.

    Increments revision_number. Resets approval and execution fields.
    Returns to PROPOSED so the full lifecycle restarts.
    """
    _assert_permission("RESUBMIT", actor_role)
    with Session(_get_engine()) as db:
        rec = db.query(DecisionAuthorityRecord).filter(
            DecisionAuthorityRecord.decision_id == decision_id
        ).one_or_none()
        if rec is None:
            raise AuthorityNotFoundError(f"No authority envelope for decision '{decision_id}'.")

        allowed_from = {"REJECTED", "RETURNED", "EXECUTION_FAILED"}
        if rec.authority_status not in allowed_from:
            raise AuthorityError(
                f"RESUBMIT requires REJECTED, RETURNED, or EXECUTION_FAILED. "
                f"Current status: '{rec.authority_status}'."
            )

        from_status = rec.authority_status
        now = _now()
        rec.authority_status = "PROPOSED"
        rec.revision_number = rec.revision_number + 1
        rec.proposed_by = actor_id
        rec.proposed_by_role = actor_role
        if rationale:
            rec.proposal_rationale = rationale
        # Reset approval / execution fields
        rec.reviewer_id = None
        rec.reviewer_role = None
        rec.review_started_at = None
        rec.authority_actor_id = None
        rec.authority_actor_role = None
        rec.authority_decided_at = None
        rec.authority_rationale = None
        rec.executed_by = None
        rec.executed_by_role = None
        rec.executed_at = None
        rec.execution_result = None
        rec.updated_at = now

        _append_event(
            db, rec.authority_id, decision_id,
            action="RESUBMIT",
            from_status=from_status,
            to_status="PROPOSED",
            actor_id=actor_id,
            actor_role=actor_role,
            notes=notes,
            metadata={"revision_number": rec.revision_number, "rationale": rationale},
        )
        db.commit()
        db.refresh(rec)
        return _record_to_dict(rec)


def override(
    decision_id: str,
    actor_id: str,
    actor_role: str,
    target_status: str,
    rationale: str,
    notes: str | None = None,
) -> dict[str, Any]:
    """Force-transition to any valid status. Admin only. Fully audited.

    Unlike normal transitions, OVERRIDE bypasses the FSM guard matrix.
    The prior status is recorded in the event metadata for full auditability.
    """
    _assert_permission("OVERRIDE", actor_role)
    if target_status not in AUTHORITY_STATUSES:
        raise AuthorityError(f"Invalid target_status for OVERRIDE: '{target_status}'.")

    with Session(_get_engine()) as db:
        rec = db.query(DecisionAuthorityRecord).filter(
            DecisionAuthorityRecord.decision_id == decision_id
        ).one_or_none()
        if rec is None:
            raise AuthorityNotFoundError(f"No authority envelope for decision '{decision_id}'.")

        from_status = rec.authority_status
        now = _now()
        rec.authority_status = target_status
        rec.authority_actor_id = actor_id
        rec.authority_actor_role = actor_role
        rec.authority_decided_at = now
        rec.authority_rationale = rationale
        rec.updated_at = now

        _append_event(
            db, rec.authority_id, decision_id,
            action="OVERRIDE",
            from_status=from_status,
            to_status=target_status,
            actor_id=actor_id,
            actor_role=actor_role,
            notes=notes,
            metadata={"override_from": from_status, "rationale": rationale},
        )
        db.commit()
        db.refresh(rec)
        return _record_to_dict(rec)


def annotate(
    decision_id: str,
    actor_id: str,
    actor_role: str,
    notes: str,
    metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Append an annotation event without changing authority_status."""
    _assert_permission("ANNOTATE", actor_role)
    with Session(_get_engine()) as db:
        rec = db.query(DecisionAuthorityRecord).filter(
            DecisionAuthorityRecord.decision_id == decision_id
        ).one_or_none()
        if rec is None:
            raise AuthorityNotFoundError(f"No authority envelope for decision '{decision_id}'.")

        current_status = rec.authority_status
        rec.updated_at = _now()

        _append_event(
            db, rec.authority_id, decision_id,
            action="ANNOTATE",
            from_status=current_status,
            to_status=current_status,  # no status change
            actor_id=actor_id,
            actor_role=actor_role,
            notes=notes,
            metadata=metadata,
        )
        db.commit()
        db.refresh(rec)
        return _record_to_dict(rec)


# ── Query API ─────────────────────────────────────────────────────────────────

def link_references(
    decision_id: str,
    actor_id: str,
    actor_role: str,
    linked_outcome_id: str | None = None,
    linked_value_id: str | None = None,
    notes: str | None = None,
) -> dict[str, Any]:
    """Attach linked_outcome_id / linked_value_id to an authority envelope.

    This is a controlled mutation — appends an ANNOTATE event to the audit trail
    so link changes are fully traceable. Does NOT change authority_status.
    """
    _assert_permission("ANNOTATE", actor_role)

    if not linked_outcome_id and not linked_value_id:
        raise AuthorityError("At least one of linked_outcome_id or linked_value_id is required.")

    with Session(_get_engine()) as db:
        rec = db.query(DecisionAuthorityRecord).filter(
            DecisionAuthorityRecord.decision_id == decision_id
        ).one_or_none()
        if rec is None:
            raise AuthorityNotFoundError(f"No authority envelope for decision '{decision_id}'.")

        metadata: dict[str, Any] = {"link_update": True}
        if linked_outcome_id:
            metadata["linked_outcome_id"] = linked_outcome_id
            rec.linked_outcome_id = linked_outcome_id
        if linked_value_id:
            metadata["linked_value_id"] = linked_value_id
            rec.linked_value_id = linked_value_id

        rec.updated_at = _now()

        _append_event(
            db, rec.authority_id, decision_id,
            action="ANNOTATE",
            from_status=rec.authority_status,
            to_status=rec.authority_status,  # no status change
            actor_id=actor_id,
            actor_role=actor_role,
            notes=notes or "Link references updated",
            metadata=metadata,
        )
        db.commit()
        db.refresh(rec)
        return _record_to_dict(rec)


def compute_authority_metrics() -> dict[str, Any]:
    """Compute authoritative queue metrics directly from the database.

    This is the single source of truth for all Control Tower summary counts.
    No frontend aggregation is permitted — this endpoint is authoritative.
    """
    with Session(_get_engine()) as db:
        records = db.query(DecisionAuthorityRecord).all()

    counts = {
        "proposed": 0,
        "under_review": 0,
        "approved_pending_execution": 0,
        "executed": 0,
        "rejected": 0,
        "failed": 0,
        "escalated": 0,
        "returned": 0,
        "revoked": 0,
        "withdrawn": 0,
        "total_active": 0,
        "total": 0,
    }

    for rec in records:
        status = rec.authority_status
        counts["total"] += 1

        if status == "PROPOSED":
            counts["proposed"] += 1
        elif status == "UNDER_REVIEW":
            counts["under_review"] += 1
        elif status in ("APPROVED", "EXECUTION_PENDING"):
            counts["approved_pending_execution"] += 1
        elif status == "EXECUTED":
            counts["executed"] += 1
        elif status == "REJECTED":
            counts["rejected"] += 1
        elif status == "EXECUTION_FAILED":
            counts["failed"] += 1
        elif status == "ESCALATED":
            counts["escalated"] += 1
        elif status == "RETURNED":
            counts["returned"] += 1
        elif status == "REVOKED":
            counts["revoked"] += 1
        elif status == "WITHDRAWN":
            counts["withdrawn"] += 1

        if status not in TERMINAL_STATES:
            counts["total_active"] += 1

    return counts


def get_by_decision(decision_id: str) -> dict[str, Any] | None:
    """Return the authority envelope for a decision, or None."""
    with Session(_get_engine()) as db:
        rec = db.query(DecisionAuthorityRecord).filter(
            DecisionAuthorityRecord.decision_id == decision_id
        ).one_or_none()
        return _record_to_dict(rec) if rec else None


def get_by_authority_id(authority_id: str) -> dict[str, Any] | None:
    """Return an authority envelope by its own ID."""
    with Session(_get_engine()) as db:
        rec = db.query(DecisionAuthorityRecord).filter(
            DecisionAuthorityRecord.authority_id == authority_id
        ).one_or_none()
        return _record_to_dict(rec) if rec else None


def list_authorities(
    status: str | None = None,
    actor_id: str | None = None,
    limit: int = 100,
    offset: int = 0,
) -> list[dict[str, Any]]:
    """List authority envelopes with optional status filter."""
    with Session(_get_engine()) as db:
        q = db.query(DecisionAuthorityRecord)
        if status:
            q = q.filter(DecisionAuthorityRecord.authority_status == status)
        if actor_id:
            q = q.filter(
                (DecisionAuthorityRecord.proposed_by == actor_id) |
                (DecisionAuthorityRecord.authority_actor_id == actor_id)
            )
        records = (
            q.order_by(DecisionAuthorityRecord.updated_at.desc())
            .offset(offset)
            .limit(limit)
            .all()
        )
        return [_record_to_dict(r) for r in records]


def get_events(authority_id: str, limit: int = 100) -> list[dict[str, Any]]:
    """Return all events for an authority in chronological order."""
    with Session(_get_engine()) as db:
        events = (
            db.query(AuthorityEventRecord)
            .filter(AuthorityEventRecord.authority_id == authority_id)
            .order_by(AuthorityEventRecord.timestamp.asc())
            .limit(limit)
            .all()
        )
        return [_event_to_dict(e) for e in events]


def get_events_by_decision(decision_id: str, limit: int = 100) -> list[dict[str, Any]]:
    """Return all events for a decision's authority in chronological order."""
    with Session(_get_engine()) as db:
        events = (
            db.query(AuthorityEventRecord)
            .filter(AuthorityEventRecord.decision_id == decision_id)
            .order_by(AuthorityEventRecord.timestamp.asc())
            .limit(limit)
            .all()
        )
        return [_event_to_dict(e) for e in events]


def verify_hash_chain(authority_id: str) -> dict[str, Any]:
    """Verify the full hash chain for an authority.

    Returns a regulator-grade verification report with:
      - valid: boolean (true only if entire chain is intact)
      - broken_at: index of first break (null if valid)
      - expected_hash / actual_hash: at the break point (null if valid)
      - events_checked: total events verified
      - chain_trace: per-event verification detail for full auditability
      - errors: list of all discrepancies found
    """
    events = get_events(authority_id)
    if not events:
        return {
            "valid": True,
            "broken_at": None,
            "expected_hash": None,
            "actual_hash": None,
            "events_checked": 0,
            "authority_id": authority_id,
            "chain_trace": [],
            "errors": [],
        }

    errors: list[dict[str, Any]] = []
    chain_trace: list[dict[str, Any]] = []
    broken_at: int | None = None
    broken_expected: str | None = None
    broken_actual: str | None = None

    for i, ev in enumerate(events):
        expected_prev = events[i - 1]["event_hash"] if i > 0 else None
        link_valid = ev["previous_event_hash"] == expected_prev

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
        hash_valid = recomputed == ev["event_hash"]

        trace_entry: dict[str, Any] = {
            "index": i,
            "event_id": ev["event_id"],
            "action": ev["action"],
            "from_status": ev["from_status"],
            "to_status": ev["to_status"],
            "timestamp": ev["timestamp"],
            "event_hash": ev["event_hash"],
            "previous_event_hash": ev["previous_event_hash"],
            "recomputed_hash": recomputed,
            "link_valid": link_valid,
            "hash_valid": hash_valid,
        }
        chain_trace.append(trace_entry)

        if not link_valid:
            err = {
                "event_index": i,
                "event_id": ev["event_id"],
                "error_type": "chain_link_break",
                "expected_previous_hash": expected_prev,
                "found_previous_hash": ev["previous_event_hash"],
            }
            errors.append(err)
            if broken_at is None:
                broken_at = i
                broken_expected = expected_prev
                broken_actual = ev["previous_event_hash"]

        if not hash_valid:
            err = {
                "event_index": i,
                "event_id": ev["event_id"],
                "error_type": "hash_mismatch",
                "expected_hash": recomputed,
                "actual_hash": ev["event_hash"],
            }
            errors.append(err)
            if broken_at is None:
                broken_at = i
                broken_expected = recomputed
                broken_actual = ev["event_hash"]

    return {
        "valid": len(errors) == 0,
        "broken_at": broken_at,
        "expected_hash": broken_expected,
        "actual_hash": broken_actual,
        "events_checked": len(events),
        "authority_id": authority_id,
        "chain_trace": chain_trace,
        "errors": errors,
    }
