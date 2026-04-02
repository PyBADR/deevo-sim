"""
Impact Observatory | مرصد الأثر — Financial Impact Engine (v4 §3.5)
Per-entity financial loss computation using v4 formula:
  Loss_i(t) = Exposure_i × ShockIntensity_s × PropagationFactor_i(t)
"""

from datetime import datetime, timezone
from typing import List

from ...domain.models.scenario import Scenario
from ...domain.models.entity import Entity
from ...domain.models.financial_impact import FinancialImpact


# Fallback GCC constants (used when entities list is empty in V1)
GCC_GDP_B = 2100
GCC_BANKING_EXPOSURE_B = 2800
GCC_INSURANCE_EXPOSURE_B = 450
GCC_FINTECH_EXPOSURE_B = 180


def compute_financial_impact(
    scenario: Scenario,
    entities: List[Entity],
    propagation_factors: dict[str, float] | None = None,
) -> List[FinancialImpact]:
    """
    v4 §3.5 — Compute per-entity financial impact.

    Formula: Loss_i(t) = Exposure_i × ShockIntensity × PropagationFactor_i(t)

    Args:
        scenario: v4 Scenario with shock_intensity
        entities: List of v4 Entity objects
        propagation_factors: Optional dict {entity_id: factor} from propagation stage

    Returns:
        List of v4 FinancialImpact, one per entity
    """
    now = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    shock = scenario.shock_intensity
    results: List[FinancialImpact] = []

    # If no entities provided (V1 mode), create synthetic sector-level entities
    if not entities:
        entities = _synthetic_entities()

    for entity in entities:
        prop_factor = (propagation_factors or {}).get(entity.entity_id, 0.65)

        # v4 formula: Loss = Exposure × ShockIntensity × PropagationFactor
        loss = entity.exposure * shock * prop_factor

        # Revenue at risk: loss × duration scaling
        revenue_at_risk = loss * (scenario.horizon_days / 14.0) * 0.8

        # Capital/liquidity after loss
        capital_after = entity.capital_buffer - (loss * 0.4)
        liquidity_after = entity.liquidity_buffer - (loss * 0.3)

        # Impact status
        if capital_after < 0 or liquidity_after < 0:
            status = "default"
        elif capital_after < entity.capital_buffer * 0.3:
            status = "breach"
        elif capital_after < entity.capital_buffer * 0.6:
            status = "watch"
        else:
            status = "stable"

        results.append(FinancialImpact(
            entity_id=entity.entity_id,
            timestamp=now,
            exposure=entity.exposure,
            shock_intensity=shock,
            propagation_factor=prop_factor,
            loss=loss,
            revenue_at_risk=revenue_at_risk,
            capital_after_loss=capital_after,
            liquidity_after_loss=liquidity_after,
            impact_status=status,
        ))

    return results


def compute_aggregate_headline(impacts: List[FinancialImpact]) -> dict:
    """Compute aggregate headline metrics from per-entity impacts."""
    total_loss = sum(i.loss for i in impacts)
    total_rar = sum(i.revenue_at_risk for i in impacts)
    breach_count = sum(1 for i in impacts if i.impact_status in ("breach", "default"))
    return {
        "total_loss": total_loss,
        "total_revenue_at_risk": total_rar,
        "entity_count": len(impacts),
        "breach_count": breach_count,
    }


def _synthetic_entities() -> List[Entity]:
    """V1 fallback: create representative entities per sector."""
    return [
        Entity(
            entity_id="bank-gcc-agg",
            entity_type="bank",
            name="GCC Banking Sector (Aggregate)",
            jurisdiction="GCC",
            exposure=GCC_BANKING_EXPOSURE_B,
            capital_buffer=GCC_BANKING_EXPOSURE_B * 0.175,
            liquidity_buffer=GCC_BANKING_EXPOSURE_B * 0.135,
            capacity=1.0, availability=1.0, route_efficiency=1.0,
            criticality=0.95,
            regulatory_classification="systemic",
            active=True,
        ),
        Entity(
            entity_id="ins-gcc-agg",
            entity_type="insurer",
            name="GCC Insurance Sector (Aggregate)",
            jurisdiction="GCC",
            exposure=GCC_INSURANCE_EXPOSURE_B,
            capital_buffer=GCC_INSURANCE_EXPOSURE_B * 0.40,
            liquidity_buffer=GCC_INSURANCE_EXPOSURE_B * 0.20,
            capacity=1.0, availability=1.0, route_efficiency=1.0,
            criticality=0.75,
            regulatory_classification="material",
            active=True,
        ),
        Entity(
            entity_id="fin-gcc-agg",
            entity_type="fintech",
            name="GCC Fintech Sector (Aggregate)",
            jurisdiction="GCC",
            exposure=GCC_FINTECH_EXPOSURE_B,
            capital_buffer=GCC_FINTECH_EXPOSURE_B * 0.25,
            liquidity_buffer=GCC_FINTECH_EXPOSURE_B * 0.15,
            capacity=1.0, availability=1.0, route_efficiency=1.0,
            criticality=0.65,
            regulatory_classification="material",
            active=True,
        ),
    ]
