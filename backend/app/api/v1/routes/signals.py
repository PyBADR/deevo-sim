"""
Impact Observatory | مرصد الأثر — Live Signal API routes

POST /api/v1/signals                        ingest raw signal → ScenarioSeed (202)
GET  /api/v1/signals/pending                list pending seeds awaiting HITL review
GET  /api/v1/signals/seeds/{seed_id}        get seed by ID (any status, checks DB fallback)
POST /api/v1/signals/seeds/{seed_id}/approve approve → triggers pipeline (OPERATOR+)
POST /api/v1/signals/seeds/{seed_id}/reject  reject → no pipeline (ANALYST+)
GET  /api/v1/signals/audit                  append-only audit log (READ_DECISION+)

Ingest flow (POST /api/v1/signals):
    validate_body → normalize → score → hitl.submit (PENDING) → broadcast → 202

Approval flow (POST /api/v1/signals/seeds/{id}/approve):
    transition_guard → hitl.approve() → run_unified_pipeline() → persist → broadcast → 200

execute_run / run_unified_pipeline is NOT called here.
It is called only inside hitl.approve(), which is the sole HITL gate.

Transition guards are enforced inside hitl.py.  The API layer returns:
    409 Conflict  — for invalid transition attempts (already approved/rejected)
    404 Not Found — for unknown seed IDs
    422 Unprocessable Entity — for malformed signal body or seed generation failure
"""

import logging
from typing import Any, Optional

from fastapi import APIRouter, Header, HTTPException, Query
from pydantic import BaseModel, Field, field_validator

from app.core.security import authenticate
from app.core.rbac import Permission, has_permission
from app.signals import hitl
from app.signals.broadcaster import (
    broadcast_seed_approved,
    broadcast_seed_pending,
    broadcast_seed_rejected,
    broadcast_signal_scored,
)
from app.signals.normalizer import NormalizationError, normalize
from app.signals.scorer import score
from app.signals.seed_generator import SeedGenerationError

logger = logging.getLogger("observatory.signals")

router = APIRouter()


# ── Request / body models ─────────────────────────────────────────────────────

