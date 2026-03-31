"""
Underwriting Restriction Scoring for GCC Insurance Intelligence.

Implements underwriting risk scoring using the GCC formula:

UW_p(t) = 0.40 * RegionRisk_p + 0.25 * LogisticsStress_p + 0.20 * ClaimsSurgePotential_p + 0.15 * IntelligenceUncertainty_p

Classification thresholds:
    0-25:   standard        (unrestricted underwriting)
    25-50:  monitored       (monitor for changes)
    50-70:  restricted      (impose underwriting restrictions)
    70+:    referral        (escalate for management review)
"""

from dataclasses import dataclass
from enum import Enum
from typing import Dict, List
import numpy as np

from .gcc_insurance_config import GCCInsuranceConfig, GCC_INSURANCE_CONFIG


class UnderwritingClassification(str, Enum):
    """Underwriting classification levels."""

    STANDARD = "standard"  # 0-25: Normal underwriting
    MONITORED = "monitored"  # 25-50: Enhanced monitoring
    RESTRICTED = "restricted"  # 50-70: Underwriting restrictions apply
    REFERRAL = "referral"  # 70+: Escalation required


@dataclass
class UnderwritingResult:
    """Results from underwriting restriction scoring."""

    score: float  # Underwriting restriction score (0-100)
    classification: UnderwritingClassification  # Classification level
    components: Dict[str, float]  # Component scores used
    recommended_actions: List[str]  # List of recommended actions


def compute_underwriting_restriction(
    region_risk: float,
    logistics_stress: float,
    claims_surge: float,
    uncertainty: float,
    config: GCCInsuranceConfig = None,
) -> UnderwritingResult:
    """
    Compute underwriting restriction score for a region or portfolio.

    The underwriting restriction formula combines regional risk, logistics stress,
    claims surge potential, and intelligence uncertainty using calibrated weights:

    UW_p(t) = 0.40 * RegionRisk_p + 0.25 * LogisticsStress_p + 0.20 * ClaimsSurgePotential_p + 0.15 * IntelligenceUncertainty_p

    The resulting score (0-100) determines underwriting restrictions:
        0-25:   standard (normal underwriting)
        25-50:  monitored (enhanced monitoring)
        50-70:  restricted (apply restrictions)
        70+:    referral (escalate for management review)

    Args:
        region_risk: Regional risk score (0-1)
        logistics_stress: Logistics/supply chain stress (0-1)
        claims_surge: Claims surge potential (0-1)
        uncertainty: Intelligence uncertainty level (0-1)
        config: GCCInsuranceConfig with weights. Uses GCC defaults if None.

    Returns:
        UnderwritingResult with score, classification, and recommended actions.

    Raises:
        ValueError: If any input is not in [0, 1].
    """
    # Validate inputs
    inputs = {
        "region_risk": region_risk,
        "logistics_stress": logistics_stress,
        "claims_surge": claims_surge,
        "uncertainty": uncertainty,
    }

    for name, value in inputs.items():
        if not 0 <= value <= 1:
            raise ValueError(f"{name} must be in [0, 1], got {value}")

    if config is None:
        config = GCC_INSURANCE_CONFIG

    config.validate()

    # Extract weights
    weights = config.underwriting_weights
    w_region = weights["region_risk"]
    w_logistics = weights["logistics_stress"]
    w_claims = weights["claims_surge"]
    w_uncertainty = weights["uncertainty"]

    # Compute component scores
    components = {
        "region_risk": region_risk * w_region,
        "logistics_stress": logistics_stress * w_logistics,
        "claims_surge": claims_surge * w_claims,
        "uncertainty": uncertainty * w_uncertainty,
    }

    # Compute underwriting restriction score (scaled to 0-100)
    score_normalized = sum(components.values())
    score = float(np.clip(score_normalized * 100.0, 0.0, 100.0))

    # Determine classification based on thresholds
    thresholds = config.underwriting_thresholds
    if score < thresholds["standard"]:
        classification = UnderwritingClassification.STANDARD
    elif score < thresholds["monitored"]:
        classification = UnderwritingClassification.MONITORED
    elif score < thresholds["restricted"]:
        classification = UnderwritingClassification.RESTRICTED
    else:
        classification = UnderwritingClassification.REFERRAL

    # Determine recommended actions based on classification
    recommended_actions = []

    if classification == UnderwritingClassification.STANDARD:
        recommended_actions = [
            "Proceed with standard underwriting",
            "Normal premium pricing",
        ]
    elif classification == UnderwritingClassification.MONITORED:
        recommended_actions = [
            "Enhanced monitoring of regional conditions",
            "Quarterly risk reassessment",
            "Consider modest premium adjustment (5-10%)",
            "Monitor logistics stress indicators",
        ]
    elif classification == UnderwritingClassification.RESTRICTED:
        recommended_actions = [
            "Apply underwriting restrictions",
            "Require additional documentation",
            "Premium adjustment (10-25%)",
            "Reduce exposure limits by 25-50%",
            "Implement enhanced claims monitoring",
            "Require additional loss control measures",
            "Quarterly policy review",
        ]
    else:  # REFERRAL
        recommended_actions = [
            "Escalate to underwriting management",
            "Require executive review and approval",
            "Consider declining new policies",
            "Evaluate portfolio reduction",
            "Implement crisis management protocols",
            "Coordinate with claims and risk management",
            "Weekly risk status reviews",
            "Prepare contingency plans",
        ]

    return UnderwritingResult(
        score=score,
        classification=classification,
        components=components,
        recommended_actions=recommended_actions,
    )
