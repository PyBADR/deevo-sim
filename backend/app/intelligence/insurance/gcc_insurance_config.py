"""
GCC Insurance Intelligence Configuration.

Centralized configuration for all GCC Insurance Intelligence Layer weights,
thresholds, and regional multipliers. All defaults are calibrated for the
Gulf Cooperation Council region and should be preserved in production.
"""

from dataclasses import dataclass
from typing import Dict


@dataclass
class GCCInsuranceConfig:
    """Configuration for GCC Insurance Intelligence calculations."""

    # Portfolio Exposure Weights
    # E_ins_p = gamma1 * TIV_p + gamma2 * RouteDependency_p + gamma3 * RegionRisk_p + gamma4 * ClaimsElasticity_p
    exposure_weights: Dict[str, float] = None
    
    # Claims Surge Potential Weights
    # S_i(t) = psi1 * R_i(t) + psi2 * D_i(t) + psi3 * Exposure_i + psi4 * PolicySensitivity_i
    claims_surge_weights: Dict[str, float] = None
    
    # Expected Claims Uplift Weights
    # DeltaClaims_p(t) = BaseClaims_p * (1 + chi1 * S_p(t) + chi2 * Stress(t) + chi3 * Uncertainty_p(t))
    claims_uplift_weights: Dict[str, float] = None
    
    # Underwriting Restriction Weights
    # UW_p(t) = 0.40 * RegionRisk_p + 0.25 * LogisticsStress_p + 0.20 * ClaimsSurgePotential_p + 0.15 * IntelligenceUncertainty_p
    underwriting_weights: Dict[str, float] = None
    
    # Underwriting Classification Thresholds
    # Classification: 0-25: standard, 25-50: monitored, 50-70: restricted, 70+: referral
    underwriting_thresholds: Dict[str, float] = None
    
    # Regional Multipliers (for severity projection)
    regional_multipliers: Dict[str, float] = None

    def __post_init__(self):
        """Initialize default values for all configurations."""
        if self.exposure_weights is None:
            self.exposure_weights = {
                "tiv": 0.30,
                "route_dep": 0.25,
                "region_risk": 0.25,
                "claims_elasticity": 0.20,
            }

        if self.claims_surge_weights is None:
            self.claims_surge_weights = {
                "risk": 0.28,
                "disruption": 0.30,
                "exposure": 0.25,
                "policy_sensitivity": 0.17,
            }

        if self.claims_uplift_weights is None:
            self.claims_uplift_weights = {
                "surge": 0.45,
                "stress": 0.30,
                "uncertainty": 0.25,
            }

        if self.underwriting_weights is None:
            self.underwriting_weights = {
                "region_risk": 0.40,
                "logistics_stress": 0.25,
                "claims_surge": 0.20,
                "uncertainty": 0.15,
            }

        if self.underwriting_thresholds is None:
            self.underwriting_thresholds = {
                "standard": 25,
                "monitored": 50,
                "restricted": 70,
            }

        if self.regional_multipliers is None:
            self.regional_multipliers = {
                "KW": 1.05,  # Kuwait: baseline with modest premium
                "SA": 1.15,  # Saudi Arabia: energy corridor exposure
                "AE": 1.20,  # UAE: logistics hub dependency
                "QA": 1.10,  # Qatar: LNG corridor
                "BH": 1.00,  # Bahrain: baseline
                "OM": 0.95,  # Oman: lower concentration
            }

    def validate(self) -> bool:
        """Validate configuration integrity."""
        # Validate weights sum to 1.0
        exposure_sum = sum(self.exposure_weights.values())
        if not abs(exposure_sum - 1.0) < 1e-6:
            raise ValueError(
                f"Exposure weights must sum to 1.0, got {exposure_sum}"
            )

        claims_surge_sum = sum(self.claims_surge_weights.values())
        if not abs(claims_surge_sum - 1.0) < 1e-6:
            raise ValueError(
                f"Claims surge weights must sum to 1.0, got {claims_surge_sum}"
            )

        claims_uplift_sum = sum(self.claims_uplift_weights.values())
        if not abs(claims_uplift_sum - 1.0) < 1e-6:
            raise ValueError(
                f"Claims uplift weights must sum to 1.0, got {claims_uplift_sum}"
            )

        underwriting_sum = sum(self.underwriting_weights.values())
        if not abs(underwriting_sum - 1.0) < 1e-6:
            raise ValueError(
                f"Underwriting weights must sum to 1.0, got {underwriting_sum}"
            )

        # Validate thresholds are in ascending order
        thresholds = self.underwriting_thresholds
        if not (0 < thresholds["standard"] < thresholds["monitored"] < thresholds["restricted"] < 100):
            raise ValueError(
                "Underwriting thresholds must be in ascending order with values between 0 and 100"
            )

        # Validate regional multipliers are positive
        for region, multiplier in self.regional_multipliers.items():
            if multiplier <= 0:
                raise ValueError(
                    f"Regional multiplier for {region} must be positive, got {multiplier}"
                )

        return True


# Singleton instance with GCC defaults
GCC_INSURANCE_CONFIG = GCCInsuranceConfig()
