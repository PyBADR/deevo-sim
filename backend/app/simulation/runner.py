"""
Impact Observatory | مرصد الأثر — Unified Simulation Runner

ONE canonical pipeline function: run_unified_pipeline().
Replaces both orchestration/pipeline.py and orchestration/pipeline_v4.py.

13-stage execution:
  1. ingest → 2. validate → 3. normalize → 4. deduplicate →
  5. enrich → 6. cluster → 7. signal → 8. graph_build →
  9. propagation → 10. math_modeling → 11. decision →
  12. trust → 13. output

No raw data may bypass stages 1-7.
All UI surfaces consume the same output from stage 13.
"""

import time
import uuid
import logging
from typing import Any

from app.domain.models.graph_snapshot import GraphSnapshot
from app.domain.models.trust_metadata import TrustMetadata
from app.ingestion.ingest import ingest_scenario
from app.quality.validate import validate_event
from app.quality.normalize import normalize_event
from app.quality.deduplicate import deduplicate_event, clear_dedup_cache
from app.quality.enrich import enrich_event
from app.quality.cluster import cluster_signals
from app.quality.signal import generate_signal
from app.graph.builder import build_graph_snapshot
from app.trust.audit import build_trust_metadata
from app.trust.confidence import aggregate_confidence
from app.trust.warnings import collect_warnings, quality_impact_score
from .state import SimulationState
from .physics_bridge import run_physics_stage
from .math_bridge import run_math_stage
from .sector_bridge import run_sector_stage

logger = logging.getLogger(__name__)


def _timed(fn, *args, **kwargs) -> tuple[Any, float]:
    """Execute fn and return (result, duration_ms)."""
    t0 = time.time()
    result = fn(*args, **kwargs)
    return result, round((time.time() - t0) * 1000, 1)


