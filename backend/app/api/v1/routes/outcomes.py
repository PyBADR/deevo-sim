"""
Impact Observatory | مرصد الأثر — Outcome Intelligence Layer API routes

POST   /api/v1/outcomes                     record a new outcome (OPERATOR+)
GET    /api/v1/outcomes                     list outcomes (ANALYST+)
GET    /api/v1/outcomes/{id}                get outcome by ID (ANALYST+)
POST   /api/v1/outcomes/{id}/observe        observe an outcome (OPERATOR+)
POST   /api/v1/outcomes/{id}/confirm        confirm an outcome with classification (OPERATOR+)
POST   /api/v1/outcomes/{id}/dispute        dispute an outcome observation (OPERATOR+)
POST   /api/v1/outcomes/{id}/close          close an outcome (OPERATOR+)

Outcome lifecycle:
    create   → PENDING_OBSERVATION
    observe  → OBSERVED
    confirm  → CONFIRMED  (requires classification)
    dispute  → DISPUTED
    close    → CLOSED     (terminal)

Linkage requirement:
    Every outcome must reference at least one of: source_decision_id, source_run_id

Error codes:
    400 — missing linkage, validation failure, invalid classification
    403 — insufficient role
    404 — outcome not found
    409 — invalid state transition
"""

import logging
from typing import Any, Optional

from fastapi import APIRouter, Header, HTTPException, Query
from pydantic import BaseModel, Field

from app.core.security import authenticate
from app.core.rbac import Permission, has_permission
from app.outcomes import engine
from app.outcomes.engine import OutcomeError
from app.domain.models.outcome import OutcomeClassification

logger = logging.getLogger("observatory.outcomes")

router = APIRouter()


# ── Request / response models ──────────────────────────────────────────────────

class CreateOutcomeBody(BaseModel):
    source_decision_id:     Optional[str]               = Field(None, max_length=64)
    source_run_id:          Optional[str]               = Field(None, max_length=64)
    source_signal_id:       Optional[str]               = Field(None, max_length=64)
    source_seed_id:         Optional[str]               = Field(None, max_length=64)
    outcome_classification: Optional[OutcomeClassification] = None
    expected_value:         Optional[float]             = None
    realized_value:         Optional[float]             = None
    evidence_payload:       Optional[dict[str, Any]]    = None
    notes:                  Optional[str]               = Field(None, max_length=1000)
    recorded_by:            Optional[str]               = Field(None, max_length=256)


class ObserveOutcomeBody(BaseModel):
    evidence_payload: Optional[dict[str, Any]] = None
    realized_value:   Optional[float]          = None
    notes:            Optional[str]            = Field(None, max_length=1000)
    observed_by:      Optional[str]            = Field(None, max_length=256)


class ConfirmOutcomeBody(BaseModel):
    outcome_classification: OutcomeClassification
    realized_value: Optional[float] = None
    notes:          Optional[str]   = Field(None, max_length=1000)
    confirmed_by:   Optional[str]   = Field(None, max_length=256)


class DisputeOutcomeBody(BaseModel):
    reason:      str               = Field(..., max_length=500)
    notes:       Optional[str]     = Field(None, max_length=1000)
    disputed_by: Optional[str]     = Field(None, max_length=256)


class CloseOutcomeBody(BaseModel):
    notes:     Optional[str] = Field(None, max_length=1000)
    closed_by: Optional[str] = Field(None, max_length=256)


# ── POST /api/v1/outcomes ──────────────────────────────────────────────────────

@router.post("/outcomes", status_code=201)
async def create_outcome(
    body: CreateOutcomeBody,
    authorization: Optional[str] = Header(None),
    x_api_key: Optional[str] = Header(None, alias="X-IO-API-Key"),
):
    """Record a new Outcome entity.

    Requires: RECORD_OUTCOME permission (OPERATOR and above).
    At least one of source_decision_id, source_run_id is required.

    Returns 201 with the created outcome.

    Error codes:
        400 — missing source linkage
        403 — insufficient role
    """
    auth = authenticate(authorization, x_api_key)
    if not has_permission(auth.role, Permission.RECORD_OUTCOME):
        raise HTTPException(status_code=403, detail="Insufficient role to record outcomes (requires OPERATOR or above)")

    recorded_by = body.recorded_by or auth.principal_id

    try:
        outcome = engine.create_outcome(
            recorded_by            = recorded_by,
            source_decision_id     = body.source_decision_id,
            source_run_id          = body.source_run_id,
            source_signal_id       = body.source_signal_id,
            source_seed_id         = body.source_seed_id,
            outcome_classification = body.outcome_classification,
            expected_value         = body.expected_value,
            realized_value         = body.realized_value,
            evidence_payload       = body.evidence_payload,
            notes                  = body.notes,
        )
    except OutcomeError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    return _outcome_response(outcome)


