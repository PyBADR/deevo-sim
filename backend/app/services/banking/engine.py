"""
Impact Observatory | مرصد الأثر — Banking Stress Engine (v4 §3.6)
Per-entity banking stress with Basel III metrics and breach flags.
"""

from datetime import datetime, timezone
from typing import List

from ...domain.models.scenario import Scenario
from ...domain.models.entity import Entity
from ...domain.models.financial_impact import FinancialImpact
from ...domain.models.banking_stress import BankingStress, BankingBreachFlags
from ...core.constants import LCR_MIN, NSFR_MIN, CET1_MIN, CAR_MIN


def compute_banking_stress(
    scenario: Scenario,
    bank_entities: List[Entity],
    financial_impacts: List[FinancialImpact],
) -> List[BankingStress]:
    """
    v4 §3.6 — Compute per-entity banking stress.

    Args:
        scenario: v4 Scenario
        bank_entities: Entities with entity_type='bank'
        financial_impacts: Per-entity financial impacts

    Returns:
        List of v4 BankingStress with breach_flags
    """
    now = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    impact_map = {fi.entity_id: fi for fi in financial_impacts}
    results: List[BankingStress] = []

    for entity in bank_entities:
        if entity.entity_type != "bank":
            continue

        fi = impact_map.get(entity.entity_id)
        shock = scenario.shock_intensity
        loss_ratio = (fi.loss / max(1, entity.exposure)) if fi else shock * 0.65

        # Deposit outflow: deposit_run_rate scaled by shock
        deposit_outflow = entity.exposure * scenario.deposit_run_rate * shock

        # Wholesale funding outflow
        wholesale_outflow = entity.exposure * 0.05 * shock

        # HQLA (High Quality Liquid Assets) — eroded by loss
        base_hqla = entity.liquidity_buffer
        hqla = max(0, base_hqla - deposit_outflow * 0.3)

        # LCR = HQLA / Net Cash Outflows (30d)
        outflows_30d = deposit_outflow + wholesale_outflow
        inflows_30d = outflows_30d * 0.25  # 25% expected inflow
        net_outflows = max(1, outflows_30d - min(inflows_30d, outflows_30d * 0.75))
        lcr = hqla / net_outflows if net_outflows > 0 else 2.0

        # NSFR
        available_stable = entity.capital_buffer + entity.exposure * 0.6
        required_stable = entity.exposure * (0.5 + 0.15 * shock)
        nsfr = available_stable / max(1, required_stable)

        # CET1 and CAR — eroded by loss
        base_cet1 = 0.125  # 12.5% baseline
        base_car = 0.175   # 17.5% baseline
        cet1_ratio = max(0, base_cet1 - loss_ratio * 0.08)
        car = max(0, base_car - loss_ratio * 0.10)

        # Breach flags (v4 §3.6)
        breach_flags = BankingBreachFlags(
            lcr_breach=lcr < LCR_MIN,
            nsfr_breach=nsfr < NSFR_MIN,
            cet1_breach=cet1_ratio < CET1_MIN,
            car_breach=car < CAR_MIN,
        )

        results.append(BankingStress(
            entity_id=entity.entity_id,
            timestamp=now,
            deposit_outflow=deposit_outflow,
            wholesale_funding_outflow=wholesale_outflow,
            hqla=hqla,
            projected_cash_outflows_30d=outflows_30d,
            projected_cash_inflows_30d=inflows_30d,
            lcr=round(lcr, 4),
            nsfr=round(nsfr, 4),
            cet1_ratio=round(cet1_ratio, 4),
            capital_adequacy_ratio=round(car, 4),
            breach_flags=breach_flags,
        ))

    return results


def aggregate_banking_metrics(stresses: List[BankingStress]) -> dict:
    """Aggregate banking metrics across all entities."""
    if not stresses:
        return {
            "aggregate_lcr": 1.35, "aggregate_nsfr": 1.15,
            "aggregate_cet1": 0.125, "aggregate_car": 0.175,
            "deposit_outflow": 0, "breach_flags": BankingBreachFlags(
                lcr_breach=False, nsfr_breach=False, cet1_breach=False, car_breach=False,
            ),
        }
    n = len(stresses)
    agg_lcr = sum(s.lcr for s in stresses) / n
    agg_nsfr = sum(s.nsfr for s in stresses) / n
    agg_cet1 = sum(s.cet1_ratio for s in stresses) / n
    agg_car = sum(s.capital_adequacy_ratio for s in stresses) / n
    total_deposit = sum(s.deposit_outflow for s in stresses)
    return {
        "aggregate_lcr": round(agg_lcr, 4),
        "aggregate_nsfr": round(agg_nsfr, 4),
        "aggregate_cet1": round(agg_cet1, 4),
        "aggregate_car": round(agg_car, 4),
        "deposit_outflow": total_deposit,
        "breach_flags": BankingBreachFlags(
            lcr_breach=any(s.breach_flags.lcr_breach for s in stresses),
            nsfr_breach=any(s.breach_flags.nsfr_breach for s in stresses),
            cet1_breach=any(s.breach_flags.cet1_breach for s in stresses),
            car_breach=any(s.breach_flags.car_breach for s in stresses),
        ),
    }
