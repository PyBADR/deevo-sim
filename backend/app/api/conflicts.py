"""Conflict Intelligence Router

Provides endpoints for querying conflict events, analyzing escalation patterns,
and extracting spatial intelligence for conflict zones.
"""

import logging
import uuid
from datetime import datetime
from typing import Optional, List

from fastapi import APIRouter, Depends, HTTPException, Query

from app.api.models import (
    ConflictListResponse, ConflictDetailResponse, ConflictHeatmapResponse,
    ConflictAnalysisResponse
)
from app.api.auth import api_key_auth

router = APIRouter()
logger = logging.getLogger(__name__)

# In-memory conflict data storage (replace with database in production)
conflicts_db = {}


@router.get(
    "/conflicts",
    response_model=ConflictListResponse,
    tags=["Conflict Intelligence"]
)
async def list_conflicts(
    region: Optional[str] = Query(None, description="Filter by region"),
    severity_min: Optional[float] = Query(None, ge=0, le=1, description="Minimum severity"),
    severity_max: Optional[float] = Query(None, ge=0, le=1, description="Maximum severity"),
    conflict_type: Optional[str] = Query(None, description="Filter by conflict type"),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=500),
    api_key: str = Depends(api_key_auth)
):
    """
    List conflict events with optional filtering.
    
    Supports filtering by:
    - region: Geographic region name
    - severity_min/max: Severity range (0-1)
    - conflict_type: Type of conflict (armed_conflict, protest, etc.)
    
    Args:
        region: Filter by region
        severity_min: Minimum severity threshold
        severity_max: Maximum severity threshold
        conflict_type: Type of conflict
        skip: Number of records to skip
        limit: Maximum records to return
        api_key: API key for authentication
        
    Returns:
        ConflictListResponse with paginated conflict list
    """
    try:
        # Filter conflicts based on criteria
        filtered = list(conflicts_db.values())
        
        if region:
            filtered = [c for c in filtered if c.get("region", "").lower() == region.lower()]
        
        if severity_min is not None:
            filtered = [c for c in filtered if c.get("severity", 0) >= severity_min]
        
        if severity_max is not None:
            filtered = [c for c in filtered if c.get("severity", 0) <= severity_max]
        
        if conflict_type:
            filtered = [c for c in filtered if c.get("type", "").lower() == conflict_type.lower()]
        
        total = len(filtered)
        data = filtered[skip:skip + limit]
        
        return ConflictListResponse(
            total=total,
            skip=skip,
            limit=limit,
            data=data
        )
    except Exception as e:
        logger.error(f"Failed to list conflicts: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to list conflicts")


@router.get(
    "/conflicts/{conflict_id}",
    response_model=ConflictDetailResponse,
    tags=["Conflict Intelligence"]
)
async def get_conflict_detail(
    conflict_id: str,
    api_key: str = Depends(api_key_auth)
):
    """
    Get detailed information about a specific conflict event.
    
    Args:
        conflict_id: ID of the conflict event
        api_key: API key for authentication
        
    Returns:
        ConflictDetailResponse with complete conflict details
        
    Raises:
        HTTPException: 404 if conflict not found
    """
    try:
        if conflict_id not in conflicts_db:
            raise HTTPException(status_code=404, detail="Conflict not found")
        
        conflict = conflicts_db[conflict_id]
        
        return ConflictDetailResponse(
            conflict_id=conflict_id,
            region=conflict.get("region"),
            name=conflict.get("name"),
            conflict_type=conflict.get("type"),
            severity=conflict.get("severity", 0.5),
            status=conflict.get("status", "ongoing"),
            start_date=conflict.get("start_date"),
            latest_event_date=conflict.get("latest_event_date"),
            latitude=conflict.get("latitude"),
            longitude=conflict.get("longitude"),
            description=conflict.get("description"),
            actors_involved=conflict.get("actors", []),
            impact_summary=conflict.get("impact_summary", {}),
            related_incidents=conflict.get("related_incidents", [])
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get conflict detail: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve conflict details")


@router.get(
    "/conflicts/active",
    response_model=ConflictListResponse,
    tags=["Conflict Intelligence"]
)
async def get_active_conflicts(
    region: Optional[str] = Query(None, description="Filter by region"),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=500),
    api_key: str = Depends(api_key_auth)
):
    """
    Get currently active conflicts in the GCC region.
    
    Filters for conflicts with 'ongoing' status.
    
    Args:
        region: Optional region filter
        skip: Number of records to skip
        limit: Maximum records to return
        api_key: API key for authentication
        
    Returns:
        ConflictListResponse with active conflicts
    """
    try:
        # Filter for active conflicts
        filtered = [
            c for c in conflicts_db.values()
            if c.get("status") == "ongoing"
        ]
        
        if region:
            filtered = [c for c in filtered if c.get("region", "").lower() == region.lower()]
        
        total = len(filtered)
        data = filtered[skip:skip + limit]
        
        return ConflictListResponse(
            total=total,
            skip=skip,
            limit=limit,
            data=data
        )
    except Exception as e:
        logger.error(f"Failed to get active conflicts: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve active conflicts")


