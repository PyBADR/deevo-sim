"""
Impact Observatory | مرصد الأثر — Sector Bridge

Wires services/{financial,banking,insurance,fintech,decision,explainability,
regulatory,time_engine}/engine.py into the unified runner.

Adapter from GraphSnapshot + physics/math output → v4 Scenario/Entity format
→ sector engine calls → typed sector stresses.

Called by simulation/runner.py at Stages 10b-11.
Does NOT duplicate sector logic — delegates to existing service engines.
"""

import logging
import uuid
from datetime import datetime, timezone
from typing import Any, Optional

from app.domain.models.graph_snapshot import GraphSnapshot, ImpactedNode
from app.domain.models.scenario import (
    Scenario, RegulatoryProfile, ScenarioTimeConfig,
)
from app.domain.models.entity import Entity
from app.domain.models.edge import Edge
from app.domain.models.financial_impact import FinancialImpact
from app.services.financial.engine import compute_financial_impact, compute_aggregate_headline
from app.services.banking.engine import compute_banking_stress, aggregate_banking_metrics
from app.services.insurance.engine import compute_insurance_stress, aggregate_insurance_metrics
from app.services.fintech.engine import compute_fintech_stress, aggregate_fintech_metrics
from app.services.decision.engine import compute_decisions
from app.services.decision.bridge import enrich_decisions_with_graph
from app.services.explainability.engine import compute_explanation
from app.services.regulatory.engine import compute_regulatory_state

logger = logging.getLogger(__name__)

# ── Default regulatory profile for GCC (SAMA/CBUAE baseline) ─────────
DEFAULT_REGULATORY_PROFILE = RegulatoryProfile(
    jurisdiction="GCC",
    regulatory_version="4.0.0",
    lcr_min=1.0,
    nsfr_min=1.0,
    cet1_min=0.045,
    capital_adequacy_min=0.08,
    insurance_solvency_min=1.0,
    insurance_reserve_min=1.0,
    fintech_availability_min=0.995,
    settlement_delay_max_minutes=30,
)

# ── Node type → entity_type mapping ──────────────────────────────────
def _classify_entity_type(node: ImpactedNode) -> Optional[str]:
    """Map graph node to v4 entity_type. Returns None if not a financial entity."""
    label = node.label.lower()
    layer = node.layer

    if layer == "finance":
        if any(k in label for k in ("bank", "sama", "cb", "central")):
            return "bank"
        if any(k in label for k in ("insur", "reinsur")):
            return "insurer"
        if any(k in label for k in ("fintech", "payment", "tadawul")):
            return "fintech"
        # Default finance node → bank
        return "bank"

    if layer == "infrastructure":
        if any(k in label for k in ("telecom", "payment")):
            return "fintech"
        return "market_infrastructure"

    if layer == "economy":
        return "market_infrastructure"

    return None


