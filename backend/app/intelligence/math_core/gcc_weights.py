"""
GCC asset-class risk weights for the canonical risk equation.

R_i(t) = w1*G + w2*P + w3*N + w4*L + w5*T + w6*U

Weights are calibrated per asset class for GCC infrastructure.
Sigmoid parameters for score normalization.
"""

# Per-asset-class weight vectors: (w1_geo, w2_prox, w3_central, w4_logistics, w5_temporal, w6_uncertainty)
AIRPORT_WEIGHTS = (0.25, 0.20, 0.15, 0.20, 0.10, 0.10)

ASSET_CLASS_WEIGHTS = {
    "airport": AIRPORT_WEIGHTS,
    "seaport": (0.20, 0.25, 0.15, 0.25, 0.08, 0.07),
    "port": (0.20, 0.25, 0.15, 0.25, 0.08, 0.07),
    "air_corridor": (0.30, 0.15, 0.10, 0.20, 0.15, 0.10),
    "maritime_corridor": (0.25, 0.20, 0.10, 0.25, 0.12, 0.08),
    "oil_facility": (0.25, 0.15, 0.20, 0.20, 0.10, 0.10),
    "refinery": (0.20, 0.15, 0.20, 0.25, 0.10, 0.10),
    "pipeline": (0.20, 0.20, 0.15, 0.25, 0.10, 0.10),
    "bank": (0.15, 0.10, 0.25, 0.15, 0.15, 0.20),
    "insurer": (0.15, 0.10, 0.20, 0.15, 0.15, 0.25),
    "fintech": (0.10, 0.10, 0.25, 0.15, 0.15, 0.25),
    "exchange": (0.15, 0.10, 0.25, 0.15, 0.15, 0.20),
    "central_bank": (0.20, 0.10, 0.25, 0.10, 0.15, 0.20),
}

# Disruption score weights (v1*R + v2*C + v3*A + v4*K + v5*B)
# Calibrated for GCC critical infrastructure
DISRUPTION_WEIGHTS = {
    "recovery_capacity": 0.20,
    "criticality": 0.30,
    "accessibility": 0.15,
    "knock_on_propagation": 0.25,
    "buffer_capacity": 0.10,
}

# Sigmoid normalization parameters
SIGMOID_SCALE = 10.0   # Steepness of sigmoid curve
SIGMOID_OFFSET = 5.0   # Horizontal shift (midpoint)
