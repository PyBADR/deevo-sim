"""
Impact Observatory | مرصد الأثر
Simulation constants — single source of truth for all formula weights.

All mathematical constants are defined here as module-level names.
Risk models, physics layer, and decision layer MUST import constants
from this module — never hardcode weights inline.

Formula reference:
  Es  = w1*I  + w2*D  + w3*U  + w4*G
  Exp = alpha_j * Es * V_j * C_j
  X_t+1 = beta*P*X_t + (1-beta)*X_t + S_t
  LSI = l1*W  + l2*F  + l3*M  + l4*C
  ISI = m1*Cf + m2*LR + m3*Re + m4*Od
  NL  = (Exp) * IF_jt * AssetBase_j * theta_j
  Conf= r1*DQ + r2*MC + r3*HS + r4*ST
  URS = g1*Es + g2*AvgExp + g3*AvgStress + g4*PS + g5*LN
"""
from __future__ import annotations

from src.core.config import settings  # noqa: F401

__all__ = ["settings"]

# ═══════════════════════════════════════════════════════════════════════════════
# Event Severity Model
# Es = w1*I + w2*D + w3*U + w4*G
#   I = infrastructure impact score    (node count proxy)
#   D = disruption scale               (base severity)
#   U = utilization stress             (cross-sector activation)
#   G = geopolitical amplification     (regional multiplier)
# ═══════════════════════════════════════════════════════════════════════════════
ES_W1: float = 0.25   # infrastructure impact weight
ES_W2: float = 0.30   # disruption scale weight
ES_W3: float = 0.20   # utilization stress weight
ES_W4: float = 0.25   # geopolitical amplification weight

# Maximum number of shock nodes used for normalization
ES_MAX_SHOCK_NODES: int = 10

# ═══════════════════════════════════════════════════════════════════════════════
# Sector Exposure Model
# Exposure_j = alpha_j * Es * V_j * C_j
#   alpha_j = sector sensitivity coefficient
#   V_j     = vulnerability (1.0 direct, 0.70 indirect, 0.35 second-hop)
#   C_j     = connectivity factor (shock_count / alpha normalizer)
# ═══════════════════════════════════════════════════════════════════════════════
SECTOR_ALPHA: dict[str, float] = {
    "energy":         0.28,
    "maritime":       0.18,
    "banking":        0.20,
    "insurance":      0.08,
    "fintech":        0.06,
    "logistics":      0.10,
    "infrastructure": 0.05,
    "government":     0.03,
    "healthcare":     0.02,
}

# Vulnerability: direct shock / first-hop / second-hop
EXPOSURE_V_DIRECT: float = 1.00
EXPOSURE_V_INDIRECT: float = 0.70
EXPOSURE_V_SECOND_HOP: float = 0.35
EXPOSURE_V_DEFAULT: float = 0.10

# ═══════════════════════════════════════════════════════════════════════════════
# Propagation Model
# X_(t+1) = beta * P * X_t + (1 - beta) * X_t + S_t
#   beta   = propagation coupling coefficient
#   P      = adjacency matrix (row-normalised)
#   X_t    = state vector at time t
#   S_t    = external shock injection at time t (decays with PROP_LAMBDA)
# ═══════════════════════════════════════════════════════════════════════════════
PROP_BETA: float = 0.65     # propagation coupling coefficient
PROP_LAMBDA: float = 0.05   # shock injection decay rate
PROP_CUTOFF: float = 0.005  # early-exit threshold (all nodes below this → stop)

# ═══════════════════════════════════════════════════════════════════════════════
# Liquidity Stress Index
# LSI = l1*W + l2*F + l3*M + l4*C
#   W = withdrawal pressure  (severity × banking_exposure × outflow_rate)
#   F = foreign exposure     (severity × GCC_foreign_dependency)
#   M = market stress        (banking + fintech sector exposure avg)
#   C = collateral stress    (severity × (1 - CAR_buffer))
# ═══════════════════════════════════════════════════════════════════════════════
LSI_L1: float = 0.30   # withdrawal pressure weight
LSI_L2: float = 0.25   # foreign exposure weight
LSI_L3: float = 0.25   # market stress weight
LSI_L4: float = 0.20   # collateral stress weight

