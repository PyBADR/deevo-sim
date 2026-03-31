"""
Route Friction/Resistance Model for GCC Decision Intelligence Platform.

Physics metaphor: Friction represents resistance to movement along a route,
analogous to physical friction in mechanics. Multiple factors contribute:
threat along route, congestion, political constraints, regulatory restrictions.

The friction model computes:
    mu_r(t) = mu0 + mu1 * ThreatAlongRoute_r + mu2 * Congestion_r
              + mu3 * PoliticalConstraint_r + mu4 * RegulatoryRestriction_r

GCC defaults:
    mu0 = 0.10 (base friction)
    mu1 = 0.35 (threat)
    mu2 = 0.25 (congestion)
    mu3 = 0.25 (political constraint)
    mu4 = 0.15 (regulatory restriction)
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional
from enum import Enum
import numpy as np


class FrictionClass(Enum):
    """Qualitative friction level categories."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class RouteFriction:
    """Friction components for a single route."""
    route_id: str
    base_friction: float
    threat_component: float
    congestion_component: float
    political_component: float
    regulatory_component: float

    def total_friction(self) -> float:
        """Compute total friction as sum of all components."""
        return (
            self.base_friction +
            self.threat_component +
            self.congestion_component +
            self.political_component +
            self.regulatory_component
        )


@dataclass
class FrictionResult:
    """Result of friction computation for a route."""
    route_id: str
    total_friction: float
    components: Dict[str, float] = field(default_factory=dict)
    friction_class: FrictionClass = FrictionClass.LOW
    
    def __post_init__(self):
        """Ensure components are populated if not provided."""
        if not self.components:
            self.components = {}


def classify_friction(total_friction: float) -> FrictionClass:
    """
    Classify friction level based on magnitude.
    
    Args:
        total_friction: Total friction value
        
    Returns:
        FrictionClass enum value
    """
    if total_friction < 0.35:
        return FrictionClass.LOW
    elif total_friction < 0.60:
        return FrictionClass.MEDIUM
    elif total_friction < 0.85:
        return FrictionClass.HIGH
    else:
        return FrictionClass.CRITICAL


def compute_friction(
    route_id: str,
    threat_along_route: float,
    congestion: float,
    political_constraint: float,
    regulatory_restriction: float,
    mu0: float = 0.10,
    mu1: float = 0.35,
    mu2: float = 0.25,
    mu3: float = 0.25,
    mu4: float = 0.15
) -> FrictionResult:
    """
    Compute route friction using GCC formula.
    
    Formula:
        mu_r = mu0 + mu1 * ThreatAlongRoute_r + mu2 * Congestion_r
               + mu3 * PoliticalConstraint_r + mu4 * RegulatoryRestriction_r
    
    All input parameters should be normalized to [0, 1] for consistent scaling.
    
    Args:
        route_id: Unique identifier for the route
        threat_along_route: Threat level along route [0, 1]
        congestion: Congestion level on route [0, 1]
        political_constraint: Political constraint factor [0, 1]
        regulatory_restriction: Regulatory restriction factor [0, 1]
        mu0: Base friction coefficient [default: 0.10]
        mu1: Threat weight coefficient [default: 0.35]
        mu2: Congestion weight coefficient [default: 0.25]
        mu3: Political constraint weight coefficient [default: 0.25]
        mu4: Regulatory restriction weight coefficient [default: 0.15]
        
    Returns:
        FrictionResult with total friction and component breakdown
    """
    # Validate input parameters are in [0, 1]
    for param_name, param_value in [
        ("threat_along_route", threat_along_route),
        ("congestion", congestion),
        ("political_constraint", political_constraint),
        ("regulatory_restriction", regulatory_restriction)
    ]:
        if not (0 <= param_value <= 1):
            raise ValueError(f"{param_name} must be in [0, 1], got {param_value}")
    
    # Compute weighted components
    threat_component = mu1 * threat_along_route
    congestion_component = mu2 * congestion
    political_component = mu3 * political_constraint
    regulatory_component = mu4 * regulatory_restriction
    
    # Compute total friction
    total_friction = (
        mu0 +
        threat_component +
        congestion_component +
        political_component +
        regulatory_component
    )
    
    # Classify friction level
    friction_class = classify_friction(total_friction)
    
    # Build components dictionary
    components = {
        "base_friction": mu0,
        "threat_component": threat_component,
        "congestion_component": congestion_component,
        "political_component": political_component,
        "regulatory_component": regulatory_component
    }
    
    return FrictionResult(
        route_id=route_id,
        total_friction=total_friction,
        components=components,
        friction_class=friction_class
    )


def batch_compute_friction(
    routes: List[Dict],
    mu0: float = 0.10,
    mu1: float = 0.35,
    mu2: float = 0.25,
    mu3: float = 0.25,
    mu4: float = 0.15
) -> List[FrictionResult]:
    """
    Compute friction for multiple routes in batch.
    
    Args:
        routes: List of dictionaries with keys:
                - route_id: str
                - threat_along_route: float [0, 1]
                - congestion: float [0, 1]
                - political_constraint: float [0, 1]
                - regulatory_restriction: float [0, 1]
        mu0: Base friction coefficient [default: 0.10]
        mu1: Threat weight coefficient [default: 0.35]
        mu2: Congestion weight coefficient [default: 0.25]
        mu3: Political constraint weight coefficient [default: 0.25]
        mu4: Regulatory restriction weight coefficient [default: 0.15]
        
    Returns:
        List of FrictionResult objects for all routes
    """
    results = []
    for route in routes:
        result = compute_friction(
            route_id=route["route_id"],
            threat_along_route=route["threat_along_route"],
            congestion=route["congestion"],
            political_constraint=route["political_constraint"],
            regulatory_restriction=route["regulatory_restriction"],
            mu0=mu0,
            mu1=mu1,
            mu2=mu2,
            mu3=mu3,
            mu4=mu4
        )
        results.append(result)
    
    return results
