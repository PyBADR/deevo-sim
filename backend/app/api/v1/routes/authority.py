"""
Impact Observatory | مرصد الأثر — Decision Authority Layer API routes

Authority lifecycle endpoints (backend source of truth):

POST   /api/v1/authority/propose
POST   /api/v1/authority/{decision_id}/submit
POST   /api/v1/authority/{decision_id}/approve
POST   /api/v1/authority/{decision_id}/reject
POST   /api/v1/authority/{decision_id}/return
POST   /api/v1/authority/{decision_id}/escalate
POST   /api/v1/authority/{decision_id}/queue-execution
POST   /api/v1/authority/{decision_id}/execute
POST   /api/v1/authority/{decision_id}/execution-failed
POST   /api/v1/authority/{decision_id}/revoke
POST   /api/v1/authority/{decision_id}/withdraw
POST   /api/v1/authority/{decision_id}/resubmit
POST   /api/v1/authority/{decision_id}/override
POST   /api/v1/authority/{decision_id}/annotate

GET    /api/v1/authority                        list envelopes
GET    /api/v1/authority/{decision_id}          get envelope by decision_id
GET    /api/v1/authority/{decision_id}/events   full audit event log
GET    /api/v1/authority/{decision_id}/verify   verify hash chain integrity

Error codes:
  400 — invalid transition, bad request body, missing required fields
  403 — insufficient role for this action
  404 — no authority envelope for this decision_id
  409 — authority already exists (on propose) / invalid state for action
"""

from __future__ import annotations

import logging
from typing import Any, Optional

from fastapi import APIRouter, Header, HTTPException, Query
from pydantic import BaseModel, Field

from app.core.security import authenticate
from app.core.rbac import Permission, has_permission
from app.authority import engine as auth_engine
from app.authority.engine import (
    AuthorityError,
    AuthorityNotFoundError,
    AuthorityPermissionError,
)

logger = logging.getLogger("observatory.authority")

router = APIRouter()


# ── Request models ─────────────────────────────────────────────────────────────

class ProposeBody(BaseModel):
    decision_id:            str                     = Field(..., max_length=64)
    rationale:              Optional[str]           = Field(None, max_length=1000)
    priority:               int                     = Field(3, ge=1, le=5)
    source_run_id:          Optional[str]           = Field(None, max_length=64)
    source_scenario_label:  Optional[str]           = Field(None, max_length=256)
    tags:                   Optional[list[str]]     = None
    notes:                  Optional[str]           = Field(None, max_length=500)
    # Actor override (if not taken from auth context)
    actor_id:               Optional[str]           = Field(None, max_length=256)


class ActorBody(BaseModel):
    """Minimal body for actions that only require actor attribution."""
    notes:    Optional[str] = Field(None, max_length=500)
    actor_id: Optional[str] = Field(None, max_length=256)


class ReviewBody(BaseModel):
    reviewer_id:   Optional[str] = Field(None, max_length=256)
    reviewer_role: Optional[str] = Field(None, max_length=64)
    notes:         Optional[str] = Field(None, max_length=500)
    actor_id:      Optional[str] = Field(None, max_length=256)


class DecisionBody(BaseModel):
    """Body for approve / reject / return — includes rationale."""
    rationale: Optional[str] = Field(None, max_length=1000)
    notes:     Optional[str] = Field(None, max_length=500)
    actor_id:  Optional[str] = Field(None, max_length=256)


class ExecuteBody(BaseModel):
    execution_result:   Optional[str] = Field(None, max_length=500)
    linked_outcome_id:  Optional[str] = Field(None, max_length=64)
    linked_value_id:    Optional[str] = Field(None, max_length=64)
    notes:              Optional[str] = Field(None, max_length=500)
    actor_id:           Optional[str] = Field(None, max_length=256)


class ExecutionFailedBody(BaseModel):
    failure_reason: Optional[str] = Field(None, max_length=500)
    notes:          Optional[str] = Field(None, max_length=500)
    actor_id:       Optional[str] = Field(None, max_length=256)


class RevokeBody(BaseModel):
    rationale: Optional[str] = Field(None, max_length=500)
    notes:     Optional[str] = Field(None, max_length=500)
    actor_id:  Optional[str] = Field(None, max_length=256)


class ResubmitBody(BaseModel):
    rationale: Optional[str] = Field(None, max_length=1000)
    notes:     Optional[str] = Field(None, max_length=500)
    actor_id:  Optional[str] = Field(None, max_length=256)


