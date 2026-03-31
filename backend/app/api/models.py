from typing import Any, Optional, Generic, TypeVar
from pydantic import BaseModel, Field
from datetime import datetime
from enum import Enum

T = TypeVar('T')

# Health and metadata models
class HealthResponse(BaseModel):
    status: str = Field(..., example="healthy")
    timestamp: datetime
    service_name: str = Field(..., example="DecisionCore Intelligence GCC")
    version: str = Field(..., example="1.0.0")

class VersionResponse(BaseModel):
    version: str = Field(..., example="1.0.0")
    build_date: datetime
    environment: str = Field(..., example="production")

# Scenario models
class ScenarioRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    scenario_type: str = Field(..., example="disruption")
    parameters: dict = Field(default_factory=dict)

class ScenarioResponse(BaseModel):
    scenario_id: str
    name: str
    description: Optional[str]
    scenario_type: str
    parameters: dict
    created_at: datetime
    updated_at: datetime

class ScenarioRunResponse(BaseModel):
    run_id: str
    scenario_id: str
    status: str = Field(..., example="completed")
    started_at: datetime
    completed_at: Optional[datetime] = None
    results: Optional[dict] = None
    error: Optional[str] = None

class ScenarioRunListResponse(BaseModel):
    total: int
    skip: int
    limit: int
    data: list[ScenarioRunResponse]

class ScenarioListResponse(BaseModel):
    total: int
    skip: int
    limit: int
    data: list[ScenarioResponse]

# Entity models
class EventEntity(BaseModel):
    event_id: str
    event_type: str
    severity: int
    location: str
    timestamp: datetime

class AirportEntity(BaseModel):
    airport_id: str
    name: str
    country: str
    status: str
    latitude: float
    longitude: float

class PortEntity(BaseModel):
    port_id: str
    name: str
    country: str
    status: str
    latitude: float
    longitude: float

class CorridorEntity(BaseModel):
    corridor_id: str
    name: str
    corridor_type: str
    origin: str
    destination: str
    capacity: int

class FlightEntity(BaseModel):
    flight_id: str
    flight_number: str
    status: str
    origin: str
    destination: str
    departure_time: datetime
    arrival_time: Optional[datetime] = None

class VesselEntity(BaseModel):
    vessel_id: str
    name: str
    vessel_type: str
    status: str
    current_location: str
    latitude: float
    longitude: float

class ActorEntity(BaseModel):
    actor_id: str
    name: str
    actor_type: str
    influence_score: float
    specialization: str

class EntityListResponse(BaseModel):
    entity_type: str
    total: int
    skip: int
    limit: int
    data: list[dict]

# Graph query models
class RiskPropagationRequest(BaseModel):
    source_entity_id: str
    source_entity_type: str
    max_hops: int = Field(default=3, ge=1, le=10)
    risk_threshold: float = Field(default=0.3, ge=0, le=1)

class RiskPropagationPath(BaseModel):
    entity_id: str
    entity_type: str
    risk_score: float
    distance: int
    propagation_vector: str

class ChokePointRequest(BaseModel):
    region: Optional[str] = None
    corridor_type: Optional[str] = None

class ChokePointAnalysis(BaseModel):
    entity_id: str
    entity_type: str
    criticality_score: float
    alternate_routes: int
    dependency_count: int

class RerouteRequest(BaseModel):
    source_location: str
    destination_location: str
    origin_lat: float
    origin_lon: float
    dest_lat: float
    dest_lon: float
    avoid_regions: Optional[list[str]] = None

class RerouteAlternative(BaseModel):
    route_id: str
    distance_km: float
    estimated_duration_hours: float
    corridor_ids: list[str]
    risk_level: str

class NearestImpactedRequest(BaseModel):
    latitude: float
    longitude: float
    radius_km: float = Field(default=500, gt=0)
    entity_types: Optional[list[str]] = None

class NearestImpactedResult(BaseModel):
    entity_id: str
    entity_type: str
    distance_km: float
    impact_severity: float
    location_name: str

class RegionCascadeRequest(BaseModel):
    region: str
    event_id: str

class CascadeEffect(BaseModel):
    source_entity_id: str
    target_entity_id: str
    target_entity_type: str
    effect_type: str
    intensity: float

class ScenarioSubgraphRequest(BaseModel):
    scenario_id: str
    include_relationships: bool = True

class GraphNode(BaseModel):
    node_id: str
    node_type: str
    properties: dict

class GraphEdge(BaseModel):
    source_id: str
    target_id: str
    relationship_type: str
    properties: dict

class GraphSubgraph(BaseModel):
    nodes: list[GraphNode]
    edges: list[GraphEdge]

class ActorInfluenceRequest(BaseModel):
    actor_id: str

class ActorInfluenceAnalysis(BaseModel):
    actor_id: str
    total_influence_score: float
    influenced_entities_count: int
    primary_influence_vectors: list[str]
    risk_contribution: float

class GraphQueryResponse(BaseModel):
    query_type: str
    success: bool
    data: Optional[dict] = None
    error: Optional[str] = None
    duration_ms: int = Field(default=0)

class GraphQueryRequest(BaseModel):
    query_type: str
    parameters: dict

class PaginationParams(BaseModel):
    skip: int = Field(default=0, ge=0)
    limit: int = Field(default=20, ge=1, le=1000)

class IngestionStatusResponse(BaseModel):
    timestamp: datetime
    status: str
    pending_jobs: int
    completed_jobs: int
    failed_jobs: int
    last_ingest_timestamp: Optional[datetime] = None

# Error response
class ErrorResponse(BaseModel):
    detail: str
    status_code: int
    timestamp: datetime

# Generic pagination wrapper
class PaginatedResponse(BaseModel, Generic[T]):
    total: int
    skip: int
    limit: int
    data: list[T]