def build_v4_scenario(
    snapshot: GraphSnapshot,
    scenario_id: str,
    severity: float,
    horizon_hours: int,
    scenario_label: str = "",
) -> tuple[Scenario, list[Entity]]:
    """Build a v4 Scenario + Entity list from graph snapshot for sector engines.

    Returns
    -------
    tuple of (Scenario, list[Entity])
        The Scenario object and the list of Entity objects adapted from graph nodes.
    """
    now = datetime.now(timezone.utc).isoformat()
    horizon_days = max(1, horizon_hours // 24)

    # Build entities from graph nodes (only nodes with financial relevance)
    entities = []
    for node in snapshot.impacted_nodes:
        entity_type = _classify_entity_type(node)
        if entity_type is None:
            continue

        # Scale graph node attributes to v4 Entity fields
        base_exposure = node.weight * 1e9  # $1B per unit weight
        capital_buffer = base_exposure * 0.15 * (1.0 - node.stress)
        liquidity_buffer = base_exposure * 0.10 * (1.0 - node.stress)

        entities.append(Entity(
            entity_id=node.node_id,
            entity_type=entity_type,
            name=node.label,
            jurisdiction="GCC",
            exposure=base_exposure,
            capital_buffer=max(0.0, capital_buffer),
            liquidity_buffer=max(0.0, liquidity_buffer),
            capacity=node.weight * 1e6,
            availability=max(0.01, 1.0 - node.stress),
            route_efficiency=max(0.1, 1.0 - node.stress * 0.5),
            criticality=node.sensitivity,
            regulatory_classification=(
                "systemic" if node.sensitivity >= 0.6
                else "material" if node.sensitivity >= 0.4
                else "standard"
            ),
            active=True,
        ))

    if not entities:
        raise ValueError("No financial entities found in graph snapshot")

    # Build v4 edges from activated graph edges (only between entities)
    entity_ids = {e.entity_id for e in entities}
    edges = []
    for edge in snapshot.activated_edges:
        if edge.source in entity_ids and edge.target in entity_ids:
            edges.append(Edge(
                edge_id=edge.edge_id,
                source_entity_id=edge.source,
                target_entity_id=edge.target,
                relation_type="market",
                exposure=edge.weight * 1e8,
                transmission_coefficient=edge.weight,
                capacity=1e6,
                availability=max(0.1, 1.0 - edge.transmission),
                route_efficiency=max(0.1, 1.0 - edge.transmission * 0.5),
                latency_ms=50,
                active=True,
            ))

    scenario = Scenario(
        scenario_id=scenario_id,
        name=scenario_label or scenario_id.replace("_", " ").title(),
        description=f"Unified pipeline run for {scenario_id} at severity {severity}",
        as_of_date=datetime.now(timezone.utc).strftime("%Y-%m-%d"),
        horizon_days=horizon_days,
        shock_intensity=severity,
        market_liquidity_haircut=min(0.5, severity * 0.3),
        deposit_run_rate=min(0.3, severity * 0.15),
        claims_spike_rate=min(0.5, severity * 0.25),
        fraud_loss_rate=min(0.1, severity * 0.05),
        regulatory_profile=DEFAULT_REGULATORY_PROFILE,
        entities=entities,
        edges=edges,
    )

    return scenario, entities


def run_sector_stage(
    snapshot: GraphSnapshot,
    scenario_id: str,
    severity: float,
    horizon_hours: int,
    scenario_label: str = "",
    run_id: str = "",
    stage_timings: Optional[dict] = None,
) -> dict:
    """Execute all sector engines using real service modules.

    Parameters
    ----------
    snapshot : GraphSnapshot
        Stage 8 output.
    scenario_id, severity, horizon_hours, scenario_label : scenario params
    run_id : str
        Pipeline run ID for traceability.
    stage_timings : dict, optional
        Stage timing data for explainability engine.

    Returns
    -------
    dict with keys:
        financial_impacts : list[dict]     — per-entity financial loss
        financial_headline : dict          — aggregate financial metrics
        banking_stresses : list[dict]      — Basel III metrics per bank
        banking_aggregate : dict           — aggregate banking metrics
        insurance_stresses : list[dict]    — solvency/reserve per insurer
        insurance_aggregate : dict         — aggregate insurance metrics
        fintech_stresses : list[dict]      — service/settlement per fintech
        fintech_aggregate : dict           — aggregate fintech metrics
        decision_plan : dict               — priority-ranked actions
        explanation : dict                 — causal explanation pack
        regulatory_state : dict            — aggregate regulatory state
    """
    # ── 0. Build v4 Scenario + Entities ──────────────────────
    try:
        scenario, entities = build_v4_scenario(
            snapshot, scenario_id, severity, horizon_hours, scenario_label
        )
    except Exception as e:
        logger.error("Failed to build v4 scenario: %s", e)
        return _empty_sector_result(str(e))

    # ── 1. Financial Impact ──────────────────────────────────
    # Build propagation_factors from graph node stress
    propagation_factors = {
        n.node_id: max(0.1, n.stress * 2.0)  # Scale stress to propagation factor range
        for n in snapshot.impacted_nodes
        if n.stress > 0
    }

    try:
        financial_impacts = compute_financial_impact(
            scenario=scenario,
            entities=entities,
            propagation_factors=propagation_factors,
        )
        financial_headline = compute_aggregate_headline(financial_impacts)
    except Exception as e:
        logger.warning("Financial engine failed: %s", e)
        financial_impacts = []
        financial_headline = {}

    # ── 2. Banking Stress ────────────────────────────────────
    bank_entities = [e for e in entities if e.entity_type == "bank"]
    try:
        banking_stresses = compute_banking_stress(
            scenario=scenario,
            bank_entities=bank_entities,
            financial_impacts=financial_impacts,
        )
        banking_aggregate = aggregate_banking_metrics(banking_stresses)
    except Exception as e:
        logger.warning("Banking engine failed: %s", e)
        banking_stresses = []
        banking_aggregate = {}

    # ── 3. Insurance Stress ──────────────────────────────────
    insurance_entities = [e for e in entities if e.entity_type == "insurer"]
    try:
        insurance_stresses = compute_insurance_stress(
            scenario=scenario,
            insurance_entities=insurance_entities,
            financial_impacts=financial_impacts,
        )
        insurance_aggregate = aggregate_insurance_metrics(insurance_stresses)
    except Exception as e:
        logger.warning("Insurance engine failed: %s", e)
        insurance_stresses = []
        insurance_aggregate = {}

    # ── 4. Fintech Stress ────────────────────────────────────
    fintech_entities = [e for e in entities if e.entity_type == "fintech"]
    try:
        fintech_stresses = compute_fintech_stress(
            scenario=scenario,
            fintech_entities=fintech_entities,
            financial_impacts=financial_impacts,
        )
        fintech_aggregate = aggregate_fintech_metrics(fintech_stresses)
    except Exception as e:
        logger.warning("Fintech engine failed: %s", e)
        fintech_stresses = []
        fintech_aggregate = {}

    # ── 5. Decision Engine ───────────────────────────────────
    decision_plan = None
    try:
        decision_plan = compute_decisions(
            run_id=run_id,
            scenario=scenario,
            financial_impacts=financial_impacts,
            banking_stresses=banking_stresses,
            insurance_stresses=insurance_stresses,
            fintech_stresses=fintech_stresses,
        )
        # Enrich with graph metadata (lat/lng, labels)
        decision_dict = decision_plan.model_dump()
        decision_dict = enrich_decisions_with_graph(decision_dict)
    except Exception as e:
        logger.warning("Decision engine failed: %s", e)
        decision_dict = {"actions": [], "error": str(e)}

    # ── 6. Explainability ────────────────────────────────────
    try:
        # Convert stage_log dict format → tuple format expected by explainability
        # Expected: dict[str, tuple[str, str, int]] → (start_time, end_time, record_count)
        converted_timings = None
        if stage_timings:
            converted_timings = {}
            for stage_name, info in stage_timings.items():
                if isinstance(info, dict):
                    converted_timings[stage_name] = (
                        info.get("status", "completed"),
                        str(info.get("duration_ms", 0)),
                        int(info.get("duration_ms", 0)),
                    )
                elif isinstance(info, (tuple, list)):
                    converted_timings[stage_name] = tuple(info)

        explanation_pack = compute_explanation(
            run_id=run_id,
            scenario=scenario,
            financial_impacts=financial_impacts,
            banking_stresses=banking_stresses,
            insurance_stresses=insurance_stresses,
            fintech_stresses=fintech_stresses,
            decision_plan=decision_plan,
            stage_timings=converted_timings,
        )
        explanation_dict = explanation_pack.model_dump()
    except Exception as e:
        logger.warning("Explainability engine failed: %s", e)
        explanation_dict = {"summary": "", "error": str(e)}

    # ── 7. Regulatory State ──────────────────────────────────
    try:
        regulatory_state = compute_regulatory_state(
            run_id=run_id,
            scenario=scenario,
            banking_stresses=banking_stresses,
            insurance_stresses=insurance_stresses,
            fintech_stresses=fintech_stresses,
        )
        regulatory_dict = regulatory_state.model_dump()
    except Exception as e:
        logger.warning("Regulatory engine failed: %s", e)
        regulatory_dict = {"breach_level": "unknown", "error": str(e)}

    # ── Serialize Pydantic models to dicts ────────────────────
    def _serialize_list(items):
        return [item.model_dump() if hasattr(item, "model_dump") else item for item in items]

    return {
        "financial_impacts": _serialize_list(financial_impacts),
        "financial_headline": financial_headline,
        "banking_stresses": _serialize_list(banking_stresses),
        "banking_aggregate": banking_aggregate,
        "insurance_stresses": _serialize_list(insurance_stresses),
        "insurance_aggregate": insurance_aggregate,
        "fintech_stresses": _serialize_list(fintech_stresses),
        "fintech_aggregate": fintech_aggregate,
        "decision_plan": decision_dict,
        "explanation": explanation_dict,
        "regulatory_state": regulatory_dict,
    }


def _empty_sector_result(error: str = "") -> dict:
    """Return empty sector result when v4 scenario construction fails."""
    return {
        "financial_impacts": [],
        "financial_headline": {},
        "banking_stresses": [],
        "banking_aggregate": {},
        "insurance_stresses": [],
        "insurance_aggregate": {},
        "fintech_stresses": [],
        "fintech_aggregate": {},
        "decision_plan": {"actions": [], "error": error},
        "explanation": {"summary": "", "error": error},
        "regulatory_state": {"breach_level": "unknown", "error": error},
    }
