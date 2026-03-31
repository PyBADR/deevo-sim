"""
Behavior functions for Mesa agents in GCC infrastructure simulation.

Implements discrete behavior modules that compute state transitions,
risk propagation, flow dynamics, and recovery mechanics.
"""

from typing import Dict, List, Tuple, Optional
import math
import numpy as np

from app.intelligence.math_core.state_vector import compute_state_vector
from app.intelligence.physics.system_stress import compute_system_stress


def compute_infrastructure_risk_update(
    current_risk_score: float,
    shock_severity: float,
    recovery_progress: float,
    network_pressure: float,
    criticality: float,
    exposure: float,
) -> float:
    """
    Compute updated risk score for infrastructure node based on local and network state.

    Incorporates shock severity, recovery progress, network effects, and node
    intrinsic properties to produce continuous risk trajectory.

    Args:
        current_risk_score: [0,1] existing risk score
        shock_severity: [0,1] direct shock severity at this node
        recovery_progress: [0,1] progress toward baseline (0=baseline, 1=fully recovered)
        network_pressure: [0,1] aggregated pressure from network
        criticality: [0,1] node criticality score
        exposure: [0,1] node exposure to disruption

    Returns:
        Updated risk score [0,1]
    """
    # Components: direct shock impact, network effects, recovery dynamics
    shock_component = shock_severity * exposure * (1.0 - recovery_progress * 0.5)
    network_component = network_pressure * criticality * 0.4
    resilience_factor = max(0.5, 1.0 - recovery_progress)

    # Weighted combination with temporal decay
    updated_risk = (
        shock_component * 0.5 + network_component * 0.3 + current_risk_score * 0.2
    ) * resilience_factor

    # Clamp to valid range
    return max(0.0, min(1.0, updated_risk))


def compute_event_decay(
    initial_severity: float,
    event_age_steps: int,
    duration_steps: int,
    decay_rate: float = 0.15,
) -> float:
    """
    Compute event severity after decay based on age and duration.

    Uses exponential decay with configurable rate. Events decline in impact
    over time until they effectively disappear.

    Args:
        initial_severity: [0,1] severity when event was created
        event_age_steps: Number of simulation steps elapsed
        duration_steps: Expected duration before decay becomes significant
        decay_rate: [0,1] exponential decay rate per step

    Returns:
        Decayed severity [0,1]
    """
    # Exponential decay with time constant
    decay_factor = math.exp(-decay_rate * event_age_steps / max(1, duration_steps))
    current_severity = initial_severity * decay_factor

    return max(0.0, min(1.0, current_severity))


def compute_flow_congestion(
    base_flow_volume: float,
    infrastructure_disruption_scores: List[float],
    network_saturation: float = 0.0,
) -> float:
    """
    Compute congestion level for a flow based on route disruption and network load.

    Aggregates disruption along the flow's path and combines with network-wide
    saturation to estimate congestion impacts.

    Args:
        base_flow_volume: [0,1] normalized flow volume
        infrastructure_disruption_scores: List of [0,1] disruption levels on route
        network_saturation: [0,1] global network saturation level

    Returns:
        Congestion level [0,1]
    """
    if not infrastructure_disruption_scores:
        return min(1.0, network_saturation)

    # Average disruption along route as primary congestion driver
    route_disruption = float(np.mean(infrastructure_disruption_scores))

    # Network saturation amplifies congestion nonlinearly
    saturation_multiplier = 1.0 + network_saturation * 0.5

    # Flow volume increases congestion impact
    volume_factor = 1.0 + base_flow_volume * 0.3

    # Combined congestion metric
    congestion = (
        route_disruption * saturation_multiplier * volume_factor
    ) / volume_factor

    return max(0.0, min(1.0, congestion))


def compute_reroute_decision(
    current_congestion: float,
    alternative_route_congestion: Optional[float] = None,
    cost_of_reroute: float = 0.1,
    congestion_threshold: float = 0.6,
) -> Tuple[bool, float]:
    """
    Determine whether a flow should reroute and quantify reroute benefit.

    Uses threshold-based decision with cost-benefit analysis. Rerouting is
    preferred when congestion exceeds threshold and alternatives exist.

    Args:
        current_congestion: [0,1] current route congestion level
        alternative_route_congestion: [0,1] congestion on best alternative
        cost_of_reroute: [0,1] cost/delay penalty for rerouting (0=free, 1=prohibitive)
        congestion_threshold: [0,1] threshold above which rerouting is considered

    Returns:
        Tuple of (should_reroute: bool, benefit_score: float [0,1])
    """
    # Only consider rerouting if current congestion exceeds threshold
    if current_congestion < congestion_threshold:
        return (False, 0.0)

    # If no alternative exists, cannot reroute
    if alternative_route_congestion is None:
        return (False, 0.0)

    # Compute benefit: reduction in congestion minus reroute cost
    congestion_benefit = max(0.0, current_congestion - alternative_route_congestion)
    net_benefit = congestion_benefit - cost_of_reroute

    # Reroute if net benefit is positive
    should_reroute = net_benefit > 0.0
    benefit_score = max(0.0, net_benefit)

    return (should_reroute, benefit_score)


def compute_recovery(
    current_disruption_level: float,
    recovery_rate: float = 0.05,
    recovery_capacity: float = 0.9,
) -> Tuple[float, float]:
    """
    Compute infrastructure recovery trajectory.

    Models recovery as progressive movement toward baseline resilience with
    capacity constraints and diminishing returns at high recovery levels.

    Args:
        current_disruption_level: [0,1] current disruption level
        recovery_rate: [0,1] recovery rate per time step
        recovery_capacity: [0,1] maximum achievable recovery level

    Returns:
        Tuple of (new_disruption_level, recovery_progress) both [0,1]
    """
    # Recovery progress is inverse of disruption
    current_recovery = 1.0 - current_disruption_level

    # Apply recovery with capacity constraint and diminishing returns
    # Near capacity, recovery slows exponentially
    capacity_gap = max(0.0, recovery_capacity - current_recovery)
    effective_recovery_rate = recovery_rate * (capacity_gap / recovery_capacity)

    # New recovery progress
    new_recovery = current_recovery + effective_recovery_rate
    new_recovery = min(recovery_capacity, new_recovery)

    # Clamp recovery progress to [0, recovery_capacity]
    recovery_progress = new_recovery / recovery_capacity

    # New disruption is inverse of recovery
    new_disruption = 1.0 - new_recovery

    return (
        max(0.0, min(1.0, new_disruption)),
        max(0.0, min(1.0, recovery_progress)),
    )