def run_unified_pipeline(
    template_id: str,
    severity: float = 0.7,
    horizon_hours: int = 168,
    label: str = "",
) -> dict:
    """Run the complete 13-stage unified pipeline.

    Parameters
    ----------
    template_id : str
        Scenario template ID — must be one of the 8 canonical scenario IDs
        registered in backend/app/governance/registry.py.
    severity : float
        Severity multiplier (0.0-1.0).
    horizon_hours : int
        Time horizon in hours.
    label : str
        Optional human-readable scenario label.

    Returns
    -------
    dict
        UnifiedRunResult containing:
        - run_id, scenario, headline metrics
        - graph_payload (nodes + edges for graph explorer)
        - map_payload (impacted entities with lat/lng for globe)
        - propagation_steps
        - sector_rollups (banking, insurance, fintech stress)
        - decision_inputs (priority-ranked actions)
        - trust metadata
    """
    state = SimulationState(
        run_id=f"run_{uuid.uuid4().hex[:12]}",
        scenario_id=template_id,
        scenario_label=label or template_id.replace("_", " ").title(),
        severity=severity,
        horizon_hours=horizon_hours,
        data_sources=["scenario_catalog"],
    )
    clear_dedup_cache()

    # ── Stage 1: Ingest ───────────────────────────────────────
    try:
        raw, ms = _timed(ingest_scenario, template_id, severity, horizon_hours, label)
        state.raw_event = raw
        state.record_stage("ingest", "completed", ms)
    except Exception as e:
        state.record_stage("ingest", "failed", detail=str(e))
        state.warnings.append(f"Ingestion failed: {e}")
        return _build_error_result(state, str(e))

    # ── Stage 2: Validate ─────────────────────────────────────
    try:
        validated, ms = _timed(validate_event, raw)
        state.validated_event = validated
        state.warnings.extend(validated.warnings)
        state.record_stage("validate", "completed", ms)
    except Exception as e:
        state.record_stage("validate", "failed", detail=str(e))
        state.warnings.append(f"Validation failed: {e}")
        return _build_error_result(state, str(e))

    # ── Stage 3: Normalize ────────────────────────────────────
    normalized, ms = _timed(normalize_event, validated)
    state.normalized_event = normalized
    state.record_stage("normalize", "completed", ms)

    # ── Stage 4: Deduplicate ──────────────────────────────────
    deduped, ms = _timed(deduplicate_event, normalized)
    state.record_stage("deduplicate", "completed", ms)

    # ── Stage 5: Enrich ───────────────────────────────────────
    enriched, ms = _timed(enrich_event, deduped)
    state.enriched_event = enriched
    state.record_stage("enrich", "completed", ms)

    # ── Stage 6: Cluster ──────────────────────────────────────
    clusters, ms = _timed(cluster_signals, [enriched])
    state.signal_clusters = clusters
    state.record_stage("cluster", "completed", ms)

    # ── Stage 7: Signal ───────────────────────────────────────
    if clusters:
        signal, ms = _timed(generate_signal, clusters[0])
        state.signal = signal
        state.record_stage("signal", "completed", ms)
    else:
        state.record_stage("signal", "skipped", detail="No clusters")

    # ── Stage 8: Graph Build ──────────────────────────────────
    # Use scenario shocks from the bridge (authoritative shock vectors)
    snapshot, ms = _timed(
        build_graph_snapshot,
        scenario_id=template_id,
        severity=severity,
    )
    state.graph_snapshot = snapshot
    state.record_stage("graph_build", "completed", ms,
                       detail=f"{snapshot.total_nodes_impacted} nodes impacted")

    # ── Stage 9: Physics/Propagation (real physics_core) ────────
    try:
        physics_output, ms = _timed(
            run_physics_stage,
            snapshot=snapshot,
            scenario_id=template_id,
            severity=severity,
            horizon_hours=horizon_hours,
        )
        # Extract propagation steps for backward compat
        prop_result = physics_output.get("propagation_result", {})
        prop_chain = prop_result.get("propagationChain", [])
        propagation_steps = prop_chain if prop_chain else _extract_propagation_steps(snapshot)
        state.propagation_result = {
            "steps": propagation_steps,
            "depth": prop_result.get("propagationDepth", snapshot.propagation_depth),
            "system_energy": prop_result.get("systemEnergy", 0.0),
            "spread_level": prop_result.get("spreadLevel", "low"),
        }
        state.record_stage("propagation", "completed", ms,
                           detail=f"{len(propagation_steps)} steps, "
                                  f"depth={state.propagation_result['depth']}")
    except Exception as e:
        logger.warning("Physics stage failed, falling back: %s", e)
        physics_output = {}
        propagation_steps = _extract_propagation_steps(snapshot)
        state.propagation_result = {"steps": propagation_steps, "depth": snapshot.propagation_depth}
        state.record_stage("propagation", "completed", 0.0,
                           detail=f"fallback: {len(propagation_steps)} steps")
        state.warnings.append(f"Physics stage degraded: {e}")

    # ── Stage 10: Math Modeling (real math_core) ─────────────
    try:
        math_output, ms = _timed(
            run_math_stage,
            snapshot=snapshot,
            physics_output=physics_output,
            severity=severity,
            horizon_hours=horizon_hours,
        )
        state.risk_scores = math_output
        state.record_stage("math_modeling", "completed", ms,
                           detail=f"{len(math_output.get('risk_scores', []))} risk scores")
    except Exception as e:
        logger.warning("Math stage failed, falling back: %s", e)
        math_output = {}
        state.record_stage("math_modeling", "completed", 0.0,
                           detail=f"fallback: {e}")
        state.warnings.append(f"Math stage degraded: {e}")

    # ── Stage 10b: Sector Rollups (label-matching, kept for backward compat) ──
    sector_rollups = _compute_sector_rollups(snapshot)
    state.banking_stress = sector_rollups.get("banking", {})
    state.insurance_stress = sector_rollups.get("insurance", {})
    state.fintech_stress = sector_rollups.get("fintech", {})

    # ── Stage 10c: Sector Engines (real service engines) ─────
    try:
        sector_output, ms = _timed(
            run_sector_stage,
            snapshot=snapshot,
            scenario_id=template_id,
            severity=severity,
            horizon_hours=horizon_hours,
            scenario_label=label,
            run_id=state.run_id,
            stage_timings=state.stage_log,
        )
        state.financial_impacts = sector_output.get("financial_impacts", [])
        state.explanation = sector_output.get("explanation", {})
        state.record_stage("sector_engines", "completed", ms,
                           detail=f"fin={len(sector_output.get('financial_impacts', []))}, "
                                  f"bank={len(sector_output.get('banking_stresses', []))}, "
                                  f"ins={len(sector_output.get('insurance_stresses', []))}, "
                                  f"fin_t={len(sector_output.get('fintech_stresses', []))}")
    except Exception as e:
        logger.warning("Sector engines failed: %s", e)
        sector_output = {}
        state.record_stage("sector_engines", "completed", 0.0,
                           detail=f"failed: {e}")
        state.warnings.append(f"Sector engines degraded: {e}")

    # ── Stage 11: Decision ────────────────────────────────────
    # Use real decision engine output if available, fall back to inline
    if sector_output and sector_output.get("decision_plan", {}).get("actions"):
        decision_inputs = sector_output["decision_plan"]
    else:
        decision_inputs = _compute_decision_inputs(snapshot, sector_rollups, severity)
    state.decisions = decision_inputs
    state.record_stage("decision", "completed", 0.0,
                       detail=f"{len(decision_inputs.get('actions', []))} actions")

    # ── Stage 12: Trust ───────────────────────────────────────
    all_warnings = collect_warnings(
        state.warnings,
        validated.warnings if validated else [],
    )
    stage_confidences = state.get_stage_confidences()
    composite_confidence = aggregate_confidence(stage_confidences)
    quality_penalty = quality_impact_score(all_warnings)
    final_confidence = max(0.1, composite_confidence - quality_penalty)

    # ── Stage 13: Build output ────────────────────────────────
    result = _build_result(
        state, final_confidence, all_warnings,
        physics_output=physics_output,
        math_output=math_output,
        sector_output=sector_output,
    )

    # Compute audit hash over the result
    trust = build_trust_metadata(
        stages_completed=state.get_stages_completed(),
        stage_log=state.stage_log,
        data_sources=state.data_sources,
        confidence_score=final_confidence,
        warnings=all_warnings,
        provenance_chain=enriched.provenance_chain if enriched else [],
        output_payload=result,
    )
    state.trust = trust
    result["trust"] = trust.model_dump()
    state.record_stage("trust", "completed", 0.0)
    state.record_stage("output", "completed", state.elapsed_ms())

    # ── Stage 13b: Governance Audit ────────────────────────────────────────
    # Attach a runtime audit object to the result. This is observational:
    # it does not modify status or raise exceptions. The audit verdict is
    # logged and stored in result["_governance"] for the API response and
    # post-hoc analysis.
    try:
        from app.governance.audit import audit_run
        _audit = audit_run(
            scenario_id=template_id,
            run_result=result,
            run_severity=severity,
        )
        result["_governance"] = _audit.to_dict()
        if _audit.overall_verdict == "FAIL":
            logger.error(_audit.log_line)
        elif _audit.overall_verdict == "WARN":
            logger.warning(_audit.log_line)
        else:
            logger.info(_audit.log_line)
    except Exception as _gov_err:
        logger.warning(f"[GOVERNANCE] Audit engine failed to run: {_gov_err}")
        result["_governance"] = {
            "overall_verdict": "UNVERIFIABLE",
            "error": str(_gov_err),
            "audit_version": "1.0.0",
        }

    return result


