"""Entity retrieval endpoints"""

import logging
from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query

from app.api.models import (
    EventEntity, AirportEntity, PortEntity, CorridorEntity,
    FlightEntity, VesselEntity, EntityListResponse
)
from app.api.auth import api_key_auth

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/events", response_model=EntityListResponse)
async def get_events(
    event_type: Optional[str] = Query(None),
    severity_min: float = Query(0, ge=0, le=1),
    severity_max: float = Query(1, ge=0, le=1),
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    api_key: str = Depends(api_key_auth)
):
    """
    Get events with filtering and pagination
    
    Args:
        event_type: Optional filter by event type
        severity_min: Minimum severity threshold
        severity_max: Maximum severity threshold
        skip: Number of records to skip
        limit: Maximum records to return
        api_key: API key for authentication
        
    Returns:
        EntityListResponse with events
    """
    # Dummy data for example
    events = [
        {
            "id": f"event_{i}",
            "name": f"Event {i}",
            "event_type": event_type or "disruption",
            "severity": 0.5 + (i * 0.1),
            "timestamp": datetime.utcnow(),
            "location": {"lat": 40.7128 + i, "lon": -74.0060 + i}
        }
        for i in range(20)
    ]
    
    # Filter by severity
    filtered = [
        e for e in events
        if severity_min <= e["severity"] <= severity_max
    ]
    
    return EntityListResponse(
        entity_type="Event",
        total=len(filtered),
        skip=skip,
        limit=limit,
        data=filtered[skip:skip + limit]
    )


@router.get("/airports", response_model=EntityListResponse)
async def get_airports(
    country: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    api_key: str = Depends(api_key_auth)
):
    """
    Get airports with filtering and pagination
    
    Args:
        country: Optional filter by country
        status: Optional filter by operational status
        skip: Number of records to skip
        limit: Maximum records to return
        api_key: API key for authentication
        
    Returns:
        EntityListResponse with airports
    """
    airports = [
        {
            "id": f"apt_{code}",
            "iata": code,
            "name": f"Airport {code}",
            "country": country or "USA",
            "status": status or "operational",
            "location": {"lat": 40.0 + i, "lon": -74.0 + i}
        }
        for i, code in enumerate(["JFK", "LAX", "ORD", "DFW", "ATL"])
    ]
    
    return EntityListResponse(
        entity_type="Airport",
        total=len(airports),
        skip=skip,
        limit=limit,
        data=airports[skip:skip + limit]
    )


@router.get("/ports", response_model=EntityListResponse)
async def get_ports(
    country: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    api_key: str = Depends(api_key_auth)
):
    """
    Get ports with filtering and pagination
    
    Args:
        country: Optional filter by country
        status: Optional filter by operational status
        skip: Number of records to skip
        limit: Maximum records to return
        api_key: API key for authentication
        
    Returns:
        EntityListResponse with ports
    """
    ports = [
        {
            "id": f"prt_{code}",
            "unlocode": code,
            "name": f"Port {code}",
            "country": country or "USA",
            "status": status or "operational",
            "location": {"lat": 40.0 + i, "lon": -74.0 + i}
        }
        for i, code in enumerate(["USNYC", "USLAX", "USHOU", "USMIA", "USSA"])
    ]
    
    return EntityListResponse(
        entity_type="Port",
        total=len(ports),
        skip=skip,
        limit=limit,
        data=ports[skip:skip + limit]
    )


@router.get("/corridors", response_model=EntityListResponse)
async def get_corridors(
    corridor_type: Optional[str] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    api_key: str = Depends(api_key_auth)
):
    """
    Get corridors with filtering and pagination
    
    Args:
        corridor_type: Optional filter by corridor type
        skip: Number of records to skip
        limit: Maximum records to return
        api_key: API key for authentication
        
    Returns:
        EntityListResponse with corridors
    """
    corridors = [
        {
            "id": f"cor_{i}",
            "name": f"Corridor {i}",
            "type": corridor_type or "sea",
            "distance_km": 1000 + (i * 100)
        }
        for i in range(15)
    ]
    
    return EntityListResponse(
        entity_type="Corridor",
        total=len(corridors),
        skip=skip,
        limit=limit,
        data=corridors[skip:skip + limit]
    )


@router.get("/flights", response_model=EntityListResponse)
async def get_flights(
    status: Optional[str] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    api_key: str = Depends(api_key_auth)
):
    """
    Get flights with filtering and pagination
    
    Args:
        status: Optional filter by flight status
        skip: Number of records to skip
        limit: Maximum records to return
        api_key: API key for authentication
        
    Returns:
        EntityListResponse with flights
    """
    flights = [
        {
            "id": f"flg_{i}",
            "callsign": f"AA{100+i}",
            "aircraft_type": "B777",
            "status": status or "scheduled",
            "departure_time": datetime.utcnow()
        }
        for i in range(20)
    ]
    
    return EntityListResponse(
        entity_type="Flight",
        total=len(flights),
        skip=skip,
        limit=limit,
        data=flights[skip:skip + limit]
    )


@router.get("/vessels", response_model=EntityListResponse)
async def get_vessels(
    vessel_type: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    api_key: str = Depends(api_key_auth)
):
    """
    Get vessels with filtering and pagination
    
    Args:
        vessel_type: Optional filter by vessel type
        status: Optional filter by vessel status
        skip: Number of records to skip
        limit: Maximum records to return
        api_key: API key for authentication
        
    Returns:
        EntityListResponse with vessels
    """
    vessels = [
        {
            "id": f"vsl_{i}",
            "mmsi": f"21{100000+i}",
            "name": f"Vessel {i}",
            "vessel_type": vessel_type or "container",
            "status": status or "in_transit",
            "flag_state": "USA"
        }
        for i in range(20)
    ]
    
    return EntityListResponse(
        entity_type="Vessel",
        total=len(vessels),
        skip=skip,
        limit=limit,
        data=vessels[skip:skip + limit]
    )
