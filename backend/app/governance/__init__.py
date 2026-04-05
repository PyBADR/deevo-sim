"""
Impact Observatory | مرصد الأثر — Governance Package

Single-import surface for all governance components.

Usage:
    from app.governance import audit_run, run_governance_checks
    from app.governance import CANONICAL_REGISTRY, get_geo_scope
    from app.governance import check_invariants, InvariantViolation, Severity
    from app.governance import FailureCluster, IncidentSignature, cluster_incidents
"""

from .registry import (
    CANONICAL_REGISTRY,
    CanonicalScenario,
    MinViableOutput,
    VALID_DOMAINS,
    get_entry,
    require_entry,
    get_all_ids,
    get_geo_scope,
    is_known_scenario,
    get_mvoe,
)

from .invariants import (
    InvariantViolation,
    Severity,
    check_invariants,
)

from .audit import (
    RunAudit,
    audit_run,
    AUDIT_VERSION,
)

from .clustering import (
    FailureCluster,
    ClusterResult,
    deterministic_cluster,
    IncidentSignature,
    jaccard_similarity,
    cluster_incidents,
    summarize_clusters,
)

from .governor import (
    CheckStatus,
    GovernanceCheck,
    GovernanceResult,
    run_governance_checks,
)

__all__ = [
    # registry
    "CANONICAL_REGISTRY", "CanonicalScenario", "MinViableOutput", "VALID_DOMAINS",
    "get_entry", "require_entry", "get_all_ids", "get_geo_scope",
    "is_known_scenario", "get_mvoe",
    # invariants
    "InvariantViolation", "Severity", "check_invariants",
    # audit
    "RunAudit", "audit_run", "AUDIT_VERSION",
    # clustering
    "FailureCluster", "ClusterResult", "deterministic_cluster",
    "IncidentSignature", "jaccard_similarity", "cluster_incidents", "summarize_clusters",
    # governor
    "CheckStatus", "GovernanceCheck", "GovernanceResult", "run_governance_checks",
]
