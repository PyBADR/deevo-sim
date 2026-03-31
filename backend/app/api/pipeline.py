"""
Pipeline API Router

Provides FastAPI endpoints for controlling and monitoring the Lifecycle Orchestration Service.
Handles pipeline creation, execution, status queries, and result retrieval.
"""

import logging
import uuid
from typing import Optional, Dict, Any

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field

from app.config.settings import Settings
from app.services.orchestrator import LifecycleOrchestrator, LifecycleExecutionResult
from app.services.pipeline_status import PipelineStatusTracker

logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/pipeline", tags=["Lifecycle Pipeline"])


# ============================================================================
# Request/Response Models
# ============================================================================

class PipelineStartRequest(BaseModel):
    """Request to start a new pipeline execution"""
    data_source: str = Field(..., description="Data source identifier (e.g., 'acled', 'aviation')")
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="Optional metadata about the pipeline")
    
    class Config:
        json_schema_extra = {
            "example": {
                "data_source": "acled",
                "metadata": {"user": "analyst@example.com", "campaign": "Q1-2026"}
            }
        }


class PipelineStartResponse(BaseModel):
    """Response from starting a pipeline"""
    pipeline_id: str = Field(..., description="Unique pipeline execution identifier")
    status: str = Field(default="created", description="Pipeline status")
    data_source: str = Field(..., description="Data source being processed")
    created_at: str = Field(..., description="ISO 8601 timestamp of pipeline creation")
    
    class Config:
        json_schema_extra = {
            "example": {
                "pipeline_id": "pipe_abc123def456",
                "status": "created",
                "data_source": "acled",
                "created_at": "2026-03-31T12:00:00Z"
            }
        }


class PipelineStepStatus(BaseModel):
    """Status of a single pipeline step"""
    stage: str = Field(..., description="Pipeline stage name")
    status: str = Field(..., description="Step status (pending, running, completed, failed)")
    duration_seconds: Optional[float] = Field(default=None, description="Execution duration in seconds")
    error: Optional[str] = Field(default=None, description="Error message if step failed")
    details: Optional[Dict[str, Any]] = Field(default=None, description="Step-specific details")
    audit_hash: Optional[str] = Field(default=None, description="SHA-256 audit hash of step results")


class PipelineStatusResponse(BaseModel):
    """Complete status of a pipeline execution"""
    pipeline_id: str = Field(..., description="Pipeline execution identifier")
    status: str = Field(..., description="Overall pipeline status")
    created_at: str = Field(..., description="Pipeline creation timestamp")
    last_update: Optional[str] = Field(default=None, description="Last update timestamp")
    steps: Dict[str, Dict[str, Any]] = Field(..., description="Status of all pipeline steps")
    progress_percent: int = Field(..., description="Overall progress percentage (0-100)")
    
    class Config:
        json_schema_extra = {
            "example": {
                "pipeline_id": "pipe_abc123",
                "status": "running",
                "created_at": "2026-03-31T12:00:00Z",
                "last_update": "2026-03-31T12:05:30Z",
                "steps": {
                    "INGEST": {"status": "completed", "duration_seconds": 45.2},
                    "NORMALIZE": {"status": "completed", "duration_seconds": 23.1},
                    "ENRICH": {"status": "running"}
                },
                "progress_percent": 30
            }
        }


class PipelineResultResponse(BaseModel):
    """Complete results of a pipeline execution"""
    pipeline_id: str = Field(..., description="Pipeline execution identifier")
    status: str = Field(..., description="Final pipeline status")
    execution_duration_seconds: float = Field(..., description="Total execution time")
    final_audit_hash: str = Field(..., description="Final SHA-256 audit hash")
    steps_completed: int = Field(..., description="Number of completed steps")
    total_steps: int = Field(default=10, description="Total number of pipeline steps")
    results: Dict[str, Any] = Field(..., description="Results from all completed steps")
    errors: Optional[Dict[str, str]] = Field(default=None, description="Errors encountered in pipeline")
    
    class Config:
        json_schema_extra = {
            "example": {
                "pipeline_id": "pipe_abc123",
                "status": "completed",
                "execution_duration_seconds": 543.2,
                "final_audit_hash": "abc123def456...",
                "steps_completed": 10,
                "total_steps": 10,
                "results": {
                    "INGEST": {"records_ingested": 1500},
                    "NORMALIZE": {"records_normalized": 1450},
                    "ENRICH": {"records_enriched": 1450}
                },
                "errors": None
            }
        }


class RecentPipelinesResponse(BaseModel):
    """List of recent pipelines"""
    pipelines: list = Field(..., description="List of recent pipeline executions")
    count: int = Field(..., description="Number of pipelines returned")


