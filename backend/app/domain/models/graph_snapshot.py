"""
Impact Observatory | مرصد الأثر — Graph Snapshot Models

Data contracts for Stage 8: Entity Graph with applied shocks.
Represents the graph state at a point in the simulation.
"""

from pydantic import Field
from .base import VersionedModel


class ImpactedNode(VersionedModel):
    """A graph node with its post-shock stress and loss values."""
    node_id: str
    label: str
    label_ar: str = ""
    layer: str = Field(..., description="geography | infrastructure | economy | finance | society")
    node_type: str = Field(default="Topic", description="Region | Organization | Ministry | Topic | Event | Person | Platform")
    lat: float = 0.0
    lng: float = 0.0
    weight: float = Field(default=0.5, ge=0.0, le=1.0)
    sensitivity: float = Field(default=0.5, ge=0.0, le=1.0)
    stress: float = Field(default=0.0, ge=0.0, le=1.0, description="Post-shock stress level")
    loss_usd: float = Field(default=0.0, ge=0.0, description="Estimated loss in USD")
    classification: str = Field(default="NOMINAL", description="NOMINAL | LOW | MODERATE | ELEVATED | CRITICAL")


class ActivatedEdge(VersionedModel):
    """A graph edge that transmitted impact during propagation."""
    edge_id: str
    source: str
    target: str
    weight: float = Field(default=0.5, ge=0.0, le=1.0)
    polarity: int = Field(default=1, description="1 = positive correlation, -1 = inverse")
    label: str = ""
    label_ar: str = ""
    transmission: float = Field(default=0.0, ge=0.0, le=1.0, description="Actual transmitted impact fraction")


class GraphSnapshot(VersionedModel):
    """Stage 8 output: full graph state after shock application."""
    impacted_nodes: list[ImpactedNode] = Field(default_factory=list)
    activated_edges: list[ActivatedEdge] = Field(default_factory=list)
    propagation_depth: int = Field(default=0, ge=0)
    total_nodes_impacted: int = Field(default=0, ge=0)
    total_estimated_loss_usd: float = Field(default=0.0, ge=0.0)
