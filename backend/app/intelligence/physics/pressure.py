"""
Pressure accumulation at network nodes.

Physics metaphor: Pressure at a node represents load stress (like fluid pressure).
Current pressure = current_load / base_capacity. When routes are disrupted,
flow reroutes to alternative paths, increasing pressure there. System pressure
is a weighted aggregate of node pressures.

GCC Physics Model:
Temporal pressure dynamics follow the exact formula:
    C_i(t+1) = rho*C_i(t) + kappa*Inflow_i(t) - omega*Outflow_i(t) + xi*Shock_i(t)

where:
    rho = 0.72 (persistence factor - previous pressure memory)
    kappa = 0.18 (inflow coupling - incoming flow drives pressure)
    omega = 0.14 (outflow damping - outflow relieves pressure)
    xi = 0.30 (shock coupling - external disruptions increase pressure)

This implementation uses GCC defaults for all parameters.
"""

from dataclasses import dataclass, field
from typing import List, Dict
import numpy as np
from .gcc_physics_config import (
    PRESSURE_PERSISTENCE_FACTOR,
    PRESSURE_INFLOW_COUPLING,
    PRESSURE_OUTFLOW_DAMPING,
    PRESSURE_SHOCK_COUPLING,
    PRESSURE_INFLOW_BASELINE,
    PRESSURE_REROUTE_INEFFICIENCY,
)


@dataclass
class PressureNode:
    """
    A network node (airport, port, corridor, etc.) with capacity and load.
    
    Attributes:
        node_id: Unique identifier
        node_type: Category ('airport', 'port', 'corridor', 'waypoint', etc.)
        base_capacity: Maximum sustainable load [0, inf)
        current_load: Current load on node [0, inf)
    """
    node_id: str
    node_type: str
    base_capacity: float
    current_load: float = 0.0

    def __post_init__(self):
        """Validate non-negative values."""
        if self.base_capacity < 0:
            raise ValueError(f"base_capacity must be non-negative, got {self.base_capacity}")
        if self.current_load < 0:
            raise ValueError(f"current_load must be non-negative, got {self.current_load}")


def compute_pressure(node: PressureNode) -> float:
    """
    Compute pressure at a single node.
    
    Physics model: pressure = current_load / base_capacity, clamped to avoid
    undefined behavior when capacity is zero.
    
    A pressure of 1.0 means the node is at rated capacity.
    A pressure > 1.0 means the node is congested.
    
    Args:
        node: PressureNode instance
        
    Returns:
        Pressure value [0, inf), typically 0-2 in normal operation
    """
    if node.base_capacity == 0:
        # If capacity is zero, any load creates infinite pressure
        return float('inf') if node.current_load > 0 else 0.0

    pressure = node.current_load / node.base_capacity
    return float(pressure)


def accumulate_pressure_dynamics(
    current_pressure: float,
    inflow: float,
    outflow: float,
    shock_intensity: float = 0.0,
    rho: float = None,
    kappa: float = None,
    omega: float = None,
    xi: float = None
) -> float:
    """
    Compute next pressure state using GCC temporal dynamics formula.
    
    Exact formula: C_i(t+1) = rho*C_i(t) + kappa*Inflow_i(t) - omega*Outflow_i(t) + xi*Shock_i(t)
    
    Args:
        current_pressure: Current pressure state C_i(t)
        inflow: Incoming flow volume Inflow_i(t) [0, 1]
        outflow: Outgoing flow volume Outflow_i(t) [0, 1]
        shock_intensity: External shock contribution Shock_i(t) [0, 1]
        rho: Persistence factor [default: GCC 0.72]
        kappa: Inflow coupling [default: GCC 0.18]
        omega: Outflow damping [default: GCC 0.14]
        xi: Shock coupling [default: GCC 0.30]
        
    Returns:
        Next pressure state C_i(t+1), clamped to [0, 1]
    """
    # Use GCC defaults if not provided
    if rho is None:
        rho = PRESSURE_PERSISTENCE_FACTOR
    if kappa is None:
        kappa = PRESSURE_INFLOW_COUPLING
    if omega is None:
        omega = PRESSURE_OUTFLOW_DAMPING
    if xi is None:
        xi = PRESSURE_SHOCK_COUPLING
    
    # Validate inputs
    if not (0 <= inflow <= 1):
        raise ValueError(f"inflow must be in [0, 1], got {inflow}")
    if not (0 <= outflow <= 1):
        raise ValueError(f"outflow must be in [0, 1], got {outflow}")
    if not (0 <= shock_intensity <= 1):
        raise ValueError(f"shock_intensity must be in [0, 1], got {shock_intensity}")
    
    # Apply exact GCC formula
    next_pressure = (
        rho * current_pressure
        + kappa * inflow
        - omega * outflow
        + xi * shock_intensity
    )
    
    # Clamp to [0, 1] for interpretability
    return float(np.clip(next_pressure, 0.0, 1.0))