def _extract_propagation_steps(snapshot: GraphSnapshot) -> list[dict]:
    """Extract propagation step data from activated edges."""
    return [
        {
            "from": e.source,
            "to": e.target,
            "weight": e.weight,
            "transmission": e.transmission,
            "label": e.label,
        }
        for e in snapshot.activated_edges
    ]


def _compute_sector_rollups(snapshot: GraphSnapshot) -> dict:
    """Compute sector-level stress rollups from graph snapshot.

    Mathematical formulas:
        sector_stress = mean(node_stress for nodes in sector)
        sector_loss = sum(node_loss for nodes in sector)
        classification = classify(sector_stress)

    Sector mapping:
        banking  → finance layer nodes
        insurance → finance layer nodes with insurance type
        fintech  → finance + infrastructure (telecom/payment nodes)
    """
    # Group impacted nodes by layer
    layer_nodes: dict[str, list] = {}
    for node in snapshot.impacted_nodes:
        if node.stress > 0:
            layer_nodes.setdefault(node.layer, []).append(node)

    def _sector_stats(nodes):
        if not nodes:
            return {"aggregate_stress": 0, "total_loss": 0, "node_count": 0, "classification": "NOMINAL"}
        stresses = [n.stress for n in nodes]
        return {
            "aggregate_stress": round(sum(stresses) / len(stresses), 4),
            "total_loss": round(sum(n.loss_usd for n in nodes), 2),
            "node_count": len(nodes),
            "classification": _classify(sum(stresses) / len(stresses)),
        }

    finance_nodes = layer_nodes.get("finance", [])
    economy_nodes = layer_nodes.get("economy", [])
    infra_nodes = layer_nodes.get("infrastructure", [])

    return {
        "banking": _sector_stats(finance_nodes),
        "insurance": _sector_stats([n for n in finance_nodes if "insur" in n.label.lower() or "reinsur" in n.label.lower()]),
        "fintech": _sector_stats([n for n in finance_nodes + infra_nodes if "telecom" in n.label.lower() or "payment" in n.label.lower() or "tadawul" in n.label.lower()]),
        "energy": _sector_stats([n for n in economy_nodes if "oil" in n.label.lower() or "fuel" in n.label.lower() or "energy" in n.label.lower()]),
        "aviation": _sector_stats([n for n in economy_nodes if "aviat" in n.label.lower() or "airline" in n.label.lower() or "airport" in n.label.lower()]),
        "shipping": _sector_stats([n for n in economy_nodes + infra_nodes if "ship" in n.label.lower() or "port" in n.label.lower()]),
    }


