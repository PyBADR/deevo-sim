"""
Impact Observatory | مرصد الأثر — ROI / Decision Value Layer API routes

POST   /api/v1/values/compute          compute value from outcome (OPERATOR+)
POST   /api/v1/values/{id}/recompute   recompute with updated inputs (OPERATOR+)
GET    /api/v1/values                  list values, optionally filtered (ANALYST+)
GET    /api/v1/values/{id}             get value by ID (ANALYST+)

Value computation:
    Every value is derived from an existing Outcome.
    No ROI without linkage to outcome.
    Formula stored in calculation_trace for full auditability.

Linkage requirement:
    source_outcome_id is required for compute.
    Outcome must exist — 404 if not found.

Error codes:
    400 — invalid inputs, outcome not found at compute time
    403 — insufficient role
    404 — value not found (for get/recompute)
"""

import logging
from typing import Optional

from fastapi import APIRouter, Header, HTTPException, Query
from pydantic import BaseModel, Field

from app.core.security import authenticate
from app.core.rbac import Permission, has_permission
from app.values import engine
from app.values.engine import ValueError_

logger = logging.getLogger("observatory.values")

router = APIRouter()


# ── Request / response models ──────────────────────────────────────────────────

class ComputeValueBody(BaseModel):
    """Request body for POST /values/compute.

    source_outcome_id is required — no value without an outcome.
    All cost fields default to 0.0 if omitted.
    """
    source_outcome_id: str               = Field(..., max_length=64)
    avoided_loss:      Optional[float]   = Field(
        None,
        ge=0.0,
        description="Monetary loss avoided. Must be >= 0. If omitted, falls back to outcome.expected_value then 0."
    )
    operational_cost:  float             = Field(0.0, ge=0.0)
    decision_cost:     float             = Field(0.0, ge=0.0)
    latency_cost:      float             = Field(0.0, ge=0.0)
    notes:             Optional[str]     = Field(None, max_length=1000)
    computed_by:       Optional[str]     = Field(None, max_length=256)


class RecomputeValueBody(BaseModel):
    """Request body for POST /values/{id}/recompute.

    Only provide fields you want to update.
    Any field left None retains its value from the original computation.
    """
    avoided_loss:     Optional[float] = Field(None, ge=0.0, description="Override avoided_loss. Must be >= 0.")
    operational_cost: Optional[float] = Field(None, ge=0.0)
    decision_cost:    Optional[float] = Field(None, ge=0.0)
    latency_cost:     Optional[float] = Field(None, ge=0.0)
    notes:            Optional[str]   = Field(None, max_length=1000)
    computed_by:      Optional[str]   = Field(None, max_length=256)


# ── POST /api/v1/values/compute ───────────────────────────────────────────────

@router.post("/values/compute", status_code=201)
async def compute_value(
    body:          ComputeValueBody,
    authorization: Optional[str] = Header(None),
    x_api_key:     Optional[str] = Header(None, alias="X-IO-API-Key"),
):
    """Compute ROI from an existing Outcome.

    Deterministic: net_value = avoided_loss - (operational_cost + decision_cost + latency_cost)
    Requires: COMPUTE_VALUE permission (OPERATOR and above).

    Error codes:
        400 — outcome not found or invalid inputs
        403 — insufficient role
    """
    auth = authenticate(authorization, x_api_key)
    if not has_permission(auth.role, Permission.COMPUTE_VALUE):
        raise HTTPException(status_code=403, detail="Insufficient role to compute values (requires OPERATOR or above)")

    computed_by = body.computed_by or auth.principal_id

    try:
        value = engine.compute_value_from_outcome(
            outcome_id       = body.source_outcome_id,
            computed_by      = computed_by,
            avoided_loss     = body.avoided_loss,
            operational_cost = body.operational_cost,
            decision_cost    = body.decision_cost,
            latency_cost     = body.latency_cost,
            notes            = body.notes,
        )
    except ValueError_ as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    return _value_response(value)


