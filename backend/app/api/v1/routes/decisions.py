"""
Impact Observatory | مرصد الأثر — Operator Decision Layer API routes

POST   /api/v1/decisions                    create a decision (ANALYST+)
GET    /api/v1/decisions                    list decisions (ANALYST+)
GET    /api/v1/decisions/{id}               get decision by ID (ANALYST+)
POST   /api/v1/decisions/{id}/execute       execute a decision (OPERATOR+)
POST   /api/v1/decisions/{id}/close         close a decision (OPERATOR+)

Decision lifecycle:
    create → CREATED
    execute → EXECUTED (or FAILED on error)
    close   → CLOSED

Linkage requirement:
    Every decision must reference at least one of:
    source_signal_id, source_seed_id, source_run_id

Error codes:
    400 — missing linkage or validation failure
    403 — insufficient role
    404 — decision not found
    409 — invalid state transition
"""

import logging
from typing import Any, Optional

from fastapi import APIRouter, Header, HTTPException, Query
from pydantic import BaseModel, Field

from app.core.security import authenticate
from app.core.rbac import Permission, has_permission
from app.decisions import engine
from app.decisions.engine import DecisionError
from app.domain.models.operator_decision import (
    DecisionType,
    OutcomeStatus,
)

logger = logging.getLogger("observatory.decisions")

router = APIRouter()


# ── Request / response models ─────────────────────────────────────────────────

class CreateDecisionBody(BaseModel):
    decision_type:    DecisionType
    source_signal_id: Optional[str] = Field(None, max_length=64)
    source_seed_id:   Optional[str] = Field(None, max_length=64)
    source_run_id:    Optional[str] = Field(None, max_length=64)
    decision_payload: Optional[dict[str, Any]] = Field(None)
    rationale:        Optional[str] = Field(None, max_length=500)
    confidence_score: Optional[float] = Field(None, ge=0.0, le=1.0)
    created_by:       Optional[str] = Field(None, max_length=256)


class ExecuteDecisionBody(BaseModel):
    params:      Optional[dict[str, Any]] = None
    executed_by: Optional[str] = Field(None, max_length=256)


class CloseDecisionBody(BaseModel):
    outcome_status: Optional[str] = Field(None)  # SUCCESS | FAILURE | PARTIAL
    closed_by:      Optional[str] = Field(None, max_length=256)


# ── POST /api/v1/decisions ────────────────────────────────────────────────────

@router.post("/decisions", status_code=201)
async def create_decision(
    body: CreateDecisionBody,
    authorization: Optional[str] = Header(None),
    x_api_key: Optional[str] = Header(None, alias="X-IO-API-Key"),
):
    """Create a new OperatorDecision.

    Requires: LAUNCH_RUN permission (ANALYST and above).
    At least one of source_signal_id, source_seed_id, source_run_id is required.

    Returns 201 with the created decision.

    Error codes:
        400 — missing source linkage
        403 — insufficient role
    """
    auth = authenticate(authorization, x_api_key)
    if not has_permission(auth.role, Permission.LAUNCH_RUN):
        raise HTTPException(status_code=403, detail="Insufficient role to create decisions")

    created_by = body.created_by or auth.principal_id

    try:
        decision = engine.create_decision(
            decision_type    = body.decision_type,
            created_by       = created_by,
            source_signal_id = body.source_signal_id,
            source_seed_id   = body.source_seed_id,
            source_run_id    = body.source_run_id,
            decision_payload = body.decision_payload,
            rationale        = body.rationale,
            confidence_score = body.confidence_score,
        )
    except DecisionError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    return _decision_response(decision)


# ── GET /api/v1/decisions ─────────────────────────────────────────────────────

@router.get("/decisions")
async def list_decisions(
    status:        Optional[str] = Query(None, description="Filter by decision_status"),
    decision_type: Optional[str] = Query(None, description="Filter by decision_type"),
    limit:         int           = Query(50, ge=1, le=500),
    authorization: Optional[str] = Header(None),
    x_api_key: Optional[str] = Header(None, alias="X-IO-API-Key"),
):
    """List OperatorDecisions, newest first.

    Optionally filter by status (CREATED, IN_REVIEW, EXECUTED, FAILED, CLOSED)
    and/or decision_type.

    Requires: READ_DECISION permission (ANALYST and above).
    """
    auth = authenticate(authorization, x_api_key)
    if not has_permission(auth.role, Permission.READ_DECISION):
        raise HTTPException(status_code=403, detail="Insufficient role to list decisions")

    decisions = engine.list_decisions(
        status=status,
        decision_type=decision_type,
        limit=limit,
    )
    return {
        "count":     len(decisions),
        "decisions": [_decision_response(d) for d in decisions],
    }


