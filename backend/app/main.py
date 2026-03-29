import os
import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

logger = logging.getLogger(__name__)

# ── Portable imports ──────────────────────────────────
def _import(module_path: str):
    """Import from app.* (Docker) or backend.app.* (local dev)."""
    import importlib
    try:
        return importlib.import_module(module_path)
    except ImportError:
        return importlib.import_module(f"backend.{module_path}")

# ── Demo router (required for launch) ─────────────────
try:
    demo_mod = _import("app.api.demo_routes")
    demo_router = demo_mod.demo_router
except Exception as e:
    logger.error(f"Failed to import demo_router: {e}")
    demo_router = None

# ── API v1 router (optional — full engine routes) ─────
try:
    router_mod = _import("app.api.router")
    api_router = router_mod.api_router
except Exception as e:
    logger.warning(f"API v1 router not available (non-critical): {e}")
    api_router = None

# ── App ───────────────────────────────────────────────
app = FastAPI(
    title="Deevo GCC Shock Intelligence API",
    version="0.2.1",
    description="Structured simulation under uncertainty for GCC shock intelligence.",
)

allowed = os.getenv("ALLOWED_ORIGINS", "http://localhost:3000,https://deevo-sim.vercel.app")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in allowed.split(",")],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Mount routers ─────────────────────────────────────
if api_router:
    app.include_router(api_router)
if demo_router:
    app.include_router(demo_router)

@app.get("/health", tags=["health"])
def health() -> dict[str, str]:
    return {
        "status": "ok",
        "version": "0.2.1",
        "engine": "deevo-sim-pilot",
        "demo": "active" if demo_router else "unavailable",
        "api_v1": "active" if api_router else "unavailable",
    }