def accumulate_pressure(
    nodes: List[PressureNode],
    disrupted_routes: List[str],
    reroute_factor: float = None
) -> Dict[str, float]:
    """
    Redistribute load when routes are disrupted.
    
    Physics model: When a route is disrupted, its load must reroute through
    alternative paths. This model assumes:
    1. Load from disrupted routes is redistributed evenly to remaining routes
    2. A reroute_factor > 1 models inefficiency (longer paths, extra hops)
    3. Pressure increases at nodes handling rerouted traffic
    
    Args:
        nodes: List of PressureNode instances
        disrupted_routes: IDs of disrupted routes (affects load redistribution)
        reroute_factor: Multiplier for rerouted load [default: GCC 1.3 = 30% increase]
        
    Returns:
        Dictionary mapping node_id -> adjusted pressure value
    """
    if reroute_factor is None:
        reroute_factor = PRESSURE_REROUTE_INEFFICIENCY
    
    # Create mutable copies of node loads
    adjusted_loads = {node.node_id: node.current_load for node in nodes}

    # Estimate load on disrupted routes
    # Use GCC baseline inflow for each disrupted route
    disrupted_load = len(disrupted_routes) * PRESSURE_INFLOW_BASELINE

    if disrupted_load > 0 and len(nodes) > 0:
        # Redistribute to remaining nodes with inefficiency factor
        per_node_increase = (disrupted_load * reroute_factor) / len(nodes)
        for node_id in adjusted_loads:
            adjusted_loads[node_id] += per_node_increase

    # Compute pressures with adjusted loads
    pressures = {}
    for node in nodes:
        adjusted_node = PressureNode(
            node.node_id,
            node.node_type,
            node.base_capacity,
            adjusted_loads[node.node_id]
        )
        pressures[node.node_id] = compute_pressure(adjusted_node)

    return pressures


def system_pressure(
    pressures: Dict[str, float],
    weights: Dict[str, float] = None
) -> float:
    """
    Compute aggregate system pressure.
    
    Physics model: System stress is a weighted sum of node pressures.
    Optionally applies weights to prioritize critical nodes.
    
    Args:
        pressures: Dictionary mapping node_id -> pressure value
        weights: Optional dictionary mapping node_id -> weight [0, 1]
                If None, all nodes weighted equally (1.0)
                
    Returns:
        Aggregate system pressure [0, inf), clamped to max 1.0 for interpretation
    """
    if not pressures:
        return 0.0

    if weights is None:
        weights = {node_id: 1.0 for node_id in pressures}

    # Compute weighted average, handling missing weights (default to 1.0)
    total_weight = 0.0
    weighted_pressure = 0.0

    for node_id, pressure in pressures.items():
        weight = weights.get(node_id, 1.0)
        weighted_pressure += pressure * weight
        total_weight += weight

    if total_weight == 0:
        return 0.0

    system_p = weighted_pressure / total_weight

    # Clamp to [0, 1] for interpretation (though raw value may exceed 1)
    return float(np.clip(system_p, 0.0, 1.0))
