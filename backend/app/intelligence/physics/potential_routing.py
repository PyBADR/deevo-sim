"""
Potential Field Routing for GCC Decision Intelligence Platform.

Physics metaphor: Route cost is modeled as an energy functional combining
distance, time, threat exposure (potential field integral), friction, and
congestion. Optimal routing minimizes this energy functional.

The route cost formula:
    J_r = theta1 * Distance_r + theta2 * Time_r + theta3 * integral(Phi(s) ds)
          + theta4 * mu_r + theta5 * Congestion_r

GCC defaults:
    theta1 = 0.18 (distance weight)
    theta2 = 0.22 (time weight)
    theta3 = 0.28 (threat integral weight)
    theta4 = 0.20 (friction weight)
    theta5 = 0.12 (congestion weight)
"""

from dataclasses import dataclass, field
from typing import List, Dict, Tuple, Optional
from enum import Enum
import numpy as np


class ViabilityClass(Enum):
    """Route viability classification."""
    OPTIMAL = "optimal"
    ACCEPTABLE = "acceptable"
    DEGRADED = "degraded"
    NON_VIABLE = "non_viable"


@dataclass
class RouteCostComponents:
    """Individual cost components for a route."""
    distance_cost: float
    time_cost: float
    threat_integral: float
    friction: float
    congestion: float


@dataclass
class RouteCostResult:
    """Result of route cost computation."""
    route_id: str
    total_cost: float
    components: RouteCostComponents
    cost_breakdown_pct: Dict[str, float] = field(default_factory=dict)
    viability_class: ViabilityClass = ViabilityClass.ACCEPTABLE


@dataclass
class OptimalRouteResult:
    """Result of optimal route selection from candidates."""
    best_route_id: str
    best_route_cost: float
    all_routes_ranked: List[Tuple[str, float]] = field(default_factory=list)
    alternatives: List[Dict] = field(default_factory=list)
    analysis_timestamp: str = ""


def classify_viability(total_cost: float) -> ViabilityClass:
    """
    Classify route viability based on total cost.
    
    Args:
        total_cost: Total route cost
        
    Returns:
        ViabilityClass enum value
    """
    if total_cost < 0.40:
        return ViabilityClass.OPTIMAL
    elif total_cost < 0.65:
        return ViabilityClass.ACCEPTABLE
    elif total_cost < 0.90:
        return ViabilityClass.DEGRADED
    else:
        return ViabilityClass.NON_VIABLE


def compute_route_cost(
    distance: float,
    time: float,
    threat_integral: float,
    friction: float,
    congestion: float,
    theta1: float = 0.18,
    theta2: float = 0.22,
    theta3: float = 0.28,
    theta4: float = 0.20,
    theta5: float = 0.12,
    route_id: str = "default"
) -> RouteCostResult:
    """
    Compute route cost using GCC potential field formula.
    
    Formula:
        J_r = theta1 * Distance_r + theta2 * Time_r + theta3 * integral(Phi(s) ds)
              + theta4 * mu_r + theta5 * Congestion_r
    
    All input parameters should be normalized to [0, 1] for consistent scaling,
    except distance and time which are in their natural units (km, hours).
    
    Args:
        distance: Route distance in km
        time: Route travel time in hours
        threat_integral: Integrated threat along route [0, inf)
        friction: Route friction coefficient [0, 1]
        congestion: Route congestion level [0, 1]
        theta1: Distance weight [default: 0.18]
        theta2: Time weight [default: 0.22]
        theta3: Threat integral weight [default: 0.28]
        theta4: Friction weight [default: 0.20]
        theta5: Congestion weight [default: 0.12]
        route_id: Unique identifier for the route
        
    Returns:
        RouteCostResult with total cost and component breakdown
    """
    # Normalize distance and time to [0, 1] using typical scales
    # Typical distance: 0-5000 km, Time: 0-100 hours
    normalized_distance = np.clip(distance / 5000.0, 0.0, 1.0)
    normalized_time = np.clip(time / 100.0, 0.0, 1.0)
    
    # Normalize threat integral (unbounded, use exponential saturation)
    # e^(-x) saturates threat to prevent dominance
    normalized_threat = 1.0 - np.exp(-threat_integral)
    
    # Compute weighted components
    distance_component = theta1 * normalized_distance
    time_component = theta2 * normalized_time
    threat_component = theta3 * normalized_threat
    friction_component = theta4 * friction
    congestion_component = theta5 * congestion
    
    # Compute total cost
    total_cost = (
        distance_component +
        time_component +
        threat_component +
        friction_component +
        congestion_component
    )
    
    # Create components dataclass
    components = RouteCostComponents(
        distance_cost=distance_component,
        time_cost=time_component,
        threat_integral=threat_component,
        friction=friction_component,
        congestion=congestion_component
    )
    
    # Compute cost breakdown percentages
    total_for_pct = sum([
        distance_component, time_component, threat_component,
        friction_component, congestion_component
    ])
    
    if total_for_pct > 0:
        cost_breakdown_pct = {
            "distance": 100.0 * distance_component / total_for_pct,
            "time": 100.0 * time_component / total_for_pct,
            "threat": 100.0 * threat_component / total_for_pct,
            "friction": 100.0 * friction_component / total_for_pct,
            "congestion": 100.0 * congestion_component / total_for_pct
        }
    else:
        cost_breakdown_pct = {
            "distance": 0.0,
            "time": 0.0,
            "threat": 0.0,
            "friction": 0.0,
            "congestion": 0.0
        }
    
    # Classify viability
    viability_class = classify_viability(total_cost)
    
    return RouteCostResult(
        route_id=route_id,
        total_cost=total_cost,
        components=components,
        cost_breakdown_pct=cost_breakdown_pct,
        viability_class=viability_class
    )


