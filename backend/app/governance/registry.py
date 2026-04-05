"""
Impact Observatory | مرصد الأثر — Canonical Scenario Registry

SINGLE SOURCE OF TRUTH for all scenario definitions.

This module eliminates fragmented registries by being the authoritative definition of:
  - Which scenario IDs are valid (CANONICAL_REGISTRY keys)
  - What geographic scope each scenario covers (replaces normalize.py TEMPLATE_GEO_SCOPE)
  - Which capabilities each scenario supports (graph_supported, map_supported)
  - What minimum outputs a successful run must produce (MinViableOutput)
  - That shock_mapping_key == scenario_id (no aliasing permitted)

Governance contract:
  - bridge.py SCENARIO_SHOCKS keys MUST equal CANONICAL_REGISTRY keys
  - backend/app/scenarios/catalog.py scenario_ids MUST equal CANONICAL_REGISTRY keys
  - normalize.py MUST call get_geo_scope() from this module
  - Any scenario not in this registry MUST be rejected at pipeline entry

No other module may define a competing list of valid scenario IDs.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional


# ── Domain types ──────────────────────────────────────────────────────────────

VALID_DOMAINS = frozenset({
    "MARITIME", "ENERGY", "FINANCIAL", "CYBER", "AVIATION", "TRADE",
})


@dataclass(frozen=True)
class MinViableOutput:
    """
    Minimum output thresholds a successful run MUST exceed at severity=1.0.

    Validation scales these values by actual run_severity before comparison:
        effective_min_loss = loss_usd × run_severity
        effective_min_nodes = impacted_nodes  (count is severity-independent — BFS propagation
                                               reaches the same topology at any non-zero severity)
        effective_min_edges = edges           (same reasoning)
        effective_min_actions = actions       (fixed minimum regardless of severity)

    Setting these to zero disables the corresponding invariant check.
    All values here are calibrated at severity=1.0 against observed Stage 8 output.
    """
    loss_usd: float        # total_loss_usd floor (dollars, at severity=1.0)
    impacted_nodes: int    # total_nodes_impacted floor
    actions: int           # minimum decision action count
    edges: int             # minimum activated edge count (only checked when graph_supported=True)


@dataclass(frozen=True)
class CanonicalScenario:
    """
    Authoritative definition of a single scenario.

    Every field here is the ground truth — any system component that needs
    scenario metadata MUST derive it from this dataclass, not from a local dict.
    """
    scenario_id: str
    domain: str                    # one of VALID_DOMAINS
    geographic_scope: List[str]    # GCC country codes — used by Stage 3 normalize
    graph_supported: bool          # graph_payload expected non-empty on success
    map_supported: bool            # map_payload.impacted_entities expected non-empty on success
    execution_expected: bool       # True = this scenario must produce non-zero output
    shock_mapping_key: str         # bridge.py SCENARIO_SHOCKS key; MUST equal scenario_id
    mvoe: MinViableOutput          # minimum viable output expectations at severity=1.0
    description_en: str

    def __post_init__(self) -> None:
        if self.domain not in VALID_DOMAINS:
            raise ValueError(f"Invalid domain '{self.domain}' for scenario '{self.scenario_id}'")
        if self.shock_mapping_key != self.scenario_id:
            raise ValueError(
                f"shock_mapping_key '{self.shock_mapping_key}' must equal "
                f"scenario_id '{self.scenario_id}' — aliasing is not permitted."
            )


# ── Canonical Registry ────────────────────────────────────────────────────────
#
# 8 canonical GCC financial stress scenarios.
# These are the ONLY valid scenario_ids in the system.
# Calibrated against Stage 8 graph builder output at severity=0.7:
#   hormuz:   58 nodes, $11.8B    → MVOE at 1.0: 50 nodes, $15B
#   fin_cyber: 50 nodes, $6.1B   → MVOE at 1.0: 45 nodes, $8B
#   liquidity: 54 nodes, $10.7B  → MVOE at 1.0: 48 nodes, $14B
#   energy:    57 nodes, $11.1B  → MVOE at 1.0: 50 nodes, $14B
#   airspace:  38 nodes, $7.3B   → MVOE at 1.0: 30 nodes, $9B
# All other scenarios: conservatively estimated.

CANONICAL_REGISTRY: Dict[str, CanonicalScenario] = {
    "hormuz_chokepoint_disruption": CanonicalScenario(
        scenario_id="hormuz_chokepoint_disruption",
        domain="MARITIME",
        geographic_scope=["SA", "UAE", "KW", "QA", "OM", "BH"],
        graph_supported=True,
        map_supported=True,
        execution_expected=True,
        shock_mapping_key="hormuz_chokepoint_disruption",
        mvoe=MinViableOutput(
            loss_usd=15_000_000_000,
            impacted_nodes=50,
            actions=1,
            edges=80,
        ),
        description_en="Strait of Hormuz strategic maritime chokepoint disruption",
    ),

    "red_sea_trade_corridor_instability": CanonicalScenario(
        scenario_id="red_sea_trade_corridor_instability",
        domain="MARITIME",
        geographic_scope=["SA", "UAE", "KW", "QA", "OM", "BH", "EG"],
        graph_supported=True,
        map_supported=True,
        execution_expected=True,
        shock_mapping_key="red_sea_trade_corridor_instability",
        mvoe=MinViableOutput(
            loss_usd=8_000_000_000,
            impacted_nodes=35,
            actions=1,
            edges=60,
        ),
        description_en="Red Sea trade corridor instability — shipping rerouting and delays",
    ),

    "energy_market_volatility_shock": CanonicalScenario(
        scenario_id="energy_market_volatility_shock",
        domain="ENERGY",
        geographic_scope=["SA", "UAE", "KW", "QA", "OM", "BH"],
        graph_supported=True,
        map_supported=True,
        execution_expected=True,
        shock_mapping_key="energy_market_volatility_shock",
        mvoe=MinViableOutput(
            loss_usd=14_000_000_000,
            impacted_nodes=48,
            actions=1,
            edges=80,
        ),
        description_en="Energy market price volatility — oil, FX, treasury pressure",
    ),

    "critical_port_operations_disruption": CanonicalScenario(
        scenario_id="critical_port_operations_disruption",
        domain="MARITIME",
        geographic_scope=["UAE", "SA", "QA", "KW"],
        graph_supported=True,
        map_supported=True,
        execution_expected=True,
        shock_mapping_key="critical_port_operations_disruption",
        mvoe=MinViableOutput(
            loss_usd=10_000_000_000,
            impacted_nodes=40,
            actions=1,
            edges=65,
        ),
        description_en="GCC critical port operations disruption — Jebel Ali and regional ports",
    ),

    "regional_airspace_disruption": CanonicalScenario(
        scenario_id="regional_airspace_disruption",
        domain="AVIATION",
        geographic_scope=["SA", "UAE", "QA", "KW", "OM", "BH"],
        graph_supported=True,
        map_supported=True,
        execution_expected=True,
        shock_mapping_key="regional_airspace_disruption",
        mvoe=MinViableOutput(
            loss_usd=9_000_000_000,
            impacted_nodes=30,
            actions=1,
            edges=50,
        ),
        description_en="Regional airspace closure or rerouting — aviation sector stress",
    ),

    "cross_border_sanctions_escalation": CanonicalScenario(
        scenario_id="cross_border_sanctions_escalation",
        domain="TRADE",
        geographic_scope=["SA", "UAE", "KW", "QA", "OM", "BH"],
        graph_supported=True,
        map_supported=True,
        execution_expected=True,
        shock_mapping_key="cross_border_sanctions_escalation",
        mvoe=MinViableOutput(
            loss_usd=12_000_000_000,
            impacted_nodes=42,
            actions=1,
            edges=70,
        ),
        description_en="Cross-border sanctions escalation — banking and payment rail exposure",
    ),

    "regional_liquidity_stress_event": CanonicalScenario(
        scenario_id="regional_liquidity_stress_event",
        domain="FINANCIAL",
        geographic_scope=["SA", "UAE", "KW", "QA", "OM", "BH"],
        graph_supported=True,
        map_supported=True,
        execution_expected=True,
        shock_mapping_key="regional_liquidity_stress_event",
        mvoe=MinViableOutput(
            loss_usd=14_000_000_000,
            impacted_nodes=48,
            actions=1,
            edges=80,
        ),
        description_en="Regional bank liquidity stress — deposit run, interbank freeze",
    ),

    "financial_infrastructure_cyber_disruption": CanonicalScenario(
        scenario_id="financial_infrastructure_cyber_disruption",
        domain="CYBER",
        geographic_scope=["SA", "UAE", "KW", "QA", "OM", "BH"],
        graph_supported=True,
        map_supported=True,
        execution_expected=True,
        shock_mapping_key="financial_infrastructure_cyber_disruption",
        mvoe=MinViableOutput(
            loss_usd=8_000_000_000,
            impacted_nodes=45,
            actions=1,
            edges=70,
        ),
        description_en="Financial infrastructure cyber attack — payment disruption and settlement delay",
    ),
}


# ── Accessor helpers ──────────────────────────────────────────────────────────

def get_entry(scenario_id: str) -> Optional[CanonicalScenario]:
    """Return registry entry or None if not found."""
    return CANONICAL_REGISTRY.get(scenario_id)


def require_entry(scenario_id: str) -> CanonicalScenario:
    """Return registry entry. Raises ValueError if scenario_id is unknown."""
    entry = CANONICAL_REGISTRY.get(scenario_id)
    if entry is None:
        raise ValueError(
            f"Unknown scenario_id '{scenario_id}'. "
            f"Registered IDs: {sorted(CANONICAL_REGISTRY.keys())}"
        )
    return entry


def get_all_ids() -> List[str]:
    """Return all canonical scenario IDs in registration order."""
    return list(CANONICAL_REGISTRY.keys())


def get_geo_scope(scenario_id: str, default: Optional[List[str]] = None) -> List[str]:
    """
    Return geographic scope for a scenario.

    This is the authoritative replacement for normalize.py's TEMPLATE_GEO_SCOPE dict.
    All pipeline stages that need geographic scope MUST call this function.

    Parameters
    ----------
    scenario_id : str
        The scenario template_id from the run request.
    default : list[str] | None
        Fallback if scenario_id is unknown. Defaults to ["SA", "UAE"].

    Returns
    -------
    list[str]
        GCC country codes for this scenario's geographic scope.
    """
    entry = CANONICAL_REGISTRY.get(scenario_id)
    if entry is not None:
        return list(entry.geographic_scope)
    return list(default) if default is not None else ["SA", "UAE"]


def is_known_scenario(scenario_id: str) -> bool:
    """Return True if scenario_id is in the canonical registry."""
    return scenario_id in CANONICAL_REGISTRY


def get_mvoe(scenario_id: str) -> Optional[MinViableOutput]:
    """Return MVOE for a scenario, or None if not found."""
    entry = CANONICAL_REGISTRY.get(scenario_id)
    return entry.mvoe if entry else None