# ── GET /api/v1/outcomes ───────────────────────────────────────────────────────

@router.get("/outcomes")
async def list_outcomes(
    decision_id:   Optional[str] = Query(None, description="Filter by source_decision_id"),
    run_id:        Optional[str] = Query(None, description="Filter by source_run_id"),
    status:        Optional[str] = Query(None, description="Filter by outcome_status"),
    limit:         int           = Query(50, ge=1, le=500),
    authorization: Optional[str] = Header(None),
    x_api_key: Optional[str] = Header(None, alias="X-IO-API-Key"),
):
    """List Outcomes, newest first.

    Optionally filter by decision_id, run_id, and/or outcome_status.

    Requires: READ_OUTCOME permission (ANALYST and above).
    """
    auth = authenticate(authorization, x_api_key)
    if not has_permission(auth.role, Permission.READ_OUTCOME):
        raise HTTPException(status_code=403, detail="Insufficient role to list outcomes")

    outcomes = engine.list_outcomes(
        decision_id = decision_id,
        run_id      = run_id,
        status      = status,
        limit       = limit,
    )
    return {
        "count":    len(outcomes),
        "outcomes": [_outcome_response(o) for o in outcomes],
    }


# ── GET /api/v1/outcomes/{id} ──────────────────────────────────────────────────

@router.get("/outcomes/{outcome_id}")
async def get_outcome(
    outcome_id:    str,
    authorization: Optional[str] = Header(None),
    x_api_key: Optional[str] = Header(None, alias="X-IO-API-Key"),
):
    """Get a single Outcome by ID.

    Requires: READ_OUTCOME permission (ANALYST and above).

    Error codes:
        404 — outcome not found
    """
    auth = authenticate(authorization, x_api_key)
    if not has_permission(auth.role, Permission.READ_OUTCOME):
        raise HTTPException(status_code=403, detail="Insufficient role to read outcomes")

    outcome = engine.get_outcome(outcome_id)
    if outcome is None:
        raise HTTPException(status_code=404, detail=f"Outcome {outcome_id!r} not found")

    return _outcome_response(outcome)


# ── POST /api/v1/outcomes/{id}/observe ────────────────────────────────────────

@router.post("/outcomes/{outcome_id}/observe", status_code=200)
async def observe_outcome(
    outcome_id:    str,
    body:          ObserveOutcomeBody = ObserveOutcomeBody(),
    authorization: Optional[str] = Header(None),
    x_api_key: Optional[str] = Header(None, alias="X-IO-API-Key"),
):
    """Observe an outcome — transition PENDING_OBSERVATION → OBSERVED.

    Requires: RECORD_OUTCOME permission (OPERATOR and above).

    Error codes:
        403 — insufficient role
        404 — outcome not found
        409 — invalid state transition
    """
    auth = authenticate(authorization, x_api_key)
    if not has_permission(auth.role, Permission.RECORD_OUTCOME):
        raise HTTPException(status_code=403, detail="Insufficient role to observe outcomes")

    actor = body.observed_by or auth.principal_id

    try:
        outcome = engine.observe_outcome(
            outcome_id       = outcome_id,
            actor            = actor,
            evidence_payload = body.evidence_payload,
            realized_value   = body.realized_value,
            notes            = body.notes,
        )
    except OutcomeError as exc:
        msg = str(exc)
        if "not found" in msg.lower():
            raise HTTPException(status_code=404, detail=msg)
        raise HTTPException(status_code=409, detail=msg)

    return _outcome_response(outcome)


# ── POST /api/v1/outcomes/{id}/confirm ────────────────────────────────────────

@router.post("/outcomes/{outcome_id}/confirm", status_code=200)
async def confirm_outcome(
    outcome_id:    str,
    body:          ConfirmOutcomeBody,
    authorization: Optional[str] = Header(None),
    x_api_key: Optional[str] = Header(None, alias="X-IO-API-Key"),
):
    """Confirm an outcome with a classification — transition OBSERVED/DISPUTED → CONFIRMED.

    Requires: RECORD_OUTCOME permission (OPERATOR and above).
    classification is required.

    Error codes:
        403 — insufficient role
        404 — outcome not found
        409 — invalid state transition
    """
    auth = authenticate(authorization, x_api_key)
    if not has_permission(auth.role, Permission.RECORD_OUTCOME):
        raise HTTPException(status_code=403, detail="Insufficient role to confirm outcomes")

    actor = body.confirmed_by or auth.principal_id

    try:
        outcome = engine.confirm_outcome(
            outcome_id     = outcome_id,
            actor          = actor,
            classification = body.outcome_classification,
            realized_value = body.realized_value,
            notes          = body.notes,
        )
    except OutcomeError as exc:
        msg = str(exc)
        if "not found" in msg.lower():
            raise HTTPException(status_code=404, detail=msg)
        raise HTTPException(status_code=409, detail=msg)

    return _outcome_response(outcome)


