"""
Impact Observatory | مرصد الأثر — Node Capacity & Utilization (v4 §L3)
Deterministic computation of per-node throughput utilization.

Formula: U_i = throughput_i / capacity_i
Where throughput is derived from incoming edge flows under shock.
"""

from typing import Dict, List, Any


def compute_node_utilization(
    entities: List[Any],
    edges: List[Any],
    shock_intensity: float,
) -> Dict[str, Dict[str, float]]:
    """
    Compute capacity utilization per entity under shock conditions.

    Under shock, throughput = sum of incoming edge exposures × (1 - shock × transmission).
    Utilization = throughput / capacity.

    Returns:
        {entity_id: {"capacity": float, "throughput": float, "utilization": float}}
    """
    # Sum incoming edge exposure per entity (weighted by shock reduction)
    incoming_flow: Dict[str, float] = {}
    for edge in edges:
        if not edge.active:
            continue
        target = edge.target_entity_id
        # Under shock, flow reduces by shock × transmission coefficient
        flow = edge.exposure * max(0.0, 1.0 - shock_intensity * edge.transmission_coefficient)
        incoming_flow[target] = incoming_flow.get(target, 0.0) + flow

    results: Dict[str, Dict[str, float]] = {}
    for entity in entities:
        if not entity.active:
            continue
        # Use exposure as implicit capacity when capacity is at default (1.0)
        # This normalizes utilization to ~1.0 under normal load
        cap = entity.capacity if entity.capacity > 1.0 else max(entity.exposure, 1e-9)
        throughput = incoming_flow.get(
            entity.entity_id,
            max(0.0, entity.exposure * (1.0 - min(shock_intensity, 1.0) * 0.3)),
        )
        utilization = min(2.0, throughput / cap)  # >1.0 = overloaded
        results[entity.entity_id] = {
            "capacity": cap,
            "throughput": round(throughput, 4),
            "utilization": round(utilization, 4),
        }
    return results
