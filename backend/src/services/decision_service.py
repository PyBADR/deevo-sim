"""Service 9: decision_service — Decision Actions (قرارات الإجراء).

Computes:
    Urgency = Time_to_failure / Time_to_act
    Value = Loss_avoided - Cost
    Priority = Value + Urgency + RegulatoryRisk

Outputs top 3 actions only.

Target users: CRO, Treasury, Actuary, Ops, Regulator.
"""

from __future__ import annotations

import logging
import uuid

from src.schemas.decision import DecisionAction, DecisionPlan
from src.schemas.banking_stress import BankingStress
from src.schemas.insurance_stress import InsuranceStress
from src.schemas.fintech_stress import FintechStress
from src.schemas.financial_impact import FinancialImpact

logger = logging.getLogger(__name__)


# ── Action Templates ──────────────────────────────────────────────────
ACTION_TEMPLATES = [
    # Banking actions
    {
        "sector": "banking",
        "action": "Activate emergency liquidity facility with central bank",
        "action_ar": "تفعيل تسهيلات السيولة الطارئة مع البنك المركزي",
        "owner": "Treasury",
        "time_to_act_hours": 24,
        "cost_usd": 50_000_000,
        "loss_avoidable_pct": 0.15,
        "regulatory_risk": 0.7,
        "trigger": lambda bs, _is, _fs: bs.liquidity_stress > 0.3,
    },
    {
        "sector": "banking",
        "action": "Reduce interbank exposure limits by 40%",
        "action_ar": "تقليل حدود التعرض بين البنوك بنسبة 40%",
        "owner": "CRO",
        "time_to_act_hours": 12,
        "cost_usd": 20_000_000,
        "loss_avoidable_pct": 0.10,
        "regulatory_risk": 0.5,
        "trigger": lambda bs, _is, _fs: bs.interbank_contagion > 0.3,
    },
    {
        "sector": "banking",
        "action": "Hedge FX exposure via forward contracts",
        "action_ar": "تحوط التعرض للعملات عبر عقود آجلة",
        "owner": "Treasury",
        "time_to_act_hours": 48,
        "cost_usd": 30_000_000,
        "loss_avoidable_pct": 0.08,
        "regulatory_risk": 0.3,
        "trigger": lambda bs, _is, _fs: bs.fx_stress > 0.4,
    },
    # Insurance actions
    {
        "sector": "insurance",
        "action": "Trigger catastrophe reinsurance treaty",
        "action_ar": "تفعيل اتفاقية إعادة التأمين ضد الكوارث",
        "owner": "Actuary",
        "time_to_act_hours": 72,
        "cost_usd": 100_000_000,
        "loss_avoidable_pct": 0.25,
        "regulatory_risk": 0.6,
        "trigger": lambda _bs, ins, _fs: ins.claims_surge_multiplier > 1.5,
    },
    {
        "sector": "insurance",
        "action": "Suspend new marine cargo underwriting in Gulf zone",
        "action_ar": "تعليق اكتتاب الشحن البحري الجديد في منطقة الخليج",
        "owner": "Actuary",
        "time_to_act_hours": 24,
        "cost_usd": 15_000_000,
        "loss_avoidable_pct": 0.12,
        "regulatory_risk": 0.4,
        "trigger": lambda _bs, ins, _fs: ins.underwriting_status in ("warning", "critical"),
    },
    {
        "sector": "insurance",
        "action": "Increase IFRS-17 risk adjustment provision",
        "action_ar": "زيادة مخصص تعديل المخاطر وفق IFRS-17",
        "owner": "Actuary",
        "time_to_act_hours": 168,
        "cost_usd": 40_000_000,
        "loss_avoidable_pct": 0.05,
        "regulatory_risk": 0.8,
        "trigger": lambda _bs, ins, _fs: ins.severity_index > 0.4,
    },
    # Fintech actions
    {
        "sector": "fintech",
        "action": "Switch cross-border payments to backup corridor (Buna)",
        "action_ar": "تحويل المدفوعات العابرة للحدود إلى ممر بديل (بنى)",
        "owner": "Ops",
        "time_to_act_hours": 6,
        "cost_usd": 5_000_000,
        "loss_avoidable_pct": 0.08,
        "regulatory_risk": 0.3,
        "trigger": lambda _bs, _is, fs: fs.cross_border_disruption > 0.3,
    },
    {
        "sector": "fintech",
        "action": "Activate payment system disaster recovery site",
        "action_ar": "تفعيل موقع التعافي من الكوارث لنظام المدفوعات",
        "owner": "Ops",
        "time_to_act_hours": 4,
        "cost_usd": 10_000_000,
        "loss_avoidable_pct": 0.15,
        "regulatory_risk": 0.5,
        "trigger": lambda _bs, _is, fs: fs.api_availability_pct < 85,
    },
    # Energy/Government actions
    {
        "sector": "energy",
        "action": "Activate strategic petroleum reserve release",
        "action_ar": "تفعيل الإفراج عن الاحتياطي النفطي الاستراتيجي",
        "owner": "Regulator",
        "time_to_act_hours": 48,
        "cost_usd": 200_000_000,
        "loss_avoidable_pct": 0.20,
        "regulatory_risk": 0.9,
        "trigger": lambda bs, _is, _fs: bs.aggregate_stress > 0.5,
    },
    {
        "sector": "maritime",
        "action": "Reroute shipping via Cape of Good Hope",
        "action_ar": "تحويل مسار الشحن عبر رأس الرجاء الصالح",
        "owner": "Ops",
        "time_to_act_hours": 72,
        "cost_usd": 150_000_000,
        "loss_avoidable_pct": 0.18,
        "regulatory_risk": 0.2,
        "trigger": lambda bs, _is, _fs: bs.aggregate_stress > 0.3,
    },
]


