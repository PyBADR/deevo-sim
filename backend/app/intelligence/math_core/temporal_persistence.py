"""
Temporal persistence scoring for GCC risk assessment.

Implements temporal persistence:
T_i(t) = sum over events e of Sev_e * exp(-lambda_t * Delta_t_e)
"""

from typing import List
import numpy as np

from .gcc_weights import TEMPORAL_DECAY_SEVERE, TEMPORAL_DECAY_SOFT


class TemporalEvent:
    """Represents an event in temporal persistence calculation."""

    def __init__(
        self,
        severity: float,
        hours_ago: float,
        is_hard_event: bool = True,
    ):
        """
        Initialize temporal event.

        Args:
            severity: Event severity in [0, 1]
            hours_ago: Hours elapsed since event
            is_hard_event: True for kinetic events, False for soft signals
        """
        self.severity = np.clip(severity, 0.0, 1.0)
        self.hours_ago = max(0.0, hours_ago)
        self.is_hard_event = is_hard_event


def compute_temporal_persistence(
    events: List[TemporalEvent],
) -> float:
    """
    Compute aggregated temporal persistence from all events.

    Implements:
    T_i(t) = sum over events e of Sev_e * exp(-lambda_t * Delta_t_e)

    Args:
        events: List of TemporalEvent objects

    Returns:
        Temporal persistence score in [0, inf) (unbounded sum)
    """
    if not events:
        return 0.0

    total_persistence = 0.0

    for event in events:
        # Select decay rate based on event type
        lambda_t = TEMPORAL_DECAY_SEVERE if event.is_hard_event else TEMPORAL_DECAY_SOFT

        # Compute temporal decay: exp(-lambda_t * Delta_t)
        temporal_decay = np.exp(-lambda_t * event.hours_ago)

        # Add contribution: Sev_e * exp(-lambda_t * Delta_t_e)
        contribution = event.severity * temporal_decay

        total_persistence += contribution

    return float(total_persistence)


def compute_event_temporal_weight(
    hours_ago: float,
    is_hard_event: bool = True,
) -> float:
    """
    Compute temporal decay weight for a single event.

    Implements:
    weight = exp(-lambda_t * Delta_t)

    Args:
        hours_ago: Hours elapsed since event
        is_hard_event: True for kinetic events (faster decay), False for soft signals

    Returns:
        Temporal decay weight in (0, 1]
    """
    hours_ago = max(0.0, hours_ago)

    # Select decay rate based on event type
    lambda_t = TEMPORAL_DECAY_SEVERE if is_hard_event else TEMPORAL_DECAY_SOFT

    # Compute exponential decay
    weight = np.exp(-lambda_t * hours_ago)

    return float(np.clip(weight, 0.0, 1.0))


def compute_event_half_life(is_hard_event: bool = True) -> float:
    """
    Compute half-life of event persistence.

    Half-life is the time at which exp(-lambda_t * t) = 0.5.
    Half-life = ln(2) / lambda_t

    Args:
        is_hard_event: True for kinetic events, False for soft signals

    Returns:
        Half-life in hours
    """
    lambda_t = TEMPORAL_DECAY_SEVERE if is_hard_event else TEMPORAL_DECAY_SOFT

    if lambda_t <= 0:
        return float('inf')

    half_life = np.log(2.0) / lambda_t

    return float(half_life)


def compute_time_weighted_severity(
    severity: float,
    hours_ago: float,
    is_hard_event: bool = True,
) -> float:
    """
    Compute severity weighted by temporal decay.

    Implements:
    weighted_severity = severity * exp(-lambda_t * Delta_t)

    Args:
        severity: Event severity in [0, 1]
        hours_ago: Hours elapsed since event
        is_hard_event: True for kinetic events, False for soft signals

    Returns:
        Time-weighted severity in [0, 1]
    """
    severity = np.clip(severity, 0.0, 1.0)
    temporal_weight = compute_event_temporal_weight(hours_ago, is_hard_event)

    weighted_severity = severity * temporal_weight

    return float(np.clip(weighted_severity, 0.0, 1.0))


def compute_aggregated_severity(
    severities: List[float],
    hours_ago_list: List[float],
    is_hard_events: List[bool] = None,
) -> float:
    """
    Compute aggregated time-weighted severity from multiple events.

    Args:
        severities: List of event severities in [0, 1]
        hours_ago_list: List of hours elapsed for each event
        is_hard_events: List of boolean flags (default all True)

    Returns:
        Aggregated severity in [0, 1]
    """
    if not severities:
        return 0.0

    if is_hard_events is None:
        is_hard_events = [True] * len(severities)

    if len(severities) != len(hours_ago_list) or len(severities) != len(is_hard_events):
        raise ValueError("All input lists must have same length")

    # Compute weighted severities
    weighted_severities = [
        compute_time_weighted_severity(sev, hours, hard)
        for sev, hours, hard in zip(severities, hours_ago_list, is_hard_events)
    ]

    # Return maximum (most severe current threat)
    return float(max(weighted_severities)) if weighted_severities else 0.0
