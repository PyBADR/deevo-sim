"""
Severity Projection Module

Projects loss ratios based on event characteristics, regional adjustments, and historical
calibration using exponential smoothing. Supports GCC-specific regional multipliers.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Tuple
import numpy as np

from .gcc_insurance_config import GCC_INSURANCE_CONFIG


class TrendDirection(str, Enum):
    """Trend direction classification for loss ratio trajectory."""
    INCREASING = "increasing"
    STABLE = "stable"
    DECREASING = "decreasing"


@dataclass
class SeverityProjection:
    """Result of severity projection calculation."""
    event_type: str
    region: str
    current_stress: float
    projected_loss_ratio: float
    confidence_interval: Tuple[float, float]  # (lower_bound, upper_bound)
    trend: TrendDirection
    regional_adjustment_factor: float
    historical_smoothed_ratio: float
    confidence_score: float
    components: Dict[str, float] = field(default_factory=dict)

    def to_dict(self) -> Dict:
        """Convert result to dictionary for serialization."""
        return {
            "event_type": self.event_type,
            "region": self.region,
            "current_stress": self.current_stress,
            "projected_loss_ratio": self.projected_loss_ratio,
            "confidence_interval": {
                "lower": self.confidence_interval[0],
                "upper": self.confidence_interval[1]
            },
            "trend": self.trend.value,
            "regional_adjustment_factor": self.regional_adjustment_factor,
            "historical_smoothed_ratio": self.historical_smoothed_ratio,
            "confidence_score": self.confidence_score,
            "components": self.components
        }


def _validate_inputs(
    event_type: str,
    region: str,
    current_stress: float,
    historical_loss_ratios: Optional[List[float]]
) -> None:
    """Validate severity projection inputs."""
    if not event_type or not isinstance(event_type, str):
        raise ValueError("event_type must be non-empty string")
    
    if not region or region not in GCC_INSURANCE_CONFIG.regional_multipliers:
        raise ValueError(
            f"region must be valid GCC country. Valid regions: "
            f"{list(GCC_INSURANCE_CONFIG.regional_multipliers.keys())}"
        )
    
    if not (0.0 <= current_stress <= 1.0):
        raise ValueError("current_stress must be in [0.0, 1.0]")
    
    if historical_loss_ratios is not None:
        if not isinstance(historical_loss_ratios, list):
            raise ValueError("historical_loss_ratios must be list or None")
        if len(historical_loss_ratios) > 0:
            for ratio in historical_loss_ratios:
                if not (0.0 <= ratio <= 2.0):
                    raise ValueError(
                        f"historical_loss_ratios values must be in [0.0, 2.0], "
                        f"got {ratio}"
                    )


def _exponential_smoothing(
    historical_loss_ratios: List[float],
    alpha: float = 0.3
) -> float:
    """
    Apply exponential smoothing to historical loss ratio data.
    
    Uses simple exponential smoothing: S_t = alpha * Y_t + (1 - alpha) * S_{t-1}
    
    Args:
        historical_loss_ratios: Historical loss ratios in chronological order
        alpha: Smoothing parameter (0 < alpha <= 1), default 0.3 (more weight on history)
    
    Returns:
        Smoothed loss ratio estimate
    """
    if not historical_loss_ratios:
        return 0.75  # Default historical baseline
    
    if len(historical_loss_ratios) == 1:
        return historical_loss_ratios[0]
    
    # Initialize with first value
    smoothed = historical_loss_ratios[0]
    
    # Apply exponential smoothing
    for ratio in historical_loss_ratios[1:]:
        smoothed = alpha * ratio + (1.0 - alpha) * smoothed
    
    return smoothed


def _calculate_trend(
    historical_loss_ratios: Optional[List[float]],
    current_stress: float
) -> Tuple[TrendDirection, float]:
    """
    Calculate trend direction and trend factor for loss ratio projection.
    
    Args:
        historical_loss_ratios: Historical loss ratios
        current_stress: Current system stress level (0-1)
    
    Returns:
        Tuple of (trend_direction, trend_factor)
        trend_factor ranges [-0.10, +0.10] as adjustment to projected ratio
    """
    if not historical_loss_ratios or len(historical_loss_ratios) < 2:
        # If insufficient data, use current stress to infer trend
        if current_stress > 0.6:
            return TrendDirection.INCREASING, 0.08
        elif current_stress < 0.3:
            return TrendDirection.DECREASING, -0.05
        else:
            return TrendDirection.STABLE, 0.0
    
    # Compare recent vs older periods
    recent_avg = np.mean(historical_loss_ratios[-3:] if len(historical_loss_ratios) >= 3 
                         else historical_loss_ratios[-2:])
    older_avg = np.mean(historical_loss_ratios[:3] if len(historical_loss_ratios) >= 3 
                        else [historical_loss_ratios[0]])
    
    ratio_change = (recent_avg - older_avg) / max(older_avg, 0.01)
    
    # Determine trend with stress consideration
    if ratio_change > 0.10 or current_stress > 0.7:
        trend = TrendDirection.INCREASING
        trend_factor = 0.08 + (current_stress * 0.02)  # Up to +0.10
    elif ratio_change < -0.10 and current_stress < 0.4:
        trend = TrendDirection.DECREASING
        trend_factor = -0.05 - (0.4 - current_stress) * 0.05  # Down to -0.10
    else:
        trend = TrendDirection.STABLE
        trend_factor = current_stress * 0.03 - 0.015  # Range [-0.015, +0.015]
    
    return trend, np.clip(trend_factor, -0.10, 0.10)


def project_severity(
    event_type: str,
    region: str,
    current_stress: float,
    historical_loss_ratios: Optional[List[float]] = None,
    config=None
) -> SeverityProjection:
    """
    Project loss ratio severity with regional adjustment and historical calibration.
    
    Implementation combines:
    1. Base loss ratio from event type characteristics
    2. Stress amplification of current conditions
    3. Regional adjustment via GCC-specific multipliers
    4. Historical loss ratio calibration with exponential smoothing
    5. Trend analysis for trajectory assessment
    
    Args:
        event_type: Type of insurance event (e.g., "catastrophe", "operational", "market")
        region: GCC country code (KW, SA, AE, QA, BH, OM)
        current_stress: Current system stress level, normalized to [0.0, 1.0]
        historical_loss_ratios: Optional list of historical loss ratios for calibration
        config: GCCInsuranceConfig instance (uses global default if None)
    
    Returns:
        SeverityProjection with projected loss ratio, confidence interval, trend, and components
    
    Raises:
        ValueError: If inputs fail validation
    """
    if config is None:
        config = GCC_INSURANCE_CONFIG
    
    # Validate all inputs
    _validate_inputs(event_type, region, current_stress, historical_loss_ratios)
    
    # Get regional adjustment factor
    regional_adjustment = config.regional_multipliers.get(region, 1.0)
    
    # Calibrate historical loss ratio via exponential smoothing
    historical_smoothed = _exponential_smoothing(
        historical_loss_ratios if historical_loss_ratios else []
    )
    
    # Determine trend and trend factor
    trend_direction, trend_factor = _calculate_trend(historical_loss_ratios, current_stress)
    
    # Event type base loss ratios (baseline expected ratios by event category)
    event_base_ratios = {
        "catastrophe": 0.95,
        "operational": 0.65,
        "market": 0.55,
        "systemic": 0.85,
        "idiosyncratic": 0.45
    }
    event_base = event_base_ratios.get(event_type.lower(), 0.60)
    
    # Stress amplification: current stress increases loss ratio
    # Formula: stress_amplified = event_base * (1 + stress_multiplier * current_stress)
    stress_multiplier = 0.40  # 40% maximum amplification from stress
    stress_amplified = event_base * (1.0 + stress_multiplier * current_stress)
    
    # Blend with historical calibration
    # Higher confidence in historical data reduces weight on event-based estimate
    historical_weight = min(0.50, len(historical_loss_ratios or []) * 0.15)
    event_weight = 1.0 - historical_weight
    
    blended_ratio = (
        event_weight * stress_amplified +
        historical_weight * historical_smoothed
    )
    
    # Apply regional adjustment
    adjusted_ratio = blended_ratio * regional_adjustment
    
    # Add trend factor
    projected_ratio = adjusted_ratio + trend_factor
    
    # Clip to valid range [0.0, 2.0]
    projected_ratio = np.clip(projected_ratio, 0.0, 2.0)
    
    # Calculate confidence interval based on data availability and stress
    # More historical data and stable conditions increase confidence
    base_interval_width = 0.25
    data_confidence_factor = 1.0 - min(0.40, len(historical_loss_ratios or []) * 0.05)
    stress_confidence_factor = 1.0 + abs(current_stress - 0.5) * 0.30
    
    interval_half_width = base_interval_width * data_confidence_factor * stress_confidence_factor
    confidence_interval = (
        np.clip(projected_ratio - interval_half_width, 0.0, 2.0),
        np.clip(projected_ratio + interval_half_width, 0.0, 2.0)
    )
    
    # Calculate confidence score (0-1) based on data availability and stability
    data_confidence = min(0.70, len(historical_loss_ratios or []) * 0.10)
    stability_confidence = 1.0 - abs(trend_factor) * 2.0  # Trends reduce confidence
    stress_impact = 1.0 - current_stress * 0.20  # High stress reduces confidence
    
    confidence_score = np.clip(
        data_confidence + stability_confidence * 0.30 + stress_impact * 0.25,
        0.50,
        0.95
    )
    
    # Build component tracking dictionary
    components = {
        "event_base": event_base,
        "stress_amplified": stress_amplified,
        "historical_smoothed": historical_smoothed,
        "historical_weight": historical_weight,
        "event_weight": event_weight,
        "blended_ratio": blended_ratio,
        "stress_multiplier_applied": stress_multiplier * current_stress,
        "regional_adjustment": regional_adjustment,
        "trend_factor": trend_factor,
        "interval_width": interval_half_width,
        "data_points_used": len(historical_loss_ratios or [])
    }
    
    return SeverityProjection(
        event_type=event_type,
        region=region,
        current_stress=current_stress,
        projected_loss_ratio=projected_ratio,
        confidence_interval=confidence_interval,
        trend=trend_direction,
        regional_adjustment_factor=regional_adjustment,
        historical_smoothed_ratio=historical_smoothed,
        confidence_score=confidence_score,
        components=components
    )