# ── POST /api/v1/outcomes/{id}/dispute ────────────────────────────────────────

@router.post("/outcomes/{outcome_id}/dispute", status_code=200)
async def dispute_outcome(
    outcome_id:    str,
    body:          DisputeOutcomeBody,
    authorization: Optional[str] = Header(None),
    x_api_key: Optional[str] = Header(None, alias="X-IO-API-Key"),
):
    """Dispute an outcome — transition OBSERVED → DISPUTED.

    Requires: RECORD_OUTCOME permission (OPERATOR and above).
    reason is required.

    Error codes:
        403 — insufficient role
        404 — outcome not found
        409 — invalid state transition
    """
    auth = authenticate(authorization, x_api_key)
    if not has_permission(auth.role, Permission.RECORD_OUTCOME):
        raise HTTPException(status_code=403, detail="Insufficient role to dispute outcomes")

    actor = body.disputed_by or auth.principal_id

    try:
        outcome = engine.dispute_outcome(
            outcome_id = outcome_id,
            actor      = actor,
            reason     = body.reason,
            notes      = body.notes,
        )
    except OutcomeError as exc:
        msg = str(exc)
        if "not found" in msg.lower():
            raise HTTPException(status_code=404, detail=msg)
        raise HTTPException(status_code=409, detail=msg)

    return _outcome_response(outcome)


# ── POST /api/v1/outcomes/{id}/close ──────────────────────────────────────────

@router.post("/outcomes/{outcome_id}/close", status_code=200)
async def close_outcome(
    outcome_id:    str,
    body:          CloseOutcomeBody = CloseOutcomeBody(),
    authorization: Optional[str] = Header(None),
    x_api_key: Optional[str] = Header(None, alias="X-IO-API-Key"),
):
    """Close an outcome (terminal state).

    Valid only from CONFIRMED, DISPUTED, or FAILED.
    Computes time_to_resolution_seconds automatically.

    Requires: RECORD_OUTCOME permission (OPERATOR and above).

    Error codes:
        403 — insufficient role
        404 — outcome not found
        409 — invalid state transition (e.g. already CLOSED)
    """
    auth = authenticate(authorization, x_api_key)
    if not has_permission(auth.role, Permission.RECORD_OUTCOME):
        raise HTTPException(status_code=403, detail="Insufficient role to close outcomes")

    actor = body.closed_by or auth.principal_id

    try:
        outcome = engine.close_outcome(
            outcome_id = outcome_id,
            actor      = actor,
            notes      = body.notes,
        )
    except OutcomeError as exc:
        msg = str(exc)
        if "not found" in msg.lower():
            raise HTTPException(status_code=404, detail=msg)
        raise HTTPException(status_code=409, detail=msg)

    return _outcome_response(outcome)


# ── Helper ─────────────────────────────────────────────────────────────────────

def _outcome_response(outcome) -> dict:
    return {
        "outcome_id":                  outcome.outcome_id,
        "source_decision_id":          outcome.source_decision_id,
        "source_run_id":               outcome.source_run_id,
        "source_signal_id":            outcome.source_signal_id,
        "source_seed_id":              outcome.source_seed_id,
        "outcome_status":              outcome.outcome_status.value,
        "outcome_classification":      outcome.outcome_classification.value if outcome.outcome_classification else None,
        "observed_at":                 outcome.observed_at.isoformat() if outcome.observed_at else None,
        "recorded_at":                 outcome.recorded_at.isoformat(),
        "updated_at":                  outcome.updated_at.isoformat(),
        "closed_at":                   outcome.closed_at.isoformat() if outcome.closed_at else None,
        "recorded_by":                 outcome.recorded_by,
        "expected_value":              outcome.expected_value,
        "realized_value":              outcome.realized_value,
        "error_flag":                  outcome.error_flag,
        "time_to_resolution_seconds":  outcome.time_to_resolution_seconds,
        "evidence_payload":            outcome.evidence_payload,
        "notes":                       outcome.notes,
    }
