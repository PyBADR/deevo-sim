"""
Impact Observatory | مرصد الأثر — Graph API Routes

Exposes the GCC Knowledge Graph (76 nodes, 190 edges) and scenario impact
simulation via the unified pipeline. No auth required for read-only graph
browsing; scenario impact runs require READ_FINANCIAL permission.

Endpoints:
  GET  /graph/nodes                    → All nodes, optional layer filter
  GET  /graph/edges                    → All edges, optional layer filter
  GET  /graph/nodes/{node_id}          → Single node by ID
  GET  /graph/subgraph                 → Ego-network around a center node
  GET  /graph/scenarios                → Available scenario templates
  POST /graph/scenario/{id}/impacts    → Run scenario → impacted subgraph
  POST /graph/unified-run              → Full 13-stage unified pipeline run
"""

from fastapi import APIRouter, Query, Header
from fastapi.responses import JSONResponse
from typing import Optional
import logging

from ....core.security import authenticate
from ....core.rbac import Permission, has_permission
from ....core.errors import InsufficientRoleError
from ..schemas.common import success_response

from ....graph.registry import (
    get_node, get_all_nodes, get_nodes_by_layer,
    get_all_edges, get_all_layers,
    get_node_count, get_edge_count,
)
from ....graph.traversal import get_subgraph
from ....graph.bridge import (
    get_available_scenarios, scenario_exists,
)
from ....graph.builder import build_graph_snapshot
from ....schema.graph_api import (
    GraphNodeResponse, GraphEdgeResponse,
    GraphNodesListResponse, GraphEdgesListResponse,
    SubgraphResponse, ScenarioImpactResponse,
)

logger = logging.getLogger("observatory.graph")

router = APIRouter(prefix="/graph")


# ── GET /graph/nodes ──────────────────────────────────────────────────────
@router.get("/nodes")
async def list_nodes(
    layer: Optional[str] = Query(None, description="Filter by layer (geography, infrastructure, economy, finance, society)"),
    authorization: Optional[str] = Header(None),
    x_api_key: Optional[str] = Header(None, alias="X-IO-API-Key"),
):
    """List all graph nodes, optionally filtered by layer."""
    authenticate(authorization, x_api_key)

    if layer:
        raw_nodes = get_nodes_by_layer(layer)
    else:
        raw_nodes = get_all_nodes()

    nodes = [GraphNodeResponse(**n) for n in raw_nodes]
    return JSONResponse(content=success_response({
        "nodes": [n.model_dump() for n in nodes],
        "total": len(nodes),
        "layers": get_all_layers(),
        "total_graph_nodes": get_node_count(),
        "total_graph_edges": get_edge_count(),
    }))


# ── GET /graph/edges ──────────────────────────────────────────────────────
@router.get("/edges")
async def list_edges(
    layer: Optional[str] = Query(None, description="Filter edges where source or target is in this layer"),
    authorization: Optional[str] = Header(None),
    x_api_key: Optional[str] = Header(None, alias="X-IO-API-Key"),
):
    """List all graph edges, optionally filtered by layer membership."""
    authenticate(authorization, x_api_key)

    raw_edges = get_all_edges()

    if layer:
        # Filter: source or target node belongs to specified layer
        layer_nodes = {n["id"] for n in get_nodes_by_layer(layer)}
        raw_edges = [e for e in raw_edges if e["source"] in layer_nodes or e["target"] in layer_nodes]

    edges = [GraphEdgeResponse(**e) for e in raw_edges]
    return JSONResponse(content=success_response({
        "edges": [e.model_dump() for e in edges],
        "total": len(edges),
    }))


# ── GET /graph/nodes/{node_id} ────────────────────────────────────────────
@router.get("/nodes/{node_id}")
async def get_single_node(
    node_id: str,
    authorization: Optional[str] = Header(None),
    x_api_key: Optional[str] = Header(None, alias="X-IO-API-Key"),
):
    """Get a single node by ID."""
    authenticate(authorization, x_api_key)

    node = get_node(node_id)
    if not node:
        return JSONResponse(
            status_code=404,
            content={"error": f"Node '{node_id}' not found in graph registry"},
        )

    return JSONResponse(content=success_response(
        GraphNodeResponse(**node).model_dump()
    ))


# ── GET /graph/subgraph ──────────────────────────────────────────────────
@router.get("/subgraph")
async def get_subgraph_endpoint(
    center: str = Query(..., description="Center node ID for ego-network"),
    depth: int = Query(2, ge=1, le=5, description="BFS traversal depth"),
    authorization: Optional[str] = Header(None),
    x_api_key: Optional[str] = Header(None, alias="X-IO-API-Key"),
):
    """Get ego-network subgraph around a center node."""
    authenticate(authorization, x_api_key)

    center_node = get_node(center)
    if not center_node:
        return JSONResponse(
            status_code=404,
            content={"error": f"Center node '{center}' not found"},
        )

    sub = get_subgraph(center, depth=depth)
    nodes = [GraphNodeResponse(**n) for n in sub["nodes"]]
    edges = [GraphEdgeResponse(**e) for e in sub["edges"]]

    return JSONResponse(content=success_response({
        "center": center,
        "depth": depth,
        "nodes": [n.model_dump() for n in nodes],
        "edges": [e.model_dump() for e in edges],
        "node_count": len(nodes),
        "edge_count": len(edges),
    }))


