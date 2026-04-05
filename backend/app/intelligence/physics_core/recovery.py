"""
Impact Observatory | مرصد الأثر — Recovery Model (v4 §L3)
Deterministic capacity recovery curve over time horizon.

Formula: R(t) = 1 - e^(-recovery_rate × t)
Where t = days since shock onset, recovery_rate = scenario parameter.

Recovery score = R(horizon_days) weighted by entity criticality.
"""

import math
from typing import Dict, List, Any


def compute_recovery_curve(
    horizon_days: int,
    recovery_rate: float = 0.05,
    shock_intensity: float = 1.0,
) -> List[Dict[str, float]]:
    """
    Compute daily recovery trajectory.

    Returns:
        [{day, recovery_ratio, residual_impact}] for each day in horizon
    """
    curve: List[Dict[str, float]] = []
    for day in range(horizon_days + 1):
        # Recovery follows exponential approach to 1.0
        # Higher shock_intensity slows recovery (reduces effective rate)
        effective_rate = recovery_rate / max(shock_intensity, 0.1)
        recovery_ratio = 1.0 - math.exp(-effective_rate * day)
        residual_impact = 1.0 - recovery_ratio
        curve.append({
            "day": day,
            "recovery_ratio": round(recovery_ratio, 6),
            "residual_impact": round(residual_impact, 6),
        })
    return curve


def compute_recovery_score(
    entities: List[Any],
    propagation_factors: Dict[str, float],
    horizon_days: int,
    recovery_rate: float = 0.05,
    shock_intensity: float = 1.0,
) -> Dict[str, Any]:
    """
    Compute system-wide recovery score at horizon end.

    Recovery score = Σ(criticality_i × R_i(horizon)) / Σ(criticality_i)
    Where R_i = per-entity recovery ratio at horizon.

    Returns:
        {
            "recovery_score": float (0-1, higher = more recovered),
            "avg_residual_impact": float,
            "full_recovery_days_est": int (estimated days to 95% recovery),
            "entity_recovery": [{entity_id, recovery_ratio, residual_impact}]
        }
    """
    effective_rate = recovery_rate / max(shock_intensity, 0.1)
    total_weighted_recovery = 0.0
    total_criticality = 0.0
    entity_recovery: List[Dict[str, Any]] = []

    for entity in entities:
        if not entity.active:
            continue
        # Per-entity recovery: entities with higher propagation impact recover slower
        prop_factor = propagation_factors.get(entity.entity_id, 0.5)
        entity_shock = shock_intensity * prop_factor
        entity_rate = recovery_rate / max(entity_shock, 0.1)
        recovery_ratio = 1.0 - math.exp(-entity_rate * horizon_days)
        residual = 1.0 - recovery_ratio

        entity_recovery.append({
            "entity_id": entity.entity_id,
            "recovery_ratio": round(recovery_ratio, 4),
            "residual_impact": round(residual, 4),
        })

        total_weighted_recovery += entity.criticality * recovery_ratio
        total_criticality += entity.criticality

    # System recovery score
    recovery_score = total_weighted_recovery / max(total_criticality, 1e-9)
    avg_residual = 1.0 - recovery_score

    # Estimate days to 95% recovery (solve R(t) = 0.95)
    # 0.95 = 1 - e^(-rate × t) → t = -ln(0.05) / rate ≈ 3.0 / rate
    full_recovery_est = int(math.ceil(3.0 / max(effective_rate, 1e-6)))

    return {
        "recovery_score": round(recovery_score, 4),
        "avg_residual_impact": round(avg_residual, 4),
        "full_recovery_days_est": min(full_recovery_est, 365),
        "entity_recovery": entity_recovery,
    }
