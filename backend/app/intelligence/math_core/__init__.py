"""
GCC (Global Critical Infrastructure) Risk Assessment Mathematical Core.

Provides complete mathematical framework for multi-dimensional risk assessment
with temporal persistence, network centrality, logistics pressure, geopolitical
threats, and uncertainty quantification.

All modules implement exact GCC specifications with preserved default parameters.
"""

# Temporal Persistence Module
from .temporal_persistence import (
    TemporalEvent,
    compute_temporal_persistence,
    compute_event_temporal_weight,
    compute_event_half_life,
    compute_time_weighted_severity,
    compute_aggregated_severity,
)

# Logistics Pressure Module
from .logistics_pressure import (
    LogisticsMetrics,
    compute_logistics_pressure,
    normalize_queue_depth,
    normalize_delay,
    compute_reroute_cost_factor,
    compute_capacity_stress,
)

# Network Centrality Module
from .network_centrality import (
    CentralityMetrics,
    compute_network_centrality,
    normalize_centrality_metric,
    compute_betweenness_centrality,
    compute_degree_centrality,
    compute_flow_share,
    compute_chokepoint_dependency,
)

# Proximity Module
from .proximity import (
    haversine_distance,
    compute_proximity_score,
    compute_proximity_continuous,
)

# Geopolitical Threat Module
from .geopolitical_threat import (
    Event,
    compute_threat_contribution,
    compute_geopolitical_threat,
    compute_threat_gradient,
)

# Uncertainty Module
from .uncertainty import (
    UncertaintyMetrics,
    compute_uncertainty,
    compute_source_quality,
    compute_cross_validation,
    compute_freshness,
    compute_signal_agreement,
)

# Disruption Score Module
from .disruption_score import (
    DisruptionMetrics,
    compute_disruption_score,
    compute_recovery_capacity,
    compute_criticality,
    compute_accessibility,
    compute_knock_on_propagation,
    compute_buffer_capacity,
)

# Exposure Score Module
from .exposure_score import (
    ExposureMetrics,
    compute_exposure_score,
    compute_herfindahl_index,
    compute_herfindahl_normalized,
    compute_supplier_diversity,
    compute_geographic_concentration,
    compute_diversification_index,
)

# Scenario Delta Module
from .scenario_delta import (
    ScenarioState,
    ScenarioDelta,
    compute_relative_delta,
    compute_absolute_delta,
    compute_scenario_delta,
    compute_impact_magnitude,
    compute_shock_severity,
)

# Calibration Module
from .calibration import (
    CalibrationMetrics,
    CalibrationResults,
    CalibrationEngine,
)

# State Vector Module
from .state_vector import (
    EntityStateVector,
    compute_state_vector,
    compute_state_vector_from_dict,
    merge_state_vectors,
)

__all__ = [
    # Temporal Persistence
    "TemporalEvent",
    "compute_temporal_persistence",
    "compute_event_temporal_weight",
    "compute_event_half_life",
    "compute_time_weighted_severity",
    "compute_aggregated_severity",
    # Logistics Pressure
    "LogisticsMetrics",
    "compute_logistics_pressure",
    "normalize_queue_depth",
    "normalize_delay",
    "compute_reroute_cost_factor",
    "compute_capacity_stress",
    # Network Centrality
    "CentralityMetrics",
    "compute_network_centrality",
    "normalize_centrality_metric",
    "compute_betweenness_centrality",
    "compute_degree_centrality",
    "compute_flow_share",
    "compute_chokepoint_dependency",
    # Proximity
    "haversine_distance",
    "compute_proximity_score",
    "compute_proximity_continuous",
    # Geopolitical Threat
    "Event",
    "compute_threat_contribution",
    "compute_geopolitical_threat",
    "compute_threat_gradient",
    # Uncertainty
    "UncertaintyMetrics",
    "compute_uncertainty",
    "compute_source_quality",
    "compute_cross_validation",
    "compute_freshness",
    "compute_signal_agreement",
    # Disruption Score
    "DisruptionMetrics",
    "compute_disruption_score",
    "compute_recovery_capacity",
    "compute_criticality",
    "compute_accessibility",
    "compute_knock_on_propagation",
    "compute_buffer_capacity",
    # Exposure Score
    "ExposureMetrics",
    "compute_exposure_score",
    "compute_herfindahl_index",
    "compute_herfindahl_normalized",
    "compute_supplier_diversity",
    "compute_geographic_concentration",
    "compute_diversification_index",
    # Scenario Delta
    "ScenarioState",
    "ScenarioDelta",
    "compute_relative_delta",
    "compute_absolute_delta",
    "compute_scenario_delta",
    "compute_impact_magnitude",
    "compute_shock_severity",
    # Calibration
    "CalibrationMetrics",
    "CalibrationResults",
    "CalibrationEngine",
    # State Vector
    "EntityStateVector",
    "compute_state_vector",
    "compute_state_vector_from_dict",
    "merge_state_vectors",
]
