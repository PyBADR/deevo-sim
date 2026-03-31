"""
Entity state vector computation for GCC risk assessment.

Implements the entity state vector with six risk components:
S_i(t) = {R_i(t), D_i(t), C_i(t), E_i(t), U_i(t), S_i(t)}

Where:
- R_i(t): Resilience (recovery capacity and redundancy)
- D_i(t): Disruption (direct impact potential)
- C_i(t): Criticality (importance in supply chain)
- E_i(t): Exposure (to geopolitical/logistics threats)
- U_i(t): Uncertainty (confidence in risk assessment)
- S_i(t): Shock susceptibility (overall risk score)
"""

from dataclasses import dataclass
from typing import Dict, Optional
import numpy as np


@dataclass
class EntityStateVector:
    """Entity state vector with six risk assessment components."""

    resilience: float  # R_i(t): Recovery capacity in [0, 1]
    disruption: float  # D_i(t): Direct impact potential in [0, 1]
    criticality: float  # C_i(t): Supply chain importance in [0, 1]
    exposure: float    # E_i(t): Threat exposure in [0, 1]
    uncertainty: float # U_i(t): Assessment confidence in [0, 1]
    shock_susceptibility: float  # S_i(t): Overall risk in [0, 1]

    def __post_init__(self):
        """Validate all components are in [0, 1] range."""
        self.resilience = np.clip(self.resilience, 0.0, 1.0)
        self.disruption = np.clip(self.disruption, 0.0, 1.0)
        self.criticality = np.clip(self.criticality, 0.0, 1.0)
        self.exposure = np.clip(self.exposure, 0.0, 1.0)
        self.uncertainty = np.clip(self.uncertainty, 0.0, 1.0)
        self.shock_susceptibility = np.clip(self.shock_susceptibility, 0.0, 1.0)

    def to_dict(self) -> Dict[str, float]:
        """Convert state vector to dictionary."""
        return {
            "resilience": self.resilience,
            "disruption": self.disruption,
            "criticality": self.criticality,
            "exposure": self.exposure,
            "uncertainty": self.uncertainty,
            "shock_susceptibility": self.shock_susceptibility,
        }

    def compute_risk_profile(self) -> Dict[str, float]:
        """
        Compute derived risk metrics from state vector components.

        Returns:
            Dictionary with derived risk metrics:
            - overall_risk: Weighted combination of all components
            - net_risk: Risk adjusted for resilience
            - uncertainty_adjusted_risk: Risk adjusted for uncertainty
            - threat_concentration: How much risk is due to criticality vs exposure
        """
        # Overall risk: weighted sum of threat factors adjusted for resilience
        threat_factors = self.disruption + self.criticality + self.exposure
        net_threat = threat_factors * (1.0 - self.resilience)

        # Overall risk combines net threat with uncertainty as multiplier
        overall_risk = min(net_threat, 1.0)

        # Net risk: threat discounted by resilience
        net_risk = overall_risk * (1.0 - self.resilience)

        # Uncertainty-adjusted risk: increase perceived risk when uncertainty is high
        uncertainty_multiplier = 1.0 + (0.5 * self.uncertainty)
        uncertainty_adjusted_risk = min(overall_risk * uncertainty_multiplier, 1.0)

        # Threat concentration: ratio of criticality to total exposure
        total_exposure = self.disruption + self.criticality + self.exposure
        threat_concentration = (
            self.criticality / total_exposure if total_exposure > 0 else 0.0
        )

        return {
            "overall_risk": float(overall_risk),
            "net_risk": float(net_risk),
            "uncertainty_adjusted_risk": float(uncertainty_adjusted_risk),
            "threat_concentration": float(threat_concentration),
        }


