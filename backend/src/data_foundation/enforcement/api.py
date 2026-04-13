"""Decision Enforcement — API routes.

Prefix: /foundation/enforcement

Endpoints:
  POST   /policies                      — create enforcement policy
  GET    /policies                      — list active policies
  GET    /policies/{policy_id}          — get single policy
  POST   /evaluate/{decision_log_id}    — evaluate enforcement for a decision
  GET    /decisions/{enforcement_id}    — get enforcement decision
  GET    /decisions/by-decision/{id}    — get enforcement by decision_log_id
  GET    /gates/by-decision/{id}        — get gate results by decision_log_id
  GET    /approvals/pending             — list pending approvals
  GET    /approvals/{approval_id}       — get single approval
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from src.data_foundation.enforcement.schemas import (
    EnforcementPolicy,
    VALID_ENFORCEMENT_ACTIONS,
    VALID_POLICY_TYPES,
    VALID_SCOPE_TYPES,
    VALID_SEVERITY_LEVELS,
)
from src.data_foundation.enforcement.execution_gate_service import (
    can_execute_decision,
    get_approval,
    get_enforcement_by_decision_log,
    get_enforcement_decision,
    get_enforcement_gates,
    get_pending_approvals,
    persist_enforcement_outcome,
)
from src.data_foundation.enforcement.enforcement_audit import (
    audit_enforcement_evaluated,
    audit_enforcement_policy_created,
    audit_decision_blocked,
    audit_approval_required,
    audit_shadow_mode_activated,
)

router = APIRouter(prefix="/foundation/enforcement", tags=["enforcement"])

# In-memory policy store (same pattern as evaluation/feedback/replay APIs)
_policy_store: Dict[str, EnforcementPolicy] = {}


# ── Request Schemas ──────────────────────────────────────────────────────────

class CreatePolicyRequest(BaseModel):
    policy_id: str
    policy_name: str
    policy_type: str
    scope_type: str = "GLOBAL"
    scope_ref: Optional[str] = None
    conditions: Dict[str, Any] = Field(default_factory=dict)
    action_on_match: str
    severity: str = "MEDIUM"
    priority: int = 100
    is_active: bool = True
    rationale: str
    created_by: str


class EvaluateRequest(BaseModel):
    decision_rule_id: Optional[str] = None
    context: Dict[str, Any] = Field(default_factory=dict)
    rule_lifecycle_status: Optional[str] = None
    truth_validation_passed: Optional[bool] = None
    truth_critical_failure: bool = False
    has_unresolved_calibration: Optional[bool] = None
    data_freshness_passed: Optional[bool] = None
    explainability_score: Optional[float] = None
    explainability_threshold: float = 0.5
    financial_exposure_usd: Optional[float] = None
    financial_threshold_usd: float = 1_000_000_000.0
    has_conflicting_actions: Optional[bool] = None
    original_confidence: Optional[float] = None
    actor: str = "system"


# ── Policy CRUD ─��────────────────────────────────────────────────────────────

@router.post("/policies", status_code=201)
async def create_policy(body: CreatePolicyRequest):
    """Create an enforcement policy."""
    policy = EnforcementPolicy(**body.model_dump())
    _policy_store[policy.policy_id] = policy
    audit_enforcement_policy_created(
        policy.policy_id, body.created_by,
        {"policy_type": body.policy_type, "action_on_match": body.action_on_match},
    )
    return policy.model_dump()


@router.get("/policies")
async def list_policies():
    """List all active enforcement policies."""
    active = [p.model_dump() for p in _policy_store.values() if p.is_active]
    active.sort(key=lambda p: p["priority"])
    return {"policies": active, "count": len(active)}


@router.get("/policies/{policy_id}")
async def get_policy(policy_id: str):
    """Get a single enforcement policy."""
    pol = _policy_store.get(policy_id)
    if not pol:
        raise HTTPException(status_code=404, detail=f"Policy {policy_id} not found")
    return pol.model_dump()


# ── Enforcement Evaluation ───────────────────────────────────────────────────

@router.post("/evaluate/{decision_log_id}")
async def evaluate_enforcement(decision_log_id: str, body: EvaluateRequest):
    """Evaluate enforcement for a decision candidate.

    Runs all gates and policies, returns enforcement decision + gate results.
    """
    policies = list(_policy_store.values())

    decision, gates = can_execute_decision(
        decision_log_id=decision_log_id,
        decision_rule_id=body.decision_rule_id,
        policies=policies,
        context=body.context,
        rule_lifecycle_status=body.rule_lifecycle_status,
        truth_validation_passed=body.truth_validation_passed,
        truth_critical_failure=body.truth_critical_failure,
        has_unresolved_calibration=body.has_unresolved_calibration,
        data_freshness_passed=body.data_freshness_passed,
        explainability_score=body.explainability_score,
        explainability_threshold=body.explainability_threshold,
        financial_exposure_usd=body.financial_exposure_usd,
        financial_threshold_usd=body.financial_threshold_usd,
        has_conflicting_actions=body.has_conflicting_actions,
        original_confidence=body.original_confidence,
    )

    persist_enforcement_outcome(decision, gates)

    # Emit audit entries
    audit_enforcement_evaluated(
        decision.enforcement_id, body.actor,
        {"action": decision.enforcement_action, "decision_log_id": decision_log_id},
    )
    if decision.enforcement_action == "BLOCK":
        audit_decision_blocked(
            decision.enforcement_id, body.actor,
            {"reasons": decision.blocking_reasons},
        )
    if decision.enforcement_action == "REQUIRE_APPROVAL":
        audit_approval_required(
            decision.enforcement_id, body.actor,
            {"approver": decision.required_approver},
        )
    if decision.enforcement_action == "SHADOW_ONLY":
        audit_shadow_mode_activated(
            decision.enforcement_id, body.actor,
            {"decision_log_id": decision_log_id},
        )

    return {
        "enforcement": decision.model_dump(),
        "gates": [g.model_dump() for g in gates],
    }


# ── Enforcement Decision Lookup ──────────────────────────────────────────────

@router.get("/decisions/{enforcement_id}")
async def get_enforcement(enforcement_id: str):
    """Get an enforcement decision by ID."""
    d = get_enforcement_decision(enforcement_id)
    if not d:
        raise HTTPException(status_code=404, detail=f"Enforcement {enforcement_id} not found")
    gates = get_enforcement_gates(enforcement_id)
    return {
        "enforcement": d.model_dump(),
        "gates": [g.model_dump() for g in gates],
    }


@router.get("/decisions/by-decision/{decision_log_id}")
async def get_enforcement_by_decision(decision_log_id: str):
    """Get enforcement decision by decision_log_id."""
    d = get_enforcement_by_decision_log(decision_log_id)
    if not d:
        raise HTTPException(status_code=404, detail=f"No enforcement for decision {decision_log_id}")
    gates = get_enforcement_gates(d.enforcement_id)
    return {
        "enforcement": d.model_dump(),
        "gates": [g.model_dump() for g in gates],
    }


# ── Gate Results ─────────────────────────────────────────────────────────────

@router.get("/gates/by-decision/{decision_log_id}")
async def get_gates_by_decision(decision_log_id: str):
    """Get gate results for a decision."""
    d = get_enforcement_by_decision_log(decision_log_id)
    if not d:
        raise HTTPException(status_code=404, detail=f"No enforcement for decision {decision_log_id}")
    gates = get_enforcement_gates(d.enforcement_id)
    return {"gates": [g.model_dump() for g in gates], "count": len(gates)}


# ── Approval Requests ────────────────────────────────────────────────────────

@router.get("/approvals/pending")
async def list_pending_approvals():
    """List all pending approval requests."""
    pending = get_pending_approvals()
    return {"approvals": [a.model_dump() for a in pending], "count": len(pending)}


@router.get("/approvals/{approval_id}")
async def get_approval_request(approval_id: str):
    """Get a single approval request."""
    a = get_approval(approval_id)
    if not a:
        raise HTTPException(status_code=404, detail=f"Approval {approval_id} not found")
    return a.model_dump()
