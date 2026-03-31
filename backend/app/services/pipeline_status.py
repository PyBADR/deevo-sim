"""
Pipeline Status Tracker Service

Manages pipeline execution state with Redis backing for distributed tracking.
Provides lifecycle status updates for each stage of the orchestration pipeline.
"""

import json
import logging
from datetime import datetime
from typing import Optional, Dict, Any
from dataclasses import asdict, dataclass

import redis.asyncio as redis
from redis.asyncio import Redis

logger = logging.getLogger(__name__)


@dataclass
class StepStatus:
    """Status information for a single pipeline step"""
    stage: str
    status: str  # pending, running, completed, failed
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    duration_seconds: Optional[float] = None
    error: Optional[str] = None
    details: Optional[Dict[str, Any]] = None
    audit_hash: Optional[str] = None


class PipelineStatusTracker:
    """
    Manages pipeline execution state with Redis backing.
    
    Provides methods to:
    - Create and track pipeline executions
    - Update step status with timing and error information
    - Store and retrieve pipeline state
    - Aggregate results across all steps
    """
    
    def __init__(self, redis_url: str = "redis://localhost:6379/0"):
        """
        Initialize the pipeline status tracker.
        
        Args:
            redis_url: Redis connection URL
        """
        self.redis_url = redis_url
        self.redis_client: Optional[Redis] = None
        self.key_prefix = "pipeline:"
        
    async def initialize(self) -> None:
        """Initialize Redis connection"""
        try:
            self.redis_client = await redis.from_url(
                self.redis_url,
                decode_responses=True,
                encoding='utf-8'
            )
            # Test connection
            await self.redis_client.ping()
            logger.info("Pipeline status tracker Redis connection established")
        except Exception as e:
            logger.error(f"Failed to initialize Redis connection: {str(e)}")
            raise
    
    async def close(self) -> None:
        """Close Redis connection"""
        if self.redis_client:
            await self.redis_client.close()
            logger.info("Pipeline status tracker Redis connection closed")
    
    def _get_pipeline_key(self, pipeline_id: str) -> str:
        """Get Redis key for a pipeline"""
        return f"{self.key_prefix}{pipeline_id}"
    
    def _get_step_key(self, pipeline_id: str, stage: str) -> str:
        """Get Redis key for a pipeline step"""
        return f"{self.key_prefix}{pipeline_id}:step:{stage}"
    
    async def create_pipeline(self, pipeline_id: str, metadata: Optional[Dict[str, Any]] = None) -> None:
        """
        Create a new pipeline execution tracking record.
        
        Args:
            pipeline_id: Unique pipeline execution identifier
            metadata: Optional metadata about the pipeline (source, user, etc.)
        """
        if not self.redis_client:
            logger.warning("Redis client not initialized for create_pipeline")
            return
        
        try:
            pipeline_key = self._get_pipeline_key(pipeline_id)
            pipeline_data = {
                "pipeline_id": pipeline_id,
                "created_at": datetime.utcnow().isoformat(),
                "status": "created",
                "steps": {},
                "metadata": json.dumps(metadata or {})
            }
            await self.redis_client.hset(
                pipeline_key,
                mapping=pipeline_data
            )
            # Set expiration to 7 days
            await self.redis_client.expire(pipeline_key, 7 * 24 * 3600)
            logger.info(f"Created pipeline tracking record: {pipeline_id}")
        except Exception as e:
            logger.error(f"Failed to create pipeline record: {str(e)}")
            raise
    
    async def update_step(
        self,
        pipeline_id: str,
        stage: str,
        status: str,
        duration_seconds: Optional[float] = None,
        error: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        audit_hash: Optional[str] = None
    ) -> None:
        """
        Update status for a single pipeline step.
        
        Args:
            pipeline_id: Pipeline execution identifier
            stage: Pipeline stage name (e.g., "INGEST", "NORMALIZE")
            status: Step status (pending, running, completed, failed)
            duration_seconds: Execution duration in seconds
            error: Error message if step failed
            details: Additional step details
            audit_hash: SHA-256 hash of step results for compliance
        """
        if not self.redis_client:
            logger.warning("Redis client not initialized for update_step")
            return
        
        try:
            step_data = {
                "stage": stage,
                "status": status,
                "timestamp": datetime.utcnow().isoformat(),
                "duration_seconds": duration_seconds or 0,
                "error": error or "",
                "details": json.dumps(details or {}),
                "audit_hash": audit_hash or ""
            }
            
            step_key = self._get_step_key(pipeline_id, stage)
            await self.redis_client.hset(
                step_key,
                mapping=step_data
            )
            
            # Update pipeline's step record
            pipeline_key = self._get_pipeline_key(pipeline_id)
            await self.redis_client.hset(
                pipeline_key,
                "last_update",
                datetime.utcnow().isoformat()
            )
            
            log_level = "error" if status == "failed" else "info"
            getattr(logger, log_level)(
                f"Updated pipeline {pipeline_id} step {stage}: {status}"
            )
        except Exception as e:
            logger.error(f"Failed to update step status: {str(e)}")
            raise
    
    async def get_pipeline_status(self, pipeline_id: str) -> Dict[str, Any]:
        """
        Get complete status for a pipeline.
        
        Args:
            pipeline_id: Pipeline execution identifier
            
        Returns:
            Dictionary with pipeline status and all step statuses
        """
        if not self.redis_client:
            logger.warning("Redis client not initialized for get_pipeline_status")
            return {"error": "Redis client not initialized"}
        
        try:
            pipeline_key = self._get_pipeline_key(pipeline_id)
            pipeline_data = await self.redis_client.hgetall(pipeline_key)
            
            if not pipeline_data:
                return {"error": f"Pipeline {pipeline_id} not found"}
            
            # Fetch all steps for this pipeline
            steps = {}
            stages = [
                "INGEST", "NORMALIZE", "ENRICH", "STORE", "GRAPH_BUILD",
                "SCORE", "PHYSICS_UPDATE", "INSURANCE_UPDATE", "SCENARIO_RUN", "API_OUTPUT"
            ]
            
            for stage in stages:
                step_key = self._get_step_key(pipeline_id, stage)
                step_data = await self.redis_client.hgetall(step_key)
                if step_data:
                    steps[stage] = step_data
            
            return {
                "pipeline_id": pipeline_id,
                "created_at": pipeline_data.get("created_at"),
                "last_update": pipeline_data.get("last_update"),
                "status": pipeline_data.get("status", "unknown"),
                "steps": steps,
                "metadata": json.loads(pipeline_data.get("metadata", "{}"))
            }
        except Exception as e:
            logger.error(f"Failed to get pipeline status: {str(e)}")
            return {"error": str(e)}
    
    async def mark_pipeline_complete(self, pipeline_id: str) -> None:
        """
        Mark pipeline as complete.
        
        Args:
            pipeline_id: Pipeline execution identifier
        """
        if not self.redis_client:
            logger.warning("Redis client not initialized for mark_pipeline_complete")
            return
        
        try:
            pipeline_key = self._get_pipeline_key(pipeline_id)
            await self.redis_client.hset(
                pipeline_key,
                mapping={
                    "status": "complete",
                    "completed_at": datetime.utcnow().isoformat()
                }
            )
            logger.info(f"Marked pipeline {pipeline_id} as complete")
        except Exception as e:
            logger.error(f"Failed to mark pipeline complete: {str(e)}")
            raise
    
    async def mark_pipeline_failed(self, pipeline_id: str, error: str) -> None:
        """
        Mark pipeline as failed.
        
        Args:
            pipeline_id: Pipeline execution identifier
            error: Error message describing the failure
        """
        if not self.redis_client:
            logger.warning("Redis client not initialized for mark_pipeline_failed")
            return
        
        try:
            pipeline_key = self._get_pipeline_key(pipeline_id)
            await self.redis_client.hset(
                pipeline_key,
                mapping={
                    "status": "failed",
                    "failed_at": datetime.utcnow().isoformat(),
                    "failure_reason": error
                }
            )
            logger.error(f"Marked pipeline {pipeline_id} as failed: {error}")
        except Exception as e:
            logger.error(f"Failed to mark pipeline failed: {str(e)}")
            raise
    
    async def get_step_status(self, pipeline_id: str, stage: str) -> Optional[Dict[str, Any]]:
        """
        Get status for a specific step.
        
        Args:
            pipeline_id: Pipeline execution identifier
            stage: Pipeline stage name
            
        Returns:
            Step status dictionary or None if not found
        """
        if not self.redis_client:
            logger.warning("Redis client not initialized for get_step_status")
            return None
        
        try:
            step_key = self._get_step_key(pipeline_id, stage)
            step_data = await self.redis_client.hgetall(step_key)
            return step_data if step_data else None
        except Exception as e:
            logger.error(f"Failed to get step status: {str(e)}")
            return None
    
    async def delete_pipeline(self, pipeline_id: str) -> None:
        """
        Delete a pipeline execution record (for cleanup).
        
        Args:
            pipeline_id: Pipeline execution identifier
        """
        if not self.redis_client:
            logger.warning("Redis client not initialized for delete_pipeline")
            return
        
        try:
            pipeline_key = self._get_pipeline_key(pipeline_id)
            
            # Get all stages and delete step records
            stages = [
                "INGEST", "NORMALIZE", "ENRICH", "STORE", "GRAPH_BUILD",
                "SCORE", "PHYSICS_UPDATE", "INSURANCE_UPDATE", "SCENARIO_RUN", "API_OUTPUT"
            ]
            
            for stage in stages:
                step_key = self._get_step_key(pipeline_id, stage)
                await self.redis_client.delete(step_key)
            
            # Delete pipeline record
            await self.redis_client.delete(pipeline_key)
            logger.info(f"Deleted pipeline record: {pipeline_id}")
        except Exception as e:
            logger.error(f"Failed to delete pipeline: {str(e)}")
            raise
    
    async def get_recent_pipelines(self, limit: int = 10) -> list:
        """
        Get recently completed pipelines.
        
        Args:
            limit: Maximum number of pipelines to return
            
        Returns:
            List of pipeline metadata dictionaries
        """
        if not self.redis_client:
            logger.warning("Redis client not initialized for get_recent_pipelines")
            return []
        
        try:
            # Get all pipeline keys
            pattern = f"{self.key_prefix}*"
            keys = await self.redis_client.keys(pattern)
            
            pipelines = []
            for key in keys:
                # Skip step keys, only process pipeline records
                if ":step:" not in key:
                    data = await self.redis_client.hgetall(key)
                    if data:
                        pipelines.append(data)
            
            # Sort by created_at descending and limit
            pipelines.sort(
                key=lambda x: x.get("created_at", ""),
                reverse=True
            )
            
            return pipelines[:limit]
        except Exception as e:
            logger.error(f"Failed to get recent pipelines: {str(e)}")
            return []
