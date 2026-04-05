"""
Impact Observatory | مرصد الأثر — Scenario Catalog (v4 §18.2)
8 GCC financial stress scenarios with typed domains, financial channel parameters,
and full sector coverage mapping to v4 pipeline stages.

Catalog parameters → v4 Scenario domain model mapping:
    flow_reduction_ratio    → market_liquidity_haircut
    claims_spike_ratio      → claims_spike_rate
    deposit_outflow_ratio   → deposit_run_rate
    fraud_risk_ratio        → fraud_loss_rate
    shock_intensity_default → shock_intensity (capped 0-1 in catalog; domain allows 0-5)

NOTE: rerouting_ratio and delay_multiplier are DISPLAY-ONLY metadata.
      They do NOT map to any v4 pipeline input field.
"""

from typing import Dict, List, Literal

# ── Typed enums ───────────────────────────────────────────────────────────
ScenarioDomainType = Literal[
    "trade_logistics",
    "markets_energy",
    "compliance_financial",
    "banking_financial",
    "aviation_logistics",
    "digital_financial",
]

TriggerType = Literal[
    "maritime_disruption",
    "corridor_instability",
    "price_volatility",
    "port_disruption",
    "airspace_constraint",
    "sanctions_escalation",
    "liquidity_stress",
    "cyber_disruption",
]

SeverityLevel = Literal["low", "medium", "medium_high", "high", "extreme"]

SectorName = Literal[
    "banking", "insurance", "fintech", "energy",
    "logistics", "retail", "sovereign", "aviation", "tourism", "trade",
]