class SignalIngestBody(BaseModel):
    """Validated ingest body.  Replaces raw dict[str, Any] to surface errors early."""
    sector:      str  = Field(..., min_length=1, max_length=32)
    event_type:  str  = Field(..., min_length=1, max_length=128)
    severity:    float = Field(..., ge=0.0, le=1.0)
    source:      Optional[str] = Field(None, max_length=64)
    confidence:  Optional[float] = Field(None, ge=0.0, le=1.0)
    lat:         Optional[float] = Field(None, ge=-90.0,  le=90.0)
    lng:         Optional[float] = Field(None, ge=-180.0, le=180.0)
    entity_ids:  Optional[list[str]] = Field(None, max_length=5)
    description: Optional[str] = Field(None, max_length=500)
    payload:     Optional[dict[str, Any]] = None

    @field_validator("sector")
    @classmethod
    def _validate_sector(cls, v: str) -> str:
        normalized = v.lower().strip()
        allowed = {"banking", "bank", "fintech", "payments", "payment"}
        if normalized not in allowed:
            raise ValueError(
                f"sector '{v}' is not accepted (MVP scope: banking, fintech). "
                f"Got: {v!r}"
            )
        return v

    @field_validator("event_type")
    @classmethod
    def _validate_event_type(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("event_type must not be blank")
        return v.strip()


class SeedReviewBody(BaseModel):
    reason:      Optional[str] = Field(None, max_length=500)
    reviewed_by: Optional[str] = Field(None, max_length=256)


# ── POST /api/v1/signals ──────────────────────────────────────────────────────

@router.post("/signals", status_code=202)
async def ingest_signal(
    body: SignalIngestBody,
    authorization: Optional[str] = Header(None),
    x_api_key: Optional[str] = Header(None, alias="X-IO-API-Key"),
):
    """Submit a raw signal.  Returns a pending ScenarioSeed.

    The seed requires explicit ADMIN/OPERATOR approval before any pipeline run
    is triggered.  This endpoint does NOT call run_unified_pipeline().

    Requires: LAUNCH_RUN permission (ANALYST, OPERATOR, ADMIN, REGULATOR).

    Error codes:
        401 — unauthenticated
        403 — insufficient role
        422 — malformed body, out-of-scope sector, or unmappable event_type
    """
    auth = authenticate(authorization, x_api_key)
    if not has_permission(auth.role, Permission.LAUNCH_RUN):
        raise HTTPException(status_code=403, detail="Insufficient role for signal ingest")

    # Convert validated Pydantic body to dict for normalizer (which handles alias resolution)
    raw: dict[str, Any] = body.model_dump(exclude_none=True)

    # Normalize (further structural validation)
    try:
        signal = normalize(raw)
    except NormalizationError as exc:
        raise HTTPException(status_code=422, detail=str(exc))

    # Score (pure function — no side effects)
    scored = score(signal)

    # Generate seed + persist + queue for HITL
    try:
        seed = hitl.submit(scored)
    except SeedGenerationError as exc:
        raise HTTPException(status_code=422, detail=str(exc))

    # Broadcast (fire-and-forget — never affects response or seed state)
    try:
        await broadcast_signal_scored(scored)
        await broadcast_seed_pending(seed)
    except Exception as exc:
        logger.warning("broadcast failed during ingest: %s", exc)

    return {
        "seed_id":                 seed.seed_id,
        "signal_id":               seed.signal_id,
        "status":                  seed.status.value,
        "sector":                  seed.sector.value,
        "suggested_template_id":   seed.suggested_template_id,
        "suggested_severity":      seed.suggested_severity,
        "suggested_horizon_hours": seed.suggested_horizon_hours,
        "signal_score":            scored.signal_score,
        "rationale":               seed.rationale,
    }


# ── GET /api/v1/signals/pending ───────────────────────────────────────────────

@router.get("/signals/pending")
async def list_pending_seeds(
    authorization: Optional[str] = Header(None),
    x_api_key: Optional[str] = Header(None, alias="X-IO-API-Key"),
):
    """List all seeds awaiting HITL review.

    Requires: READ_DECISION permission (ANALYST and above).
    """
    auth = authenticate(authorization, x_api_key)
    if not has_permission(auth.role, Permission.READ_DECISION):
        raise HTTPException(status_code=403, detail="Insufficient role to read pending seeds")

    seeds = hitl.list_pending()
    return {
        "count": len(seeds),
        "seeds": [_seed_summary(s) for s in seeds],
    }


# ── GET /api/v1/signals/seeds/{seed_id} ──────────────────────────────────────

@router.get("/signals/seeds/{seed_id}")
async def get_seed(
    seed_id: str,
    authorization: Optional[str] = Header(None),
    x_api_key: Optional[str] = Header(None, alias="X-IO-API-Key"),
):
    """Get a seed by ID (any status).  Falls back to persistent store if not in cache.

    Requires: READ_DECISION permission.
    """
    auth = authenticate(authorization, x_api_key)
    if not has_permission(auth.role, Permission.READ_DECISION):
        raise HTTPException(status_code=403, detail="Insufficient role to read seed")

    seed = hitl.get_seed(seed_id)
    if seed is None:
        raise HTTPException(status_code=404, detail=f"Seed {seed_id!r} not found")
    return _seed_summary(seed)


# ── POST /api/v1/signals/seeds/{seed_id}/approve ─────────────────────────────

@router.post("/signals/seeds/{seed_id}/approve", status_code=200)
async def approve_seed(
    seed_id: str,
    body: SeedReviewBody = SeedReviewBody(),
    authorization: Optional[str] = Header(None),
    x_api_key: Optional[str] = Header(None, alias="X-IO-API-Key"),
):
    """Approve a pending seed.  Triggers the pipeline synchronously.

    Requires: LAUNCH_RUN_WITH_OVERRIDES permission (OPERATOR, ADMIN, REGULATOR).
    run_unified_pipeline() is called inside hitl.approve() — not here.

    Error codes:
        403 — insufficient role
        404 — seed not found
        409 — seed already reviewed or invalid transition
    """
    auth = authenticate(authorization, x_api_key)
    if not has_permission(auth.role, Permission.LAUNCH_RUN_WITH_OVERRIDES):
        raise HTTPException(
            status_code=403,
            detail="Insufficient role to approve seeds (requires OPERATOR or above)",
        )

    reviewed_by = body.reviewed_by or auth.principal_id

    try:
        result = hitl.approve(seed_id, reviewed_by=reviewed_by, reason=body.reason)
    except hitl.HITLError as exc:
        msg = str(exc)
        # Distinguish not-found from invalid-transition for correct status codes
        if "not found" in msg.lower():
            raise HTTPException(status_code=404, detail=msg)
        raise HTTPException(status_code=409, detail=msg)

    # Broadcast (fire-and-forget)
    try:
        await broadcast_seed_approved(result.seed, result.run_id)
    except Exception as exc:
        logger.warning("broadcast failed on approve: %s", exc)

    return {
        "seed_id":       result.seed.seed_id,
        "status":        result.seed.status.value,
        "run_id":        result.run_id,
        "reviewed_by":   result.seed.reviewed_by,
        "review_reason": result.seed.review_reason,
    }


# ── POST /api/v1/signals/seeds/{seed_id}/reject ──────────────────────────────

@router.post("/signals/seeds/{seed_id}/reject", status_code=200)
async def reject_seed(
    seed_id: str,
    body: SeedReviewBody = SeedReviewBody(),
    authorization: Optional[str] = Header(None),
    x_api_key: Optional[str] = Header(None, alias="X-IO-API-Key"),
):
    """Reject a pending seed.  No pipeline run is triggered.

    Requires: LAUNCH_RUN permission (ANALYST and above).

    Error codes:
        403 — insufficient role
        404 — seed not found
        409 — seed already reviewed or invalid transition
    """
    auth = authenticate(authorization, x_api_key)
    if not has_permission(auth.role, Permission.LAUNCH_RUN):
        raise HTTPException(status_code=403, detail="Insufficient role to reject seeds")

    reviewed_by = body.reviewed_by or auth.principal_id

    try:
        rejected = hitl.reject(seed_id, reviewed_by=reviewed_by, reason=body.reason)
    except hitl.HITLError as exc:
        msg = str(exc)
        if "not found" in msg.lower():
            raise HTTPException(status_code=404, detail=msg)
        raise HTTPException(status_code=409, detail=msg)

    # Broadcast (fire-and-forget)
    try:
        await broadcast_seed_rejected(rejected)
    except Exception as exc:
        logger.warning("broadcast failed on reject: %s", exc)

    return {
        "seed_id":       rejected.seed_id,
        "status":        rejected.status.value,
        "reviewed_by":   rejected.reviewed_by,
        "review_reason": rejected.review_reason,
    }


# ── GET /api/v1/signals/audit ─────────────────────────────────────────────────

@router.get("/signals/audit")
async def get_audit_log(
    entity_id:  Optional[str] = Query(None, description="Filter by signal_id or seed_id"),
    event_type: Optional[str] = Query(None, description="Filter by event type (e.g. seed.approved)"),
    limit:      int           = Query(50, ge=1, le=500),
    authorization: Optional[str] = Header(None),
    x_api_key: Optional[str] = Header(None, alias="X-IO-API-Key"),
):
    """Read the append-only signal layer audit log.

    Returns events newest-first.  Filterable by entity_id and event_type.

    Requires: READ_DECISION permission (ANALYST and above).
    """
    auth = authenticate(authorization, x_api_key)
    if not has_permission(auth.role, Permission.READ_DECISION):
        raise HTTPException(status_code=403, detail="Insufficient role to read audit log")

    from app.signals import store
    events = store.get_audit_log(entity_id=entity_id, event_type=event_type, limit=limit)
    return {
        "count":  len(events),
        "events": events,
    }


# ── Helper ────────────────────────────────────────────────────────────────────

def _seed_summary(seed) -> dict:
    return {
        "seed_id":                 seed.seed_id,
        "signal_id":               seed.signal_id,
        "status":                  seed.status.value,
        "sector":                  seed.sector.value,
        "suggested_template_id":   seed.suggested_template_id,
        "suggested_severity":      seed.suggested_severity,
        "suggested_horizon_hours": seed.suggested_horizon_hours,
        "rationale":               seed.rationale,
        "reviewed_by":             seed.reviewed_by,
        "review_reason":           seed.review_reason,
        "created_at":              seed.created_at.isoformat(),
    }