# ── GET /graph/scenarios ─────────────────────────────────────────────────
@router.get("/scenarios")
async def list_graph_scenarios(
    authorization: Optional[str] = Header(None),
    x_api_key: Optional[str] = Header(None, alias="X-IO-API-Key"),
):
    """List available scenario templates for graph impact simulation."""
    authenticate(authorization, x_api_key)

    scenarios = get_available_scenarios()
    return JSONResponse(content=success_response({
        "scenarios": scenarios,
        "total": len(scenarios),
    }))


# ── POST /graph/scenario/{scenario_id}/impacts ───────────────────────────
@router.post("/scenario/{scenario_id}/impacts")
async def run_scenario_impacts(
    scenario_id: str,
    body: dict = None,
    authorization: Optional[str] = Header(None),
    x_api_key: Optional[str] = Header(None, alias="X-IO-API-Key"),
):
    """Run a scenario against the graph and return impacted nodes/edges.

    This is a lightweight graph-only impact computation (no full pipeline).
    For the full 13-stage pipeline, use POST /graph/unified-run.
    """
    auth = authenticate(authorization, x_api_key)
    if not has_permission(auth.role, Permission.READ_FINANCIAL):
        err = InsufficientRoleError(auth.role.value)
        return JSONResponse(status_code=403, content=err.to_envelope())

    if not scenario_exists(scenario_id):
        return JSONResponse(
            status_code=404,
            content={"error": f"Scenario '{scenario_id}' not found. Use GET /graph/scenarios for available templates."},
        )

    params = body or {}
    severity = min(1.0, max(0.0, float(params.get("severity", 0.7))))

    snapshot = build_graph_snapshot(scenario_id=scenario_id, severity=severity)

    # Build response
    impacted = [
        GraphNodeResponse(
            id=n.node_id, label=n.label, label_ar=n.label_ar,
            layer=n.layer, type=n.node_type, weight=n.weight,
            lat=n.lat, lng=n.lng, sensitivity=n.sensitivity,
            stress=n.stress, classification=n.classification,
        ).model_dump()
        for n in snapshot.impacted_nodes
        if n.stress > 0
    ]

    edges = [
        GraphEdgeResponse(
            id=e.edge_id, source=e.source, target=e.target,
            weight=e.weight, polarity=e.polarity,
            label=e.label, label_ar=e.label_ar,
            transmission=e.transmission,
        ).model_dump()
        for e in snapshot.activated_edges
    ]

    return JSONResponse(content=success_response({
        "scenario_id": scenario_id,
        "severity": severity,
        "impacted_nodes": impacted,
        "activated_edges": edges,
        "total_nodes_impacted": snapshot.total_nodes_impacted,
        "total_estimated_loss_usd": snapshot.total_estimated_loss_usd,
        "propagation_depth": snapshot.propagation_depth,
    }))


# ── POST /graph/unified-run ─────────────────────────────────────────────
@router.post("/unified-run")
async def run_unified(
    body: dict = None,
    authorization: Optional[str] = Header(None),
    x_api_key: Optional[str] = Header(None, alias="X-IO-API-Key"),
):
    """Run the full 13-stage unified pipeline.

    Returns graph_payload, map_payload, sector_rollups, decision_inputs,
    propagation_steps, trust metadata — everything all UI surfaces need.

    Body:
        template_id: str (required) — one of 17 canonical scenario IDs
        severity: float (0.0-1.0, default 0.7)
        horizon_hours: int (1-8760, default 168)
        label: str (optional)
    """
    auth = authenticate(authorization, x_api_key)
    if not has_permission(auth.role, Permission.LAUNCH_RUN):
        err = InsufficientRoleError(auth.role.value)
        return JSONResponse(status_code=403, content=err.to_envelope())

    params = body or {}
    template_id = params.get("template_id", "")

    if not template_id:
        return JSONResponse(
            status_code=400,
            content={"error": "template_id is required. Use GET /graph/scenarios for available templates."},
        )

    if not scenario_exists(template_id):
        return JSONResponse(
            status_code=404,
            content={"error": f"Scenario '{template_id}' not found."},
        )

    severity = min(1.0, max(0.0, float(params.get("severity", 0.7))))
    horizon_hours = max(1, min(8760, int(params.get("horizon_hours", 168))))
    label = params.get("label", "")

    from ....simulation.runner import run_unified_pipeline
    result = run_unified_pipeline(
        template_id=template_id,
        severity=severity,
        horizon_hours=horizon_hours,
        label=label,
    )

    logger.info(
        f"Unified run {result.get('run_id')}: "
        f"{result.get('headline', {}).get('total_nodes_impacted', 0)} nodes impacted, "
        f"${result.get('headline', {}).get('total_loss_usd', 0):,.0f} loss, "
        f"{result.get('duration_ms', 0):.1f}ms"
    )

    return JSONResponse(content=success_response(result))