# ── Catalog entries ───────────────────────────────────────────────────────
SCENARIO_CATALOG: List[Dict] = [
    {
        "scenario_id": "hormuz_chokepoint_disruption",
        "scenario_name_en": "Strategic Maritime Chokepoint Disruption (Hormuz)",
        "scenario_name_ar": "تعطّل نقطة اختناق بحرية استراتيجية (مضيق هرمز)",
        "domain": "trade_logistics",
        "trigger_type": "maritime_disruption",
        "geographic_scope": ["GCC", "Hormuz", "Arabian Gulf"],
        "severity_default": "high",
        "shock_intensity_default": 0.82,
        "primary_channels": [
            "shipping_delay",
            "fuel_cost",
            "insurance_cost",
            "banking_liquidity",
            "payment_disruption",
        ],
        "affected_sectors": [
            "banking",
            "insurance",
            "fintech",
            "energy",
            "logistics",
        ],
        "scenario_parameters": {
            "flow_reduction_ratio": 0.45,
            "rerouting_ratio": 0.30,
            "delay_multiplier": 1.80,
            "claims_spike_ratio": 0.18,
            "deposit_outflow_ratio": 0.12,
            "fraud_risk_ratio": 0.06,
        },
    },
    {
        "scenario_id": "red_sea_trade_corridor_instability",
        "scenario_name_en": "Red Sea Trade Corridor Instability",
        "scenario_name_ar": "اضطراب ممر التجارة في البحر الأحمر",
        "domain": "trade_logistics",
        "trigger_type": "corridor_instability",
        "geographic_scope": ["Red Sea", "GCC", "Suez-linked trade"],
        "severity_default": "medium_high",
        "shock_intensity_default": 0.72,
        "primary_channels": [
            "rerouting_cost",
            "shipping_delay",
            "cargo_insurance",
            "import_inflation",
        ],
        "affected_sectors": [
            "insurance",
            "logistics",
            "banking",
            "retail",
            "fintech",
        ],
        "scenario_parameters": {
            "flow_reduction_ratio": 0.32,
            "rerouting_ratio": 0.44,
            "delay_multiplier": 1.55,
            "claims_spike_ratio": 0.12,
            "deposit_outflow_ratio": 0.04,
            "fraud_risk_ratio": 0.03,
        },
    },
    {
        "scenario_id": "energy_market_volatility_shock",
        "scenario_name_en": "Energy Market Volatility Shock",
        "scenario_name_ar": "صدمة تقلبات أسواق الطاقة",
        "domain": "markets_energy",
        "trigger_type": "price_volatility",
        "geographic_scope": ["GCC", "Global Energy Markets"],
        "severity_default": "high",
        "shock_intensity_default": 0.78,
        "primary_channels": [
            "price_shock",
            "treasury_loss",
            "hedging_gap",
            "margin_pressure",
        ],
        "affected_sectors": [
            "banking",
            "energy",
            "insurance",
            "sovereign",
            "fintech",
        ],
        "scenario_parameters": {
            "flow_reduction_ratio": 0.10,
            "rerouting_ratio": 0.08,
            "delay_multiplier": 1.10,
            "claims_spike_ratio": 0.07,
            "deposit_outflow_ratio": 0.08,
            "fraud_risk_ratio": 0.02,
        },
    },
    {
        "scenario_id": "critical_port_operations_disruption",
        "scenario_name_en": "Critical Port Operations Disruption",
        "scenario_name_ar": "تعطّل عمليات ميناء حيوي",
        "domain": "trade_logistics",
        "trigger_type": "port_disruption",
        "geographic_scope": ["GCC Ports"],
        "severity_default": "medium_high",
        "shock_intensity_default": 0.70,
        "primary_channels": [
            "port_congestion",
            "inventory_delay",
            "trade_cost",
            "claims_increase",
        ],
        "affected_sectors": [
            "logistics",
            "insurance",
            "retail",
            "banking",
            "fintech",
        ],
        "scenario_parameters": {
            "flow_reduction_ratio": 0.38,
            "rerouting_ratio": 0.22,
            "delay_multiplier": 1.65,
            "claims_spike_ratio": 0.11,
            "deposit_outflow_ratio": 0.03,
            "fraud_risk_ratio": 0.02,
        },
    },
    {
        "scenario_id": "regional_airspace_disruption",
        "scenario_name_en": "Regional Airspace Disruption Scenario",
        "scenario_name_ar": "سيناريو تعطّل المجال الجوي الإقليمي",
        "domain": "aviation_logistics",
        "trigger_type": "airspace_constraint",
        "geographic_scope": ["GCC", "Regional Air Corridors"],
        "severity_default": "medium",
        "shock_intensity_default": 0.60,
        "primary_channels": [
            "air_cargo_delay",
            "passenger_disruption",
            "tourism_loss",
            "rerouting_cost",
        ],
        "affected_sectors": [
            "aviation",
            "tourism",
            "insurance",
            "banking",
            "fintech",
        ],
        "scenario_parameters": {
            "flow_reduction_ratio": 0.28,
            "rerouting_ratio": 0.26,
            "delay_multiplier": 1.40,
            "claims_spike_ratio": 0.09,
            "deposit_outflow_ratio": 0.02,
            "fraud_risk_ratio": 0.02,
        },
    },
    {
        "scenario_id": "cross_border_sanctions_escalation",
        "scenario_name_en": "Cross-Border Sanctions Escalation",
        "scenario_name_ar": "تصاعد العقوبات العابرة للحدود",
        "domain": "compliance_financial",
        "trigger_type": "sanctions_escalation",
        "geographic_scope": ["GCC", "Cross-Border Trade and Payments"],
        "severity_default": "high",
        "shock_intensity_default": 0.76,
        "primary_channels": [
            "compliance_cost",
            "trade_rerouting",
            "banking_exposure",
            "payment_restrictions",
        ],
        "affected_sectors": [
            "banking",
            "fintech",
            "trade",
            "insurance",
        ],
        "scenario_parameters": {
            "flow_reduction_ratio": 0.20,
            "rerouting_ratio": 0.35,
            "delay_multiplier": 1.25,
            "claims_spike_ratio": 0.05,
            "deposit_outflow_ratio": 0.07,
            "fraud_risk_ratio": 0.04,
        },
    },
    {
        "scenario_id": "regional_liquidity_stress_event",
        "scenario_name_en": "Regional Liquidity Stress Event",
        "scenario_name_ar": "أزمة سيولة مصرفية إقليمية",
        "domain": "banking_financial",
        "trigger_type": "liquidity_stress",
        "geographic_scope": ["GCC Financial System"],
        "severity_default": "high",
        "shock_intensity_default": 0.84,
        "primary_channels": [
            "deposit_run",
            "interbank_stress",
            "funding_gap",
            "regulatory_breach",
        ],
        "affected_sectors": [
            "banking",
            "fintech",
            "insurance",
        ],
        "scenario_parameters": {
            "flow_reduction_ratio": 0.12,
            "rerouting_ratio": 0.05,
            "delay_multiplier": 1.05,
            "claims_spike_ratio": 0.04,
            "deposit_outflow_ratio": 0.18,
            "fraud_risk_ratio": 0.03,
        },
    },
    {
        "scenario_id": "financial_infrastructure_cyber_disruption",
        "scenario_name_en": "Financial Infrastructure Cyber Disruption",
        "scenario_name_ar": "تعطّل البنية المالية نتيجة هجوم سيبراني",
        "domain": "digital_financial",
        "trigger_type": "cyber_disruption",
        "geographic_scope": ["GCC Payments and Financial Rails"],
        "severity_default": "high",
        "shock_intensity_default": 0.74,
        "primary_channels": [
            "service_outage",
            "fraud_surge",
            "settlement_delay",
            "confidence_loss",
        ],
        "affected_sectors": [
            "fintech",
            "banking",
            "insurance",
        ],
        "scenario_parameters": {
            "flow_reduction_ratio": 0.15,
            "rerouting_ratio": 0.10,
            "delay_multiplier": 1.30,
            "claims_spike_ratio": 0.08,
            "deposit_outflow_ratio": 0.05,
            "fraud_risk_ratio": 0.09,
        },
    },
]


# ── Lookup helpers ────────────────────────────────────────────────────────
def get_scenario_catalog() -> List[Dict]:
    """Return the full catalog for GET /scenarios."""
    return SCENARIO_CATALOG


def get_scenario_by_id(scenario_id: str) -> Dict:
    """Lookup a single scenario by ID. Raises ValueError if not found."""
    for scenario in SCENARIO_CATALOG:
        if scenario["scenario_id"] == scenario_id:
            return scenario
    raise ValueError(f"Unknown scenario_id: {scenario_id}")


def get_catalog_ids() -> List[str]:
    """Return all scenario IDs in catalog order."""
    return [s["scenario_id"] for s in SCENARIO_CATALOG]


def get_scenarios_by_sector(sector: str) -> List[Dict]:
    """Filter catalog by affected sector."""
    return [s for s in SCENARIO_CATALOG if sector in s["affected_sectors"]]


# ── Catalog → v4 domain model parameter mapping ──────────────────────────
CATALOG_TO_DOMAIN_FIELD_MAP = {
    "flow_reduction_ratio": "market_liquidity_haircut",
    "claims_spike_ratio": "claims_spike_rate",
    "deposit_outflow_ratio": "deposit_run_rate",
    "fraud_risk_ratio": "fraud_loss_rate",
}

# Display-only parameters (NOT pipeline inputs):
DISPLAY_ONLY_PARAMS = {"rerouting_ratio", "delay_multiplier"}
