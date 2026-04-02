"""
Impact Observatory | مرصد الأثر — Core Constants (v4 §2, §8)
Hard constants, decision weights, propagation limits, and default thresholds.
"""

# ============================================================================
# DECISION ENGINE WEIGHTS (v4 §2 — mandatory, frozen)
# ============================================================================
DECISION_WEIGHT_URGENCY = 0.25
DECISION_WEIGHT_VALUE = 0.30
DECISION_WEIGHT_REG_RISK = 0.20
DECISION_WEIGHT_FEASIBILITY = 0.15
DECISION_WEIGHT_TIME_EFFECT = 0.10
DECISION_TOP_K = 3
DECISION_MIN_FEASIBILITY = 0.25

# ============================================================================
# PROPAGATION ENGINE LIMITS (v4 §2)
# ============================================================================
PROPAGATION_MAX_ITERATIONS = 50
PROPAGATION_CONVERGENCE_EPSILON = 1e-6
PROPAGATION_FACTOR_MAX = 5.0
SHOCK_INTENSITY_MAX = 5.0

# ============================================================================
# DEFAULT REGULATORY THRESHOLDS (v4 §8.2)
# ============================================================================
LCR_MIN_DEFAULT = 1.0
NSFR_MIN_DEFAULT = 1.0
CET1_MIN_DEFAULT = 0.045
CAR_MIN_DEFAULT = 0.08
INSURANCE_SOLVENCY_MIN_DEFAULT = 1.0
INSURANCE_RESERVE_MIN_DEFAULT = 1.0
FINTECH_AVAILABILITY_MIN_DEFAULT = 0.995
SETTLEMENT_DELAY_MAX_MINUTES_DEFAULT = 30

# Short aliases used by service engines
LCR_MIN = LCR_MIN_DEFAULT
NSFR_MIN = NSFR_MIN_DEFAULT
CET1_MIN = CET1_MIN_DEFAULT
CAR_MIN = CAR_MIN_DEFAULT
SOLVENCY_MIN = INSURANCE_SOLVENCY_MIN_DEFAULT
COMBINED_RATIO_MAX = 1.2
RESERVE_RATIO_MIN = 0.5
SERVICE_AVAILABILITY_MIN = FINTECH_AVAILABILITY_MIN_DEFAULT
SETTLEMENT_DELAY_MAX_MIN = SETTLEMENT_DELAY_MAX_MINUTES_DEFAULT
OPERATIONAL_RISK_MAX = 0.8

# ============================================================================
# VERSIONING
# ============================================================================
MODEL_VERSION = "4.0.0"
API_PREFIX = "/api/v1"

# ============================================================================
# PIPELINE STAGES (v4 §7.1 — exact order)
# ============================================================================
PIPELINE_STAGES = [
    "scenario", "physics", "graph", "propagation",
    "financial", "risk", "regulatory", "decision", "explanation",
]

# ============================================================================
# BUSINESS SEVERITY MAPPING (v4 §16.5)
# ============================================================================
SEVERITY_MAPPING = {
    "low": "monitor",
    "medium": "intervene",
    "high": "escalate",
    "severe": "crisis",
}

# ============================================================================
# PRODUCT IDENTITY
# ============================================================================
PRODUCT = {
    "name_en": "Impact Observatory",
    "name_ar": "مرصد الأثر",
    "short_name": "impact-observatory",
    "positioning_en": "Decision Intelligence for Financial Impact",
    "positioning_ar": "ذكاء القرار لقياس الأثر المالي",
}
