"""
Impact Observatory | مرصد الأثر — API v1 Router (v4 §4)
Mounts all v4 endpoints under /api/v1.
"""

from fastapi import APIRouter
from .routes import scenarios, runs

api_v1_router = APIRouter(prefix="/api/v1")

# Write endpoints
api_v1_router.include_router(scenarios.router, tags=["scenarios"])
api_v1_router.include_router(runs.router, tags=["runs"])
