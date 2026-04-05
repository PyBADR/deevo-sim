"""
Impact Observatory — Scenario-to-Graph Bridge

Maps 17 canonical scenarios to their shock vectors.
Ported from @deevo/gcc-knowledge-graph scenarios.ts.
"""


SCENARIO_SHOCKS: dict[str, list[dict]] = {
    "hormuz_closure": [
        {"node_id": "geo_hormuz", "impact": 0.9},
    ],
    "us_iran_escalation": [
        {"node_id": "geo_hormuz", "impact": 0.55},
        {"node_id": "fin_insurers", "impact": 0.7},
        {"node_id": "fin_reinsure", "impact": 0.65},
        {"node_id": "eco_shipping", "impact": 0.4},
    ],
    "military_repositioning": [
        {"node_id": "geo_hormuz", "impact": 0.4},
        {"node_id": "eco_shipping", "impact": 0.5},
        {"node_id": "inf_jebel", "impact": 0.35},
    ],
    "airspace_restriction": [
        {"node_id": "eco_aviation", "impact": 0.75},
    ],
    "hajj_disruption": [
        {"node_id": "soc_hajj", "impact": 0.9},
        {"node_id": "inf_jed", "impact": 0.75},
        {"node_id": "soc_travel_d", "impact": 0.65},
    ],
    "flight_rerouting": [
        {"node_id": "eco_aviation", "impact": 0.65},
        {"node_id": "eco_fuel", "impact": 0.55},
        {"node_id": "eco_av_stress", "impact": 0.7},
    ],
    "jebel_ali_disruption": [
        {"node_id": "inf_jebel", "impact": 0.85},
        {"node_id": "eco_shipping", "impact": 0.7},
    ],
    "gcc_port_congestion": [
        {"node_id": "inf_jebel", "impact": 0.55},
        {"node_id": "inf_dammam", "impact": 0.5},
        {"node_id": "inf_hamad", "impact": 0.45},
        {"node_id": "inf_khalifa", "impact": 0.4},
        {"node_id": "inf_shuwaikh", "impact": 0.4},
        {"node_id": "eco_shipping", "impact": 0.55},
    ],
    "food_security_shock": [
        {"node_id": "eco_food", "impact": 0.9},
        {"node_id": "eco_shipping", "impact": 0.6},
        {"node_id": "geo_hormuz", "impact": 0.5},
    ],
    "liquidity_stress": [
        {"node_id": "fin_banking", "impact": 0.85},
        {"node_id": "fin_sama", "impact": 0.6},
        {"node_id": "eco_oil", "impact": 0.7},
    ],
    "fx_gold_crypto_shock": [
        {"node_id": "fin_sama", "impact": 0.55},
        {"node_id": "fin_uae_cb", "impact": 0.5},
        {"node_id": "fin_kw_cb", "impact": 0.45},
        {"node_id": "fin_qa_cb", "impact": 0.45},
        {"node_id": "fin_tadawul", "impact": 0.65},
    ],
    "insurance_repricing": [
        {"node_id": "fin_reinsure", "impact": 0.85},
        {"node_id": "fin_ins_risk", "impact": 0.75},
    ],
    "gcc_grid_failure": [
        {"node_id": "inf_power", "impact": 0.9},
        {"node_id": "inf_desal", "impact": 0.8},
        {"node_id": "inf_telecom", "impact": 0.7},
    ],
    "water_electricity_disruption": [
        {"node_id": "inf_power", "impact": 0.85},
        {"node_id": "inf_desal", "impact": 0.85},
        {"node_id": "gov_water", "impact": 0.7},
    ],
    "summer_utility_stress": [
        {"node_id": "inf_power", "impact": 0.75},
        {"node_id": "inf_desal", "impact": 0.65},
        {"node_id": "eco_fuel", "impact": 0.7},
        {"node_id": "geo_hormuz", "impact": 0.45},
    ],
    "vision2030_stress": [
        {"node_id": "fin_sama", "impact": 0.4},
    ],
    "mega_projects_pressure": [
        {"node_id": "soc_housing", "impact": 0.5},
        {"node_id": "fin_banking", "impact": 0.4},
    ],
}


def get_scenario_shock_vector(scenario_id: str) -> list[dict]:
    return SCENARIO_SHOCKS.get(scenario_id, [])


def apply_scenario_shocks(scenario_id: str, severity: float = 1.0) -> dict[str, float]:
    shocks = get_scenario_shock_vector(scenario_id)
    result = {}
    for s in shocks:
        impact = s["impact"] * severity
        result[s["node_id"]] = min(impact, 1.0)
    return result


def get_available_scenarios() -> list[dict]:
    """Return all scenario IDs with metadata for API/UI."""
    return [
        {
            "id": sid,
            "label": sid.replace("_", " ").title(),
            "shock_count": len(shocks),
        }
        for sid, shocks in SCENARIO_SHOCKS.items()
    ]


def get_available_scenario_ids() -> list[str]:
    """Return just the scenario ID strings."""
    return list(SCENARIO_SHOCKS.keys())


def scenario_exists(scenario_id: str) -> bool:
    return scenario_id in SCENARIO_SHOCKS