def find_optimal_route(
    candidate_routes: List[Dict],
    theta1: float = 0.18,
    theta2: float = 0.22,
    theta3: float = 0.28,
    theta4: float = 0.20,
    theta5: float = 0.12
) -> OptimalRouteResult:
    """
    Evaluate candidate routes and return optimal selection.
    
    Args:
        candidate_routes: List of route dictionaries with keys:
                         - route_id: str
                         - distance: float (km)
                         - time: float (hours)
                         - threat_integral: float
                         - friction: float [0, 1]
                         - congestion: float [0, 1]
        theta1: Distance weight [default: 0.18]
        theta2: Time weight [default: 0.22]
        theta3: Threat integral weight [default: 0.28]
        theta4: Friction weight [default: 0.20]
        theta5: Congestion weight [default: 0.12]
        
    Returns:
        OptimalRouteResult with best route and ranked alternatives
    """
    if not candidate_routes:
        raise ValueError("No candidate routes provided")
    
    # Evaluate all routes
    route_results = []
    for route in candidate_routes:
        result = compute_route_cost(
            distance=route["distance"],
            time=route["time"],
            threat_integral=route["threat_integral"],
            friction=route["friction"],
            congestion=route["congestion"],
            theta1=theta1,
            theta2=theta2,
            theta3=theta3,
            theta4=theta4,
            theta5=theta5,
            route_id=route["route_id"]
        )
        route_results.append(result)
    
    # Sort by total cost (ascending)
    sorted_results = sorted(route_results, key=lambda x: x.total_cost)
    
    # Build ranked list
    all_routes_ranked = [
        (r.route_id, r.total_cost)
        for r in sorted_results
    ]
    
    # Build alternatives list (top 3 besides best)
    alternatives = []
    for i, result in enumerate(sorted_results[1:4]):
        alternatives.append({
            "rank": i + 2,
            "route_id": result.route_id,
            "total_cost": result.total_cost,
            "viability_class": result.viability_class.value,
            "cost_breakdown_pct": result.cost_breakdown_pct
        })
    
    # Best route is first in sorted list
    best = sorted_results[0]
    
    return OptimalRouteResult(
        best_route_id=best.route_id,
        best_route_cost=best.total_cost,
        all_routes_ranked=all_routes_ranked,
        alternatives=alternatives
    )


def compute_threat_integral_along_route(
    route_waypoints: List[Tuple[float, float]],
    threat_field
) -> float:
    """
    Compute integrated threat along a route using trapezoidal integration.
    
    Physics model: Threat integral represents cumulative threat exposure:
        integral = sum_{i=0}^{n-1} [ (threat_i + threat_{i+1})/2 * distance_i ]
    
    This models the total "threat energy" accumulated along the path.
    
    Args:
        route_waypoints: List of (lat, lon) tuples defining the route path
        threat_field: ThreatField instance with evaluate(lat, lon) method
        
    Returns:
        Integrated threat value along route [0, inf)
    """
    if not route_waypoints or len(route_waypoints) == 0:
        return 0.0
    
    if len(route_waypoints) == 1:
        # Single point: threat at that point
        lat, lon = route_waypoints[0]
        return threat_field.evaluate(lat, lon)
    
    # Integrate threat along path using trapezoidal rule
    threat_integral = 0.0
    for i in range(len(route_waypoints) - 1):
        lat1, lon1 = route_waypoints[i]
        lat2, lon2 = route_waypoints[i + 1]
        
        # Threat at endpoints
        threat1 = threat_field.evaluate(lat1, lon1)
        threat2 = threat_field.evaluate(lat2, lon2)
        
        # Approximate segment distance in km
        # 1 degree ~ 111 km at equator
        dx_km = (lat2 - lat1) * 111.0
        dy_km = (lon2 - lon1) * 111.0 * np.cos(np.radians((lat1 + lat2) / 2))
        segment_distance_km = np.sqrt(dx_km * dx_km + dy_km * dy_km)
        
        # Trapezoidal integration
        threat_integral += (threat1 + threat2) / 2.0 * segment_distance_km
    
    return float(threat_integral)