def compute_decision_plan(
    run_id: str,
    financial_impacts: list[FinancialImpact],
    banking: BankingStress,
    insurance: InsuranceStress,
    fintech: FintechStress,
    scenario_label: str | None = None,
) -> DecisionPlan:
    """Compute prioritized decision actions.

    Priority = Value + Urgency + RegulatoryRisk
    where:
        Urgency = time_to_failure / time_to_act
        Value = loss_avoided - cost
    """
    total_loss = sum(i.loss_usd for i in financial_impacts)
    peak_day = max((i.peak_day for i in financial_impacts), default=0)

    # Earliest time to failure across all sectors
    time_to_failure = min(
        banking.time_to_liquidity_breach_hours,
        insurance.time_to_insolvency_hours,
        fintech.time_to_payment_failure_hours,
    )

    all_actions: list[DecisionAction] = []

    for template in ACTION_TEMPLATES:
        # Check if this action is triggered
        try:
            triggered = template["trigger"](banking, insurance, fintech)
        except Exception:
            triggered = False

        if not triggered:
            continue

        # Compute priority components
        time_to_act = template["time_to_act_hours"]
        loss_avoided = total_loss * template["loss_avoidable_pct"]
        cost = template["cost_usd"]
        regulatory_risk = template["regulatory_risk"]

        # Urgency = time_to_failure / time_to_act (higher = more urgent)
        urgency = time_to_failure / max(time_to_act, 1) if time_to_failure < float("inf") else 1.0
        urgency = min(urgency, 100.0)  # cap

        # Value = loss_avoided - cost (normalized to billions for scoring)
        value = (loss_avoided - cost) / 1e9

        # Priority = Value + Urgency + RegulatoryRisk
        priority = value + urgency + regulatory_risk

        # Confidence based on data quality
        confidence = 0.7 if urgency > 10 else 0.8

        action = DecisionAction(
            id=f"act-{uuid.uuid4().hex[:8]}",
            action=template["action"],
            action_ar=template["action_ar"],
            sector=template["sector"],
            owner=template["owner"],
            urgency=round(urgency, 2),
            value=round(value, 4),
            regulatory_risk=regulatory_risk,
            priority=round(priority, 4),
            time_to_act_hours=time_to_act,
            time_to_failure_hours=time_to_failure,
            loss_avoided_usd=round(loss_avoided, 2),
            cost_usd=cost,
            confidence=confidence,
        )
        all_actions.append(action)

    # Sort by priority descending
    all_actions.sort(key=lambda a: a.priority, reverse=True)

    # Top 3 only
    top_3 = all_actions[:3]

    return DecisionPlan(
        run_id=run_id,
        scenario_label=scenario_label,
        total_loss_usd=round(total_loss, 2),
        peak_day=peak_day,
        time_to_failure_hours=time_to_failure,
        actions=top_3,
        all_actions=all_actions,
    )