# ============================================================================
# Dependency Injection
# ============================================================================

def get_settings() -> Settings:
    """Get application settings"""
    return Settings()


async def get_orchestrator(settings: Settings = Depends(get_settings)) -> LifecycleOrchestrator:
    """Get or create orchestrator instance"""
    # In production, this would be a singleton managed by the app
    # For now, create a fresh instance per request
    orchestrator = LifecycleOrchestrator()
    await orchestrator.initialize()
    return orchestrator


async def get_status_tracker(settings: Settings = Depends(get_settings)) -> PipelineStatusTracker:
    """Get or create status tracker instance"""
    tracker = PipelineStatusTracker(redis_url=settings.redis_url)
    await tracker.initialize()
    return tracker


# ============================================================================
# Endpoints
# ============================================================================

@router.post(
    "/start",
    response_model=PipelineStartResponse,
    summary="Start a new pipeline execution",
    description="Initiates a new lifecycle orchestration pipeline for the specified data source"
)
async def start_pipeline(
    request: PipelineStartRequest,
    orchestrator: LifecycleOrchestrator = Depends(get_orchestrator),
    status_tracker: PipelineStatusTracker = Depends(get_status_tracker)
) -> PipelineStartResponse:
    """
    Start a new pipeline execution.
    
    Creates a new pipeline tracking record and initiates the 10-step lifecycle orchestration.
    
    Args:
        request: Pipeline start request with data source and optional metadata
        
    Returns:
        Pipeline start response with pipeline ID and creation timestamp
        
    Raises:
        HTTPException: If pipeline creation fails
    """
    try:
        # Generate unique pipeline ID
        pipeline_id = f"pipe_{uuid.uuid4().hex[:12]}"
        
        # Create pipeline tracking record
        await status_tracker.create_pipeline(
            pipeline_id=pipeline_id,
            metadata={
                "data_source": request.data_source,
                **(request.metadata if request.metadata else {})
            }
        )
        
        logger.info(f"Started pipeline {pipeline_id} for {request.data_source}")
        
        return PipelineStartResponse(
            pipeline_id=pipeline_id,
            status="created",
            data_source=request.data_source,
            created_at=__import__('datetime').datetime.utcnow().isoformat()
        )
    except Exception as e:
        logger.error(f"Failed to start pipeline: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to start pipeline: {str(e)}"
        )


@router.post(
    "/{pipeline_id}/execute",
    response_model=PipelineResultResponse,
    summary="Execute the complete pipeline",
    description="Executes all 10 stages of the lifecycle orchestration pipeline in strict order"
)
async def execute_pipeline(
    pipeline_id: str,
    orchestrator: LifecycleOrchestrator = Depends(get_orchestrator),
    status_tracker: PipelineStatusTracker = Depends(get_status_tracker)
) -> PipelineResultResponse:
    """
    Execute the complete lifecycle orchestration pipeline.
    
    Runs all 10 stages (INGEST → NORMALIZE → ENRICH → STORE → GRAPH_BUILD → SCORE → 
    PHYSICS_UPDATE → INSURANCE_UPDATE → SCENARIO_RUN → API_OUTPUT) in strict order.
    
    Args:
        pipeline_id: Unique pipeline execution identifier
        
    Returns:
        Complete execution results with all step outputs and timing information
        
    Raises:
        HTTPException: If pipeline execution fails
    """
    try:
        logger.info(f"Executing pipeline {pipeline_id}")
        
        # Execute the complete lifecycle
        result: LifecycleExecutionResult = await orchestrator.execute_lifecycle(
            pipeline_id=pipeline_id,
            status_tracker=status_tracker
        )
        
        # Mark pipeline complete or failed
        if result.status == "completed":
            await status_tracker.mark_pipeline_complete(pipeline_id)
        else:
            error_msg = "; ".join(result.errors) if result.errors else "Unknown error"
            await status_tracker.mark_pipeline_failed(pipeline_id, error_msg)
        
        logger.info(f"Pipeline {pipeline_id} execution finished with status: {result.status}")
        
        # Build response
        return PipelineResultResponse(
            pipeline_id=pipeline_id,
            status=result.status,
            execution_duration_seconds=result.execution_duration_seconds,
            final_audit_hash=result.final_audit_hash,
            steps_completed=len([s for s in result.step_results if s.get("status") == "completed"]),
            total_steps=10,
            results={
                stage: result.step_results.get(stage, {})
                for stage in [
                    "INGEST", "NORMALIZE", "ENRICH", "STORE", "GRAPH_BUILD",
                    "SCORE", "PHYSICS_UPDATE", "INSURANCE_UPDATE", "SCENARIO_RUN", "API_OUTPUT"
                ]
            },
            errors=result.errors if result.errors else None
        )
    except Exception as e:
        logger.error(f"Failed to execute pipeline {pipeline_id}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to execute pipeline: {str(e)}"
        )


