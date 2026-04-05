"""
Impact Observatory | مرصد الأثر — Graph Snapshot Builder

Stage 8: Apply signal/scenario shocks to the entity graph and produce
a GraphSnapshot representing the post-shock state of all 76 nodes.

Loss estimation formula (simplified):
    loss_usd = stress × weight × BASE_VALUE_PER_UNIT

Stress classification thresholds:
    CRITICAL  ≥ 0.80
    ELEVATED  ≥ 0.60
    MODERATE  ≥ 0.40
    LOW       ≥ 0.20
    NOMINAL   < 0.20
"""

from app.domain.models.graph_snapshot import GraphSnapshot, ImpactedNode, ActivatedEdge
from .registry import NODES, EDGES, get_node, _ensure_indexes
from .bridge import apply_scenario_shocks
from .traversal import get_impacted_nodes


# Base value: $1B per unit weight. A node with weight 0.95 represents ~$950M exposure.
BASE_VALUE_PER_UNIT: float = 1_000_000_000.0


def classify_stress(stress: float) -> str:
    """Map stress level to Classification enum string."""
    if stress >= 0.80:
        return "CRITICAL"
    if stress >= 0.60:
        return "ELEVATED"
    if stress >= 0.40:
        return "MODERATE"
    if stress >= 0.20:
        return "LOW"
    return "NOMINAL"


def build_graph_snapshot(
    scenario_id: str | None = None,
    severity: float = 0.7,
    shock_vector: list[dict] | None = None,
) -> GraphSnapshot:
    """Build a GraphSnapshot from either a scenario ID or a direct shock vector.

    Parameters
    ----------
    scenario_id : str | None
        One of the 8 canonical scenario IDs registered in
        backend/app/governance/registry.py
        (e.g. "hormuz_chokepoint_disruption").
    severity : float
        Severity multiplier applied to scenario shocks (0.0-1.0).
    shock_vector : list[dict] | None
        Direct shock vector [{node_id, impact}]. Overrides scenario_id if provided.

    Returns
    -------
    GraphSnapshot
        Full graph state with stress levels, losses, and activated edges.
    """
    _ensure_indexes()

    # Determine shock vector
    if shock_vector:
        shocks = shock_vector
    elif scenario_id:
        shock_map = apply_scenario_shocks(scenario_id, severity)
        shocks = [{"node_id": nid, "impact": imp} for nid, imp in shock_map.items()]
    else:
        shocks = []

    # BFS propagate impacts through graph edges
    impacted = get_impacted_nodes(shocks, max_depth=3)
    impact_map = {n["node_id"]: n["impact"] for n in impacted}

    # Build full node list (all 76 nodes, stress set for impacted ones)
    impacted_nodes: list[ImpactedNode] = []
    for node in NODES:
        stress = impact_map.get(node["id"], 0.0)
        loss_usd = stress * node["weight"] * BASE_VALUE_PER_UNIT
        impacted_nodes.append(ImpactedNode(
            node_id=node["id"],
            label=node["label"],
            label_ar=node.get("label_ar", ""),
            layer=node["layer"],
            node_type=node.get("type", "Topic"),
            lat=node["lat"],
            lng=node["lng"],
            weight=node["weight"],
            sensitivity=node.get("sensitivity", 0.5),
            stress=round(stress, 4),
            loss_usd=round(loss_usd, 2),
            classification=classify_stress(stress),
        ))

    # Build activated edges (edges where source had non-trivial impact)
    activated_edges: list[ActivatedEdge] = []
    for edge in EDGES:
        src_impact = impact_map.get(edge["source"], 0.0)
        if src_impact > 0.01:
            transmission = src_impact * edge["weight"]
            activated_edges.append(ActivatedEdge(
                edge_id=edge["id"],
                source=edge["source"],
                target=edge["target"],
                weight=edge["weight"],
                polarity=edge["polarity"],
                label=edge["label"],
                label_ar=edge.get("label_ar", ""),
                transmission=round(transmission, 4),
            ))

    total_loss = sum(n.loss_usd for n in impacted_nodes if n.stress > 0)
    nodes_impacted = sum(1 for n in impacted_nodes if n.stress > 0)

    return GraphSnapshot(
        impacted_nodes=impacted_nodes,
        activated_edges=activated_edges,
        propagation_depth=3,
        total_nodes_impacted=nodes_impacted,
        total_estimated_loss_usd=round(total_loss, 2),
    )