# Basel III thresholds
LSI_BASE_OUTFLOW_RATE: float = 0.25
LSI_BANKING_OUTFLOW_COEFF: float = 0.50
LSI_FINTECH_OUTFLOW_COEFF: float = 0.15
LSI_SOVEREIGN_BUFFER: float = 0.85       # GCC sovereign buffer factor
LSI_CAR_BASE: float = 0.105              # minimum CAR ratio
LSI_LCR_SEVERITY_COEFF: float = 0.65    # LCR degrades by this × severity
LSI_GCC_FOREIGN_DEPENDENCY: float = 0.35  # fraction of banking assets foreign

# ═══════════════════════════════════════════════════════════════════════════════
# Insurance Stress Index
# ISI = m1*Cf + m2*LR + m3*Re + m4*Od
#   Cf = claims frequency index      (normalised surge factor)
#   LR = loss ratio                  (0.55 + severity*0.35)
#   Re = reserve erosion             (severity × (1 - reserve_adequacy))
#   Od = operational disruption      (severity × insurance_exposure)
# ═══════════════════════════════════════════════════════════════════════════════
ISI_M1: float = 0.30   # claims frequency weight
ISI_M2: float = 0.30   # loss ratio weight
ISI_M3: float = 0.25   # reserve erosion weight
ISI_M4: float = 0.15   # operational disruption weight

# IFRS-17 thresholds
ISI_CLAIMS_SURGE_COEFF: float = 2.5     # multiplier at max severity
ISI_BASE_LOSS_RATIO: float = 0.55
ISI_SEVERITY_LR_COEFF: float = 0.35
ISI_EXPENSE_RATIO: float = 0.28
ISI_RESERVE_RATIO: float = 0.18         # minimum reserve requirement
ISI_REINSURANCE_COVERAGE: float = 0.60  # GCC average cession rate
ISI_MAX_CLAIMS_SURGE: float = 3.5       # normalisation denominator for Cf

# ═══════════════════════════════════════════════════════════════════════════════
# Financial Loss Model
# NormalizedLoss_j = Exposure_j * ImpactFactor_(j,t) * AssetBase_j * theta_j
#   Exposure_j     = sector exposure score (0–1)
#   ImpactFactor   = severity^2 × prop_factor
#   AssetBase_j    = fraction of scenario base loss allocated to sector j
#   theta_j        = sector loss amplification factor
# ═══════════════════════════════════════════════════════════════════════════════
SECTOR_THETA: dict[str, float] = {
    "energy":         1.40,
    "maritime":       1.20,
    "banking":        1.15,
    "insurance":      1.10,
    "logistics":      1.05,
    "fintech":        1.08,
    "infrastructure": 1.03,
    "government":     1.00,
    "healthcare":     1.00,
}

# Sector base loss allocation fractions (must sum to ≤ 1.0)
SECTOR_LOSS_ALLOCATION: dict[str, float] = {
    "energy":         0.30,
    "maritime":       0.20,
    "banking":        0.18,
    "insurance":      0.10,
    "logistics":      0.08,
    "fintech":        0.06,
    "infrastructure": 0.05,
    "government":     0.02,
    "healthcare":     0.01,
}

# ═══════════════════════════════════════════════════════════════════════════════
# Confidence Score
# Conf = r1*DQ + r2*MC + r3*HS + r4*ST
#   DQ = data quality          (degrades at extreme severities)
#   MC = model coverage        (higher for well-calibrated scenarios)
#   HS = historical similarity (known scenarios have precedent)
#   ST = scenario tractability (degrades with shock node count)
# ═══════════════════════════════════════════════════════════════════════════════
CONF_R1: float = 0.30   # data quality weight
CONF_R2: float = 0.25   # model coverage weight
CONF_R3: float = 0.25   # historical similarity weight
CONF_R4: float = 0.20   # scenario tractability weight

