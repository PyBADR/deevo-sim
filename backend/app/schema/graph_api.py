"""
Impact Observatory | مرصد الأثر — Graph API Schemas

Pydantic response models for /api/v1/graph/* endpoints.
"""

from pydantic import BaseModel, Field
from typing import Optional


class GraphNodeResponse(BaseModel):
    id: str
    label: str
    label_ar: str = ""
    layer: str
    type: str = "Topic"
    weight: float
    lat: float
    lng: float
    sensitivity: float = 0.5
    stress: Optional[float] = None
    classification: Optional[str] = None

    model_config = {"extra": "ignore"}


class GraphEdgeResponse(BaseModel):
    id: str
    source: str
    target: str
    weight: float
    polarity: int = 1
    label: str = ""
    label_ar: str = ""
    transmission: Optional[float] = None

    model_config = {"extra": "ignore"}


class GraphNodesListResponse(BaseModel):
    nodes: list[GraphNodeResponse]
    total: int


class GraphEdgesListResponse(BaseModel):
    edges: list[GraphEdgeResponse]
    total: int


class SubgraphResponse(BaseModel):
    center: str
    depth: int
    nodes: list[GraphNodeResponse]
    edges: list[GraphEdgeResponse]


class ScenarioImpactResponse(BaseModel):
    scenario_id: str
    scenario_label: str = ""
    shock_vector: list[dict]
    impacted_nodes: list[GraphNodeResponse]
    total_estimated_loss_usd: float
