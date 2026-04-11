"""P1 Data Foundation — Logistics Node Profiles.

Ports, airports, free zones, and trade corridors tracked by the observatory.
"""

from __future__ import annotations

from pydantic import Field

from p1_foundation.models.base import ConfidenceMixin, GeoMixin, P1BaseModel, ProvenanceMixin
from p1_foundation.models.enums import Sector


class LogisticsNodeProfile(P1BaseModel, GeoMixin, ConfidenceMixin, ProvenanceMixin):
    """Profile of a logistics infrastructure node."""

    sector: str = Field(default=Sector.LOGISTICS.value, description="Always 'logistics'")
    entity_id: str = Field(..., description="FK to EntityRegistryEntry.id")
    node_name: str = Field(..., description="Facility name")
    node_type: str = Field(..., description="Type: port, airport, free_zone, pipeline, corridor")
    capacity_teu: float | None = Field(default=None, ge=0, description="Container capacity (TEU) for ports")
    throughput_teu: float | None = Field(default=None, ge=0, description="Current throughput (TEU)")
    utilization_pct: float | None = Field(default=None, ge=0, le=100, description="Capacity utilization %")
    cargo_volume_mt: float | None = Field(default=None, ge=0, description="Cargo volume (metric tons)")
    vessel_calls: int | None = Field(default=None, ge=0, description="Vessel calls per period")
    flight_movements: int | None = Field(default=None, ge=0, description="Flight movements per period")
    connected_nodes: list[str] = Field(default_factory=list, description="IDs of connected logistics nodes")
    trade_corridors: list[str] = Field(default_factory=list, description="Trade corridor names")
    disruption_risk_score: float = Field(default=0.0, ge=0.0, le=1.0, description="Disruption risk [0,1]")
    is_operational: bool = Field(default=True, description="Whether node is operational")
    period: str = Field(..., description="Reporting period")
    dataset_id: str | None = Field(default=None, description="FK to DatasetRegistryEntry.id")
