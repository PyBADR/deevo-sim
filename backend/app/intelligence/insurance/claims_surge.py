"""
Claims Surge Potential Assessment for GCC Insurance Intelligence.

Implements claims surge potential scoring using the GCC formula:

S_i(t) = psi1 * R_i(t) + psi2 * D_i(t) + psi3 * Exposure_i + psi4 * PolicySensitivity_i

Where:
    psi1 = 0.28 (Risk score weight)
    psi2 = 0.30 (Disruption score weight)
    psi3 = 0.25 (Exposure weight)
    psi4 = 0.17 (Policy sensitivity weight)
"""

from dataclasses import dataclass
from enum import Enum
from typing import Dict
import numpy as np

from .gcc_insurance_config import GCCInsuranceConfig, GCC_INSURANCE_CONFIG


class SeverityLevel(str, Enum):
    """Severity levels for claims surge potential."""

    NORMAL = "normal"  # 0-0.25
    ELEVATED = "elevated"  # 0.25-0.50
    CRITICAL = "critical"  # 0.50-0.75
    EXTREME = "extreme"  # 0.75-1.00


@dataclass
class ClaimsSurgeResult:
    """Results from claims surge potential computation."""

    surge_score: float  # Overall surge potential score (0-1)
    components: Dict[str, float]  # Breakdown of component scores
    severity_level: SeverityLevel  # Categorical severity level
    confidence: float  # Confidence in assessment (0-1)


def compute_claims_surge_potential(
    risk_score: float,
    disruption_score: float,
    exposure: float,
    policy_sensitivity: float,
    config: GCCInsuranceConfig = None,
) -> ClaimsSurgeResult:
    """
    Compute claims surge potential for a policy or portfolio.

    The claims surge potential formula combines risk, disruption, exposure,
    and policy sensitivity using calibrated weights:

    S_i(t) = psi1 * R_i(t) + psi2 * D_i(t) + psi3 * Exposure_i + psi4 * PolicySensitivity_i

    This score indicates the likelihood and magnitude of claims spikes
    in response to adverse events or system stress.

    Args:
        risk_score: Current risk score (0-1)
        disruption_score: Disruption level (0-1)
        exposure: Exposure level (0-1)
        policy_sensitivity: Policy sensitivity to events (0-1)
        config: GCCInsuranceConfig with weights. Uses GCC defaults if None.

    Returns:
        ClaimsSurgeResult with surge score, components, and severity level.

    Raises:
        ValueError: If any input is not in [0, 1].
    """
    # Validate inputs
    inputs = {
        "risk_score": risk_score,
        "disruption_score": disruption_score,
        "exposure": exposure,
        "policy_sensitivity": policy_sensitivity,
    }

    for name, value in inputs.items():
        if not 0 <= value <= 1:
            raise ValueError(f"{name} must be in [0, 1], got {value}")

    if config is None:
        config = GCC_INSURANCE_CONFIG

    config.validate()

    # Extract weights
    weights = config.claims_surge_weights
    psi1 = weights["risk"]
    psi2 = weights["disruption"]
    psi3 = weights["exposure"]
    psi4 = weights["policy_sensitivity"]

    # Compute weighted components
    components = {
        "risk": risk_score * psi1,
        "disruption": disruption_score * psi2,
        "exposure": exposure * psi3,
        "policy_sensitivity": policy_sensitivity * psi4,
    }

    # Compute surge score using GCC formula
    surge_score = sum(components.values())
    surge_score = float(np.clip(surge_score, 0.0, 1.0))

    # Determine severity level
    if surge_score >= 0.75:
        severity_level = SeverityLevel.EXTREME
        confidence = 0.95
    elif surge_score >= 0.50:
        severity_level = SeverityLevel.CRITICAL
        confidence = 0.90
    elif surge_score >= 0.25:
        severity_level = SeverityLevel.ELEVATED
        confidence = 0.80
    else:
        severity_level = SeverityLevel.NORMAL
        confidence = 0.75

    return ClaimsSurgeResult(
        surge_score=surge_score,
        components=components,
        severity_level=severity_level,
        confidence=confidence,
    )
