from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
import logging
from datetime import datetime

from app.services.graph_ingestion import GraphIngestionService, IngestionResult
from app.graph.client import GraphClient
from app.api.auth import api_key_auth

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/ingest", tags=["ingestion"])

# Request models for ingestion
class EventIngestionRequest(BaseModel):
    batch_size: int = Field(default=100, gt=0, le=10000)
    event_types: Optional[list[str]] = None
    limit: Optional[int] = None

class AirportIngestionRequest(BaseModel):
    batch_size: int = Field(default=100, gt=0, le=10000)
    countries: Optional[list[str]] = None
    limit: Optional[int] = None

class PortIngestionRequest(BaseModel):
    batch_size: int = Field(default=100, gt=0, le=10000)
    countries: Optional[list[str]] = None
    limit: Optional[int] = None

class CorridorIngestionRequest(BaseModel):
    batch_size: int = Field(default=100, gt=0, le=10000)
    corridor_types: Optional[list[str]] = None
    limit: Optional[int] = None

class FlightIngestionRequest(BaseModel):
    batch_size: int = Field(default=100, gt=0, le=10000)
    statuses: Optional[list[str]] = None
    limit: Optional[int] = None

class VesselIngestionRequest(BaseModel):
    batch_size: int = Field(default=100, gt=0, le=10000)
    vessel_types: Optional[list[str]] = None
    limit: Optional[int] = None

class ActorIngestionRequest(BaseModel):
    batch_size: int = Field(default=100, gt=0, le=10000)
    actor_types: Optional[list[str]] = None
    limit: Optional[int] = None

class IngestionStatusResponse(BaseModel):
    timestamp: datetime
    status: str
    pending_jobs: int
    completed_jobs: int
    failed_jobs: int
    last_ingest_timestamp: Optional[datetime] = None

# In-memory ingestion tracking
_ingestion_status = {
    "pending_jobs": 0,
    "completed_jobs": 0,
    "failed_jobs": 0,
    "last_ingest_timestamp": None
}

@router.post("/events", response_model=IngestionResult)
async def ingest_events(
    request: EventIngestionRequest,
    api_key: str = Depends(api_key_auth)
):
    """Ingest events into the graph database"""
    try:
        graph_client = GraphClient.get_instance()
        service = GraphIngestionService(graph_client)
        
        result = await service.ingest_events(
            batch_size=request.batch_size,
            event_types=request.event_types,
            limit=request.limit
        )
        
        _ingestion_status["completed_jobs"] += 1
        _ingestion_status["last_ingest_timestamp"] = datetime.utcnow()
        
        return result
    except Exception as e:
        logger.error(f"Error ingesting events: {str(e)}")
        _ingestion_status["failed_jobs"] += 1
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Event ingestion failed: {str(e)}"
        )

@router.post("/airports", response_model=IngestionResult)
async def ingest_airports(
    request: AirportIngestionRequest,
    api_key: str = Depends(api_key_auth)
):
    """Ingest airports into the graph database"""
    try:
        graph_client = GraphClient.get_instance()
        service = GraphIngestionService(graph_client)
        
        result = await service.ingest_airports(
            batch_size=request.batch_size,
            countries=request.countries,
            limit=request.limit
        )
        
        _ingestion_status["completed_jobs"] += 1
        _ingestion_status["last_ingest_timestamp"] = datetime.utcnow()
        
        return result
    except Exception as e:
        logger.error(f"Error ingesting airports: {str(e)}")
        _ingestion_status["failed_jobs"] += 1
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Airport ingestion failed: {str(e)}"
        )

@router.post("/ports", response_model=IngestionResult)
async def ingest_ports(
    request: PortIngestionRequest,
    api_key: str = Depends(api_key_auth)
):
    """Ingest ports into the graph database"""
    try:
        graph_client = GraphClient.get_instance()
        service = GraphIngestionService(graph_client)
        
        result = await service.ingest_ports(
            batch_size=request.batch_size,
            countries=request.countries,
            limit=request.limit
        )
        
        _ingestion_status["completed_jobs"] += 1
        _ingestion_status["last_ingest_timestamp"] = datetime.utcnow()
        
        return result
    except Exception as e:
        logger.error(f"Error ingesting ports: {str(e)}")
        _ingestion_status["failed_jobs"] += 1
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Port ingestion failed: {str(e)}"
        )

