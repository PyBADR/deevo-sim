"""
Impact Observatory | مرصد الأثر — Run endpoints (v4 §4.3-4.9, §16.4, §17.5, §19.3)
POST /runs → 202 Accepted + run pipeline synchronously (V1 in-memory)
GET /runs/{run_id}/status
GET /runs/{run_id}/financial, banking, insurance, fintech, decision, explanation
GET /runs/{run_id}/business-impact, timeline, regulatory-timeline, executive-explanation
"""

from fastapi import APIRouter, Header
from fastapi.responses import JSONResponse
from typing import Optional
from datetime import datetime, timezone
import uuid
import logging

from ....core.security import authenticate
from ....core.rbac import Permission, has_permission
from ....core.errors import (
    InsufficientRoleError, RunNotFoundError, RunNotReadyError,
    DecisionAccessDeniedError,
)
from ....core.constants import MODEL_VERSION
from ..schemas.common import success_response

logger = logging.getLogger("observatory.runs")

router = APIRouter()

# In-memory run store for V1
_runs: dict[str, dict] = {}
_run_results: dict[str, dict] = {}


# ── Serializer ─────────────────────────────────────────────────────────────
def _serialize_pipeline_result(result) -> dict:
    """
    Convert V4PipelineResult → JSON-serializable dict keyed by API section.
    Each GET endpoint reads one key from this dict.
    """

    def _dump(obj):
        """Safe Pydantic / dataclass → dict."""
        if obj is None:
            return {}
        if hasattr(obj, "model_dump"):
            return obj.model_dump()
        if isinstance(obj, dict):
            return obj
        return {}

    def _dump_list(lst):
        """Serialize a list of Pydantic models."""
        return [_dump(item) for item in (lst or [])]

    return {
        "financial": {
            "aggregate": result.financial_aggregate,
            "entities": _dump_list(result.financial_impacts),
            "count": len(result.financial_impacts),
        },
        "banking": {
            "aggregate": result.banking_aggregate,
            "entities": _dump_list(result.banking_stresses),
            "count": len(result.banking_stresses),
        },
        "insurance": {
            "aggregate": result.insurance_aggregate,
            "entities": _dump_list(result.insurance_stresses),
            "count": len(result.insurance_stresses),
        },
        "fintech": {
            "aggregate": result.fintech_aggregate,
            "entities": _dump_list(result.fintech_stresses),
            "count": len(result.fintech_stresses),
        },
        "decision": _dump(result.decision_plan),
        "explanation": _dump(result.explanation),
        "business_impact": _dump(result.business_impact),
        "timeline": _dump_list(result.timeline),
        "regulatory_timeline": _dump(result.regulatory_state),
        "executive_explanation": {
            "explanation": _dump(result.explanation),
            "decision": _dump(result.decision_plan),
            "business_impact": _dump(result.business_impact),
        },
        "_meta": {
            "run_id": result.run_id,
            "stages_completed": result.stages_completed,
            "stages_skipped": result.stages_skipped,
            "warnings": result.warnings,
            "stage_log": result.stage_log,
            "audit_hash": result.audit_hash,
            "computed_in_ms": result.computed_in_ms,
        },
    }


# ── Seed resolver ──────────────────────────────────────────────────────────
def _resolve_scenario(scenario_id: str, template_id: str = ""):
    """
    Resolve a scenario from: (1) in-memory store, (2) seed templates.
    V1 supports the 'hormuz-closure-v1' template out of the box.
    """
    # Try in-memory scenario store first
    from .scenarios import get_scenario_store
    store = get_scenario_store()
    if scenario_id and scenario_id in store:
        from ....domain.models.scenario import Scenario
        return Scenario(**store[scenario_id])

    # Try seed templates
    template = template_id or scenario_id
    if template in ("hormuz-closure-v1", "hormuz_disruption", "hormuz"):
        from ....seeds.hormuz_v1 import build_hormuz_v1_scenario
        return build_hormuz_v1_scenario()

    return None