# ── POST /api/v1/values/{id}/recompute ───────────────────────────────────────

@router.post("/values/{value_id}/recompute", status_code=201)
async def recompute_value(
    value_id:      str,
    body:          RecomputeValueBody,
    authorization: Optional[str] = Header(None),
    x_api_key:     Optional[str] = Header(None, alias="X-IO-API-Key"),
):
    """Recompute ROI with updated cost inputs.

    Writes a NEW DecisionValue row (new value_id). The original is preserved.
    Any input field left null retains its original value.

    Requires: COMPUTE_VALUE permission (OPERATOR and above).

    Error codes:
        400 — invalid inputs
        403 — insufficient role
        404 — original value not found
    """
    auth = authenticate(authorization, x_api_key)
    if not has_permission(auth.role, Permission.COMPUTE_VALUE):
        raise HTTPException(status_code=403, detail="Insufficient role to recompute values")

    computed_by = body.computed_by or auth.principal_id

    try:
        value = engine.recompute_value(
            value_id         = value_id,
            computed_by      = computed_by,
            avoided_loss     = body.avoided_loss,
            operational_cost = body.operational_cost,
            decision_cost    = body.decision_cost,
            latency_cost     = body.latency_cost,
            notes            = body.notes,
        )
    except ValueError_ as exc:
        msg = str(exc)
        if "not found" in msg.lower():
            raise HTTPException(status_code=404, detail=msg)
        raise HTTPException(status_code=400, detail=msg)

    return _value_response(value)


# ── GET /api/v1/values ────────────────────────────────────────────────────────

@router.get("/values")
async def list_values(
    outcome_id:    Optional[str] = Query(None, description="Filter by source_outcome_id"),
    decision_id:   Optional[str] = Query(None, description="Filter by source_decision_id"),
    run_id:        Optional[str] = Query(None, description="Filter by source_run_id"),
    limit:         int           = Query(50, ge=1, le=500),
    authorization: Optional[str] = Header(None),
    x_api_key:     Optional[str] = Header(None, alias="X-IO-API-Key"),
):
    """List DecisionValues, newest first.

    Optionally filter by outcome_id, decision_id, and/or run_id.
    Requires: READ_VALUE permission (ANALYST and above).
    """
    auth = authenticate(authorization, x_api_key)
    if not has_permission(auth.role, Permission.READ_VALUE):
        raise HTTPException(status_code=403, detail="Insufficient role to list values")

    values = engine.list_values(
        outcome_id  = outcome_id,
        decision_id = decision_id,
        run_id      = run_id,
        limit       = limit,
    )
    return {
        "count":  len(values),
        "values": [_value_response(v) for v in values],
    }


# ── GET /api/v1/values/{id} ───────────────────────────────────────────────────

@router.get("/values/{value_id}")
async def get_value(
    value_id:      str,
    authorization: Optional[str] = Header(None),
    x_api_key:     Optional[str] = Header(None, alias="X-IO-API-Key"),
):
    """Get a single DecisionValue by ID.

    Requires: READ_VALUE permission (ANALYST and above).

    Error codes:
        404 — value not found
    """
    auth = authenticate(authorization, x_api_key)
    if not has_permission(auth.role, Permission.READ_VALUE):
        raise HTTPException(status_code=403, detail="Insufficient role to read values")

    value = engine.get_value(value_id)
    if value is None:
        raise HTTPException(status_code=404, detail=f"DecisionValue {value_id!r} not found")

    return _value_response(value)


# ── Helper ─────────────────────────────────────────────────────────────────────

def _value_response(value) -> dict:
    return {
        "value_id":               value.value_id,
        "source_outcome_id":      value.source_outcome_id,
        "source_decision_id":     value.source_decision_id,
        "source_run_id":          value.source_run_id,
        "computed_at":            value.computed_at.isoformat(),
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
