"""
Impact Observatory | مرصد الأثر — Math Bridge

Wires intelligence/math_core modules into the unified runner.
Adapter from GraphSnapshot + physics output → math_core function inputs.

Called by simulation/runner.py at Stage 10 (Math Modeling).
Does NOT duplicate math logic — delegates to existing math_core modules.
"""

import logging
from typing import Any

from app.domain.models.graph_snapshot import GraphSnapshot
from app.intelligence.math_core.risk_score import (
    compute_gcc_risk_score,
    compute_risk_score_batch,
)
from app.intelligence.math_core.confidence import (
    compute_model_confidence,
    compute_confidence_interval,
)
from app.intelligence.math_core.disruption import (
    compute_disruption_score,
    compute_disruption_index,
)
from app.intelligence.math_core.exposure import (
    compute_exposure_score as compute_exposure,
    compute_sector_exposure,
)
from app.intelligence.math_core.propagation import (
    compute_system_energy,
    compute_propagation_depth,
    compute_sector_spread,
)

logger = logging.getLogger(__name__)

# Map graph layer to risk_score asset_class
LAYER_TO_ASSET_CLASS = {
    "infrastructure": "airport",   # Default for infra nodes
    "economy": "seaport",          # Default for economy nodes
    "finance": "bank",             # Default for finance nodes
    "geography": "airport",        # Spatial layer
    "society": "airport",          # Social layer
}

# Regional multipliers by country identifier in node_id
REGIONAL_MULTIPLIERS = {
    "sa": 1.15,
    "uae": 1.20,
    "kw": 1.05,
    "qa": 1.10,
    "om": 0.95,
    "bh": 1.00,
}


