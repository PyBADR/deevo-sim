"""FastAPI Application - Phase 7

Main application entry point for DecisionCore Intelligence GCC platform.
Sets up routes, middleware, and application lifecycle management.
"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse

from app.config.settings import Settings
from app.graph.client import GraphClient
from app.graph.schema import GraphSchema
from app.api import health, scenarios, entities, graph, ingest, auth

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load settings
settings = Settings()

# Global graph client
graph_client: GraphClient = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Manage application lifecycle.
    Handles startup and shutdown events.
    """
    # Startup
    logger.info("Starting DecisionCore Intelligence application...")
    
    try:
        global graph_client
        graph_client = GraphClient(
            uri=settings.neo4j_uri,
            user=settings.neo4j_user,
            password=settings.neo4j_password,
            max_connection_pool_size=settings.neo4j_max_pool_size,
            connection_timeout=settings.neo4j_timeout
        )
        
        await graph_client.initialize()
        schema = GraphSchema()
        await graph_client.initialize_schema(schema)
        
        logger.info("Graph database initialized successfully")
        
        # Store in app state for access in routes
        app.state.graph_client = graph_client
        
    except Exception as e:
        logger.error(f"Failed to initialize graph client: {str(e)}")
        raise

    yield

    # Shutdown
    logger.info("Shutting down DecisionCore Intelligence application...")
    try:
        if graph_client:
            await graph_client.close()
            logger.info("Graph database connection closed")
    except Exception as e:
        logger.error(f"Error closing graph connection: {str(e)}")


# Create FastAPI app
app = FastAPI(
    title="DecisionCore Intelligence GCC Platform",
    description="Global Connectivity and Criticality Intelligence Platform",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=getattr(settings, 'allowed_origins', ["*"]),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["X-Total-Count", "X-Page-Count"]
)

# Add trusted host middleware
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=getattr(settings, 'trusted_hosts', ["*"])
)


# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Handle unhandled exceptions"""
    logger.error(f"Unhandled exception: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error", "error": str(exc)}
    )


# Include routers
app.include_router(health.router, tags=["Health"])
app.include_router(scenarios.router, prefix=settings.api_prefix, tags=["Scenarios"])
app.include_router(entities.router, prefix=settings.api_prefix, tags=["Entities"])
app.include_router(graph.router, prefix=settings.api_prefix, tags=["Graph Intelligence"])
app.include_router(ingest.router, prefix=settings.api_prefix, tags=["Data Ingestion"])


# Root endpoint
@app.get("/", tags=["Root"])
async def root():
    """Root endpoint with API information"""
    return {
        "service": "DecisionCore Intelligence GCC Platform",
        "version": "1.0.0",
        "status": "operational",
        "endpoints": {
            "health": "/health",
            "version": "/version",
            "docs": "/api/docs",
            "api_prefix": settings.api_prefix
        }
    }


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "backend.app.main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.debug_mode,
        log_level="info"
    )
