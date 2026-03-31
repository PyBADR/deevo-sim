"""
Scenario delta scoring for GCC risk assessment.

Computes deltas between baseline state and post-shock scenarios.
Delta = abs(post_shock_value - baseline_value) / baseline_value (if baseline > 0)
"""

from dataclasses import dataclass
from typing import List, Dict
import numpy as np


@dataclass
class ScenarioState:
    """Represents system state at a point in time."""

    geopolitical_threat: float  # G_i(t)
    disruption_score: float  # D_i(t)
    logistics_pressure: float  # L_i(t)
    network_centrality: float  # N_i(t)
    uncertainty: float  # U_i(t)
    exposure: float  # E_i(t)
    timestamp: str = ""  # Optional timestamp identifier


@dataclass
class ScenarioDelta:
    """Represents changes from baseline to post-shock scenario."""

    delta_threat: float  # Change in geopolitical threat
    delta_disruption: float  # Change in disruption
    delta_logistics: float  # Change in logistics pressure
    delta_centrality: float  # Change in network centrality
    delta_uncertainty: float  # Change in uncertainty
    delta_exposure: float  # Change in exposure
    total_impact: float  # Overall impact magnitude


def compute_relative_delta(
    baseline_value: float,
    post_shock_value: float,
    epsilon: float = 1e-6,
) -> float:
    """
    Compute relative change between baseline and post-shock values.

    Delta = (post_shock - baseline) / baseline

    Args:
        baseline_value: Value in baseline scenario
        post_shock_value: Value in post-shock scenario
        epsilon: Small value to prevent division by zero (default 1e-6)

    Returns:
        Relative delta as float (can be negative or positive)
    """
    denominator = max(abs(baseline_value), epsilon)
    delta = (post_shock_value - baseline_value) / denominator

    return float(delta)


def compute_absolute_delta(
    baseline_value: float,
    post_shock_value: float,
) -> float:
    """
    Compute absolute change between baseline and post-shock values.

    AbsDelta = abs(post_shock - baseline)

    Args:
        baseline_value: Value in baseline scenario
        post_shock_value: Value in post-shock scenario

    Returns:
        Absolute delta as float (always non-negative)
    """
    delta = abs(post_shock_value - baseline_value)
    return float(delta)


def compute_scenario_delta(
    baseline: ScenarioState,
    post_shock: ScenarioState,
    use_relative: bool = True,
) -> ScenarioDelta:
    """
    Compute scenario delta across all risk dimensions.

    Args:
        baseline: ScenarioState for baseline scenario
        post_shock: ScenarioState for post-shock scenario
        use_relative: If True use relative change, else absolute change

    Returns:
        ScenarioDelta with all component deltas and total impact
    """
    if use_relative:
        delta_func = compute_relative_delta
    else:
        delta_func = compute_absolute_delta

    # Compute deltas for each component
    delta_threat = delta_func(baseline.geopolitical_threat, post_shock.geopolitical_threat)
    delta_disruption = delta_func(baseline.disruption_score, post_shock.disruption_score)
    delta_logistics = delta_func(baseline.logistics_pressure, post_shock.logistics_pressure)
    delta_centrality = delta_func(baseline.network_centrality, post_shock.network_centrality)
    delta_uncertainty = delta_func(baseline.uncertainty, post_shock.uncertainty)
    delta_exposure = delta_func(baseline.exposure, post_shock.exposure)

    # Compute total impact as RMS of all deltas
    deltas = [
        delta_threat,
        delta_disruption,
        delta_logistics,
        delta_centrality,
        delta_uncertainty,
        delta_exposure,
    ]
    total_impact = float(np.sqrt(np.mean(np.array(deltas) ** 2)))

    return ScenarioDelta(
        delta_threat=float(delta_threat),
        delta_disruption=float(delta_disruption),
        delta_logistics=float(delta_logistics),
        delta_centrality=float(delta_centrality),
        delta_uncertainty=float(delta_uncertainty),
        delta_exposure=float(delta_exposure),
        total_impact=total_impact,
    )