def run_math_stage(
    snapshot: GraphSnapshot,
    physics_output: dict,
    severity: float,
    horizon_hours: int,
) -> dict:
    """Execute the full math modeling stage using real math_core modules.

    Parameters
    ----------
    snapshot : GraphSnapshot
        Stage 8 output with impacted_nodes and activated_edges.
    physics_output : dict
        Output from physics_bridge.run_physics_stage().
    severity : float
        Severity multiplier (0.0-1.0).
    horizon_hours : int
        Time horizon in hours.

    Returns
    -------
    dict with keys:
        risk_scores : list[dict]     — per-node GCC risk scores
        model_confidence : float     — aggregate model confidence
        confidence_interval : dict   — 95% CI bounds
        disruption_index : dict      — system disruption metrics
        sector_exposure : dict       — per-sector exposure analysis
        system_energy : float        — total system energy Σ x_i²
        propagation_depth : int      — max propagation depth
        sector_spread : int          — number of affected sectors
    """
    # ── 1. Per-node GCC Risk Scores ──────────────────────────
    risk_scores = _compute_risk_scores(snapshot, physics_output)

    # ── 2. Model Confidence ──────────────────────────────────
    try:
        impact_values = [n.stress for n in snapshot.impacted_nodes if n.stress > 0]
        impact_variance = _variance(impact_values) if impact_values else 0.0
        model_confidence = compute_model_confidence(impact_variance)
    except Exception as e:
        logger.warning("Model confidence computation failed: %s", e)
        model_confidence = 0.5

    # ── 3. Confidence Interval ───────────────────────────────
    try:
        if impact_values and len(impact_values) > 1:
            confidence_interval = compute_confidence_interval(impact_values, confidence=0.95)
        else:
            confidence_interval = {"mean": 0.0, "lower": 0.0, "upper": 0.0, "confidence": 0.95}
    except Exception as e:
        logger.warning("Confidence interval failed: %s", e)
        confidence_interval = {"mean": 0.0, "lower": 0.0, "upper": 0.0, "confidence": 0.95}

    # ── 4. Disruption Index ──────────────────────────────────
    try:
        affected_count = sum(1 for n in snapshot.impacted_nodes if n.stress > 0.01)
        total_count = len(snapshot.impacted_nodes)
        avg_severity = (
            sum(n.stress for n in snapshot.impacted_nodes if n.stress > 0.01) / max(affected_count, 1)
        )
        duration_days = max(1, horizon_hours // 24)

        disruption_index = compute_disruption_index(
            affected_nodes=affected_count,
            total_nodes=total_count,
            avg_severity=avg_severity,
            duration_days=duration_days,
        )
    except Exception as e:
        logger.warning("Disruption index failed: %s", e)
        disruption_index = {"disruption_score": 0.0, "error": str(e)}

    # ── 5. Sector Exposure ───────────────────────────────────
    try:
        sector_impacts = {}
        for node in snapshot.impacted_nodes:
            if node.stress > 0:
                sector_impacts.setdefault(node.layer, []).append(node.stress)

        sector_avg = {
            layer: sum(stresses) / len(stresses)
            for layer, stresses in sector_impacts.items()
        }
        sector_exposure = compute_sector_exposure(sector_avg)
    except Exception as e:
        logger.warning("Sector exposure failed: %s", e)
        sector_exposure = {}

    # ── 6. System Energy ─────────────────────────────────────
    try:
        node_impacts = {
            n.node_id: n.stress
            for n in snapshot.impacted_nodes
        }
        system_energy = compute_system_energy(node_impacts)
    except Exception as e:
        logger.warning("System energy failed: %s", e)
        system_energy = 0.0

    # ── 7. Propagation Depth ─────────────────────────────────
    try:
        prop_result = physics_output.get("propagation_result", {})
        iteration_snapshots = prop_result.get("iterationSnapshots", [])
        propagation_depth = compute_propagation_depth(iteration_snapshots)
    except Exception as e:
        logger.warning("Propagation depth failed: %s", e)
        propagation_depth = snapshot.propagation_depth

    # ── 8. Sector Spread ─────────────────────────────────────
    try:
        affected_sectors = [
            {"sector": layer, "avg_impact": sum(s) / len(s)}
            for layer, s in sector_impacts.items()
            if sum(s) / len(s) > 0.01
        ]
        sector_spread = compute_sector_spread(affected_sectors)
    except Exception as e:
        logger.warning("Sector spread failed: %s", e)
        sector_spread = len(sector_impacts) if sector_impacts else 0

    return {
        "risk_scores": risk_scores,
        "model_confidence": model_confidence,
        "confidence_interval": confidence_interval,
        "disruption_index": disruption_index,
        "sector_exposure": sector_exposure,
        "system_energy": system_energy,
        "propagation_depth": propagation_depth,
        "sector_spread": sector_spread,
    }


def _compute_risk_scores(snapshot: GraphSnapshot, physics_output: dict) -> list[dict]:
    """Compute per-node GCC risk scores using math_core/risk_score.py.

    Maps graph node attributes to the 6-factor risk equation:
    R_i = w1*G + w2*P + w3*N + w4*L + w5*T + w6*U
    """
    risk_scores = []

    prop_result = physics_output.get("propagation_result", {})
    node_impacts = prop_result.get("nodeImpacts", {}) if isinstance(prop_result, dict) else {}

    for node in snapshot.impacted_nodes:
        if node.stress < 0.01:
            continue

        try:
            # Determine asset class from node layer/type
            asset_class = _infer_asset_class(node)

            # Regional multiplier from node_id prefix
            regional_mult = _infer_regional_multiplier(node.node_id)

            # Map graph attributes to risk equation factors:
            # G = geopolitical_threat (stress from shock propagation)
            # P = proximity_score (sensitivity × stress → local proximity to shock)
            # N = network_centrality (weight → how connected the node is)
            # L = logistics_pressure (from physics utilization if available)
            # T = temporal_persistence (stress decay over time → higher = more persistent)
            # U = uncertainty (1 - confidence of impact)

            geopolitical_threat = min(1.0, node.stress * 1.2)
            proximity_score = min(1.0, node.sensitivity * node.stress)
            network_centrality = node.weight
            logistics_pressure = _get_utilization(node.node_id, physics_output)
            temporal_persistence = min(1.0, node.stress * 0.8)  # Persistent if high stress
            uncertainty = max(0.1, 1.0 - abs(node_impacts.get(node.node_id, node.stress)))

            score = compute_gcc_risk_score(
                geopolitical_threat=geopolitical_threat,
                proximity_score=proximity_score,
                network_centrality=network_centrality,
                logistics_pressure=logistics_pressure,
                temporal_persistence=temporal_persistence,
                uncertainty=uncertainty,
                asset_class=asset_class,
                normalize=True,
                regional_multiplier=regional_mult,
            )

            risk_scores.append({
                "node_id": node.node_id,
                "label": node.label,
                "label_ar": node.label_ar,
                "layer": node.layer,
                **score,
            })
        except Exception as e:
            logger.warning("Risk score failed for %s: %s", node.node_id, e)

    # Sort by risk score descending
    risk_scores.sort(key=lambda x: x.get("risk_score", 0), reverse=True)
    return risk_scores


def _infer_asset_class(node) -> str:
    """Infer asset_class from node label and layer for risk weight lookup."""
    label_lower = node.label.lower()

    if "airport" in label_lower or "aviat" in label_lower:
        return "airport"
    if "port" in label_lower or "ship" in label_lower:
        return "seaport"
    if "oil" in label_lower or "refiner" in label_lower or "aramco" in label_lower or "adnoc" in label_lower or "kpc" in label_lower:
        return "oil_facility"
    if "pipeline" in label_lower:
        return "pipeline"
    if "bank" in label_lower or "sama" in label_lower or "cb" in label_lower or "central" in label_lower:
        return "bank"
    if "insur" in label_lower or "reinsur" in label_lower:
        return "insurer"
    if "fintech" in label_lower or "payment" in label_lower or "tadawul" in label_lower:
        return "fintech"
    if "exchange" in label_lower:
        return "exchange"
    if "telecom" in label_lower:
        return "fintech"  # Closest match
    if "power" in label_lower or "desal" in label_lower:
        return "refinery"  # Infrastructure utility

    return LAYER_TO_ASSET_CLASS.get(node.layer, "airport")


def _infer_regional_multiplier(node_id: str) -> float:
    """Infer regional multiplier from node_id country prefix."""
    parts = node_id.split("_")
    if len(parts) >= 2:
        country_hint = parts[1].lower()
        for prefix, mult in REGIONAL_MULTIPLIERS.items():
            if country_hint.startswith(prefix):
                return mult
    # Default: Saudi Arabia (largest GCC economy)
    return 1.15


def _get_utilization(node_id: str, physics_output: dict) -> float:
    """Extract node utilization from physics output, fallback to 0.5."""
    utilization_map = physics_output.get("utilization_map", {})
    if node_id in utilization_map:
        util_data = utilization_map[node_id]
        if isinstance(util_data, dict):
            return util_data.get("utilization", 0.5)
        return float(util_data)
    return 0.5


def _variance(values: list[float]) -> float:
    """Compute variance of a list of floats."""
    if len(values) < 2:
        return 0.0
    mean = sum(values) / len(values)
    return sum((v - mean) ** 2 for v in values) / len(values)
