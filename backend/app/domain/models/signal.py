"""
Impact Observatory | مرصد الأثر — Signal Models

Data contracts for Stage 6-7: Clustering → Signal Generation.
"""

from typing import Optional
from pydantic import Field
from .base import VersionedModel


class Signal(VersionedModel):
    """Stage 7 output: scored signal ready for graph/simulation."""
    signal_id: str
    source_events: list[str] = Field(default_factory=list, description="Event IDs that produced this signal")
    signal_type: str = Field(default="disruption", description="disruption | escalation | recovery")
    strength: float = Field(default=0.5, ge=0.0, le=1.0)
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)
    affected_nodes: list[str] = Field(default_factory=list, description="Graph node IDs")
    shock_vector: list[dict] = Field(default_factory=list, description="[{node_id, impact}]")
    cluster_id: Optional[str] = None


class SignalCluster(VersionedModel):
    """Stage 6 output: group of related signals."""
    cluster_id: str
    signals: list[str] = Field(default_factory=list, description="Signal IDs")
    composite_strength: float = Field(default=0.0, ge=0.0, le=1.0)
    theme: str = Field(default="", description="Cluster label")
    affected_nodes: list[str] = Field(default_factory=list, description="Union of all signal node IDs")
