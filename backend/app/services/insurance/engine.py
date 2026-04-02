"""
Impact Observatory | مرصد الأثر — Insurance Stress Engine (v4 §3.7)
Per-entity insurance stress with solvency metrics and breach flags.
"""

from datetime import datetime, timezone
from typing import List

from ...domain.models.scenario import Scenario
from ...domain.models.entity import Entity
from ...domain.models.financial_impact import FinancialImpact
from ...domain.models.insurance_stress import InsuranceStress, InsuranceBreachFlags
from ...core.constants import SOLVENCY_MIN, COMBINED_RATIO_MAX, RESERVE_RATIO_MIN


def compute_insurance_stress(
    scenario: Scenario,
    insurance_entities: List[Entity],
    financial_impacts: List[FinancialImpact],
) -> List[InsuranceStress]:
    """
    v4 §3.7 — Compute per-entity insurance stress.

    Args:
        scenario: v4 Scenario with claims_spike_rate
        insurance_entities: Entities with entity_type='insurer'
        financial_impacts: Per-entity financial impacts

    Returns:
        List of v4 InsuranceStress with breach_flags
    """
    now = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    impact_map = {fi.entity_id: fi for fi in financial_impacts}
    results: List[InsuranceStress] = []

    for entity in insurance_entities:
        if entity.entity_type != "insurer":
            continue

        fi = impact_map.get(entity.entity_id)
        shock = scenario.shock_intensity
        loss_ratio = (fi.loss / max(1, entity.exposure)) if fi else shock * 0.65

        # Premium drop: proportional to shock severity
        premium_drop = entity.exposure * 0.15 * shock

        # Claims spike: scenario claims_spike_rate × shock
        claims_spike = scenario.claims_spike_rate * shock

        # Reserve ratio
        base_reserve = 1.2
        reserve_ratio = max(0.1, base_reserve - loss_ratio * 1.5)

        # Solvency ratio
        base_solvency = 1.8
        solvency_ratio = max(0.3, base_solvency - shock * 1.3)

        # Combined ratio
        combined_ratio = 0.95 + (0.45 * shock)

        # Liquidity gap
        liquidity_gap = entity.exposure * 0.08 * shock

        # Breach flags (v4 §3.7)
        breach_flags = InsuranceBreachFlags(
            solvency_breach=solvency_ratio < SOLVENCY_MIN,
            reserve_breach=reserve_ratio < RESERVE_RATIO_MIN,
            liquidity_breach=combined_ratio > COMBINED_RATIO_MAX,
        )

        results.append(InsuranceStress(
            entity_id=entity.entity_id,
            timestamp=now,
            premium_drop=round(premium_drop, 4),
            claims_spike=round(claims_spike, 4),
            reserve_ratio=round(reserve_ratio, 4),
            solvency_ratio=round(solvency_ratio, 4),
            combined_ratio=round(combined_ratio, 4),
            liquidity_gap=round(liquidity_gap, 4),
            breach_flags=breach_flags,
        ))

    return results


def aggregate_insurance_metrics(stresses: List[InsuranceStress]) -> dict:
    """Aggregate insurance metrics across all entities."""
    if not stresses:
        return {
            "aggregate_solvency": 1.8, "aggregate_combined_ratio": 0.95,
            "aggregate_reserve_ratio": 1.2, "claims_spike": 0,
            "breach_flags": InsuranceBreachFlags(
                solvency_breach=False, reserve_breach=False, liquidity_breach=False,
            ),
        }
    n = len(stresses)
    return {
        "aggregate_solvency": round(sum(s.solvency_ratio for s in stresses) / n, 4),
        "aggregate_combined_ratio": round(sum(s.combined_ratio for s in stresses) / n, 4),
        "aggregate_reserve_ratio": round(sum(s.reserve_ratio for s in stresses) / n, 4),
        "claims_spike": round(sum(s.claims_spike for s in stresses) / n, 4),
        "breach_flags": InsuranceBreachFlags(
            solvency_breach=any(s.breach_flags.solvency_breach for s in stresses),
            reserve_breach=any(s.breach_flags.reserve_breach for s in stresses),
            liquidity_breach=any(s.breach_flags.liquidity_breach for s in stresses),
        ),
    }
