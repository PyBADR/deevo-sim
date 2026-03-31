"""
Network centrality scoring for GCC risk assessment.

Implements network centrality:
N_i(t) = alpha1*Betweenness + alpha2*Degree + alpha3*FlowShare + alpha4*ChokepointDependency
"""

from dataclasses import dataclass
from typing import Dict
import numpy as np

from .gcc_weights import CENTRALITY_WEIGHTS


@dataclass
class CentralityMetrics:
    """Container for network centrality metrics."""

    betweenness: float  # Betweenness centrality [0, 1]
    degree: float  # Degree centrality [0, 1]
    flow_share: float  # Flow share / betweenness flow [0, 1]
    chokepoint_dependency: float  # Chokepoint dependency [0, 1]


def compute_network_centrality(
    metrics: CentralityMetrics,
    weights: Dict[str, float] = None,
) -> float:
    """
    Compute network centrality score from component metrics.

    Implements:
    N_i(t) = alpha1*Betweenness + alpha2*Degree + alpha3*FlowShare + alpha4*ChokepointDependency

    Args:
        metrics: CentralityMetrics object with component values
        weights: Custom weight dictionary. Defaults to CENTRALITY_WEIGHTS if None.

    Returns:
        Network centrality score in [0, 1]
    """
    if weights is None:
        weights = CENTRALITY_WEIGHTS.copy()

    # Validate weights sum to 1.0
    weight_sum = sum(weights.values())
    if not np.isclose(weight_sum, 1.0, rtol=1e-6):
        raise ValueError(f"Weights must sum to 1.0, got {weight_sum}")

    # Validate input metrics are in [0, 1]
    betweenness = np.clip(metrics.betweenness, 0.0, 1.0)
    degree = np.clip(metrics.degree, 0.0, 1.0)
    flow_share = np.clip(metrics.flow_share, 0.0, 1.0)
    chokepoint_dep = np.clip(metrics.chokepoint_dependency, 0.0, 1.0)

    # Compute weighted sum
    centrality = (
        weights["betweenness"] * betweenness
        + weights["degree"] * degree
        + weights["flow_share"] * flow_share
        + weights["chokepoint_dep"] * chokepoint_dep
    )

    return float(np.clip(centrality, 0.0, 1.0))


def normalize_centrality_metric(
    value: float,
    metric_max: float,
) -> float:
    """
    Normalize centrality metric to [0, 1] range.

    Args:
        value: Raw metric value
        metric_max: Maximum observed value in network

    Returns:
        Normalized value in [0, 1]
    """
    if metric_max <= 0:
        return 0.0

    normalized = value / metric_max
    return float(np.clip(normalized, 0.0, 1.0))


def compute_betweenness_centrality(
    edge_count_on_path: int,
    total_edges: int,
) -> float:
    """
    Compute normalized betweenness centrality.

    Betweenness = (number of shortest paths through node) / (all shortest paths).

    Args:
        edge_count_on_path: Number of shortest paths through this node
        total_edges: Total shortest paths in network

    Returns:
        Betweenness centrality in [0, 1]
    """
    if total_edges <= 0:
        return 0.0

    betweenness = edge_count_on_path / total_edges
    return float(np.clip(betweenness, 0.0, 1.0))


def compute_degree_centrality(
    connected_neighbors: int,
    total_nodes: int,
) -> float:
    """
    Compute normalized degree centrality.

    Degree = (number of neighbors) / (total possible neighbors).

    Args:
        connected_neighbors: Number of directly connected neighbors
        total_nodes: Total nodes in network

    Returns:
        Degree centrality in [0, 1]
    """
    if total_nodes <= 1:
        return 0.0

    degree = connected_neighbors / (total_nodes - 1)
    return float(np.clip(degree, 0.0, 1.0))


def compute_flow_share(
    flow_through_node: float,
    total_flow: float,
) -> float:
    """
    Compute flow share / betweenness flow.

    Flow share = (flow through this node) / (total network flow).

    Args:
        flow_through_node: Flow/traffic through this node
        total_flow: Total flow in network

    Returns:
        Flow share in [0, 1]
    """
    if total_flow <= 0:
        return 0.0

    share = flow_through_node / total_flow
    return float(np.clip(share, 0.0, 1.0))


def compute_chokepoint_dependency(
    alternative_routes: int,
    baseline_routes: int,
) -> float:
    """
    Compute chokepoint dependency (inverse of route redundancy).

    Chokepoint dependency = 1 - (alternative routes / baseline routes).

    Args:
        alternative_routes: Number of alternative routes if this node fails
        baseline_routes: Number of baseline routes through this node

    Returns:
        Chokepoint dependency in [0, 1]
    """
    if baseline_routes <= 0:
        return 0.0

    redundancy = alternative_routes / baseline_routes
    dependency = 1.0 - np.clip(redundancy, 0.0, 1.0)

    return float(dependency)