class OverrideBody(BaseModel):
    target_status: str           = Field(..., max_length=32)
    rationale:     str           = Field(..., max_length=1000)
    notes:         Optional[str] = Field(None, max_length=500)
    actor_id:      Optional[str] = Field(None, max_length=256)


class AnnotateBody(BaseModel):
    notes:    str                      = Field(..., max_length=2000)
    metadata: Optional[dict[str, Any]] = None
    actor_id: Optional[str]           = Field(None, max_length=256)


# ── Auth helpers ───────────────────────────────────────────────────────────────

def _auth(authorization: Optional[str], x_api_key: Optional[str]):
    try:
        return authenticate(authorization, x_api_key)
    except Exception as exc:
        raise HTTPException(status_code=401, detail=str(exc))


def _require(ctx, permission: Permission):
    if not has_permission(ctx.role, permission):
        raise HTTPException(
            status_code=403,
            detail=f"Role '{ctx.role.value}' lacks permission '{permission.value}'.",
        )


def _actor_id(ctx, body_actor_id: Optional[str]) -> str:
    return body_actor_id or ctx.principal_id


def _actor_role(ctx) -> str:
    return ctx.role.value


# ── Error → HTTP mapping ───────────────────────────────────────────────────────

def _handle_engine_error(exc: Exception):
    if isinstance(exc, AuthorityNotFoundError):
        raise HTTPException(status_code=404, detail=str(exc))
    if isinstance(exc, AuthorityPermissionError):
        raise HTTPException(status_code=403, detail=str(exc))
    if isinstance(exc, AuthorityError):
        # Distinguish "already exists" (409) from other transition errors (400)
        msg = str(exc)
        status = 409 if "already has an authority envelope" in msg else 400
        raise HTTPException(status_code=status, detail=msg)
    raise exc


# ── POST /api/v1/authority/propose ────────────────────────────────────────────

@router.post("/authority/propose", status_code=201)
async def propose_authority(
    body: ProposeBody,
    authorization: Optional[str] = Header(None),
    x_api_key:     Optional[str] = Header(None, alias="X-IO-API-Key"),
) -> dict[str, Any]:
    """Create a new authority envelope for a decision.

    Requires: PROPOSE_AUTHORITY (ANALYST+)
    Returns: authority envelope (201)
    Errors: 409 if authority already exists for this decision_id
    """
    ctx = _auth(authorization, x_api_key)
    _require(ctx, Permission.PROPOSE_AUTHORITY)
    try:
        result = auth_engine.propose(
            decision_id=body.decision_id,
            actor_id=_actor_id(ctx, body.actor_id),
            actor_role=_actor_role(ctx),
            rationale=body.rationale,
            priority=body.priority,
            source_run_id=body.source_run_id,
            source_scenario_label=body.source_scenario_label,
            tags=body.tags,
            notes=body.notes,
        )
    except Exception as exc:
        _handle_engine_error(exc)
    return result


# ── POST /api/v1/authority/{decision_id}/submit ───────────────────────────────

@router.post("/authority/{decision_id}/submit", status_code=200)
async def submit_for_review(
    decision_id: str,
    body: ReviewBody,
    authorization: Optional[str] = Header(None),
    x_api_key:     Optional[str] = Header(None, alias="X-IO-API-Key"),
) -> dict[str, Any]:
    """Submit a PROPOSED authority for review.

    Requires: SUBMIT_AUTHORITY (ANALYST+)
    Transitions: PROPOSED → UNDER_REVIEW
    """
    ctx = _auth(authorization, x_api_key)
    _require(ctx, Permission.SUBMIT_AUTHORITY)
    try:
        result = auth_engine.submit_for_review(
            decision_id=decision_id,
            actor_id=_actor_id(ctx, body.actor_id),
            actor_role=_actor_role(ctx),
            reviewer_id=body.reviewer_id,
            reviewer_role=body.reviewer_role,
            notes=body.notes,
        )
    except Exception as exc:
        _handle_engine_error(exc)
    return result


# ── POST /api/v1/authority/{decision_id}/approve ──────────────────────────────

@router.post("/authority/{decision_id}/approve", status_code=200)
async def approve_authority(
    decision_id: str,
    body: DecisionBody,
    authorization: Optional[str] = Header(None),
    x_api_key:     Optional[str] = Header(None, alias="X-IO-API-Key"),
) -> dict[str, Any]:
    """Approve a decision under review.

    Requires: APPROVE_AUTHORITY (ADMIN / executive)
    Transitions: UNDER_REVIEW → APPROVED
    """
    ctx = _auth(authorization, x_api_key)
    _require(ctx, Permission.APPROVE_AUTHORITY)
    try:
        result = auth_engine.approve(
            decision_id=decision_id,
            actor_id=_actor_id(ctx, body.actor_id),
            actor_role=_actor_role(ctx),
            rationale=body.rationale,
            notes=body.notes,
        )
    except Exception as exc:
        _handle_engine_error(exc)
    return result


