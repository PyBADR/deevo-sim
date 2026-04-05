"""
Impact Observatory | مرصد الأثر — Runtime Audit Engine

Evaluates every run result against the governance invariants and produces
a structured RunAudit object attached to the result as result["_governance"].

The audit is OBSERVATIONAL at runtime — it never modifies run status or
blocks execution. It logs warnings/errors for governance violations.
The BUILD GOVERNOR (governor.py) is what blocks deployments.

RunAudit fields:
  scenario_id, run_id, run_severity     — identity
  status                                — from run result
  loss_valid, impact_valid,             — per-output validity flags
  actions_valid, graph_valid,
  map_valid, geo_scope_valid
  invariant_violations                  — list of InvariantViolation
  hard_fail_count, soft_fail_count,     — violation counts by severity
  silent_failure_count
  failure_cluster                       — primary FailureCluster label
  secondary_clusters                    — additional matching clusters
  overall_verdict                       — PASS | WARN | FAIL | UNVERIFIABLE
  audit_timestamp, audit_version        — metadata
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from .registry import get_entry, is_known_scenario
from .invariants import check_invariants, InvariantViolation, Severity
from .clustering import deterministic_cluster, FailureCluster


AUDIT_VERSION = "1.0.0"

# Overall verdict mapping:
#   FAIL        — at least one HARD_FAIL or SILENT_FAILURE violation
#   WARN        — at least one SOFT_FAIL, no HARD_FAIL / SILENT_FAILURE
#   PASS        — no violations, run completed with non-zero outputs
#   UNVERIFIABLE — no violations but run status is not completed/failed
#                  (e.g. run is still processing, or status field absent)


@dataclass
class RunAudit:
    # ── Identity ──────────────────────────────────────────────────────────────
    scenario_id: str
    run_id: str
    run_severity: float

    # ── Pipeline status ───────────────────────────────────────────────────────
    status: str

    # ── Per-output validity flags ─────────────────────────────────────────────
    loss_valid: bool           # total_loss_usd > 0
    impact_valid: bool         # total_nodes_impacted > 0
    actions_valid: bool        # decision actions >= MVOE
    graph_valid: bool          # graph_payload.edges non-empty (when graph_supported)
    map_valid: bool            # map_payload.impacted_entities non-empty (when map_supported)
    geo_scope_valid: bool      # scenario_id is in canonical registry → geo_scope is correct

    # ── Invariant analysis ────────────────────────────────────────────────────
    invariant_violations: List[InvariantViolation]
    hard_fail_count: int
    soft_fail_count: int
    silent_failure_count: int

    # ── Cluster assignment ────────────────────────────────────────────────────
    failure_cluster: str            # primary FailureCluster.value
    secondary_clusters: List[str]   # secondary FailureCluster.value list

    # ── Verdict ───────────────────────────────────────────────────────────────
    overall_verdict: str            # "PASS" | "WARN" | "FAIL" | "UNVERIFIABLE"

    # ── Metadata ──────────────────────────────────────────────────────────────
    audit_timestamp: str
    audit_version: str

    def to_dict(self) -> dict:
        return {
            "scenario_id": self.scenario_id,
            "run_id": self.run_id,
            "run_severity": self.run_severity,
            "status": self.status,
            "loss_valid": self.loss_valid,
            "impact_valid": self.impact_valid,
            "actions_valid": self.actions_valid,
            "graph_valid": self.graph_valid,
            "map_valid": self.map_valid,
            "geo_scope_valid": self.geo_scope_valid,
            "invariant_violations": [v.to_dict() for v in self.invariant_violations],
            "hard_fail_count": self.hard_fail_count,
            "soft_fail_count": self.soft_fail_count,
            "silent_failure_count": self.silent_failure_count,
            "failure_cluster": self.failure_cluster,
            "secondary_clusters": self.secondary_clusters,
            "overall_verdict": self.overall_verdict,
            "audit_timestamp": self.audit_timestamp,
            "audit_version": self.audit_version,
        }

    @property
    def is_clean(self) -> bool:
        return self.overall_verdict == "PASS"

    @property
    def is_silent_failure(self) -> bool:
        return self.failure_cluster == FailureCluster.SILENT_ZERO_COMPLETION.value

    @property
    def log_line(self) -> str:
        """Single-line log summary for run audit."""
        violations_summary = (
            f"hard={self.hard_fail_count} "
            f"silent={self.silent_failure_count} "
            f"soft={self.soft_fail_count}"
        )
        return (
            f"[GOVERNANCE] verdict={self.overall_verdict} "
            f"cluster={self.failure_cluster} "
            f"{violations_summary} "
            f"scenario={self.scenario_id} "
            f"run={self.run_id}"
        )


def audit_run(
    scenario_id: str,
    run_result: Dict[str, Any],
    run_severity: float = 0.7,
    shock_vector: Optional[List[dict]] = None,
) -> RunAudit:
    """
    Evaluate a run result against all governance invariants.

    This function is called at the end of run_unified_pipeline() and its
    output is attached to result["_governance"]. It is also callable
    independently for post-hoc analysis of stored results.

    Parameters
    ----------
    scenario_id : str
        The scenario_id that was executed.
    run_result : dict
        The full pipeline result dict (UnifiedRunResult shape).
    run_severity : float
        The severity value used for this run. Used to scale loss MVOE.
    shock_vector : list[dict] | None
        If provided, passed to RULE-005. If None, RULE-005 resolves it
        from bridge.py directly.

    Returns
    -------
    RunAudit
        Full audit object. Call .to_dict() to serialize.
    """
    entry = get_entry(scenario_id)

    # ── Extract output fields ─────────────────────────────────────────────────
    headline = run_result.get("headline", {}) or {}
    total_loss = headline.get("total_loss_usd") or 0
    total_nodes = headline.get("total_nodes_impacted") or 0

    graph_payload = run_result.get("graph_payload", {}) or {}
    edges = graph_payload.get("edges") or []

    map_payload = run_result.get("map_payload", {}) or {}
    map_entities = map_payload.get("impacted_entities") or []

    decision_inputs = run_result.get("decision_inputs", {}) or {}
    actions = decision_inputs.get("actions") or []

    status = run_result.get("status", "unknown")

    # ── Run invariant checks ──────────────────────────────────────────────────
    violations = check_invariants(
        scenario_id=scenario_id,
        run_result=run_result,
        run_severity=run_severity,
        shock_vector=shock_vector,
    )

    hard_fails = [v for v in violations if v.severity == Severity.HARD_FAIL]
    soft_fails = [v for v in violations if v.severity == Severity.SOFT_FAIL]
    silent_failures = [v for v in violations if v.severity == Severity.SILENT_FAILURE]

    # ── Per-output validity flags ─────────────────────────────────────────────
    loss_valid = total_loss > 0
    impact_valid = total_nodes > 0
    actions_valid = len(actions) >= (entry.mvoe.actions if entry else 1)

    # graph_valid: only enforced when scenario declares graph_supported=True
    if entry and entry.graph_supported:
        graph_valid = len(edges) > 0
    else:
        graph_valid = True  # capability not declared — not a violation

    # map_valid: only enforced when scenario declares map_supported=True
    if entry and entry.map_supported:
        map_valid = len(map_entities) > 0
    else:
        map_valid = True

    # geo_scope_valid: True if scenario is in canonical registry (meaning Stage 3
    # would have called get_geo_scope() and gotten a real scope, not the fallback)
    geo_scope_valid = is_known_scenario(scenario_id)

    # ── Failure cluster assignment ────────────────────────────────────────────
    violated_rule_ids = {v.rule_id for v in violations}
    cluster_result = deterministic_cluster(
        violation_rule_ids=violated_rule_ids,
        status=status,
        total_loss=total_loss,
        total_nodes=total_nodes,
        total_actions=len(actions),
        total_edges=len(edges),
    )

    # ── Overall verdict ───────────────────────────────────────────────────────
    if hard_fails or silent_failures:
        overall_verdict = "FAIL"
    elif soft_fails:
        overall_verdict = "WARN"
    elif status in ("completed", "failed"):
        overall_verdict = "PASS"
    else:
        overall_verdict = "UNVERIFIABLE"

    return RunAudit(
        scenario_id=scenario_id,
        run_id=run_result.get("run_id", ""),
        run_severity=run_severity,
        status=status,
        loss_valid=loss_valid,
        impact_valid=impact_valid,
        actions_valid=actions_valid,
        graph_valid=graph_valid,
        map_valid=map_valid,
        geo_scope_valid=geo_scope_valid,
        invariant_violations=violations,
        hard_fail_count=len(hard_fails),
        soft_fail_count=len(soft_fails),
        silent_failure_count=len(silent_failures),
        failure_cluster=cluster_result.primary_cluster.value,
        secondary_clusters=[c.value for c in cluster_result.secondary_clusters],
        overall_verdict=overall_verdict,
        audit_timestamp=datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        audit_version=AUDIT_VERSION,
    )
