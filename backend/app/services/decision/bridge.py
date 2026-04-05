"""
Impact Observatory | مرصد الأثر — Decision Bridge

Enriches decision actions with graph node metadata (coordinates, labels).
Bridges simulation output → decision engine input.
Does NOT duplicate decision engine logic.
"""

from app.graph.registry import get_node


def enrich_decisions_with_graph(decision_pack: dict) -> dict:
    """Add graph node context to each decision action.

    For each action with a target_node_id, adds:
    - target_label, target_label_ar
    - target_lat, target_lng
    - target_layer
    """
    actions = decision_pack.get("actions", [])
    enriched = []
    for action in actions:
        node_id = action.get("target_node_id")
        if node_id:
            node = get_node(node_id)
            if node:
                action["target_label"] = node["label"]
                action["target_label_ar"] = node.get("label_ar", "")
                action["target_lat"] = node["lat"]
                action["target_lng"] = node["lng"]
                action["target_layer"] = node["layer"]
        enriched.append(action)

    decision_pack["actions"] = enriched
    return decision_pack