def _classify(stress: float) -> str:
    if stress >= 0.8: return "CRITICAL"
    if stress >= 0.6: return "ELEVATED"
    if stress >= 0.4: return "MODERATE"
    if stress >= 0.2: return "LOW"
    return "NOMINAL"


def _compute_decision_inputs(
    snapshot: GraphSnapshot,
    sector_rollups: dict,
    severity: float,
) -> dict:
    """Derive decision inputs from simulation outputs.

    Priority formula:
        Priority = 0.25 × Urgency + 0.30 × Value + 0.20 × RegRisk + 0.15 × Feasibility + 0.10 × TimeEffect

    These inputs feed the existing decision engine (services/decision/engine.py).
    """
    # Top impacted nodes → action candidates
    critical_nodes = [n for n in snapshot.impacted_nodes if n.classification in ("CRITICAL", "ELEVATED")]
    critical_nodes.sort(key=lambda n: -n.stress)

    actions = []
    for i, node in enumerate(critical_nodes[:5]):
        urgency = min(1.0, node.stress * severity * 1.5)
        value = node.loss_usd
        reg_risk = 0.5 if node.layer == "finance" else 0.3
        feasibility = 0.7
        time_effect = 0.8 if node.stress > 0.7 else 0.5

        priority = (0.25 * urgency + 0.30 * min(1.0, value / 1e9) +
                    0.20 * reg_risk + 0.15 * feasibility + 0.10 * time_effect)

        actions.append({
            "id": f"act_{i+1:03d}",
            "action": f"Mitigate stress on {node.label}",
            "action_ar": f"تخفيف الضغط على {node.label_ar}",
            "sector": node.layer,
            "owner": "Risk Committee" if node.layer == "finance" else "Operations",
            "urgency": round(urgency, 2),
            "value": round(value, 2),
            "regulatory_risk": round(reg_risk, 2),
            "priority": round(priority, 4),
            "target_node_id": node.node_id,
            "target_lat": node.lat,
            "target_lng": node.lng,
            "loss_avoided_usd": round(value * 0.6, 2),
            "cost_usd": round(value * 0.05, 2),
            "confidence": round(1.0 - node.stress * 0.3, 2),
        })

    actions.sort(key=lambda a: -a["priority"])

    return {
        "run_id": "",  # Filled by caller
        "total_loss_usd": snapshot.total_estimated_loss_usd,
        "actions": actions,
        "all_actions": actions,
    }


