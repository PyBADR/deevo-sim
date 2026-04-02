"""
Impact Observatory | مرصد الأثر — Time Engine (v4 §17.3)
Temporal simulation with shock decay and per-timestep state.

ShockEffective(t) = ShockIntensity × (1 - shock_decay_rate)^t
"""

from datetime import datetime, timezone, timedelta
from typing import List

from ...domain.models.scenario import Scenario
from ...domain.models.entity import Entity
from ...domain.models.time_engine import TimeStepState, EntityTemporalImpact


def compute_temporal_simulation(
    run_id: str,
    scenario: Scenario,
    entities: List[Entity],
    propagation_factors: dict[str, float] | None = None,
) -> List[TimeStepState]:
    """
    v4 §17.3 — Compute timestep-by-timestep temporal simulation.

    Args:
        run_id: Run identifier
        scenario: v4 Scenario with time_config
        entities: Entity list
        propagation_factors: Optional per-entity propagation factors

    Returns:
        List of TimeStepState, one per timestep
    """
    # Time config — v4 §17.2 uses time_granularity_minutes
    timestep_hours = 24.0  # default: daily
    decay_rate = 0.05
    if scenario.time_config:
        timestep_hours = scenario.time_config.time_granularity_minutes / 60.0
        decay_rate = scenario.time_config.shock_decay_rate

    total_timesteps = int(scenario.horizon_days * 24 / timestep_hours)
    total_timesteps = min(total_timesteps, 365)  # cap at 1 year

    base_time = datetime.now(timezone.utc)
    results: List[TimeStepState] = []

    # Track previous state for deltas
    prev_impacts: dict[str, float] = {}
    prev_flows: dict[str, float] = {}
    prev_losses: dict[str, float] = {}

    for t in range(total_timesteps):
        ts = (base_time + timedelta(hours=t * timestep_hours)).isoformat().replace("+00:00", "Z")

        # v4 §17.3: ShockEffective(t) = ShockIntensity × (1 - decay_rate)^t
        shock_eff = scenario.shock_intensity * ((1 - decay_rate) ** t)

        entity_impacts: List[EntityTemporalImpact] = []
        agg_loss = 0.0
        agg_flow = 0.0
        breach_count = 0

        for entity in entities:
            prop = (propagation_factors or {}).get(entity.entity_id, 0.65)

            # Impact score: shock × criticality × propagation
            impact = shock_eff * entity.criticality * prop

            # Flow: Capacity × Availability × RouteEfficiency (v4 §3.4)
            # Clamp multiplier to [0, 1] so flow never goes negative
            flow = entity.capacity * entity.availability * entity.route_efficiency * max(0.0, 1 - impact * 0.5)

            # Loss: Exposure × ShockEffective × PropagationFactor
            loss = entity.exposure * shock_eff * prop * 0.005  # daily fraction

            # Deltas
            prev_i = prev_impacts.get(entity.entity_id, 0)
            prev_f = prev_flows.get(entity.entity_id, entity.capacity)
            prev_l = prev_losses.get(entity.entity_id, 0)

            # Status — Literal["stable", "watch", "breach", "failed"]
            if impact > 0.8:
                status = "failed"
                breach_count += 1
            elif impact > 0.5:
                status = "breach"
                breach_count += 1
            elif impact > 0.2:
                status = "watch"
            else:
                status = "stable"

            entity_impacts.append(EntityTemporalImpact(
                entity_id=entity.entity_id,
                impact_score=round(impact, 6),
                impact_delta=round(impact - prev_i, 6),
                flow_value=round(flow, 6),
                flow_delta=round(flow - prev_f, 6),
                loss_value=round(loss, 6),
                loss_delta=round(loss - prev_l, 6),
                status=status,
            ))

            agg_loss += loss
            agg_flow += flow
            prev_impacts[entity.entity_id] = impact
            prev_flows[entity.entity_id] = flow
            prev_losses[entity.entity_id] = loss

        # System status — Literal["stable", "degrading", "critical", "failed"]
        breach_ratio = breach_count / max(1, len(entities))
        if breach_ratio > 0.5:
            sys_status = "failed"
        elif breach_ratio > 0.3:
            sys_status = "critical"
        elif breach_ratio > 0.1:
            sys_status = "degrading"
        else:
            sys_status = "stable"

        results.append(TimeStepState(
            run_id=run_id,
            timestep_index=t,
            timestamp=ts,
            shock_intensity_effective=round(shock_eff, 6),
            entity_impacts=entity_impacts,
            aggregate_loss=round(agg_loss, 4),
            aggregate_flow=round(agg_flow, 4),
            regulatory_breach_count=breach_count,
            system_status=sys_status,
        ))

    return results
