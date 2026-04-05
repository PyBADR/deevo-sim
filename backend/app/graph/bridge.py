"""
Impact Observatory — Scenario-to-Graph Bridge

Maps the 8 canonical catalog scenario IDs to their shock vectors.
Keys MUST match scenario_id values in backend/app/scenarios/catalog.py
and frontend/src/lib/dashboard-mapping.ts.
"""


SCENARIO_SHOCKS: dict[str, list[dict]] = {
    # ── Maritime: Strait of Hormuz closure (highest severity maritime shock) ──
    "hormuz_chokepoint_disruption": [
        {"node_id": "geo_hormuz", "impact": 0.9},
        {"node_id": "eco_shipping", "impact": 0.7},
        {"node_id": "eco_oil", "impact": 0.65},
        {"node_id": "fin_insurers", "impact": 0.55},
    ],
    # ── Maritime: Red Sea corridor instability (rerouting + trade delay) ──────
    "red_sea_trade_corridor_instability": [
        {"node_id": "geo_hormuz", "impact": 0.4},
        {"node_id": "eco_shipping", "impact": 0.5},
        {"node_id": "inf_jebel", "impact": 0.35},
        {"node_id": "fin_reinsure", "impact": 0.45},
    ],
    # ── Energy: Price volatility shock (oil + FX + treasury) ─────────────────
    "energy_market_volatility_shock": [
        {"node_id": "fin_sama", "impact": 0.55},
        {"node_id": "fin_uae_cb", "impact": 0.5},
        {"node_id": "fin_kw_cb", "impact": 0.45},
        {"node_id": "fin_qa_cb", "impact": 0.45},
        {"node_id": "fin_tadawul", "impact": 0.65},
        {"node_id": "eco_oil", "impact": 0.7},
    ],
    # ── Maritime: Critical port operations disruption (Jebel Ali + GCC ports) ─
    "critical_port_operations_disruption": [
        {"node_id": "inf_jebel", "impact": 0.85},
        {"node_id": "eco_shipping", "impact": 0.7},
        {"node_id": "inf_dammam", "impact": 0.5},
        {"node_id": "inf_hamad", "impact": 0.45},
        {"node_id": "inf_khalifa", "impact": 0.4},
        {"node_id": "inf_shuwaikh", "impact": 0.4},
    ],
    # ── Aviation: Regional airspace closure / rerouting ───────────────────────
    "regional_airspace_disruption": [
        {"node_id": "eco_aviation", "impact": 0.75},
        {"node_id": "eco_fuel", "impact": 0.55},
        {"node_id": "eco_av_stress", "impact": 0.7},
    ],
    # ── Trade/Compliance: Sanctions escalation (banking + payment rails) ──────
    "cross_border_sanctions_escalation": [
        {"node_id": "geo_hormuz", "impact": 0.55},
        {"node_id": "fin_insurers", "impact": 0.7},
        {"node_id": "fin_reinsure", "impact": 0.65},
        {"node_id": "eco_shipping", "impact": 0.4},
        {"node_id": "fin_banking", "impact": 0.5},
    ],
    # ── Financial: Liquidity stress / deposit run / interbank freeze ──────────
    "regional_liquidity_stress_event": [
        {"node_id": "fin_banking", "impact": 0.85},
        {"node_id": "fin_sama", "impact": 0.6},
        {"node_id": "eco_oil", "impact": 0.7},
    ],
    # ── Cyber: Financial infrastructure attack (payments, settlement, fraud) ──
    "financial_infrastructure_cyber_disruption": [
        {"node_id": "inf_power", "impact": 0.9},
        {"node_id": "inf_desal", "impact": 0.8},
        {"node_id": "inf_telecom", "impact": 0.7},
        {"node_id": "fin_banking", "impact": 0.6},
    ],
}


def get_scenario_shock_vector(scenario_id: str) -> list[dict]:
    """Return shock vector for scenario_id.  Raises ValueError if not found.

    Raises
    ------
    ValueError
        If scenario_id is not present in SCENARIO_SHOCKS.  This surfaces as a
        pipeline failure (status='failed') rather than a silent zero-impact run.
    """
    shocks = SCENARIO_SHOCKS.get(scenario_id)
    if shocks is None:
        raise ValueError(
            f"No shock vector configured for scenario_id='{scenario_id}'. "
            f"Available: {sorted(SCENARIO_SHOCKS.keys())}"
        )
    return shocks


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
