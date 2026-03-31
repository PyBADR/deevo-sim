"""
Portfolio Exposure Analysis for GCC Insurance Intelligence.

Implements portfolio-level exposure scoring using the GCC formula:

E_ins_p = gamma1 * TIV_p + gamma2 * RouteDependency_p + gamma3 * RegionRisk_p + gamma4 * ClaimsElasticity_p

Where:
    gamma1 = 0.30 (Total Insured Value weight)
    gamma2 = 0.25 (Route Dependency weight)
    gamma3 = 0.25 (Region Risk weight)
    gamma4 = 0.20 (Claims Elasticity weight)
"""

from dataclasses import dataclass, field
from typing import List, Dict
import numpy as np

from .gcc_insurance_config import GCCInsuranceConfig, GCC_INSURANCE_CONFIG


@dataclass
class PolicyExposure:
    """Individual policy exposure input."""

    policy_id: str
    tiv: float  # Total Insured Value (normalized 0-1)
    route_dependency: float  # Route dependency factor (0-1)
    region_risk: float  # Regional risk score (0-1)
    claims_elasticity: float  # Claims elasticity factor (0-1)

    def __post_init__(self):
        """Validate all inputs are in valid ranges."""
        for field_name, value in [
            ("tiv", self.tiv),
            ("route_dependency", self.route_dependency),
            ("region_risk", self.region_risk),
            ("claims_elasticity", self.claims_elasticity),
        ]:
            if not 0 <= value <= 1:
                raise ValueError(f"{field_name} must be in [0, 1], got {value}")


@dataclass
class PortfolioExposureResult:
    """Results from portfolio exposure computation."""

    per_policy_scores: Dict[str, float]  # policy_id -> exposure score
    total_exposure: float  # Sum of all policy exposures
    concentration_index: float  # Herfindahl-Hirschman Index (HHI)
    top_exposed_policies: List[tuple]  # List of (policy_id, score) tuples
    policy_count: int  # Total number of policies
    average_exposure: float  # Mean exposure per policy


def compute_portfolio_exposure(
    policies: List[PolicyExposure],
    config: GCCInsuranceConfig = None,
) -> PortfolioExposureResult:
    """
    Compute portfolio-level insurance exposure using GCC formula.

    The portfolio exposure formula combines TIV, route dependency, regional risk,
    and claims elasticity using calibrated weights:

    E_ins_p = gamma1 * TIV_p + gamma2 * RouteDependency_p + gamma3 * RegionRisk_p + gamma4 * ClaimsElasticity_p

    Args:
        policies: List of PolicyExposure objects
        config: GCCInsuranceConfig with weights. Uses GCC defaults if None.

    Returns:
        PortfolioExposureResult with per-policy scores, totals, and concentration metrics.

    Raises:
        ValueError: If policies list is empty or contains invalid data.
    """
    if not policies:
        raise ValueError("Policies list cannot be empty")

    if config is None:
        config = GCC_INSURANCE_CONFIG

    config.validate()

    # Extract weights
    weights = config.exposure_weights
    gamma1 = weights["tiv"]
    gamma2 = weights["route_dep"]
    gamma3 = weights["region_risk"]
    gamma4 = weights["claims_elasticity"]

    # Compute per-policy exposure scores
    per_policy_scores = {}
    exposure_values = []

    for policy in policies:
        # Apply GCC formula
        exposure_score = (
            gamma1 * policy.tiv
            + gamma2 * policy.route_dependency
            + gamma3 * policy.region_risk
            + gamma4 * policy.claims_elasticity
        )

        # Clip to valid range [0, 1]
        exposure_score = float(np.clip(exposure_score, 0.0, 1.0))
        per_policy_scores[policy.policy_id] = exposure_score
        exposure_values.append(exposure_score)

    exposure_values = np.array(exposure_values, dtype=np.float64)

    # Compute total exposure
    total_exposure = float(np.sum(exposure_values))

    # Compute concentration index (HHI - Herfindahl-Hirschman Index)
    # HHI = sum of squared market shares
    # Measures portfolio concentration: higher = more concentrated
    if total_exposure > 1e-10:
        market_shares = exposure_values / total_exposure
        concentration_index = float(np.sum(market_shares ** 2))
    else:
        concentration_index = 0.0

    # Identify top exposed policies (top 10 or all if fewer)
    top_n = min(10, len(policies))
    sorted_policies = sorted(
        [(p.policy_id, per_policy_scores[p.policy_id]) for p in policies],
        key=lambda x: x[1],
        reverse=True,
    )
    top_exposed_policies = sorted_policies[:top_n]

    # Compute average exposure per policy
    average_exposure = float(np.mean(exposure_values)) if exposure_values.size > 0 else 0.0

    return PortfolioExposureResult(
        per_policy_scores=per_policy_scores,
        total_exposure=total_exposure,
        concentration_index=concentration_index,
        top_exposed_policies=top_exposed_policies,
        policy_count=len(policies),
        average_exposure=average_exposure,
    )