# ── POST /api/v1/authority/{decision_id}/reject ───────────────────────────────

@router.post("/authority/{decision_id}/reject", status_code=200)
async def reject_authority(
    decision_id: str,
    body: DecisionBody,
    authorization: Optional[str] = Header(None),
    x_api_key:     Optional[str] = Header(None, alias="X-IO-API-Key"),
) -> dict[str, Any]:
    """Reject a decision under review.

    Requires: REJECT_AUTHORITY (ADMIN)
    Transitions: UNDER_REVIEW → REJECTED
    """
    ctx = _auth(authorization, x_api_key)
    _require(ctx, Permission.REJECT_AUTHORITY)
    try:
        result = auth_engine.reject(
            decision_id=decision_id,
            actor_id=_actor_id(ctx, body.actor_id),
            actor_role=_actor_role(ctx),
            rationale=body.rationale,
            notes=body.notes,
        )
    except Exception as exc:
        _handle_engine_error(exc)
    return result


# ── POST /api/v1/authority/{decision_id}/return ───────────────────────────────

@router.post("/authority/{decision_id}/return", status_code=200)
async def return_authority(
    decision_id: str,
    body: DecisionBody,
    authorization: Optional[str] = Header(None),
    x_api_key:     Optional[str] = Header(None, alias="X-IO-API-Key"),
) -> dict[str, Any]:
    """Return a decision for revision.

    Requires: RETURN_AUTHORITY (ADMIN)
    Transitions: UNDER_REVIEW → RETURNED
    """
    ctx = _auth(authorization, x_api_key)
    _require(ctx, Permission.RETURN_AUTHORITY)
    try:
        result = auth_engine.return_for_revision(
            decision_id=decision_id,
            actor_id=_actor_id(ctx, body.actor_id),
            actor_role=_actor_role(ctx),
            rationale=body.rationale,
            notes=body.notes,
        )
    except Exception as exc:
        _handle_engine_error(exc)
    return result


# ── POST /api/v1/authority/{decision_id}/escalate ─────────────────────────────

@router.post("/authority/{decision_id}/escalate", status_code=200)
async def escalate_authority(
    decision_id: str,
    body: ActorBody,
    authorization: Optional[str] = Header(None),
    x_api_key:     Optional[str] = Header(None, alias="X-IO-API-Key"),
) -> dict[str, Any]:
    """Escalate a decision under review.

    Requires: ESCALATE_AUTHORITY (OPERATOR+)
    Transitions: UNDER_REVIEW → ESCALATED (increments escalation_level)
    """
    ctx = _auth(authorization, x_api_key)
    _require(ctx, Permission.ESCALATE_AUTHORITY)
    try:
        result = auth_engine.escalate(
            decision_id=decision_id,
            actor_id=_actor_id(ctx, body.actor_id),
            actor_role=_actor_role(ctx),
            notes=body.notes,
        )
    except Exception as exc:
        _handle_engine_error(exc)
    return result


# ── POST /api/v1/authority/{decision_id}/queue-execution ──────────────────────

@router.post("/authority/{decision_id}/queue-execution", status_code=200)
async def queue_execution(
    decision_id: str,
    body: ActorBody,
    authorization: Optional[str] = Header(None),
    x_api_key:     Optional[str] = Header(None, alias="X-IO-API-Key"),
) -> dict[str, Any]:
    """Move an approved decision to the execution queue.

    Requires: EXECUTE_AUTHORITY (OPERATOR+)
    Transitions: APPROVED → EXECUTION_PENDING
    """
    ctx = _auth(authorization, x_api_key)
    _require(ctx, Permission.EXECUTE_AUTHORITY)
    try:
        result = auth_engine.queue_execution(
            decision_id=decision_id,
            actor_id=_actor_id(ctx, body.actor_id),
            actor_role=_actor_role(ctx),
            notes=body.notes,
        )
    except Exception as exc:
        _handle_engine_error(exc)
    return result


# ── POST /api/v1/authority/{decision_id}/execute ──────────────────────────────

