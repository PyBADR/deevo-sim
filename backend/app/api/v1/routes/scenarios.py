"""
Impact Observatory | مرصد الأثر — Scenario endpoints (v4 §4.2, §18.2)
GET  /scenarios          → List all catalog scenarios (no auth required for catalog)
POST /scenarios          → Create custom scenario (auth required)
GET  /scenarios/{id}     → Get scenario by ID (in-memory store or catalog fallback)
"""

from fastapi import APIRouter, Request, Header
from fastapi.responses import JSONResponse
from typing import Optional
from datetime import datetime, timezone
import uuid

from ....domain.models.scenario import Scenario
from ....core.security import authenticate
from ....core.rbac import Permission, has_permission
from ....core.errors import InsufficientRoleError, SchemaValidationError
from ..schemas.common import success_response
from ....scenarios.catalog import get_scenario_catalog, get_scenario_by_id as catalog_lookup

router = APIRouter()

# In-memory store for V1 (replaced by PostgreSQL in production)
_scenarios: dict[str, dict] = {}


@router.get("/scenarios")
async def list_scenarios(
    authorization: Optional[str] = Header(None),
    x_api_key: Optional[str] = Header(None, alias="X-IO-API-Key"),
):
    """v4 §18.2 — List all available scenarios from the catalog."""
    authenticate(authorization, x_api_key)
    catalog = get_scenario_catalog()
    return JSONResponse(content=success_response(catalog))


@router.post("/scenarios", status_code=201)
async def create_scenario(
    request: Request,
    idempotency_key: Optional[str] = Header(None, alias="Idempotency-Key"),
    authorization: Optional[str] = Header(None),
    x_api_key: Optional[str] = Header(None, alias="X-IO-API-Key"),
):
    """v4 §4.2 — Create scenario. Roles: analyst, operator, admin, regulator."""
    # Auth
    auth = authenticate(authorization, x_api_key)
    if not has_permission(auth.role, Permission.CREATE_SCENARIO):
        err = InsufficientRoleError(auth.role.value)
        return JSONResponse(status_code=403, content=err.to_envelope())

    # Parse body
    try:
        body = await request.json()
    except Exception:
        err = SchemaValidationError([{"field": "body", "issue": "invalid JSON"}])
        return JSONResponse(status_code=400, content=err.to_envelope())

    # Assign server-managed fields
    scenario_id = str(uuid.uuid4())  # UUIDv7 in production
    now = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")

    body["scenario_id"] = scenario_id
    body["scenario_version"] = "1.0.0"
    body["created_by"] = auth.principal_id
    body["created_at"] = now
    body["status"] = "active"

    # Validate
    try:
        scenario = Scenario(**body)
    except Exception as e:
        err = SchemaValidationError([{"field": "body", "issue": str(e)}])
        return JSONResponse(status_code=400, content=err.to_envelope())

    # Persist (in-memory for V1)
    _scenarios[scenario_id] = scenario.model_dump()

    return JSONResponse(
        status_code=201,
        content=success_response(scenario.model_dump()),
    )


@router.get("/scenarios/{scenario_id}")
async def get_scenario(
    scenario_id: str,
    authorization: Optional[str] = Header(None),
    x_api_key: Optional[str] = Header(None, alias="X-IO-API-Key"),
):
    """Get a scenario by ID. Checks in-memory store first, then catalog."""
    authenticate(authorization, x_api_key)

    # 1. Check in-memory store (custom scenarios)
    if scenario_id in _scenarios:
        return JSONResponse(content=success_response(_scenarios[scenario_id]))

    # 2. Fall back to catalog
    try:
        entry = catalog_lookup(scenario_id)
        return JSONResponse(content=success_response(entry))
    except ValueError:
        pass

    from ....core.errors import ScenarioNotFoundError
    err = ScenarioNotFoundError(scenario_id)
    return JSONResponse(status_code=404, content=err.to_envelope())


def get_scenario_store() -> dict:
    """Access the in-memory scenario store (for run creation)."""
    return _scenarios