@router.post("/corridors", response_model=IngestionResult)
async def ingest_corridors(
    request: CorridorIngestionRequest,
    api_key: str = Depends(api_key_auth)
):
    """Ingest corridors into the graph database"""
    try:
        graph_client = GraphClient.get_instance()
        service = GraphIngestionService(graph_client)
        
        result = await service.ingest_corridors(
            batch_size=request.batch_size,
            corridor_types=request.corridor_types,
            limit=request.limit
        )
        
        _ingestion_status["completed_jobs"] += 1
        _ingestion_status["last_ingest_timestamp"] = datetime.utcnow()
        
        return result
    except Exception as e:
        logger.error(f"Error ingesting corridors: {str(e)}")
        _ingestion_status["failed_jobs"] += 1
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Corridor ingestion failed: {str(e)}"
        )

@router.post("/flights", response_model=IngestionResult)
async def ingest_flights(
    request: FlightIngestionRequest,
    api_key: str = Depends(api_key_auth)
):
    """Ingest flights into the graph database"""
    try:
        graph_client = GraphClient.get_instance()
        service = GraphIngestionService(graph_client)
        
        result = await service.ingest_flights(
            batch_size=request.batch_size,
            statuses=request.statuses,
            limit=request.limit
        )
        
        _ingestion_status["completed_jobs"] += 1
        _ingestion_status["last_ingest_timestamp"] = datetime.utcnow()
        
        return result
    except Exception as e:
        logger.error(f"Error ingesting flights: {str(e)}")
        _ingestion_status["failed_jobs"] += 1
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Flight ingestion failed: {str(e)}"
        )

@router.post("/vessels", response_model=IngestionResult)
async def ingest_vessels(
    request: VesselIngestionRequest,
    api_key: str = Depends(api_key_auth)
):
    """Ingest vessels into the graph database"""
    try:
        graph_client = GraphClient.get_instance()
        service = GraphIngestionService(graph_client)
        
        result = await service.ingest_vessels(
            batch_size=request.batch_size,
            vessel_types=request.vessel_types,
            limit=request.limit
        )
        
        _ingestion_status["completed_jobs"] += 1
        _ingestion_status["last_ingest_timestamp"] = datetime.utcnow()
        
        return result
    except Exception as e:
        logger.error(f"Error ingesting vessels: {str(e)}")
        _ingestion_status["failed_jobs"] += 1
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Vessel ingestion failed: {str(e)}"
        )

@router.post("/actors", response_model=IngestionResult)
async def ingest_actors(
    request: ActorIngestionRequest,
    api_key: str = Depends(api_key_auth)
):
    """Ingest actors into the graph database"""
    try:
        graph_client = GraphClient.get_instance()
        service = GraphIngestionService(graph_client)
        
        result = await service.ingest_actors(
            batch_size=request.batch_size,
            actor_types=request.actor_types,
            limit=request.limit
        )
        
        _ingestion_status["completed_jobs"] += 1
        _ingestion_status["last_ingest_timestamp"] = datetime.utcnow()
        
        return result
    except Exception as e:
        logger.error(f"Error ingesting actors: {str(e)}")
        _ingestion_status["failed_jobs"] += 1
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Actor ingestion failed: {str(e)}"
        )

@router.get("/status", response_model=IngestionStatusResponse)
async def get_ingestion_status(api_key: str = Depends(api_key_auth)):
    """Get current ingestion status"""
    return IngestionStatusResponse(
        timestamp=datetime.utcnow(),
        status="operational",
        pending_jobs=_ingestion_status["pending_jobs"],
        completed_jobs=_ingestion_status["completed_jobs"],
        failed_jobs=_ingestion_status["failed_jobs"],
        last_ingest_timestamp=_ingestion_status["last_ingest_timestamp"]
    )