@router.post("/authority/{decision_id}/execute", status_code=200)
async def execute_authority(
    decision_id: str,
    body: ExecuteBody,
    authorization: Optional[str] = Header(None),
    x_api_key:     Optional[str] = Header(None, alias="X-IO-API-Key"),
) -> dict[str, Any]:
    """Execute an approved decision.

    ENFORCEMENT: Requires authority_status == APPROVED or EXECUTION_PENDING.
    Execution without prior approval is rejected with 400.

    Requires: EXECUTE_AUTHORITY (OPERATOR+)
    Transitions: APPROVED | EXECUTION_PENDING → EXECUTED
    """
    ctx = _auth(authorization, x_api_key)
    _require(ctx, Permission.EXECUTE_AUTHORITY)
    try:
        result = auth_engine.execute(
            decision_id=decision_id,
            actor_id=_actor_id(ctx, body.actor_id),
            actor_role=_actor_role(ctx),
            execution_result=body.execution_result,
            linked_outcome_id=body.linked_outcome_id,
            linked_value_id=body.linked_value_id,
            notes=body.notes,
        )
    except Exception as exc:
        _handle_engine_error(exc)
    return result


# ── POST /api/v1/authority/{decision_id}/execution-failed ─────────────────────

@router.post("/authority/{decision_id}/execution-failed", status_code=200)
async def execution_failed(
    decision_id: str,
    body: ExecutionFailedBody,
    authorization: Optional[str] = Header(None),
    x_api_key:     Optional[str] = Header(None, alias="X-IO-API-Key"),
) -> dict[str, Any]:
    """Report that execution of a queued decision has failed.

    Requires: REPORT_AUTHORITY_EXECUTION_FAILURE (OPERATOR+)
    Transitions: EXECUTION_PENDING → EXECUTION_FAILED
    """
    ctx = _auth(authorization, x_api_key)
    _require(ctx, Permission.REPORT_AUTHORITY_EXECUTION_FAILURE)
    try:
        result = auth_engine.report_execution_failure(
            decision_id=decision_id,
            actor_id=_actor_id(ctx, body.actor_id),
            actor_role=_actor_role(ctx),
            failure_reason=body.failure_reason,
            notes=body.notes,
        )
    except Exception as exc:
        _handle_engine_error(exc)
    return result


# ── POST /api/v1/authority/{decision_id}/revoke ───────────────────────────────

@router.post("/authority/{decision_id}/revoke", status_code=200)
async def revoke_authority(
    decision_id: str,
    body: RevokeBody,
    authorization: Optional[str] = Header(None),
    x_api_key:     Optional[str] = Header(None, alias="X-IO-API-Key"),
) -> dict[str, Any]:
    """Revoke an authority from any non-terminal state.

    Requires: REVOKE_AUTHORITY (ADMIN)
    Target: REVOKED (terminal)
    """
    ctx = _auth(authorization, x_api_key)
    _require(ctx, Permission.REVOKE_AUTHORITY)
    try:
        result = auth_engine.revoke(
            decision_id=decision_id,
            actor_id=_actor_id(ctx, body.actor_id),
            actor_role=_actor_role(ctx),
            rationale=body.rationale,
            notes=body.notes,
        )
    except Exception as exc:
        _handle_engine_error(exc)
    return result


# ── POST /api/v1/authority/{decision_id}/withdraw ─────────────────────────────

@router.post("/authority/{decision_id}/withdraw", status_code=200)
async def withdraw_authority(
    decision_id: str,
    body: ActorBody,
    authorization: Optional[str] = Header(None),
    x_api_key:     Optional[str] = Header(None, alias="X-IO-API-Key"),
) -> dict[str, Any]:
    """Withdraw an authority from any non-terminal state.

    Requires: WITHDRAW_AUTHORITY (ANALYST+)
    Target: WITHDRAWN (terminal)
    """
    ctx = _auth(authorization, x_api_key)
    _require(ctx, Permission.WITHDRAW_AUTHORITY)
    try:
        result = auth_engine.withdraw(
            decision_id=decision_id,
            actor_id=_actor_id(ctx, body.actor_id),
            actor_role=_actor_role(ctx),
            notes=body.notes,
        )
    except Exception as exc:
        _handle_engine_error(exc)
    return result


# ── POST /api/v1/authority/{decision_id}/resubmit ─────────────────────────────