def compute_impact_magnitude(
    delta: ScenarioDelta,
    weights: Dict[str, float] = None,
) -> float:
    """
    Compute weighted impact magnitude from scenario delta.

    Impact = weighted sum of absolute deltas

    Args:
        delta: ScenarioDelta object
        weights: Optional weights for each component. If None, equal weighting.

    Returns:
        Impact magnitude as float [0, inf)
    """
    if weights is None:
        weights = {
            "threat": 0.167,
            "disruption": 0.167,
            "logistics": 0.167,
            "centrality": 0.167,
            "uncertainty": 0.167,
            "exposure": 0.167,
        }

    # Normalize weights to sum to 1.0
    weight_sum = sum(weights.values())
    if weight_sum > 0:
        weights = {k: v / weight_sum for k, v in weights.items()}

    impact = (
        weights.get("threat", 0) * abs(delta.delta_threat)
        + weights.get("disruption", 0) * abs(delta.delta_disruption)
        + weights.get("logistics", 0) * abs(delta.delta_logistics)
        + weights.get("centrality", 0) * abs(delta.delta_centrality)
        + weights.get("uncertainty", 0) * abs(delta.delta_uncertainty)
        + weights.get("exposure", 0) * abs(delta.delta_exposure)
    )

    return float(impact)


def compute_shock_severity(
    baseline: ScenarioState,
    post_shock: ScenarioState,
) -> float:
    """
    Compute overall severity of shock based on combined impact.

    Severity combines magnitude of change with baseline conditions.

    Args:
        baseline: ScenarioState for baseline scenario
        post_shock: ScenarioState for post-shock scenario

    Returns:
        Severity score in [0, 1]
    """
    delta = compute_scenario_delta(baseline, post_shock, use_relative=True)

    # Combine baseline risk level with delta magnitude
    baseline_risk = np.mean([
        baseline.geopolitical_threat,
        baseline.disruption_score,
        baseline.logistics_pressure,
        baseline.network_centrality,
        baseline.uncertainty,
        baseline.exposure,
    ])

    # Severity = baseline risk + impact magnitude, capped at 1.0
    impact = compute_impact_magnitude(delta)
    severity = baseline_risk + min(impact, 1.0 - baseline_risk)

    return float(np.clip(severity, 0.0, 1.0))


def compute_resilience_impact(
    delta: ScenarioDelta,
    recovery_multiplier: float = 1.0,
) -> float:
    """
    Compute impact on system resilience from scenario.

    Resilience impact quantifies how the scenario affects recovery capacity.

    Args:
        delta: ScenarioDelta object
        recovery_multiplier: Multiplier for recovery rate (default 1.0)

    Returns:
        Resilience impact in [0, 1] where 1 = system cannot recover
    """
    # Negative uncertainty delta (more certainty) improves resilience
    # Positive disruption/threat deltas reduce resilience
    resilience_reduction = (
        abs(delta.delta_threat) * 0.25
        + abs(delta.delta_disruption) * 0.25
        + abs(delta.delta_logistics) * 0.15
        + abs(delta.delta_centrality) * 0.15
        + max(0, -delta.delta_uncertainty) * 0.10  # Increased certainty helps
        + abs(delta.delta_exposure) * 0.10
    )

    # Apply recovery multiplier (higher multiplier = better recovery = lower impact)
    resilience_impact = resilience_reduction / max(recovery_multiplier, 1.0)

    return float(np.clip(resilience_impact, 0.0, 1.0))


def compare_scenarios(
    baseline: ScenarioState,
    scenarios: List[ScenarioState],
) -> List[Dict]:
    """
    Compare multiple post-shock scenarios to baseline.

    Args:
        baseline: ScenarioState for baseline scenario
        scenarios: List of ScenarioState objects for alternative scenarios

    Returns:
        List of dictionaries with delta and impact for each scenario
    """
    results = []

    for scenario in scenarios:
        delta = compute_scenario_delta(baseline, scenario)
        impact = compute_impact_magnitude(delta)
        severity = compute_shock_severity(baseline, scenario)

        results.append({
            "scenario_id": scenario.timestamp,
            "delta": delta,
            "impact": impact,
            "severity": severity,
            "total_impact_rms": delta.total_impact,
        })

    return results


def rank_scenarios_by_impact(
    baseline: ScenarioState,
    scenarios: List[ScenarioState],
) -> List[tuple]:
    """
    Rank scenarios by total impact from most to least severe.

    Args:
        baseline: ScenarioState for baseline scenario
        scenarios: List of ScenarioState objects

    Returns:
        List of tuples (scenario_index, impact_score, severity) sorted by impact descending
    """
    comparisons = compare_scenarios(baseline, scenarios)

    rankings = [
        (i, comp["impact"], comp["severity"])
        for i, comp in enumerate(comparisons)
    ]

    # Sort by impact descending
    rankings.sort(key=lambda x: x[1], reverse=True)

    return rankings