# ── GET /api/v1/decisions/{id} ────────────────────────────────────────────────

@router.get("/decisions/{decision_id}")
async def get_decision(
    decision_id:   str,
    authorization: Optional[str] = Header(None),
    x_api_key: Optional[str] = Header(None, alias="X-IO-API-Key"),
):
    """Get a single OperatorDecision by ID.

    Requires: READ_DECISION permission (ANALYST and above).

    Error codes:
        404 — decision not found
    """
    auth = authenticate(authorization, x_api_key)
    if not has_permission(auth.role, Permission.READ_DECISION):
        raise HTTPException(status_code=403, detail="Insufficient role to read decisions")

    decision = engine.get_decision(decision_id)
    if decision is None:
        raise HTTPException(status_code=404, detail=f"Decision {decision_id!r} not found")

    return _decision_response(decision)


# ── POST /api/v1/decisions/{id}/execute ──────────────────────────────────────

@router.post("/decisions/{decision_id}/execute", status_code=200)
async def execute_decision(
    decision_id:   str,
    body:          ExecuteDecisionBody = ExecuteDecisionBody(),
    authorization: Optional[str] = Header(None),
    x_api_key: Optional[str] = Header(None, alias="X-IO-API-Key"),
):
    """Execute an OperatorDecision — dispatch action based on decision_type.

    Requires: LAUNCH_RUN_WITH_OVERRIDES permission (OPERATOR and above).

    Error codes:
        403 — insufficient role
        404 — decision not found
        409 — invalid state transition or already executed/closed
    """
    auth = authenticate(authorization, x_api_key)
    if not has_permission(auth.role, Permission.LAUNCH_RUN_WITH_OVERRIDES):
        raise HTTPException(
            status_code=403,
            detail="Insufficient role to execute decisions (requires OPERATOR or above)",
        )

    actor = body.executed_by or auth.principal_id

    try:
        decision = engine.execute_decision(
            decision_id = decision_id,
            actor       = actor,
            params      = body.params,
        )
    except DecisionError as exc:
        msg = str(exc)
        if "not found" in msg.lower():
            raise HTTPException(status_code=404, detail=msg)
        raise HTTPException(status_code=409, detail=msg)

    return _decision_response(decision)


# ── POST /api/v1/decisions/{id}/close ────────────────────────────────────────

@router.post("/decisions/{decision_id}/close", status_code=200)
async def close_decision(
    decision_id:   str,
    body:          CloseDecisionBody = CloseDecisionBody(),
    authorization: Optional[str] = Header(None),
    x_api_key: Optional[str] = Header(None, alias="X-IO-API-Key"),
):
    """Close an OperatorDecision (terminal state).

    Valid only from EXECUTED or FAILED status.

    Requires: LAUNCH_RUN_WITH_OVERRIDES permission (OPERATOR and above).

    Error codes:
        403 — insufficient role
        404 — decision not found
        409 — invalid state transition (e.g. not yet executed)
    """
    auth = authenticate(authorization, x_api_key)
    if not has_permission(auth.role, Permission.LAUNCH_RUN_WITH_OVERRIDES):
        raise HTTPException(
            status_code=403,
            detail="Insufficient role to close decisions (requires OPERATOR or above)",
        )

    # Resolve outcome_status enum
    outcome_status = OutcomeStatus.SUCCESS
    if body.outcome_status:
        try:
            outcome_status = OutcomeStatus(body.outcome_status.upper())
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid outcome_status {body.outcome_status!r}. "
                       f"Valid values: SUCCESS, FAILURE, PARTIAL",
            )

    try:
        decision = engine.close_decision(
            decision_id    = decision_id,
            actor          = body.closed_by or auth.principal_id,
            outcome_status = outcome_status,
        )
    except DecisionError as exc:
        msg = str(exc)
        if "not found" in msg.lower():
            raise HTTPException(status_code=404, detail=msg)
        raise HTTPException(status_code=409, detail=msg)

    return _decision_response(decision)


# ── Helper ────────────────────────────────────────────────────────────────────

def _decision_response(decision) -> dict:
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
        "created_at":        decision.created_at.isoformat(),
        "updated_at":        decision.updated_at.isoformat(),
        "closed_at":         decision.closed_at.isoformat() if decision.closed_at else None,
    }
