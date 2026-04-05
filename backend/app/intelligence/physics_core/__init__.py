"""Physics core intelligence module — threat fields, flow fields, friction, pressure, shockwaves, routing, capacity, bottleneck, recovery."""

from .threat_field import compute_threat_field
from .flow_field import compute_flow_field
from .friction import compute_friction
from .pressure import compute_system_pressure
from .shockwave import compute_shockwave, compute_shockwave_field, haversine
from .potential_routing import dijkstra, find_alternative_routes
from .system_stress import compute_system_stress
from .capacity import compute_node_utilization
from .bottleneck import detect_bottlenecks
from .flow_conservation import validate_flow_conservation
from .recovery import compute_recovery_curve, compute_recovery_score

__all__ = [
    "compute_threat_field",
    "compute_flow_field",
    "compute_friction",
    "compute_system_pressure",
    "compute_shockwave",
    "compute_shockwave_field",
    "haversine",
    "dijkstra",
    "find_alternative_routes",
    "compute_system_stress",
    "compute_node_utilization",
    "detect_bottlenecks",
    "validate_flow_conservation",
    "compute_recovery_curve",
    "compute_recovery_score",
]
