"""
Logistics pressure scoring for GCC risk assessment.

Implements logistics pressure:
L_i(t) = beta1*Q(t) + beta2*Delay(t) + beta3*ReRouteCost(t) + beta4*CapacityStress(t)
"""

from dataclasses import dataclass
from typing import Dict
import numpy as np

from .gcc_weights import LOGISTICS_WEIGHTS


@dataclass
class LogisticsMetrics:
    """Container for logistics pressure metrics."""

    queue_depth: float  # Q(t): Queue depth [0, 1]
    delay_hours: float  # Delay(t): Delay in hours [0, 1]
    reroute_cost_factor: float  # ReRouteCost(t): Extra cost ratio [0, 1]
    capacity_stress: float  # CapacityStress(t): Utilization stress [0, 1]


def compute_logistics_pressure(
    metrics: LogisticsMetrics,
    weights: Dict[str, float] = None,
) -> float:
    """
    Compute logistics pressure score from component metrics.

    Implements:
    L_i(t) = beta1*Q(t) + beta2*Delay(t) + beta3*ReRouteCost(t) + beta4*CapacityStress(t)

    Args:
        metrics: LogisticsMetrics object with component values
        weights: Custom weight dictionary. Defaults to LOGISTICS_WEIGHTS if None.

    Returns:
        Logistics pressure score in [0, 1]
    """
    if weights is None:
        weights = LOGISTICS_WEIGHTS.copy()

    # Validate weights sum to 1.0
    weight_sum = sum(weights.values())
    if not np.isclose(weight_sum, 1.0, rtol=1e-6):
        raise ValueError(f"Weights must sum to 1.0, got {weight_sum}")

    # Validate input metrics are in [0, 1]
    queue = np.clip(metrics.queue_depth, 0.0, 1.0)
    delay = np.clip(metrics.delay_hours, 0.0, 1.0)
    reroute = np.clip(metrics.reroute_cost_factor, 0.0, 1.0)
    capacity = np.clip(metrics.capacity_stress, 0.0, 1.0)

    # Compute weighted sum
    pressure = (
        weights["queue"] * queue
        + weights["delay"] * delay
        + weights["reroute_cost"] * reroute
        + weights["capacity_stress"] * capacity
    )

    return float(np.clip(pressure, 0.0, 1.0))


def normalize_queue_depth(
    current_queue: int,
    max_queue: int,
) -> float:
    """
    Normalize queue depth to [0, 1] range.

    Q(t) = min(current_queue / max_queue, 1.0)

    Args:
        current_queue: Current number of items in queue
        max_queue: Maximum queue capacity

    Returns:
        Normalized queue depth in [0, 1]
    """
    if max_queue <= 0:
        return 0.0

    queue_ratio = current_queue / max_queue
    return float(np.clip(queue_ratio, 0.0, 1.0))


def normalize_delay(
    delay_hours: float,
    baseline_hours: float = 24.0,
) -> float:
    """
    Normalize delay in hours to [0, 1] range.

    Delay(t) = min(delay_hours / baseline_hours, 1.0)

    Args:
        delay_hours: Current delay in hours
        baseline_hours: Baseline delay for normalization (default 24 hours)

    Returns:
        Normalized delay in [0, 1]
    """
    if baseline_hours <= 0:
        return 0.0

    delay_ratio = delay_hours / baseline_hours
    return float(np.clip(delay_ratio, 0.0, 1.0))


def compute_reroute_cost_factor(
    baseline_cost: float,
    current_cost: float,
) -> float:
    """
    Compute cost factor for rerouting.

    ReRouteCost(t) = (current_cost - baseline_cost) / baseline_cost

    Args:
        baseline_cost: Baseline route cost
        current_cost: Current rerouted cost

    Returns:
        Reroute cost factor in [0, 1]
    """
    if baseline_cost <= 0:
        return 0.0

    cost_increase = (current_cost - baseline_cost) / baseline_cost
    return float(np.clip(cost_increase, 0.0, 1.0))


def compute_capacity_stress(
    current_utilization: float,
    capacity_utilization_threshold: float = 0.85,
) -> float:
    """
    Compute capacity stress based on utilization.

    CapacityStress(t) = max(0, (current_utilization - threshold) / (1 - threshold))

    Args:
        current_utilization: Current capacity utilization [0, 1]
        capacity_utilization_threshold: Stress threshold (default 0.85)

    Returns:
        Capacity stress in [0, 1]
    """
    current_utilization = np.clip(current_utilization, 0.0, 1.0)

    if current_utilization <= capacity_utilization_threshold:
        return 0.0

    stress_numerator = current_utilization - capacity_utilization_threshold
    stress_denominator = 1.0 - capacity_utilization_threshold

    if stress_denominator <= 0:
        return 0.0

    stress = stress_numerator / stress_denominator
    return float(np.clip(stress, 0.0, 1.0))
