"""
System-level stress score aggregating multiple disruption metrics.

Physics metaphor: System stress is a multi-dimensional scalar that aggregates
pressure (load on nodes), congestion (flow density), disruptions (unresolved
events), and uncertainty (epistemic limits). Like total mechanical stress in
a structure, high system stress indicates increased risk of cascading failures.

GCC Physics Model:
System stress is computed as weighted sum of four components:
    Stress(t) = 0.35*C_i(t) + 0.30*R_i(t) + 0.20*U_i(t) + 0.15*S_i(t)

where:
    C_i(t) = Pressure component (node load stress) - weight 0.35
    R_i(t) = Congestion component (flow density) - weight 0.30
    U_i(t) = Disruption component (unresolved events) - weight 0.20
    S_i(t) = Uncertainty component (epistemic uncertainty) - weight 0.15

All components are normalized to [0, 1] before aggregation.
This implementation uses GCC defaults for all weights and normalization.
"""

from dataclasses import dataclass, field
from typing import Dict, Optional
from enum import Enum
import numpy as np
from .gcc_physics_config import (
    STRESS_PRESSURE_WEIGHT,
    STRESS_CONGESTION_WEIGHT,
    STRESS_DISRUPTION_WEIGHT,
    STRESS_UNCERTAINTY_WEIGHT,
    STRESS_PRESSURE_NORMALIZATION,
    STRESS_DISRUPTION_DECAY_RATE,
    STRESS_LEVEL_NOMINAL_THRESHOLD,
    STRESS_LEVEL_ELEVATED_THRESHOLD,
    STRESS_LEVEL_HIGH_THRESHOLD,
)


class StressLevel(Enum):
    """Qualitative stress level categories."""
    NOMINAL = "nominal"
    ELEVATED = "elevated"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class SystemStressResult:
    """
    Result of system stress computation.
    
    Attributes:
        stress_score: Quantitative stress [0, 1]
        level: Qualitative stress level (nominal/elevated/high/critical)
        components: Dictionary of individual component contributions
                   Keys: 'pressure', 'congestion', 'disruptions', 'uncertainty'
        narrative: Human-readable summary of stress state
    """
    stress_score: float
    level: StressLevel
    components: Dict[str, float] = field(default_factory=dict)
    narrative: str = ""


def compute_system_stress(
    pressures: Dict[str, float],
    congestion_scores: Dict[str, float],
    unresolved_disruptions: int = 0,
    uncertainty: float = 0.0,
    weights: Optional[Dict[str, float]] = None
) -> SystemStressResult:
    """
    Compute aggregate system stress from multiple metrics using GCC formula.
    
    Physics model: System stress combines four sources of system strain:
    1. Pressure: Sum of node load stresses (normalized)
    2. Congestion: Average flow density across corridors (normalized)
    3. Disruptions: Count of unresolved disruptions (exponential scaling)
    4. Uncertainty: Epistemic uncertainty about state (normalized)
    
    These are combined using weighted sum (GCC defaults):
        Stress(t) = w_p*C_i(t) + w_c*R_i(t) + w_d*U_i(t) + w_u*S_i(t)
    
    where GCC weights are:
        w_p = 0.35 (pressure weight)
        w_c = 0.30 (congestion weight)
        w_d = 0.20 (disruption weight)
        w_u = 0.15 (uncertainty weight)
    
    The result is clamped to [0, 1] for interpretation.
    
    Args:
        pressures: Dict mapping node_id -> pressure value
        congestion_scores: Dict mapping corridor_id -> congestion [0,1]
        unresolved_disruptions: Count of ongoing disruptions [default: 0]
        uncertainty: Epistemic uncertainty [0, 1] [default: 0.0]
        weights: Optional weights for each component
                Keys: 'pressure', 'congestion', 'disruptions', 'uncertainty'
                If None, uses GCC defaults [0.35, 0.30, 0.20, 0.15]
                
    Returns:
        SystemStressResult with stress_score, level, and component breakdown
    """
    # Use GCC defaults if weights not provided
    if weights is None:
        weights = {
            'pressure': STRESS_PRESSURE_WEIGHT,
            'congestion': STRESS_CONGESTION_WEIGHT,
            'disruptions': STRESS_DISRUPTION_WEIGHT,
            'uncertainty': STRESS_UNCERTAINTY_WEIGHT
        }

    # Validate weights sum to approximately 1.0
    weight_sum = sum(weights.values())
    if not np.isclose(weight_sum, 1.0, atol=0.01):
        # Normalize weights if they don't sum to 1
        for key in weights:
            weights[key] /= weight_sum

    # Component 1: Pressure stress (mean of all node pressures, normalized)
    if pressures:
        pressure_stress = np.mean(list(pressures.values()))
        # Normalize by GCC normalization factor (2.0)
        pressure_stress = float(np.clip(pressure_stress / STRESS_PRESSURE_NORMALIZATION, 0.0, 1.0))
    else:
        pressure_stress = 0.0

    # Component 2: Congestion stress (average of all corridors)
    if congestion_scores:
        congestion_stress = float(np.mean(list(congestion_scores.values())))
        congestion_stress = float(np.clip(congestion_stress, 0.0, 1.0))
    else:
        congestion_stress = 0.0

    # Component 3: Disruption stress (exponential scaling with GCC decay rate)
    # Formula: stress = 1 - exp(-decay_rate * disruption_count)
    # GCC decay rate = 0.5
    disruption_stress = float(1.0 - np.exp(-STRESS_DISRUPTION_DECAY_RATE * unresolved_disruptions))

    # Component 4: Uncertainty stress (direct normalization)
    uncertainty_stress = float(np.clip(uncertainty, 0.0, 1.0))

    # Aggregate with GCC weights: Stress(t) = 0.35*P + 0.30*C + 0.20*D + 0.15*U
    stress_score = (
        weights['pressure'] * pressure_stress
        + weights['congestion'] * congestion_stress
        + weights['disruptions'] * disruption_stress
        + weights['uncertainty'] * uncertainty_stress
    )

    # Determine stress level using GCC thresholds
    if stress_score < STRESS_LEVEL_NOMINAL_THRESHOLD:  # 0.25
        level = StressLevel.NOMINAL
    elif stress_score < STRESS_LEVEL_ELEVATED_THRESHOLD:  # 0.50
        level = StressLevel.ELEVATED
    elif stress_score < STRESS_LEVEL_HIGH_THRESHOLD:  # 0.75
        level = StressLevel.HIGH
    else:
        level = StressLevel.CRITICAL

    # Build narrative
    active_components = []
    if pressure_stress > 0.1:
        active_components.append(f"node pressure {pressure_stress:.2f}")
    if congestion_stress > 0.1:
        active_components.append(f"congestion {congestion_stress:.2f}")
    if unresolved_disruptions > 0:
        active_components.append(f"{unresolved_disruptions} disruption(s)")
    if uncertainty_stress > 0.1:
        active_components.append(f"uncertainty {uncertainty_stress:.2f}")

    if active_components:
        narrative = f"System under {level.value} stress. Active stressors: {', '.join(active_components)}."
    else:
        narrative = "System nominal. All metrics within acceptable ranges."

    return SystemStressResult(
        stress_score=float(np.clip(stress_score, 0.0, 1.0)),
        level=level,
        components={
            'pressure': pressure_stress,
            'congestion': congestion_stress,
            'disruptions': disruption_stress,
            'uncertainty': uncertainty_stress
        },
        narrative=narrative
    )