def _build_result(
    state: SimulationState,
    confidence: float,
    warnings: list[str],
    physics_output: dict = None,
    math_output: dict = None,
    sector_output: dict = None,
) -> dict:
    """Build the unified result dict from simulation state."""
    snapshot = state.graph_snapshot
    physics_output = physics_output or {}
    math_output = math_output or {}
    sector_output = sector_output or {}

    # Graph payload (for Graph Explorer)
    graph_payload = {
        "nodes": [n.model_dump() for n in snapshot.impacted_nodes] if snapshot else [],
        "edges": [e.model_dump() for e in snapshot.activated_edges] if snapshot else [],
        "categories": ["geography", "infrastructure", "economy", "finance", "society"],
    }

    # Map payload (for Impact Map surface)
    map_payload = {
        "impacted_entities": [
            {
                "node_id": n.node_id,
                "label": n.label,
                "label_ar": n.label_ar,
                "lat": n.lat,
                "lng": n.lng,
                "stress": n.stress,
                "loss_usd": n.loss_usd,
                "classification": n.classification,
                "layer": n.layer,
            }
            for n in (snapshot.impacted_nodes if snapshot else [])
            if n.stress > 0
        ],
        "total_estimated_loss_usd": snapshot.total_estimated_loss_usd if snapshot else 0,
    }

    return {
        "run_id": state.run_id,
        "status": "completed",
        "scenario": {
            "template_id": state.scenario_id,
            "label": state.scenario_label,
            "severity": state.severity,
            "horizon_hours": state.horizon_hours,
        },
        "headline": {
            "total_loss_usd": snapshot.total_estimated_loss_usd if snapshot else 0,
            "total_nodes_impacted": snapshot.total_nodes_impacted if snapshot else 0,
            "propagation_depth": snapshot.propagation_depth if snapshot else 0,
        },
        "graph_payload": graph_payload,
        "map_payload": map_payload,
        "propagation_steps": state.propagation_result.get("steps", []) if state.propagation_result else [],
        "sector_rollups": {
            "banking": state.banking_stress or {},
            "insurance": state.insurance_stress or {},
            "fintech": state.fintech_stress or {},
        },
        "decision_inputs": state.decisions or {"actions": []},
        "confidence": confidence,
        "warnings": warnings,
        "stages_completed": state.get_stages_completed(),
        "stage_log": state.stage_log,
        "duration_ms": state.elapsed_ms(),
        # ── New fields from real engines ─────────────────────
        "physics": {
            "utilization_map": physics_output.get("utilization_map", {}),
            "bottlenecks": physics_output.get("bottlenecks", {}),
            "flow_conservation": physics_output.get("flow_conservation", {}),
            "recovery": physics_output.get("recovery", {}),
            "system_stress": physics_output.get("system_stress", {}),
            "system_pressure": physics_output.get("system_pressure", {}),
            "shockwave_field": physics_output.get("shockwave_field", []),
            "propagation_result": physics_output.get("propagation_result", {}),
        },
        "math": {
            "risk_scores": math_output.get("risk_scores", []),
            "model_confidence": math_output.get("model_confidence", 0.0),
            "confidence_interval": math_output.get("confidence_interval", {}),
            "disruption_index": math_output.get("disruption_index", {}),
            "sector_exposure": math_output.get("sector_exposure", {}),
            "system_energy": math_output.get("system_energy", 0.0),
            "propagation_depth": math_output.get("propagation_depth", 0),
            "sector_spread": math_output.get("sector_spread", 0),
        },
        "sectors": {
            "financial_impacts": sector_output.get("financial_impacts", []),
            "financial_headline": sector_output.get("financial_headline", {}),
            "banking_stresses": sector_output.get("banking_stresses", []),
            "banking_aggregate": sector_output.get("banking_aggregate", {}),
            "insurance_stresses": sector_output.get("insurance_stresses", []),
            "insurance_aggregate": sector_output.get("insurance_aggregate", {}),
            "fintech_stresses": sector_output.get("fintech_stresses", []),
            "fintech_aggregate": sector_output.get("fintech_aggregate", {}),
            "decision_plan": sector_output.get("decision_plan", {}),
            "explanation": sector_output.get("explanation", {}),
            "regulatory_state": sector_output.get("regulatory_state", {}),
        },
        "assumptions": _build_assumptions(state, physics_output, math_output, sector_output),
    }


