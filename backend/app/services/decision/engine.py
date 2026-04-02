"""
Impact Observatory | مرصد الأثر — Decision Engine (v4 §3.9-3.10)
5-Factor Priority Formula producing top-3 DecisionAction objects.

Priority = 0.25×Urgency + 0.30×Value + 0.20×RegRisk + 0.15×Feasibility + 0.10×TimeEffect
"""

import math
import uuid
from typing import List

from ...domain.models.scenario import Scenario
from ...domain.models.financial_impact import FinancialImpact
from ...domain.models.banking_stress import BankingStress
from ...domain.models.insurance_stress import InsuranceStress
from ...domain.models.fintech_stress import FintechStress
from ...domain.models.decision import DecisionAction, DecisionPlan
from ...core.constants import (
    DECISION_WEIGHT_URGENCY, DECISION_WEIGHT_VALUE,
    DECISION_WEIGHT_REG_RISK, DECISION_WEIGHT_FEASIBILITY,
    DECISION_WEIGHT_TIME_EFFECT, DECISION_TOP_K, DECISION_MIN_FEASIBILITY,
)


def compute_decisions(
    run_id: str,
    scenario: Scenario,
    financial_impacts: List[FinancialImpact],
    banking_stresses: List[BankingStress],
    insurance_stresses: List[InsuranceStress],
    fintech_stresses: List[FintechStress],
) -> DecisionPlan:
    """
    v4 §3.9-3.10 — Compute top-3 decision actions via multi-objective optimization.

    Returns:
        DecisionPlan with ranked actions and metadata
    """
    from datetime import datetime, timezone
    now = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")

    # Aggregate metrics for candidate evaluation
    total_loss = sum(fi.loss for fi in financial_impacts) or 1.0
    any_banking_breach = any(
        s.breach_flags.lcr_breach or s.breach_flags.car_breach
        for s in banking_stresses
    )
    any_insurance_breach = any(
        s.breach_flags.solvency_breach or s.breach_flags.reserve_breach
        for s in insurance_stresses
    )
    any_fintech_breach = any(
        s.breach_flags.availability_breach or s.breach_flags.settlement_breach
        for s in fintech_stresses
    )

    # Time to failure estimate (hours)
    ttf_hours = max(24, int((14 * 24) / max(0.1, scenario.shock_intensity * 2)))

    # Candidate pool (v4 action_type enum values)
    candidates = [
        {
            "action_type": "inject_liquidity",
            "target_level": "sector", "target_ref": "banking",
            "cost": 2.5e9, "loss_reduction": 45,
            "reg_risk": 0.15, "exec_prob": 0.90, "resource": 0.85,
            "time_to_act_h": 24, "time_to_effect_h": 12,
            "execution_window": 48,
            "reason_codes": ["lcr_breach", "car_breach", "flow_interrupted"],
            "applies": any_banking_breach,
            "requires_override": False,
        },
        {
            "action_type": "activate_bcp",
            "target_level": "sector", "target_ref": "fintech",
            "cost": 350e6, "loss_reduction": 8,
            "reg_risk": 0.10, "exec_prob": 0.95, "resource": 0.90,
            "time_to_act_h": 12, "time_to_effect_h": 6,
            "execution_window": 24,
            "reason_codes": ["availability_breach", "settlement_breach"],
            "applies": any_fintech_breach,
            "requires_override": False,
        },
        {
            "action_type": "increase_reserves",
            "target_level": "sector", "target_ref": "insurance",
            "cost": 800e6, "loss_reduction": 12,
            "reg_risk": 0.20, "exec_prob": 0.85, "resource": 0.80,
            "time_to_act_h": 48, "time_to_effect_h": 72,
            "execution_window": 72,
            "reason_codes": ["solvency_breach", "reserve_breach", "loss_exceeds_threshold"],
            "applies": any_insurance_breach,
            "requires_override": True,
        },
        {
            "action_type": "restrict_exposure",
            "target_level": "system", "target_ref": "all",
            "cost": 1.2e9, "loss_reduction": 18,
            "reg_risk": 0.25, "exec_prob": 0.75, "resource": 0.70,
            "time_to_act_h": 72, "time_to_effect_h": 120,
            "execution_window": 96,
            "reason_codes": ["loss_exceeds_threshold"],
            "applies": total_loss > 100,
            "requires_override": False,
        },
        {
            "action_type": "raise_capital_buffer",
            "target_level": "sector", "target_ref": "banking",
            "cost": 15e9, "loss_reduction": 65,
            "reg_risk": 0.30, "exec_prob": 0.80, "resource": 0.75,
            "time_to_act_h": 48, "time_to_effect_h": 48,
            "execution_window": 72,
            "reason_codes": ["cet1_breach", "car_breach"],
            "applies": any(s.breach_flags.cet1_breach for s in banking_stresses),
            "requires_override": True,
        },
        {
            "action_type": "trigger_regulatory_escalation",
            "target_level": "system", "target_ref": "regulator",
            "cost": 400e6, "loss_reduction": 5,
            "reg_risk": 0.45, "exec_prob": 0.70, "resource": 0.60,
            "time_to_act_h": 24, "time_to_effect_h": 48,
            "execution_window": 48,
            "reason_codes": ["solvency_breach", "lcr_breach"],
            "applies": any_banking_breach and any_insurance_breach,
            "requires_override": True,
        },
        {
            "action_type": "reroute_flow",
            "target_level": "sector", "target_ref": "fintech",
            "cost": 500e6, "loss_reduction": 6,
            "reg_risk": 0.15, "exec_prob": 0.80, "resource": 0.75,
            "time_to_act_h": 72, "time_to_effect_h": 96,
            "execution_window": 96,
            "reason_codes": ["settlement_breach", "flow_interrupted"],
            "applies": any_fintech_breach,
            "requires_override": False,
        },
        {
            "action_type": "reduce_counterparty_limit",
            "target_level": "entity", "target_ref": "bank-gcc-001",
            "cost": 250e6, "loss_reduction": 4,
            "reg_risk": 0.55, "exec_prob": 0.60, "resource": 0.50,
            "time_to_act_h": 96, "time_to_effect_h": 120,
            "execution_window": 120,
            "reason_codes": ["operational_risk_breach"],
            "applies": any(s.breach_flags.operational_risk_breach for s in fintech_stresses),
            "requires_override": True,
        },
    ]

    # Filter applicable
    applicable = [c for c in candidates if c["applies"]]
    if not applicable:
        applicable = sorted(candidates, key=lambda x: x["loss_reduction"], reverse=True)[:DECISION_TOP_K]

    # Compute 5-factor priority
    LAMBDA = 0.01
    for c in applicable:
        urgency = max(0.0, 1.0 - c["time_to_act_h"] / max(1.0, ttf_hours))
        value = min(1.0, max(0.0, (c["loss_reduction"] * 1e9 - c["cost"]) / max(1, total_loss * 1e9)))
        feasibility = c["exec_prob"] * c["resource"]
        time_effect = math.exp(-LAMBDA * c["time_to_effect_h"])

        priority = (
            DECISION_WEIGHT_URGENCY * urgency +
            DECISION_WEIGHT_VALUE * value +
            DECISION_WEIGHT_REG_RISK * c["reg_risk"] +
            DECISION_WEIGHT_FEASIBILITY * feasibility +
            DECISION_WEIGHT_TIME_EFFECT * time_effect
        )
        c["_urgency"] = round(urgency, 4)
        c["_value"] = round(value, 4)
        c["_feasibility"] = round(feasibility, 4)
        c["_time_effect"] = round(time_effect, 4)
        c["_priority"] = round(min(1.0, max(0.0, priority)), 4)

    # Filter by minimum feasibility
    feasible = [c for c in applicable if c["_feasibility"] >= DECISION_MIN_FEASIBILITY]
    if not feasible:
        feasible = applicable

    # Sort and take top K
    sorted_actions = sorted(feasible, key=lambda x: x["_priority"], reverse=True)[:DECISION_TOP_K]

    # Build v4 DecisionAction objects
    actions: List[DecisionAction] = []
    for rank, c in enumerate(sorted_actions, start=1):
        actions.append(DecisionAction(
            action_id=str(uuid.uuid4()),
            run_id=run_id,
            rank=rank,
            action_type=c["action_type"],
            target_level=c["target_level"],
            target_ref=c["target_ref"],
            urgency=c["_urgency"],
            value=c["_value"],
            reg_risk=c["reg_risk"],
            feasibility=c["_feasibility"],
            time_effect=c["_time_effect"],
            priority_score=c["_priority"],
            reason_codes=c["reason_codes"],
            preconditions=[],
            expected_loss_reduction=c["loss_reduction"],
            expected_flow_recovery=0.0,
            execution_window_hours=c["execution_window"],
            requires_override=c["requires_override"],
        ))

    # Build DecisionPlan
    plan = DecisionPlan(
        run_id=run_id,
        generated_at=now,
        model_version="4.0.0",
        candidate_count=len(candidates),
        feasible_count=len(feasible),
        actions=actions,
        dropped_actions_count=len(feasible) - len(actions),
        constrained_by_rbac=False,
        constrained_by_regulation=any(c["requires_override"] for c in sorted_actions),
        plan_status="complete" if actions else "empty",
    )

    return plan