@router.get(
    "/conflicts/heatmap",
    response_model=ConflictHeatmapResponse,
    tags=["Conflict Intelligence"]
)
async def get_conflict_heatmap(
    grid_size: int = Query(10, ge=1, le=100, description="Grid size (cells per side)"),
    min_severity: Optional[float] = Query(0, ge=0, le=1),
    api_key: str = Depends(api_key_auth)
):
    """
    Get conflict density heatmap for visualization.
    
    Returns gridded conflict data for rendering heatmap layers on maps.
    
    Args:
        grid_size: Number of grid cells per side
        min_severity: Minimum severity to include
        api_key: API key for authentication
        
    Returns:
        ConflictHeatmapResponse with grid data and densities
    """
    try:
        # Filter conflicts by severity
        filtered = [
            c for c in conflicts_db.values()
            if c.get("severity", 0) >= (min_severity or 0)
        ]
        
        # Build grid heatmap
        grid_cells = []
        
        # Simple grid approach: partition GCC region into grid_size x grid_size cells
        # GCC region roughly: lat 24-32N, lon 43-60E (simplified bounds)
        lat_min, lat_max = 24.0, 32.0
        lon_min, lon_max = 43.0, 60.0
        
        lat_step = (lat_max - lat_min) / grid_size
        lon_step = (lon_max - lon_min) / grid_size
        
        for i in range(grid_size):
            for j in range(grid_size):
                cell_lat_min = lat_min + (i * lat_step)
                cell_lat_max = lat_min + ((i + 1) * lat_step)
                cell_lon_min = lon_min + (j * lon_step)
                cell_lon_max = lon_min + ((j + 1) * lon_step)
                
                # Count conflicts in this cell
                conflicts_in_cell = [
                    c for c in filtered
                    if (cell_lat_min <= c.get("latitude", 0) < cell_lat_max and
                        cell_lon_min <= c.get("longitude", 0) < cell_lon_max)
                ]
                
                if conflicts_in_cell:
                    avg_severity = sum(c.get("severity", 0) for c in conflicts_in_cell) / len(conflicts_in_cell)
                    
                    grid_cells.append({
                        "cell_id": f"cell_{i}_{j}",
                        "lat_min": cell_lat_min,
                        "lat_max": cell_lat_max,
                        "lon_min": cell_lon_min,
                        "lon_max": cell_lon_max,
                        "conflict_count": len(conflicts_in_cell),
                        "avg_severity": avg_severity,
                        "intensity": avg_severity * len(conflicts_in_cell) / 10  # Normalized intensity
                    })
        
        return ConflictHeatmapResponse(
            grid_size=grid_size,
            bounds={
                "north": lat_max,
                "south": lat_min,
                "east": lon_max,
                "west": lon_min
            },
            cells=grid_cells,
            total_conflicts=len(filtered),
            timestamp=datetime.utcnow()
        )
    except Exception as e:
        logger.error(f"Failed to compute conflict heatmap: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to compute heatmap")


@router.post(
    "/conflicts/analyze",
    response_model=ConflictAnalysisResponse,
    tags=["Conflict Intelligence"]
)
async def analyze_conflicts(
    conflict_ids: List[str],
    api_key: str = Depends(api_key_auth)
):
    """
    Analyze a set of conflicts for patterns and escalation risk.
    
    Identifies:
    - Geographic clustering
    - Temporal patterns (frequency, escalation trends)
    - Actor involvement patterns
    - Risk of spillover/escalation
    
    Args:
        conflict_ids: List of conflict IDs to analyze
        api_key: API key for authentication
        
    Returns:
        ConflictAnalysisResponse with analysis results
    """
    try:
        if not conflict_ids:
            raise HTTPException(status_code=400, detail="conflict_ids required")
        
        # Validate all conflicts exist
        selected_conflicts = []
        for cid in conflict_ids:
            if cid not in conflicts_db:
                raise HTTPException(status_code=404, detail=f"Conflict {cid} not found")
            selected_conflicts.append(conflicts_db[cid])
        
        # Analyze patterns
        regions = set(c.get("region") for c in selected_conflicts if c.get("region"))
        conflict_types = set(c.get("type") for c in selected_conflicts if c.get("type"))
        actors = set()
        for c in selected_conflicts:
            actors.update(c.get("actors", []))
        
        # Compute severity statistics
        severities = [c.get("severity", 0.5) for c in selected_conflicts]
        avg_severity = sum(severities) / len(severities) if severities else 0
        max_severity = max(severities) if severities else 0
        
        # Escalation risk: based on severity and recency
        recent_conflicts = [
            c for c in selected_conflicts
            if (datetime.utcnow() - c.get("latest_event_date", datetime.utcnow())).days < 30
        ]
        escalation_risk = min(1.0, len(recent_conflicts) / len(selected_conflicts)) if selected_conflicts else 0
        
        # Spillover risk: geographic proximity
        if len(selected_conflicts) > 1:
            spillover_risk = 0.3 + (0.2 * len(regions) / len(selected_conflicts))  # More regions = more spillover risk
            spillover_risk = min(1.0, spillover_risk)
        else:
            spillover_risk = 0.1
        
        return ConflictAnalysisResponse(
            conflict_count=len(selected_conflicts),
            regions_involved=list(regions),
            types_involved=list(conflict_types),
            actors_involved=list(actors),
            avg_severity=avg_severity,
            max_severity=max_severity,
            severity_trend="stable",  # Would compute from historical data
            temporal_pattern="distributed",  # Would analyze event timing
            escalation_risk=escalation_risk,
            spillover_risk=spillover_risk,
            recommended_actions=[
                "Monitor border security",
                "Increase intelligence gathering",
                "Prepare contingency routes"
            ],
            analysis_timestamp=datetime.utcnow()
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Conflict analysis failed: {str(e)}")
        raise HTTPException(status_code=500, detail="Analysis failed")
