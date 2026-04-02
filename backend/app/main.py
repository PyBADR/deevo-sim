"""
Impact Observatory | مرصد الأثر — V1 Application Entry Point

V1-minimal FastAPI application. Mounts only the routers that have working
source files. Neo4j, Redis, and Orchestrator are deferred to V2 (graceful skip).

Routers mounted:
  - /health             (health checks)
  - /api/v1/scenarios   (v4 scenario CRUD)
  - /api/v1/runs        (v4 pipeline execution — THE critical V1 path)
  - /api/v1/observatory (unified observatory flow)
"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config.settings import Settings

# ── Logging ─────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# ── Settings ────────────────────────────────────────────────────────────────
settings = Settings()


# ── Lifespan (V1: lightweight — no Neo4j, no Redis, no Orchestrator) ────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    """V1 lifespan: log startup, yield, log shutdown. No external deps."""
    logger.info("Starting Impact Observatory V1 (in-memory mode)...")
    logger.info("Neo4j / Redis / Orchestrator skipped — V1 runs in-memory only.")
    yield
    logger.info("Shutting down Impact Observatory V1.")


# ── App ─────────────────────────────────────────────────────────────────────
app = FastAPI(
    title="Impact Observatory | مرصد الأثر",
    description=(
        "GCC Decision Intelligence Platform — "
        "Simulate systemic stress, quantify financial impact, act before failure."
    ),
    version="4.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
    lifespan=lifespan,
)

# ── CORS ────────────────────────────────────────────────────────────────────
origins = settings.allowed_origins
if isinstance(origins, str):
    origins = [o.strip() for o in origins.split(",") if o.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins or ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["X-Total-Count", "X-Page-Count", "X-IO-Trace-Id", "X-IO-Run-Id"],
)


# ── Global exception handler ───────────────────────────────────────────────
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    logger.error(f"Unhandled exception: {exc!s}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error", "error": str(exc)},
    )


# ── Mount routers ──────────────────────────────────────────────────────────
# Health (no prefix — lives at /health)
from app.api import health  # noqa: E402

app.include_router(health.router, tags=["Health"])

# Observatory unified flow
try:
    from app.api.observatory import router as observatory_router  # noqa: E402

    app.include_router(
        observatory_router, prefix=settings.api_prefix, tags=["Observatory"]
    )
    logger.info("Mounted observatory router")
except ImportError as e:
    logger.warning(f"Observatory router unavailable: {e}")

# ── V4 canonical API (scenarios + runs) — HARD REQUIREMENT for V1 ──────────
from app.api.v1.router import api_v1_router as v4_router  # noqa: E402

app.include_router(v4_router, tags=["Observatory v4"])
logger.info("Mounted v4 canonical API router (/api/v1/scenarios, /api/v1/runs)")


# ── Root endpoint ──────────────────────────────────────────────────────────
@app.get("/", tags=["Root"])
async def root():
    return {
        "service": "Impact Observatory | مرصد الأثر",
        "version": "4.0.0",
        "mode": "v1-in-memory",
        "status": "operational",
        "endpoints": {
            "health": "/health",
            "docs": "/api/docs",
            "v4_scenarios": "/api/v1/scenarios",
            "v4_runs": "/api/v1/runs",
        },
    }


# ── Direct run ─────────────────────────────────────────────────────────────
if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info",
    )