@router.get(
    "/{pipeline_id}/status",
    response_model=PipelineStatusResponse,
    summary="Get pipeline execution status",
    description="Retrieve current status and progress of a pipeline execution"
)
async def get_pipeline_status(
    pipeline_id: str,
    status_tracker: PipelineStatusTracker = Depends(get_status_tracker)
) -> PipelineStatusResponse:
    """
    Get the current status of a pipeline execution.
    
    Args:
        pipeline_id: Pipeline execution identifier
        
    Returns:
        Current pipeline status with step progress
        
    Raises:
        HTTPException: If pipeline not found
    """
    try:
        status = await status_tracker.get_pipeline_status(pipeline_id)
        
        if "error" in status:
            raise HTTPException(
                status_code=404,
                detail=f"Pipeline {pipeline_id} not found"
            )
        
        # Calculate progress
        steps = status.get("steps", {})
        completed_steps = sum(
            1 for step in steps.values()
            if step.get("status") == "completed"
        )
        progress_percent = int((completed_steps / 10) * 100)
        
        return PipelineStatusResponse(
            pipeline_id=pipeline_id,
            status=status.get("status", "unknown"),
            created_at=status.get("created_at", ""),
            last_update=status.get("last_update"),
            steps=steps,
            progress_percent=progress_percent
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get pipeline status: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get pipeline status: {str(e)}"
        )


@router.get(
    "",
    response_model=RecentPipelinesResponse,
    summary="List recent pipelines",
    description="Retrieve a list of recently executed pipelines"
)
async def list_pipelines(
    limit: int = Query(10, ge=1, le=100, description="Maximum number of pipelines to return"),
    status_tracker: PipelineStatusTracker = Depends(get_status_tracker)
) -> RecentPipelinesResponse:
    """
    Get a list of recent pipeline executions.
    
    Args:
        limit: Maximum number of pipelines to return (1-100)
        
    Returns:
        List of recent pipelines with their status
    """
    try:
        pipelines = await status_tracker.get_recent_pipelines(limit=limit)
        return RecentPipelinesResponse(
            pipelines=pipelines,
            count=len(pipelines)
        )
    except Exception as e:
        logger.error(f"Failed to list pipelines: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to list pipelines: {str(e)}"
        )


@router.get(
    "/{pipeline_id}/step/{stage}",
    response_model=Optional[PipelineStepStatus],
    summary="Get specific step status",
    description="Retrieve status and details for a specific pipeline step"
)
async def get_step_status(
    pipeline_id: str,
    stage: str,
    status_tracker: PipelineStatusTracker = Depends(get_status_tracker)
) -> Optional[PipelineStepStatus]:
    """
    Get status for a specific pipeline step.
    
    Args:
        pipeline_id: Pipeline execution identifier
        stage: Pipeline stage name (INGEST, NORMALIZE, etc.)
        
    Returns:
        Step status with timing and error information
        
    Raises:
        HTTPException: If step not found
    """
    try:
        step_status = await status_tracker.get_step_status(pipeline_id, stage)
        
        if not step_status:
            raise HTTPException(
                status_code=404,
                detail=f"Step {stage} not found for pipeline {pipeline_id}"
            )
        
        return PipelineStepStatus(
            stage=step_status.get("stage", stage),
            status=step_status.get("status", "unknown"),
            duration_seconds=float(step_status.get("duration_seconds", 0)) or None,
            error=step_status.get("error") or None,
            details=__import__('json').loads(step_status.get("details", "{}")),
            audit_hash=step_status.get("audit_hash") or None
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get step status: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get step status: {str(e)}"
        )


@router.delete(
    "/{pipeline_id}",
    summary="Delete pipeline record",
    description="Remove a pipeline execution record from tracking"
)
async def delete_pipeline(
    pipeline_id: str,
    status_tracker: PipelineStatusTracker = Depends(get_status_tracker)
) -> Dict[str, str]:
    """
    Delete a pipeline execution record.
    
    Args:
        pipeline_id: Pipeline execution identifier
        
    Returns:
        Confirmation message
    """
    try:
        await status_tracker.delete_pipeline(pipeline_id)
        return {"message": f"Pipeline {pipeline_id} deleted successfully"}
    except Exception as e:
        logger.error(f"Failed to delete pipeline: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to delete pipeline: {str(e)}"
        )