# Well-calibrated GCC scenarios (get higher MC and HS scores)
CONF_WELL_KNOWN_SCENARIOS: frozenset[str] = frozenset({
    "hormuz_chokepoint_disruption",
    "uae_banking_crisis",
    "gcc_cyber_attack",
    "saudi_oil_shock",
    "qatar_lng_disruption",
    "bahrain_sovereign_stress",
    "kuwait_fiscal_shock",
    "oman_port_closure",
})
CONF_DQ_EXTREME_PENALTY: float = 0.40   # penalty factor at extreme severities
CONF_MC_WELL_KNOWN: float = 0.92
CONF_MC_UNKNOWN: float = 0.72
CONF_HS_WELL_KNOWN: float = 0.88
CONF_HS_UNKNOWN: float = 0.65
CONF_ST_NODE_PENALTY: float = 0.04     # per additional shock node beyond first
CONF_ST_MIN: float = 0.55
CONF_ST_MAX: float = 0.97

# ═══════════════════════════════════════════════════════════════════════════════
# Unified Risk Score
# URS = g1*Es + g2*AvgExposure + g3*AvgStress + g4*PropagationScore + g5*LossNorm
#   Es              = event severity score
#   AvgExposure     = mean sector exposure
#   AvgStress       = mean(LSI, ISI)
#   PropagationScore = normalised propagation intensity
#   LossNorm        = severity² (proxy for normalized financial loss)
# ═══════════════════════════════════════════════════════════════════════════════
URS_G1: float = 0.35   # event severity weight           (calibrated: Es range 0.18-0.85)
URS_G2: float = 0.10   # peak sector exposure weight    (calibrated: peak_exp range 0.01-0.28)
URS_G3: float = 0.15   # peak stress weight             (calibrated: max(LSI,ISI) range 0.07-0.50)
URS_G4: float = 0.30   # propagation score weight       (calibrated: PS range 0.6-1.0)
URS_G5: float = 0.10   # normalized loss weight         (severity² proxy range 0.04-1.0)

# ═══════════════════════════════════════════════════════════════════════════════
# Risk Classification Thresholds (0–1 scale)
# Equivalent 0–100 scale: 0–20 Low, 20–35 Guarded, 35–50 Elevated,
#                          50–65 High, 65–80 Severe, 80–100 Critical
# ═══════════════════════════════════════════════════════════════════════════════
RISK_THRESHOLDS: dict[str, tuple[float, float]] = {
    "NOMINAL":  (0.00, 0.20),
    "LOW":      (0.20, 0.35),
    "GUARDED":  (0.35, 0.50),
    "ELEVATED": (0.50, 0.65),
    "HIGH":     (0.65, 0.80),
    "SEVERE":   (0.80, 1.01),
}

# ═══════════════════════════════════════════════════════════════════════════════
# Physics Constants (owned by physics_intelligence_layer.py)
# ═══════════════════════════════════════════════════════════════════════════════
PHYS_ALPHA: float = 0.08   # shock wave decay coefficient (dP/dt = -α*P + β*Σ)
PHYS_BETA: float = 0.65    # shock wave coupling (same as PROP_BETA for consistency)
PHYS_FLOW_IMBALANCE_THRESHOLD: float = 0.01   # 1% — trigger PhysicsViolationError
PHYS_CONGESTION_ONSET: float = 0.75           # utilisation above this → congestion
PHYS_RECOVERY_BASE_RATE: float = 0.08         # base daily recovery rate

# ═══════════════════════════════════════════════════════════════════════════════
# Decision Layer Priority Formula
# Priority = P_W1*urgency + P_W2*loss_avoided_norm + P_W3*reg_risk
#          + P_W4*feasibility + P_W5*time_effect
# ═══════════════════════════════════════════════════════════════════════════════
DL_P_W1: float = 0.25   # urgency weight
DL_P_W2: float = 0.30   # loss avoided (normalised) weight
DL_P_W3: float = 0.20   # regulatory risk weight
DL_P_W4: float = 0.15   # feasibility weight
DL_P_W5: float = 0.10   # time effect weight