# ── POST /runs ─────────────────────────────────────────────────────────────
@router.post("/runs", status_code=202)
async def create_run(
    request_body: dict = None,
    idempotency_key: Optional[str] = Header(None, alias="Idempotency-Key"),
    authorization: Optional[str] = Header(None),
    x_api_key: Optional[str] = Header(None, alias="X-IO-API-Key"),
):
    """v4 §4.3 — Create run from scenario. Resolves scenario, runs pipeline, returns 202."""
    auth = authenticate(authorization, x_api_key)
    if not has_permission(auth.role, Permission.LAUNCH_RUN):
        err = InsufficientRoleError(auth.role.value)
        return JSONResponse(status_code=403, content=err.to_envelope())

    run_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    body = request_body or {}

    scenario_id = body.get("scenario_id", "")
    template_id = body.get("template_id", "")

    run_meta = {
        "run_id": run_id,
        "scenario_id": scenario_id or template_id,
        "scenario_version": "1.0.0",
        "model_version": MODEL_VERSION,
        "dataset_version": "2026.04.02",
        "regulatory_version": "2.4.0",
        "status": "running",
        "created_at": now,
    }
    _runs[run_id] = run_meta

    # Resolve scenario
    scenario = _resolve_scenario(scenario_id, template_id)
    if not scenario:
        run_meta["status"] = "failed"
        run_meta["error"] = f"Cannot resolve scenario: id={scenario_id} template={template_id}"
        return JSONResponse(
            status_code=202,
            content=success_response(run_meta),
        )

    # Run pipeline synchronously (V1 — in-memory, sub-second)
    try:
        from ....orchestration.pipeline_v4 import run_v4_pipeline
        result = run_v4_pipeline(scenario, run_id=run_id)

        # Serialize and store
        _run_results[run_id] = _serialize_pipeline_result(result)

        run_meta["status"] = "completed"
        run_meta["completed_at"] = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
        run_meta["computed_in_ms"] = result.computed_in_ms
        run_meta["stages_completed"] = len(result.stages_completed)
        run_meta["stages_total"] = 9

        logger.info(
            f"Run {run_id} completed: "
            f"{len(result.stages_completed)}/9 stages, "
            f"{result.computed_in_ms:.1f}ms"
        )
    except Exception as e:
        run_meta["status"] = "failed"
        run_meta["error"] = str(e)
        logger.error(f"Run {run_id} failed: {e}", exc_info=True)

    return JSONResponse(status_code=202, content=success_response(run_meta))


# ── GET /runs/{run_id}/status ──────────────────────────────────────────────
@router.get("/runs/{run_id}/status")
async def get_run_status(
    run_id: str,
    authorization: Optional[str] = Header(None),
    x_api_key: Optional[str] = Header(None, alias="X-IO-API-Key"),
):
    """v4 §4.3.2 — Poll run status."""
    authenticate(authorization, x_api_key)
    if run_id not in _runs:
        err = RunNotFoundError(run_id)
        return JSONResponse(status_code=404, content=err.to_envelope())

    meta = _runs[run_id]
    payload = {
        "run_id": run_id,
        "status": meta["status"],
        "created_at": meta["created_at"],
        "completed_at": meta.get("completed_at"),
        "computed_in_ms": meta.get("computed_in_ms"),
        "stages_completed": meta.get("stages_completed", 0),
        "stages_total": meta.get("stages_total", 9),
    }

    if run_id in _run_results:
        payload["warnings"] = _run_results[run_id].get("_meta", {}).get("warnings", [])
        payload["stage_log"] = _run_results[run_id].get("_meta", {}).get("stage_log", {})
        payload["audit_hash"] = _run_results[run_id].get("_meta", {}).get("audit_hash", "")

    return JSONResponse(content=success_response(payload))


# ── Result helpers ─────────────────────────────────────────────────────────
def _get_run_or_error(run_id: str, auth_ctx, permission: Permission):
    """Helper: validate run exists, completed, and user has permission."""
    if not has_permission(auth_ctx.role, permission):
        return None, InsufficientRoleError(auth_ctx.role.value)
    if run_id not in _runs:
        return None, RunNotFoundError(run_id)
    if run_id not in _run_results:
        status = _runs[run_id].get("status", "unknown")
        return None, RunNotReadyError(run_id, status)
    return _run_results[run_id], None


@router.get("/runs/{run_id}/financial")
async def get_financial(
    run_id: str,
    authorization: Optional[str] = Header(None),
    x_api_key: Optional[str] = Header(None, alias="X-IO-API-Key"),
):
    """v4 §4.4 — Financial impact results."""
    auth = authenticate(authorization, x_api_key)
    data, err = _get_run_or_error(run_id, auth, Permission.READ_FINANCIAL)
    if err:
        return JSONResponse(status_code=err.http_status, content=err.to_envelope())
    return JSONResponse(content=success_response(data.get("financial", {})))


@router.get("/runs/{run_id}/banking")
async def get_banking(
    run_id: str,
    authorization: Optional[str] = Header(None),
    x_api_key: Optional[str] = Header(None, alias="X-IO-API-Key"),
):
    """v4 §4.5 — Banking stress results."""
    auth = authenticate(authorization, x_api_key)
    data, err = _get_run_or_error(run_id, auth, Permission.READ_BANKING)
    if err:
        return JSONResponse(status_code=err.http_status, content=err.to_envelope())
    return JSONResponse(content=success_response(data.get("banking", {})))


