"""
Impact Observatory | مرصد الأثر — V1 Application Entry Point

V1-minimal FastAPI application. Mounts only the routers that have working
source files. Neo4j, Redis, and Orchestrator are deferred to V2 (graceful skip).

Routers mounted:
  - /health             (health checks)
  - /api/v1/scenarios   (v4 scenario CRUD)
  - /api/v1/runs        (v4 pipeline execution — THE critical V1 path)
"""

import asyncio
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


# ── Background expiry task ───────────────────────────────────────────────────

async def _periodic_seed_expiry(interval_s: int = 3_600) -> None:
    """Expire stale seeds every interval_s seconds (default: 1 hour).

    Runs as an asyncio background task started in lifespan.
    Failures are logged and the loop continues — never crashes the server.
    """
    while True:
        await asyncio.sleep(interval_s)
        try:
            from app.signals.hitl import reconcile_expired_seeds
            expired = reconcile_expired_seeds()
            if expired:
                logger.info("Periodic seed expiry: %d seeds expired", len(expired))
        except Exception as exc:
            logger.error("Periodic seed expiry task failed: %s", exc)


# ── Lifespan (V1: lightweight — no Neo4j, no Redis, no Orchestrator) ────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    """V1 lifespan: initialize persistent signal store, restore caches, yield, shutdown."""
    logger.info("Starting Impact Observatory V1...")
    logger.info("Neo4j / Redis / Orchestrator skipped — V1 runs in-memory pipeline mode.")

    # ── Signal store: create SQLite tables, restore caches, expire stale seeds ─
    _expiry_task = None
    try:
        # ── Authority models must be imported BEFORE init_db() so their table
        # definitions are registered on the shared SQLAlchemy Base before
        # Base.metadata.create_all() is called inside init_db().
        import app.authority.models as _authority_models  # noqa: F401

        from app.signals.store import init_db
        from app.signals.hitl import load_pending_from_db, reconcile_expired_seeds
        from app.api.v1.routes.runs import load_runs_from_db

        db_path = init_db()  # lazy engine creation; creates ALL tables (incl. authority)
        logger.info("Signal store initialized at: %s", db_path)

        load_pending_from_db()     # restore pending seeds into _pending cache
        load_runs_from_db()        # restore run metadata into _runs cache (result blobs on-demand)
        reconcile_expired_seeds()  # expire any seeds whose horizon elapsed while offline

        # Start background task for periodic expiry (1-hour default)
        _expiry_task = asyncio.create_task(_periodic_seed_expiry())
        logger.info("Signal store ready. Periodic seed expiry task started.")

    except Exception as exc:
        # Non-fatal: log and continue.  Signals will still work; persistence
        # will be retried per-write.  Missing tables will be recreated on next boot.
        logger.error("Signal store startup failed (non-fatal): %s", exc)

    # ── Data trust quarantine store: separate SQLite DB ──────────────────────
    try:
        from app.data_trust.quarantine.store import init_quarantine_db
        quarantine_path = init_quarantine_db()
        logger.info("Data trust quarantine store initialized at: %s", quarantine_path)
    except Exception as exc:
        logger.error("Data trust quarantine store startup failed (non-fatal): %s", exc)

    yield

    # ── Shutdown ─────────────────────────────────────────────────────────────
    if _expiry_task is not None:
        _expiry_task.cancel()
        try:
            await _expiry_task
        except asyncio.CancelledError:
            pass
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

# ── V4 canonical API (scenarios + runs) — HARD REQUIREMENT for V1 ──────────
from app.api.v1.router import api_v1_router as v4_router  # noqa: E402

app.include_router(v4_router, tags=["Observatory v4"])
logger.info("Mounted v4 canonical API router (/api/v1/scenarios, /api/v1/runs, /api/v1/signals)")


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


# ── Live Signal Layer — WebSocket feed ────────────────────────────────────────
# Push-only.  Clients connect and receive signal / seed events.
# No auth required (events carry no PII).
@app.websocket("/ws/signals")
async def ws_signal_feed(websocket):
    from app.signals.broadcaster import manager
    await manager.connect(websocket)
    try:
        while True:
            # Drain any client frames (connection keepalive / close handshake).
            # We do not process client messages — push-only contract.
            await websocket.receive_text()
    except Exception:
        pass
    finally:
        manager.disconnect(websocket)


# ── Root endpoint update (reflect signals endpoint) ──────────────────────────


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
