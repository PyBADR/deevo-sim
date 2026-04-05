"""
Impact Observatory | مرصد الأثر — Bottleneck Detection (v4 §L3)
Identifies constrained nodes where utilization exceeds capacity threshold.

Formula: B_i = utilization_i / threshold
Bottleneck when utilization > threshold (default 0.85 = 85% capacity).
"""

from typing import Dict, List, Any

# Default: entity is bottleneck at 85%+ utilization
BOTTLENECK_THRESHOLD = 0.85


def detect_bottlenecks(
    utilization_map: Dict[str, Dict[str, float]],
    entities: List[Any],
    threshold: float = BOTTLENECK_THRESHOLD,
) -> Dict[str, Any]:
    """
    Detect bottleneck nodes from utilization data.

    Returns:
        {
            "bottleneck_nodes": [{entity_id, name, utilization, bottleneck_score, severity}],
            "congestion_score": float (0-1 system-wide),
            "bottleneck_count": int,
        }
    """
    entity_map = {e.entity_id: e for e in entities if e.active}
    bottleneck_nodes: List[Dict[str, Any]] = []
    total_util = 0.0
    count = 0

    for entity_id, util_data in utilization_map.items():
        utilization = util_data["utilization"]
        total_util += min(utilization, 2.0)
        count += 1

        if utilization >= threshold:
            entity = entity_map.get(entity_id)
            name = entity.name if entity else entity_id
            # Bottleneck score: how far over threshold (normalized 0-1)
            bottleneck_score = min(1.0, (utilization - threshold) / (1.0 - threshold + 1e-9))
            severity = (
                "critical" if utilization >= 1.5
                else "high" if utilization >= 1.2
                else "elevated" if utilization >= 1.0
                else "moderate"
            )
            bottleneck_nodes.append({
                "entity_id": entity_id,
                "name": name,
                "utilization": round(utilization, 4),
                "bottleneck_score": round(bottleneck_score, 4),
                "severity": severity,
            })

    # Sort by bottleneck severity
    bottleneck_nodes.sort(key=lambda x: x["utilization"], reverse=True)

    # System-wide congestion score: average utilization normalized to 0-1
    congestion_score = min(1.0, (total_util / max(count, 1)) / 1.5)

    return {
        "bottleneck_nodes": bottleneck_nodes,
        "congestion_score": round(congestion_score, 4),
        "bottleneck_count": len(bottleneck_nodes),
    }