def compute_state_vector(
    resilience: float,
    disruption: float,
    criticality: float,
    exposure: float,
    uncertainty: float,
    shock_weight_r: float = 0.15,
    shock_weight_d: float = 0.30,
    shock_weight_c: float = 0.25,
    shock_weight_e: float = 0.20,
    shock_weight_u: float = 0.10,
) -> EntityStateVector:
    """
    Compute entity state vector from component risk scores.

    The shock susceptibility S_i(t) combines all components:
    S_i(t) = shock_weight_r*R + shock_weight_d*D + shock_weight_c*C + 
             shock_weight_e*E + shock_weight_u*U

    Weights must sum to 1.0 to ensure normalized shock susceptibility.

    Args:
        resilience: Recovery capacity in [0, 1]
        disruption: Direct impact potential in [0, 1]
        criticality: Supply chain importance in [0, 1]
        exposure: Threat exposure in [0, 1]
        uncertainty: Assessment confidence in [0, 1]
        shock_weight_r: Resilience weight (default 0.15)
        shock_weight_d: Disruption weight (default 0.30)
        shock_weight_c: Criticality weight (default 0.25)
        shock_weight_e: Exposure weight (default 0.20)
        shock_weight_u: Uncertainty weight (default 0.10)

    Returns:
        EntityStateVector with all components normalized to [0, 1]
    """
    # Clip all input components to valid range
    resilience = np.clip(resilience, 0.0, 1.0)
    disruption = np.clip(disruption, 0.0, 1.0)
    criticality = np.clip(criticality, 0.0, 1.0)
    exposure = np.clip(exposure, 0.0, 1.0)
    uncertainty = np.clip(uncertainty, 0.0, 1.0)

    # Validate weights sum to 1.0
    weight_sum = (
        shock_weight_r
        + shock_weight_d
        + shock_weight_c
        + shock_weight_e
        + shock_weight_u
    )
    if not np.isclose(weight_sum, 1.0, rtol=1e-6):
        raise ValueError(f"Shock weights must sum to 1.0, got {weight_sum}")

    # Compute shock susceptibility as weighted combination
    shock_susceptibility = (
        shock_weight_r * resilience
        + shock_weight_d * disruption
        + shock_weight_c * criticality
        + shock_weight_e * exposure
        + shock_weight_u * uncertainty
    )

    shock_susceptibility = np.clip(shock_susceptibility, 0.0, 1.0)

    return EntityStateVector(
        resilience=float(resilience),
        disruption=float(disruption),
        criticality=float(criticality),
        exposure=float(exposure),
        uncertainty=float(uncertainty),
        shock_susceptibility=float(shock_susceptibility),
    )


def compute_state_vector_from_dict(
    component_dict: Dict[str, float],
    weights: Optional[Dict[str, float]] = None,
) -> EntityStateVector:
    """
    Compute entity state vector from dictionary of component values.

    Args:
        component_dict: Dictionary with keys: resilience, disruption, criticality,
                       exposure, uncertainty (each in [0, 1])
        weights: Optional dictionary with keys: shock_weight_r, shock_weight_d,
                shock_weight_c, shock_weight_e, shock_weight_u

    Returns:
        EntityStateVector with all components in [0, 1]
    """
    # Default weights if not provided
    if weights is None:
        weights = {
            "shock_weight_r": 0.15,
            "shock_weight_d": 0.30,
            "shock_weight_c": 0.25,
            "shock_weight_e": 0.20,
            "shock_weight_u": 0.10,
        }

    return compute_state_vector(
        resilience=component_dict.get("resilience", 0.0),
        disruption=component_dict.get("disruption", 0.0),
        criticality=component_dict.get("criticality", 0.0),
        exposure=component_dict.get("exposure", 0.0),
        uncertainty=component_dict.get("uncertainty", 0.0),
        shock_weight_r=weights.get("shock_weight_r", 0.15),
        shock_weight_d=weights.get("shock_weight_d", 0.30),
        shock_weight_c=weights.get("shock_weight_c", 0.25),
        shock_weight_e=weights.get("shock_weight_e", 0.20),
        shock_weight_u=weights.get("shock_weight_u", 0.10),
    )


def merge_state_vectors(
    vectors: list,
    weights: Optional[list] = None,
) -> EntityStateVector:
    """
    Merge multiple state vectors using weighted averaging.

    Useful for aggregating risk assessments from different analysis methods
    or combining assessments from multiple analysts.

    Args:
        vectors: List of EntityStateVector objects
        weights: Optional list of weights for each vector (must sum to 1.0)

    Returns:
        Merged EntityStateVector with component averages
    """
    if not vectors:
        return EntityStateVector(
            resilience=0.0,
            disruption=0.0,
            criticality=0.0,
            exposure=0.0,
            uncertainty=0.0,
            shock_susceptibility=0.0,
        )

    if weights is None:
        weights = [1.0 / len(vectors)] * len(vectors)

    if len(vectors) != len(weights):
        raise ValueError("Number of vectors must match number of weights")

    weight_sum = sum(weights)
    if not np.isclose(weight_sum, 1.0, rtol=1e-6):
        raise ValueError(f"Weights must sum to 1.0, got {weight_sum}")

    # Weighted average of each component
    avg_resilience = sum(v.resilience * w for v, w in zip(vectors, weights))
    avg_disruption = sum(v.disruption * w for v, w in zip(vectors, weights))
    avg_criticality = sum(v.criticality * w for v, w in zip(vectors, weights))
    avg_exposure = sum(v.exposure * w for v, w in zip(vectors, weights))
    avg_uncertainty = sum(v.uncertainty * w for v, w in zip(vectors, weights))
    avg_shock = sum(v.shock_susceptibility * w for v, w in zip(vectors, weights))

    return EntityStateVector(
        resilience=float(avg_resilience),
        disruption=float(avg_disruption),
        criticality=float(avg_criticality),
        exposure=float(avg_exposure),
        uncertainty=float(avg_uncertainty),
        shock_susceptibility=float(avg_shock),
    )