def _build_assumptions(
    state: SimulationState,
    physics_output: dict,
    math_output: dict,
    sector_output: dict,
) -> list[str]:
    """Build explicit assumptions list for audit trail."""
    assumptions = [
        f"Scenario: {state.scenario_id} at severity={state.severity}",
        f"Horizon: {state.horizon_hours}h ({state.horizon_hours // 24}d)",
        "Graph: 76-node GCC knowledge graph with 190 causal edges",
        "Propagation: 6-iteration discrete dynamic model with damping",
        "Loss model: stress × weight × $1B base value per unit",
        "Regional multipliers: SA=1.15, UAE=1.20, KW=1.05, QA=1.10, OM=0.95, BH=1.00",
    ]

    if physics_output:
        recovery = physics_output.get("recovery", {})
        if isinstance(recovery, dict) and "recovery_score" in recovery:
            assumptions.append(f"Recovery rate: 0.05/day, score={recovery['recovery_score']:.2f}")

    if math_output:
        mc = math_output.get("model_confidence", 0)
        if mc:
            assumptions.append(f"Model confidence: {mc:.3f}")

    if sector_output:
        fin_count = len(sector_output.get("financial_impacts", []))
        if fin_count:
            assumptions.append(f"Financial entities modeled: {fin_count}")
        reg = sector_output.get("regulatory_state", {})
        if isinstance(reg, dict) and reg.get("jurisdiction"):
            assumptions.append(f"Regulatory jurisdiction: {reg['jurisdiction']}")

    return assumptions


def _build_error_result(state: SimulationState, error: str) -> dict:
    """Build an error result when the pipeline fails early.

    Must include ALL keys from _build_result to satisfy the frontend contract.
    Missing keys cause adapter crashes (toFixed on undefined, .map on null).
    """
    return {
        "run_id": state.run_id,
        "status": "failed",
        "error": error,
        "scenario": {
            "template_id": state.scenario_id,
            "label": state.scenario_label,
            "severity": state.severity,
            "horizon_hours": state.horizon_hours,
        },
        "headline": {"total_loss_usd": 0, "total_nodes_impacted": 0, "propagation_depth": 0},
        "graph_payload": {"nodes": [], "edges": [], "categories": []},
        "map_payload": {"impacted_entities": [], "total_estimated_loss_usd": 0},
        "propagation_steps": [],
        "sector_rollups": {"banking": {}, "insurance": {}, "fintech": {}},
        "decision_inputs": {"actions": []},
        "confidence": 0.1,
        "warnings": state.warnings + [f"Pipeline failed: {error}"],
        "stages_completed": state.get_stages_completed(),
        "stage_log": state.stage_log,
        "duration_ms": state.elapsed_ms(),
        "physics": {
            "utilization_map": {}, "bottlenecks": {}, "flow_conservation": {},
            "recovery": {}, "system_stress": {}, "system_pressure": {},
            "shockwave_field": [], "propagation_result": {},
        },
        "math": {
            "risk_scores": [], "model_confidence": 0.0, "confidence_interval": {},
            "disruption_index": {}, "sector_exposure": {}, "system_energy": 0.0,
            "propagation_depth": 0, "sector_spread": 0,
        },
        "sectors": {
            "financial_impacts": [], "financial_headline": {},
            "banking_stresses": [], "banking_aggregate": {},
            "insurance_stresses": [], "insurance_aggregate": {},
            "fintech_stresses": [], "fintech_aggregate": {},
            "decision_plan": {}, "explanation": {}, "regulatory_state": {},
        },
        "assumptions": [],
        "trust": {},
    }
