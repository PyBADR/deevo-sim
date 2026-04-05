"""
Impact Observatory | مرصد الأثر — API v1 Router (v4 §4)
Mounts all v4 endpoints under /api/v1.
"""

from fastapi import APIRouter
from .routes import scenarios, runs, graph, signals, decisions, outcomes, values, intelligence, authority

api_v1_router = APIRouter(prefix="/api/v1")

# Scenario + Run endpoints (legacy v4 pipeline)
api_v1_router.include_router(scenarios.router, tags=["scenarios"])
api_v1_router.include_router(runs.router, tags=["runs"])

# Graph + Unified Pipeline endpoints (Core Intelligence Layer)
api_v1_router.include_router(graph.router, tags=["graph"])

# Live Signal Layer — HITL-gated signal ingest + seed approval
api_v1_router.include_router(signals.router, tags=["signals"])

# Operator Layer — structured decision lifecycle on top of signal/seed/run
api_v1_router.include_router(decisions.router, tags=["decisions"])

# Outcome Intelligence Layer — first-class outcome tracking linked to decisions/runs
api_v1_router.include_router(outcomes.router, tags=["outcomes"])

# ROI / Decision Value Layer — deterministic value computation from confirmed outcomes
api_v1_router.include_router(values.router, tags=["values"])

# Intelligence Adapter Layer — normalize / validate external intelligence payloads
api_v1_router.include_router(intelligence.router, tags=["intelligence"])

# Decision Authority Layer — backend-native authority lifecycle, approvals, audit
api_v1_router.include_router(authority.router, tags=["authority"])
