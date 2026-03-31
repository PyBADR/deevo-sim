"""
GCC weight configuration for mathematical core.

Provides all canonical weights used in GCC risk, centrality, logistics, disruption,
and uncertainty calculations. Per-asset-class weight vectors are preserved exactly.
"""

# Per-asset-class GCC default weights for risk equation:
# R_i(t) = w1*G + w2*P + w3*N + w4*L + w5*T + w6*U
AIRPORT_WEIGHTS = [0.27, 0.16, 0.19, 0.17, 0.11, 0.10]
SEAPORT_WEIGHTS = [0.24, 0.14, 0.22, 0.23, 0.09, 0.08]
AIR_CORRIDOR_WEIGHTS = [0.28, 0.13, 0.21, 0.20, 0.10, 0.08]
MARITIME_CORRIDOR_WEIGHTS = [0.30, 0.12, 0.20, 0.24, 0.08, 0.06]
ROAD_HUB_WEIGHTS = [0.25, 0.18, 0.20, 0.19, 0.10, 0.08]
RAIL_HUB_WEIGHTS = [0.26, 0.15, 0.21, 0.20, 0.11, 0.07]
WAREHOUSE_WEIGHTS = [0.22, 0.20, 0.18, 0.22, 0.10, 0.08]
PIPELINE_WEIGHTS = [0.23, 0.17, 0.19, 0.25, 0.09, 0.07]

# Map asset class to weights
ASSET_CLASS_WEIGHTS = {
    "airport": AIRPORT_WEIGHTS,
    "seaport": SEAPORT_WEIGHTS,
    "port": SEAPORT_WEIGHTS,
    "air_corridor": AIR_CORRIDOR_WEIGHTS,
    "maritime_corridor": MARITIME_CORRIDOR_WEIGHTS,
    "road_hub": ROAD_HUB_WEIGHTS,
    "rail_hub": RAIL_HUB_WEIGHTS,
    "warehouse": WAREHOUSE_WEIGHTS,
    "pipeline": PIPELINE_WEIGHTS,
}

# GCC event multipliers: M_e values for Phi_e(i,t)
EVENT_MULTIPLIERS = {
    "missile_strike": 1.40,
    "naval_attack": 1.40,
    "port_closure": 1.35,
    "chokepoint_threat": 1.35,
    "airport_shutdown": 1.30,
    "protest_civil_unrest": 0.75,
    "rumor_unverified": 0.40,
}

# Network centrality weights: alpha1*Betweenness + alpha2*Degree + alpha3*FlowShare + alpha4*ChokepointDependency
CENTRALITY_WEIGHTS = {
    "betweenness": 0.30,
    "degree": 0.15,
    "flow_share": 0.30,
    "chokepoint_dep": 0.25,
}

# Logistics pressure weights: beta1*Q + beta2*Delay + beta3*ReRouteCost + beta4*CapacityStress
LOGISTICS_WEIGHTS = {
    "queue": 0.25,
    "delay": 0.25,
    "reroute_cost": 0.30,
    "capacity_stress": 0.20,
}

# Disruption weights: v1*R + v2*C + v3*A + v4*K + v5*B
DISRUPTION_WEIGHTS = {
    "risk": 0.28,
    "congestion": 0.22,
    "accessibility": 0.18,
    "reroute": 0.22,
    "barrier": 0.10,
}

# Uncertainty weights: eta1*SourceQuality + eta2*CrossValidation + eta3*DataFreshness + eta4*SignalAgreement
UNCERTAINTY_WEIGHTS = {
    "source_quality": 0.30,
    "cross_validation": 0.30,
    "data_freshness": 0.20,
    "signal_agreement": 0.20,
}

# Temporal decay rates
TEMPORAL_DECAY_SEVERE = 0.015  # per hour for kinetic/missile/airspace events
TEMPORAL_DECAY_SOFT = 0.035    # per hour for soft signals

# Spatial decay lambda values
SPATIAL_DECAY_LAMBDA = (0.0035, 0.006)  # range per km, smaller for chokepoint sensitivity

# Sigmoid offset for normalization (GCC calibration)
SIGMOID_OFFSET = 2.5

# Sigmoid scale for normalization (GCC calibration)
SIGMOID_SCALE = 40.0
