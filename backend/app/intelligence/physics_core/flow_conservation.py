"""
Impact Observatory | مرصد الأثر — Flow Conservation Validation (v4 §L4)
Validates that entity graph respects flow conservation law.

Formula: |Σ inflow_i - Σ outflow_i| ≤ tolerance × max(Σ inflow_i, Σ outflow_i)
Violations indicate graph integrity issues.
"""

from typing import Dict, List, Any

DEFAULT_TOLERANCE = 0.15  # 15% imbalance tolerance


def validate_flow_conservation(
    entities: List[Any],
    edges: List[Any],
    tolerance: float = DEFAULT_TOLERANCE,
) -> Dict[str, Any]:
    """
    Validate flow conservation across the entity graph.

    Returns:
        {
            "valid": bool,
            "violations": [{entity_id, name, inflow, outflow, imbalance_ratio}],
            "total_inflow": float,
            "total_outflow": float,
            "system_balance_ratio": float,
        }
    """
    # Compute inflow/outflow per entity from edge exposures
    inflow: Dict[str, float] = {}
    outflow: Dict[str, float] = {}

    for edge in edges:
        if not edge.active:
            continue
        src = edge.source_entity_id
        tgt = edge.target_entity_id
        exp = edge.exposure

        outflow[src] = outflow.get(src, 0.0) + exp
        inflow[tgt] = inflow.get(tgt, 0.0) + exp

    violations: List[Dict[str, Any]] = []
    total_in = sum(inflow.values())
    total_out = sum(outflow.values())

    for entity in entities:
        if not entity.active:
            continue
        eid = entity.entity_id
        e_in = inflow.get(eid, 0.0)
        e_out = outflow.get(eid, 0.0)
        denominator = max(e_in, e_out, 1e-9)
        imbalance = abs(e_in - e_out) / denominator

        if imbalance > tolerance and (e_in + e_out) > 0:
            violations.append({
                "entity_id": eid,
                "name": entity.name,
                "inflow": round(e_in, 2),
                "outflow": round(e_out, 2),
                "imbalance_ratio": round(imbalance, 4),
            })

    # System-wide balance
    system_denom = max(total_in, total_out, 1e-9)
    system_balance = 1.0 - abs(total_in - total_out) / system_denom

    return {
        "valid": len(violations) == 0,
        "violations": violations,
        "violation_count": len(violations),
        "total_inflow": round(total_in, 2),
        "total_outflow": round(total_out, 2),
        "system_balance_ratio": round(system_balance, 4),
    }