@router.post("/authority/{decision_id}/resubmit", status_code=200)
async def resubmit_authority(
    decision_id: str,
    body: ResubmitBody,
    authorization: Optional[str] = Header(None),
    x_api_key:     Optional[str] = Header(None, alias="X-IO-API-Key"),
) -> dict[str, Any]:
    """Resubmit after rejection, return, or execution failure.

    Increments revision_number. Resets approval and execution fields.

    Requires: PROPOSE_AUTHORITY (ANALYST+)
    Transitions: REJECTED | RETURNED | EXECUTION_FAILED → PROPOSED
    """
    ctx = _auth(authorization, x_api_key)
    _require(ctx, Permission.PROPOSE_AUTHORITY)
    try:
        result = auth_engine.resubmit(
            decision_id=decision_id,
            actor_id=_actor_id(ctx, body.actor_id),
            actor_role=_actor_role(ctx),
            rationale=body.rationale,
            notes=body.notes,
        )
    except Exception as exc:
        _handle_engine_error(exc)
    return result


# ── POST /api/v1/authority/{decision_id}/override ─────────────────────────────

@router.post("/authority/{decision_id}/override", status_code=200)
async def override_authority(
    decision_id: str,
    body: OverrideBody,
    authorization: Optional[str] = Header(None),
    x_api_key:     Optional[str] = Header(None, alias="X-IO-API-Key"),
) -> dict[str, Any]:
    """Force-transition to any valid status. Fully audited. ADMIN only.

    Requires: OVERRIDE_AUTHORITY (ADMIN)
    """
    ctx = _auth(authorization, x_api_key)
    _require(ctx, Permission.OVERRIDE_AUTHORITY)
    try:
        result = auth_engine.override(
            decision_id=decision_id,
            actor_id=_actor_id(ctx, body.actor_id),
            actor_role=_actor_role(ctx),
            target_status=body.target_status,
            rationale=body.rationale,
            notes=body.notes,
        )
    except Exception as exc:
        _handle_engine_error(exc)
    return result


# ── POST /api/v1/authority/{decision_id}/annotate ─────────────────────────────

@router.post("/authority/{decision_id}/annotate", status_code=200)
async def annotate_authority(
    decision_id: str,
    body: AnnotateBody,
    authorization: Optional[str] = Header(None),
    x_api_key:     Optional[str] = Header(None, alias="X-IO-API-Key"),
) -> dict[str, Any]:
    """Append an annotation note to the authority audit trail (no status change).

    Requires: ANNOTATE_AUTHORITY (ANALYST+, REGULATOR)
    """
    ctx = _auth(authorization, x_api_key)
    _require(ctx, Permission.ANNOTATE_AUTHORITY)
    try:
        result = auth_engine.annotate(
            decision_id=decision_id,
            actor_id=_actor_id(ctx, body.actor_id),
            actor_role=_actor_role(ctx),
            notes=body.notes,
            metadata=body.metadata,
        )
    except Exception as exc:
        _handle_engine_error(exc)
    return result


# ── POST /api/v1/authority/{decision_id}/link ─────────────────────────────────

class LinkBody(BaseModel):
    """Attach outcome_id and/or value_id to an existing authority envelope."""
    linked_outcome_id: Optional[str] = Field(None, max_length=64)
    linked_value_id:   Optional[str] = Field(None, max_length=64)
    notes:             Optional[str] = Field(None, max_length=500)
    actor_id:          Optional[str] = Field(None, max_length=256)


@router.post("/authority/{decision_id}/link", status_code=200)
async def link_authority(
    decision_id: str,
    body: LinkBody,
    authorization: Optional[str] = Header(None),
    x_api_key:     Optional[str] = Header(None, alias="X-IO-API-Key"),
) -> dict[str, Any]:
    """Attach linked_outcome_id / linked_value_id to an authority envelope.

    This is the ONLY way to associate outcome/value links — frontend MUST NOT
    mutate these fields locally.

    Requires: ANNOTATE_AUTHORITY (ANALYST+)
    """
    ctx = _auth(authorization, x_api_key)
    _require(ctx, Permission.ANNOTATE_AUTHORITY)
    try:
        result = auth_engine.link_references(
            decision_id=decision_id,
            actor_id=_actor_id(ctx, body.actor_id),
            actor_role=_actor_role(ctx),
            linked_outcome_id=body.linked_outcome_id,
            linked_value_id=body.linked_value_id,
            notes=body.notes,
        )
    except Exception as exc:
        _handle_engine_error(exc)
    return result


# ── GET /api/v1/authority/metrics ─────────────────────────────────────────────

