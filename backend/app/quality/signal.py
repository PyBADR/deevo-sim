"""
Impact Observatory | مرصد الأثر — Signal Generation (Stage 7)

Converts signal clusters into scored Signals ready for graph/simulation.

Signal scoring formula:
    event_impact = severity × 0.45 + confidence × 0.30 + source_weight × 0.25
    signal_score = event_impact × propagation_multiplier × sector_sensitivity

Where:
    propagation_multiplier = 1.0 + (num_affected_nodes / 76) × 0.5
    sector_sensitivity = mean of affected node sensitivities
"""

import uuid
from app.domain.models.signal import Signal, SignalCluster
from app.graph.registry import get_node


def score_signal(
    severity: float,
    confidence: float,
    source_weight: float,
    num_affected_nodes: int,
    avg_sensitivity: float,
) -> float:
    """Deterministic signal scoring formula.

    event_impact = severity × 0.45 + confidence × 0.30 + source_weight × 0.25
    propagation_multiplier = 1.0 + (num_affected_nodes / 76) × 0.5
    sector_sensitivity = avg_sensitivity (mean of node sensitivities)
    signal_score = event_impact × propagation_multiplier × sector_sensitivity
    """
    event_impact = severity * 0.45 + confidence * 0.30 + source_weight * 0.25
    propagation_multiplier = 1.0 + (num_affected_nodes / 76.0) * 0.5
    signal_score = event_impact * propagation_multiplier * avg_sensitivity
    return round(min(1.0, signal_score), 4)


def generate_signal(cluster: SignalCluster) -> Signal:
    """Convert a SignalCluster into a scored Signal.

    The Signal is the final quality-gate output that enters the
    graph/simulation layers. It carries:
    - Deterministic score (from formula above)
    - Full provenance
    - Shock vector from affected nodes
    """
    # Compute average sensitivity of affected nodes
    sensitivities = []
    for nid in cluster.affected_nodes:
        node = get_node(nid)
        if node:
            sensitivities.append(node.get("sensitivity", 0.5))
    avg_sensitivity = sum(sensitivities) / len(sensitivities) if sensitivities else 0.5

    # Source weight defaults to 1.0 for scenario catalog
    source_weight = 1.0  # Will be overridden by pipeline context if external source

    signal_strength = score_signal(
        severity=cluster.composite_strength,
        confidence=1.0,  # Will be set from enrichment stage
        source_weight=source_weight,
        num_affected_nodes=len(cluster.affected_nodes),
        avg_sensitivity=avg_sensitivity,
    )

    return Signal(
        signal_id=f"sig_{uuid.uuid4().hex[:12]}",
        source_events=cluster.signals,
        signal_type="disruption",
        strength=signal_strength,
        confidence=cluster.composite_strength,
        affected_nodes=cluster.affected_nodes,
        shock_vector=[
            {"node_id": nid, "impact": cluster.composite_strength}
            for nid in cluster.affected_nodes
        ],
        cluster_id=cluster.cluster_id,
    )
