"""
Uncertainty scoring for GCC risk assessment.

Implements uncertainty:
U_i(t) = 1 - (eta1*SrcQ + eta2*CrossVal + eta3*Freshness + eta4*SigAgree) / (eta1+eta2+eta3+eta4)
"""

from dataclasses import dataclass
from typing import Dict
import numpy as np

from .gcc_weights import UNCERTAINTY_WEIGHTS


@dataclass
class UncertaintyMetrics:
    """Container for uncertainty metrics."""

    source_quality: float  # SrcQ: Quality of information sources [0, 1]
    cross_validation: float  # CrossVal: Cross-validation score [0, 1]
    freshness: float  # Freshness: Data freshness / recency [0, 1]
    signal_agreement: float  # SigAgree: Agreement among signal sources [0, 1]


def compute_uncertainty(
    metrics: UncertaintyMetrics,
    weights: Dict[str, float] = None,
) -> float:
    """
    Compute uncertainty score from component metrics.

    Implements:
    U_i(t) = 1 - (eta1*SrcQ + eta2*CrossVal + eta3*Freshness + eta4*SigAgree) / (eta1+eta2+eta3+eta4)

    Args:
        metrics: UncertaintyMetrics object with component values
        weights: Custom weight dictionary. Defaults to UNCERTAINTY_WEIGHTS if None.

    Returns:
        Uncertainty score in [0, 1] where 1 = maximum uncertainty, 0 = perfect confidence
    """
    if weights is None:
        weights = UNCERTAINTY_WEIGHTS.copy()

    # Validate weights sum to 1.0
    weight_sum = sum(weights.values())
    if not np.isclose(weight_sum, 1.0, rtol=1e-6):
        raise ValueError(f"Weights must sum to 1.0, got {weight_sum}")

    # Validate input metrics are in [0, 1]
    src_quality = np.clip(metrics.source_quality, 0.0, 1.0)
    cross_val = np.clip(metrics.cross_validation, 0.0, 1.0)
    freshness = np.clip(metrics.freshness, 0.0, 1.0)
    sig_agree = np.clip(metrics.signal_agreement, 0.0, 1.0)

    # Compute weighted sum of confidence indicators
    confidence_sum = (
        weights["source_quality"] * src_quality
        + weights["cross_validation"] * cross_val
        + weights["freshness"] * freshness
        + weights["signal_agreement"] * sig_agree
    )

    # Uncertainty = 1 - confidence
    uncertainty = 1.0 - confidence_sum

    return float(np.clip(uncertainty, 0.0, 1.0))


def compute_source_quality(
    trusted_sources: int,
    total_sources: int,
    avg_accuracy: float = 0.95,
) -> float:
    """
    Compute source quality metric.

    SrcQ = (trusted_sources / total_sources) * avg_accuracy

    Args:
        trusted_sources: Number of trusted/verified sources
        total_sources: Total number of sources
        avg_accuracy: Average accuracy of trusted sources [0, 1]

    Returns:
        Source quality in [0, 1]
    """
    if total_sources <= 0:
        return 0.0

    avg_accuracy = np.clip(avg_accuracy, 0.0, 1.0)
    trust_ratio = trusted_sources / total_sources
    quality = np.clip(trust_ratio, 0.0, 1.0) * avg_accuracy

    return float(np.clip(quality, 0.0, 1.0))


def compute_cross_validation(
    agreement_count: int,
    total_validations: int,
) -> float:
    """
    Compute cross-validation agreement score.

    CrossVal = agreement_count / total_validations

    Args:
        agreement_count: Number of validations that confirm signal
        total_validations: Total number of validations performed

    Returns:
        Cross-validation score in [0, 1]
    """
    if total_validations <= 0:
        return 0.0

    agreement_ratio = agreement_count / total_validations
    return float(np.clip(agreement_ratio, 0.0, 1.0))


def compute_freshness(
    hours_since_update: float,
    baseline_hours: float = 24.0,
) -> float:
    """
    Compute data freshness metric (inverse of staleness).

    Freshness = max(0, 1 - (hours_since_update / baseline_hours))

    Args:
        hours_since_update: Hours since last data update
        baseline_hours: Baseline age for freshness threshold (default 24 hours)

    Returns:
        Freshness score in [0, 1] where 1 = fresh, 0 = stale
    """
    if baseline_hours <= 0:
        return 0.0

    hours_since_update = max(0.0, hours_since_update)
    staleness_ratio = hours_since_update / baseline_hours

    freshness = 1.0 - np.clip(staleness_ratio, 0.0, 1.0)
    return float(np.clip(freshness, 0.0, 1.0))


def compute_signal_agreement(
    agreeing_signals: int,
    total_signals: int,
) -> float:
    """
    Compute agreement among independent signal sources.

    SigAgree = agreeing_signals / total_signals

    Args:
        agreeing_signals: Number of signals indicating same conclusion
        total_signals: Total number of independent signals

    Returns:
        Signal agreement in [0, 1]
    """
    if total_signals <= 0:
        return 0.0

    agreement_ratio = agreeing_signals / total_signals
    return float(np.clip(agreement_ratio, 0.0, 1.0))


def compute_aggregated_uncertainty(
    source_qualities: list,
    cross_validations: list,
    freshness_scores: list,
    signal_agreements: list,
    weights: Dict[str, float] = None,
) -> float:
    """
    Compute aggregated uncertainty from multiple data streams.

    Averages metrics across streams, then applies uncertainty formula.

    Args:
        source_qualities: List of source quality scores
        cross_validations: List of cross-validation scores
        freshness_scores: List of freshness scores
        signal_agreements: List of signal agreement scores
        weights: Custom weight dictionary

    Returns:
        Aggregated uncertainty score in [0, 1]
    """
    if not source_qualities:
        return 1.0  # Maximum uncertainty for empty input

    # Average each metric across all streams
    avg_src_quality = float(np.mean(source_qualities)) if source_qualities else 0.0
    avg_cross_val = float(np.mean(cross_validations)) if cross_validations else 0.0
    avg_freshness = float(np.mean(freshness_scores)) if freshness_scores else 0.0
    avg_sig_agree = float(np.mean(signal_agreements)) if signal_agreements else 0.0

    # Create aggregated metrics object
    metrics = UncertaintyMetrics(
        source_quality=avg_src_quality,
        cross_validation=avg_cross_val,
        freshness=avg_freshness,
        signal_agreement=avg_sig_agree,
    )

    return compute_uncertainty(metrics, weights)