@router.get("/authority/metrics", status_code=200)
async def get_authority_metrics(
    authorization: Optional[str] = Header(None),
    x_api_key:     Optional[str] = Header(None, alias="X-IO-API-Key"),
) -> dict[str, Any]:
    """Return authoritative queue metrics computed from the database.

    This is the ONLY source of truth for Control Tower counts/aggregations.
    The frontend MUST NOT derive these values locally.

    Requires: READ_AUTHORITY (ANALYST+)
    """
    ctx = _auth(authorization, x_api_key)
    _require(ctx, Permission.READ_AUTHORITY)
    try:
        metrics = auth_engine.compute_authority_metrics()
    except Exception as exc:
        _handle_engine_error(exc)
    return metrics


# ── GET /api/v1/authority ─────────────────────────────────────────────────────

@router.get("/authority", status_code=200)
async def list_authorities(
    status: Optional[str] = Query(None, description="Filter by authority_status"),
    limit:  int           = Query(50, ge=1, le=200),
    offset: int           = Query(0, ge=0),
    authorization: Optional[str] = Header(None),
    x_api_key:     Optional[str] = Header(None, alias="X-IO-API-Key"),
) -> dict[str, Any]:
    """List authority envelopes. Optionally filtered by status.

    Requires: READ_AUTHORITY (ANALYST+)
    """
    ctx = _auth(authorization, x_api_key)
    _require(ctx, Permission.READ_AUTHORITY)
    try:
        items = auth_engine.list_authorities(status=status, limit=limit, offset=offset)
    except Exception as exc:
        _handle_engine_error(exc)
    return {"items": items, "count": len(items), "offset": offset, "limit": limit}


# ── GET /api/v1/authority/{decision_id} ───────────────────────────────────────

@router.get("/authority/{decision_id}", status_code=200)
async def get_authority(
    decision_id: str,
    authorization: Optional[str] = Header(None),
    x_api_key:     Optional[str] = Header(None, alias="X-IO-API-Key"),
) -> dict[str, Any]:
    """Get authority envelope for a specific decision.

    Requires: READ_AUTHORITY (ANALYST+)
    Errors: 404 if no authority exists for this decision_id
    """
    ctx = _auth(authorization, x_api_key)
    _require(ctx, Permission.READ_AUTHORITY)
    try:
        result = auth_engine.get_by_decision(decision_id)
    except Exception as exc:
        _handle_engine_error(exc)
    if result is None:
        raise HTTPException(
            status_code=404,
            detail=f"No authority envelope found for decision '{decision_id}'.",
        )
    return result


# ── GET /api/v1/authority/{decision_id}/events ────────────────────────────────

@router.get("/authority/{decision_id}/events", status_code=200)
async def get_authority_events(
    decision_id: str,
    limit:       int = Query(100, ge=1, le=500),
    authorization: Optional[str] = Header(None),
    x_api_key:     Optional[str] = Header(None, alias="X-IO-API-Key"),
) -> dict[str, Any]:
    """Return the full audit event log for a decision's authority.

    Requires: READ_AUTHORITY_AUDIT (ANALYST+, REGULATOR)
    Events are in chronological order with full hash chain.
    """
    ctx = _auth(authorization, x_api_key)
    _require(ctx, Permission.READ_AUTHORITY_AUDIT)
    try:
        events = auth_engine.get_events_by_decision(decision_id, limit=limit)
    except Exception as exc:
        _handle_engine_error(exc)
    return {"decision_id": decision_id, "events": events, "count": len(events)}


# ── GET /api/v1/authority/{decision_id}/verify ────────────────────────────────

@router.get("/authority/{decision_id}/verify", status_code=200)
async def verify_authority_chain(
    decision_id: str,
    authorization: Optional[str] = Header(None),
    x_api_key:     Optional[str] = Header(None, alias="X-IO-API-Key"),
) -> dict[str, Any]:
    """Verify hash chain integrity for a decision's authority audit trail.

    Returns verification report: valid flag, events checked, any chain errors.
    Requires: READ_AUTHORITY_AUDIT (ANALYST+, REGULATOR)
    """
    ctx = _auth(authorization, x_api_key)
    _require(ctx, Permission.READ_AUTHORITY_AUDIT)
    try:
        authority = auth_engine.get_by_decision(decision_id)
        if authority is None:
            raise HTTPException(
                status_code=404,
                detail=f"No authority envelope found for decision '{decision_id}'.",
            )
        report = auth_engine.verify_hash_chain(authority["authority_id"])
    except HTTPException:
        raise
    except Exception as exc:
        _handle_engine_error(exc)
    return report