@router.get("/runs/{run_id}/insurance")
async def get_insurance(
    run_id: str,
    authorization: Optional[str] = Header(None),
    x_api_key: Optional[str] = Header(None, alias="X-IO-API-Key"),
):
    """v4 §4.6 — Insurance stress results."""
    auth = authenticate(authorization, x_api_key)
    data, err = _get_run_or_error(run_id, auth, Permission.READ_INSURANCE)
    if err:
        return JSONResponse(status_code=err.http_status, content=err.to_envelope())
    return JSONResponse(content=success_response(data.get("insurance", {})))


@router.get("/runs/{run_id}/fintech")
async def get_fintech(
    run_id: str,
    authorization: Optional[str] = Header(None),
    x_api_key: Optional[str] = Header(None, alias="X-IO-API-Key"),
):
    """v4 §4.7 — Fintech stress results."""
    auth = authenticate(authorization, x_api_key)
    data, err = _get_run_or_error(run_id, auth, Permission.READ_FINTECH)
    if err:
        return JSONResponse(status_code=err.http_status, content=err.to_envelope())
    return JSONResponse(content=success_response(data.get("fintech", {})))


@router.get("/runs/{run_id}/decision")
async def get_decision(
    run_id: str,
    authorization: Optional[str] = Header(None),
    x_api_key: Optional[str] = Header(None, alias="X-IO-API-Key"),
):
    """v4 §4.8 — Decision plan. Viewer excluded."""
    auth = authenticate(authorization, x_api_key)
    if not has_permission(auth.role, Permission.READ_DECISION):
        err = DecisionAccessDeniedError()
        return JSONResponse(status_code=403, content=err.to_envelope())
    data, err = _get_run_or_error(run_id, auth, Permission.READ_DECISION)
    if err:
        return JSONResponse(status_code=err.http_status, content=err.to_envelope())
    return JSONResponse(content=success_response(data.get("decision", {})))


@router.get("/runs/{run_id}/explanation")
async def get_explanation(
    run_id: str,
    authorization: Optional[str] = Header(None),
    x_api_key: Optional[str] = Header(None, alias="X-IO-API-Key"),
):
    """v4 §4.9 — Explanation pack."""
    auth = authenticate(authorization, x_api_key)
    data, err = _get_run_or_error(run_id, auth, Permission.READ_EXPLANATION)
    if err:
        return JSONResponse(status_code=err.http_status, content=err.to_envelope())
    return JSONResponse(content=success_response(data.get("explanation", {})))


@router.get("/runs/{run_id}/business-impact")
async def get_business_impact(
    run_id: str,
    authorization: Optional[str] = Header(None),
    x_api_key: Optional[str] = Header(None, alias="X-IO-API-Key"),
):
    """v4 §16.4.1 — Business impact summary and loss trajectory."""
    auth = authenticate(authorization, x_api_key)
    data, err = _get_run_or_error(run_id, auth, Permission.READ_BUSINESS_IMPACT)
    if err:
        return JSONResponse(status_code=err.http_status, content=err.to_envelope())
    return JSONResponse(content=success_response(data.get("business_impact", {})))


@router.get("/runs/{run_id}/timeline")
async def get_timeline(
    run_id: str,
    authorization: Optional[str] = Header(None),
    x_api_key: Optional[str] = Header(None, alias="X-IO-API-Key"),
):
    """v4 §17.5.1 — Timestep-by-timestep temporal output."""
    auth = authenticate(authorization, x_api_key)
    data, err = _get_run_or_error(run_id, auth, Permission.READ_TIMELINE)
    if err:
        return JSONResponse(status_code=err.http_status, content=err.to_envelope())
    return JSONResponse(content=success_response(data.get("timeline", {})))


@router.get("/runs/{run_id}/regulatory-timeline")
async def get_regulatory_timeline(
    run_id: str,
    authorization: Optional[str] = Header(None),
    x_api_key: Optional[str] = Header(None, alias="X-IO-API-Key"),
):
    """v4 §16.4 — Regulatory breach events over time."""
    auth = authenticate(authorization, x_api_key)
    data, err = _get_run_or_error(run_id, auth, Permission.READ_REGULATORY_TIMELINE)
    if err:
        return JSONResponse(status_code=err.http_status, content=err.to_envelope())
    return JSONResponse(content=success_response(data.get("regulatory_timeline", {})))


@router.get("/runs/{run_id}/executive-explanation")
async def get_executive_explanation(
    run_id: str,
    authorization: Optional[str] = Header(None),
    x_api_key: Optional[str] = Header(None, alias="X-IO-API-Key"),
):
    """v4 §19.3 — Executive narrative explanation."""
    auth = authenticate(authorization, x_api_key)
    data, err = _get_run_or_error(run_id, auth, Permission.READ_EXECUTIVE_EXPLANATION)
    if err:
        return JSONResponse(status_code=err.http_status, content=err.to_envelope())
    return JSONResponse(content=success_response(data.get("executive_explanation", {})))


def get_run_store():
    """Access the in-memory run store."""
    return _runs


def get_result_store():
    """Access the in-memory result store."""
    return _run_results
