"""
Geopolitical threat field computation for GCC risk assessment.

Implements the GCC threat field equation:
Phi_e(i,t) = M_e * Sev_e * Conf_e * exp(-lambda_d * d(i,e)) * exp(-lambda_t * Delta_t_e)
G_i(t) = sum over all active events e of Phi_e(i,t)
"""

from dataclasses import dataclass
from typing import List, Tuple
import numpy as np

from .gcc_weights import (
    EVENT_MULTIPLIERS,
    SPATIAL_DECAY_LAMBDA,
    TEMPORAL_DECAY_SEVERE,
    TEMPORAL_DECAY_SOFT,
)


@dataclass
class Event:
    """Geopolitical event with threat characteristics."""

    event_type: str  # Key into EVENT_MULTIPLIERS
    severity: float  # Sev_e in [0, 1]
    confidence: float  # Conf_e in [0, 1]
    latitude: float  # Event location latitude
    longitude: float  # Event location longitude
    hours_ago: float  # Delta_t_e = current time - event time
    is_hard_event: bool = True  # True for kinetic, False for soft signals


def haversine_distance(
    lat1: float,
    lon1: float,
    lat2: float,
    lon2: float,
) -> float:
    """
    Calculate great-circle distance between two points in kilometers.

    Args:
        lat1: Latitude of point 1 (degrees)
        lon1: Longitude of point 1 (degrees)
        lat2: Latitude of point 2 (degrees)
        lon2: Longitude of point 2 (degrees)

    Returns:
        Distance in kilometers
    """
    R = 6371.0  # Earth radius in kilometers

    lat1_rad = np.radians(lat1)
    lon1_rad = np.radians(lon1)
    lat2_rad = np.radians(lat2)
    lon2_rad = np.radians(lon2)

    dlat = lat2_rad - lat1_rad
    dlon = lon2_rad - lon1_rad

    a = (
        np.sin(dlat / 2) ** 2
        + np.cos(lat1_rad) * np.cos(lat2_rad) * np.sin(dlon / 2) ** 2
    )
    c = 2 * np.arctan2(np.sqrt(a), np.sqrt(1 - a))
    distance = R * c

    return float(distance)


def compute_threat_contribution(
    entity_lat: float,
    entity_lon: float,
    event: Event,
    lambda_d: float = 0.005,
) -> float:
    """
    Compute threat contribution Phi_e(i,t) from single event to entity.

    Implements:
    Phi_e(i,t) = M_e * Sev_e * Conf_e * exp(-lambda_d * d(i,e)) * exp(-lambda_t * Delta_t_e)

    Args:
        entity_lat: Entity latitude (degrees)
        entity_lon: Entity longitude (degrees)
        event: Event object with severity, confidence, location, and age
        lambda_d: Spatial decay rate (default 0.005)

    Returns:
        Threat contribution in [0, 1]
    """
    # Get event multiplier M_e
    M_e = EVENT_MULTIPLIERS.get(event.event_type, 1.0)

    # Get severity Sev_e and confidence Conf_e
    Sev_e = np.clip(event.severity, 0.0, 1.0)
    Conf_e = np.clip(event.confidence, 0.0, 1.0)

    # Compute spatial decay exp(-lambda_d * d)
    distance_km = haversine_distance(
        entity_lat, entity_lon, event.latitude, event.longitude
    )
    spatial_decay = np.exp(-lambda_d * distance_km)

    # Compute temporal decay exp(-lambda_t * Delta_t)
    # Use different decay rate for hard vs soft events
    lambda_t = TEMPORAL_DECAY_SEVERE if event.is_hard_event else TEMPORAL_DECAY_SOFT
    temporal_decay = np.exp(-lambda_t * event.hours_ago)

    # Compute threat contribution
    threat = M_e * Sev_e * Conf_e * spatial_decay * temporal_decay

    return float(np.clip(threat, 0.0, 1.0))


def compute_geopolitical_threat(
    entity_lat: float,
    entity_lon: float,
    events: List[Event],
    lambda_d: float = 0.005,
) -> float:
    """
    Compute aggregated geopolitical threat field at entity location.

    Implements:
    G_i(t) = sum over all active events e of Phi_e(i,t)

    Args:
        entity_lat: Entity latitude (degrees)
        entity_lon: Entity longitude (degrees)
        events: List of Event objects affecting the region
        lambda_d: Spatial decay rate (default 0.005 per km)

    Returns:
        Aggregated threat score in [0, inf) (unbounded sum)
    """
    if not events:
        return 0.0

    # Sum threat contributions from all events
    total_threat = sum(
        compute_threat_contribution(entity_lat, entity_lon, event, lambda_d)
        for event in events
    )

    return float(total_threat)


def compute_threat_gradient(
    entity_lat: float,
    entity_lon: float,
    events: List[Event],
    lambda_d: float = 0.005,
    delta_km: float = 50.0,
) -> Tuple[float, float]:
    """
    Compute spatial gradient of threat field at entity location.

    Estimates dG/dlat and dG/dlon using finite differences.

    Args:
        entity_lat: Entity latitude (degrees)
        entity_lon: Entity longitude (degrees)
        events: List of Event objects
        lambda_d: Spatial decay rate
        delta_km: Distance for finite difference calculation (default 50 km)

    Returns:
        Tuple of (dG/dlat, dG/dlon) approximations
    """
    # Approximate 1 degree latitude as 111 km
    delta_lat = delta_km / 111.0

    # Approximate 1 degree longitude as 111*cos(lat) km
    delta_lon = delta_km / (111.0 * np.cos(np.radians(entity_lat)))

    # Compute threat at shifted locations
    G_center = compute_geopolitical_threat(entity_lat, entity_lon, events, lambda_d)
    G_north = compute_geopolitical_threat(
        entity_lat + delta_lat, entity_lon, events, lambda_d
    )
    G_east = compute_geopolitical_threat(
        entity_lat, entity_lon + delta_lon, events, lambda_d
    )

    # Finite difference approximation
    dG_dlat = (G_north - G_center) / delta_lat if delta_lat > 0 else 0.0
    dG_dlon = (G_east - G_center) / delta_lon if delta_lon > 0 else 0.0

    return (float(dG_dlat), float(dG_dlon))
