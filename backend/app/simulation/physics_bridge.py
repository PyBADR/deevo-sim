"""
Impact Observatory | مرصد الأثر — Physics Bridge

Wires intelligence/physics_core modules into the unified runner.
Adapter from GraphSnapshot + graph registry data → physics_core function inputs.

Called by simulation/runner.py at Stage 9 (Physics/Propagation).
Does NOT duplicate physics logic — delegates to existing physics_core modules.
"""

import logging
from typing import Any

from app.domain.models.graph_snapshot import GraphSnapshot
from app.graph.registry import get_all_nodes, get_all_edges
from app.graph.bridge import get_scenario_shock_vector
from app.intelligence.engines.propagation_engine import run_propagation, result_to_dict
from app.intelligence.physics_core.capacity import compute_node_utilization
from app.intelligence.physics_core.bottleneck import detect_bottlenecks
from app.intelligence.physics_core.flow_conservation import validate_flow_conservation
from app.intelligence.physics_core.recovery import compute_recovery_score
from app.intelligence.physics_core.shockwave import compute_shockwave_field, haversine
from app.intelligence.physics_core.system_stress import compute_system_stress
from app.intelligence.physics_core.pressure import compute_system_pressure

logger = logging.getLogger(__name__)


def run_physics_stage(
    snapshot: GraphSnapshot,
    scenario_id: str,
    severity: float,
    horizon_hours: int,
) -> dict:
    """Execute the full physics stage using real physics_core modules.

    Parameters
    ----------
    snapshot : GraphSnapshot
        Stage 8 output with impacted_nodes and activated_edges.
    scenario_id : str
        Canonical scenario template ID (for shock vectors).
    severity : float
        Severity multiplier (0.0-1.0).
    horizon_hours : int
        Time horizon in hours.

    Returns
    -------
    dict with keys:
        propagation_result : dict  — full propagation engine output
        utilization_map : dict     — per-node capacity utilization
        bottlenecks : dict         — bottleneck detection results
        flow_conservation : dict   — flow conservation validation
        recovery : dict            — system recovery score + curve
        system_stress : dict       — combined stress metric
        system_pressure : dict     — systemic risk indicator
        shockwave_field : list     — per-target shockwave amplitude/energy
    """
    # ── 1. Run Propagation Engine ────────────────────────────
    # Convert graph registry data to the format propagation_engine expects
    all_nodes = get_all_nodes()
    all_edges = get_all_edges()
    shock_vector = get_scenario_shock_vector(scenario_id)

    # Build shocks in propagation_engine format
    shocks = [
        {"nodeId": s["node_id"], "impact": min(s["impact"] * severity, 1.0)}
        for s in shock_vector
    ]

    try:
        prop_result = run_propagation(
            nodes=all_nodes,
            edges=all_edges,
            shocks=shocks,
            max_iterations=6,
            decay_rate=0.05,
        )
        propagation_dict = result_to_dict(prop_result)
    except Exception as e:
        logger.warning("Propagation engine failed: %s", e)
        propagation_dict = {"error": str(e)}

    # ── 2. Build entity/edge lists for physics modules ───────
    # physics_core modules expect entity objects with specific attributes.
    # We adapt ImpactedNodes to lightweight dicts that physics functions accept.
    entities = _snapshot_to_entities(snapshot)
    edges = _snapshot_to_edges(snapshot)

    # ── 3. Capacity & Utilization ────────────────────────────
    try:
        utilization_map = compute_node_utilization(
            entities=entities,
            edges=edges,
            shock_intensity=severity,
        )
    except Exception as e:
        logger.warning("Capacity computation failed: %s", e)
        utilization_map = {}

    # ── 4. Bottleneck Detection ──────────────────────────────
    try:
        bottlenecks = detect_bottlenecks(
            utilization_map=utilization_map,
            entities=entities,
        )
    except Exception as e:
        logger.warning("Bottleneck detection failed: %s", e)
        bottlenecks = {"bottlenecks": [], "severity": 0.0}

    # ── 5. Flow Conservation ─────────────────────────────────
    try:
        flow_conservation = validate_flow_conservation(
            entities=entities,
            edges=edges,
        )
    except Exception as e:
        logger.warning("Flow conservation failed: %s", e)
        flow_conservation = {"balanced": False, "error": str(e)}

    # ── 6. Recovery Score ────────────────────────────────────
    # Build propagation_factors from snapshot node stress values
    propagation_factors = {
        n.node_id: n.stress
        for n in snapshot.impacted_nodes
        if n.stress > 0
    }
    horizon_days = max(1, horizon_hours // 24)

    try:
        recovery = compute_recovery_score(
            entities=entities,
            propagation_factors=propagation_factors,
            horizon_days=horizon_days,
            recovery_rate=0.05,
            shock_intensity=severity,
        )
    except Exception as e:
        logger.warning("Recovery computation failed: %s", e)
        recovery = {"recovery_score": 0.0, "error": str(e)}

    # ── 7. System Stress ─────────────────────────────────────
    try:
        # Get system pressure first
        impacts = {n.node_id: n.stress for n in snapshot.impacted_nodes if n.stress > 0}
        system_pressure = compute_system_pressure(impacts)

        # Compute shockwave energy from the propagation result
        shockwave_energy = propagation_dict.get("systemEnergy", 0.0) if isinstance(propagation_dict, dict) else 0.0

        system_stress = compute_system_stress(
            shockwave_energy=shockwave_energy,
            system_pressure=system_pressure.get("pressure", 0.0),
            diffusion_rate=0.05,
            time_hours=horizon_hours,
        )
    except Exception as e:
        logger.warning("System stress computation failed: %s", e)
        system_stress = {"stress_level": "unknown", "error": str(e)}
        system_pressure = {"pressure": 0.0}

    # ── 8. Shockwave Field ───────────────────────────────────
    try:
        # Find origin of the scenario (first shock node)
        origin_node = None
        if shock_vector:
            first_shock_id = shock_vector[0]["node_id"]
            for node in all_nodes:
                if node["id"] == first_shock_id:
                    origin_node = {"lat": node["lat"], "lng": node["lng"]}
                    break

        if origin_node:
            targets = [
                {"id": n.node_id, "lat": n.lat, "lng": n.lng}
                for n in snapshot.impacted_nodes
                if n.stress > 0 and n.node_id != shock_vector[0]["node_id"]
            ]
            shockwave_field = compute_shockwave_field(
                origin=origin_node,
                targets=targets,
                amplitude_0=severity,
                time_hours=min(horizon_hours, 72),
            )
        else:
            shockwave_field = []
    except Exception as e:
        logger.warning("Shockwave field failed: %s", e)
        shockwave_field = []

    return {
        "propagation_result": propagation_dict,
        "utilization_map": utilization_map,
        "bottlenecks": bottlenecks,
        "flow_conservation": flow_conservation,
        "recovery": recovery,
        "system_stress": system_stress,
        "system_pressure": system_pressure,
        "shockwave_field": shockwave_field,
    }


def _snapshot_to_entities(snapshot: GraphSnapshot) -> list:
    """Convert ImpactedNode list to lightweight entity objects for physics_core.

    physics_core modules expect objects with attributes:
    entity_id, capacity, availability, route_efficiency, criticality, exposure, weight
    """
    class _PhysicsEntity:
        """Lightweight entity adapter for physics_core functions."""
        __slots__ = (
            "entity_id", "capacity", "availability", "route_efficiency",
            "criticality", "exposure", "weight", "name", "layer", "active",
        )

        def __init__(self, node):
            self.entity_id = node.node_id
            self.name = node.label
            self.layer = node.layer
            self.weight = node.weight
            self.capacity = node.weight * 1e9  # Scale weight to capacity units
            self.availability = max(0.0, 1.0 - node.stress)
            self.route_efficiency = max(0.1, 1.0 - node.stress * 0.8)
            self.criticality = node.sensitivity
            self.exposure = node.loss_usd
            self.active = True

    return [_PhysicsEntity(n) for n in snapshot.impacted_nodes]


def _snapshot_to_edges(snapshot: GraphSnapshot) -> list:
    """Convert ActivatedEdge list to lightweight edge objects for physics_core.

    physics_core modules expect objects with attributes:
    source, target, weight, transmission
    """
    class _PhysicsEdge:
        """Lightweight edge adapter for physics_core functions."""
        __slots__ = ("source", "target", "weight", "transmission", "active",
                     "exposure", "capacity", "availability", "route_efficiency",
                     "latency_ms", "source_entity_id", "target_entity_id",
                     "transmission_coefficient")

        def __init__(self, edge):
            self.source = edge.source
            self.target = edge.target
            self.source_entity_id = edge.source
            self.target_entity_id = edge.target
            self.weight = edge.weight
            self.transmission = edge.transmission
            self.active = True
            self.exposure = edge.weight * 1e8
            self.capacity = 1e6
            self.availability = max(0.1, 1.0 - edge.transmission)
            self.route_efficiency = max(0.1, 1.0 - edge.transmission * 0.5)
            self.latency_ms = 50
            self.transmission_coefficient = edge.weight

    return [_PhysicsEdge(e) for e in snapshot.activated_edges]
