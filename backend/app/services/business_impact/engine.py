"""
Impact Observatory | مرصد الأثر — Business Impact Engine (v4 §16)
Loss trajectory, time-to-failure, regulatory breach events, and business severity.

Temporal formula: ShockEffective(t) = ShockIntensity × (1 - shock_decay_rate)^t
"""

from datetime import datetime, timezone
from typing import List, Optional

from ...domain.models.scenario import Scenario
from ...domain.models.entity import Entity
from ...domain.models.financial_impact import FinancialImpact
from ...domain.models.banking_stress import BankingStress
from ...domain.models.insurance_stress import InsuranceStress
from ...domain.models.fintech_stress import FintechStress
from ...domain.models.business_impact import (
    LossTrajectoryPoint, TimeToFailure, RegulatoryBreachEvent,
    BusinessImpactSummary,
)
from ...core.constants import SEVERITY_MAPPING, LCR_MIN, CAR_MIN, SOLVENCY_MIN


def compute_business_impact(
    run_id: str,
    scenario: Scenario,
    entities: List[Entity],
    financial_impacts: List[FinancialImpact],
    banking_stresses: List[BankingStress],
    insurance_stresses: List[InsuranceStress],
    fintech_stresses: List[FintechStress],
) -> BusinessImpactSummary:
    """
    v4 §16 — Compute business impact summary with loss trajectory,
    time-to-failure estimates, and regulatory breach events.
    """
    now = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    total_exposure = sum(e.exposure for e in entities) or 3430

    # Shock decay config
    decay_rate = 0.05
    if scenario.time_config:
        decay_rate = scenario.time_config.shock_decay_rate

    # Loss trajectory (v4 canonical fields)
    trajectory: List[LossTrajectoryPoint] = []
    cumulative = 0.0
    prev_step_loss = 0.0
    prev_velocity = 0.0
    timesteps = min(scenario.horizon_days, 30)

    for t in range(timesteps):
        shock_eff = scenario.shock_intensity * ((1 - decay_rate) ** t)
        step_loss = total_exposure * shock_eff * 0.65 * 0.005

        direct = step_loss * 0.6
        propagated = step_loss * 0.4
        cumulative += step_loss
        revenue_at_risk = cumulative * 0.8
        velocity = step_loss - prev_step_loss
        acceleration = velocity - prev_velocity

        # Status: stable → deteriorating → critical → failed
        total_loss_ref = sum(fi.loss for fi in financial_impacts) or cumulative
        if cumulative > total_loss_ref * 0.8:
            status = "failed"
        elif cumulative > total_loss_ref * 0.5:
            status = "critical"
        elif cumulative > total_loss_ref * 0.2:
            status = "deteriorating"
        else:
            status = "stable"

        trajectory.append(LossTrajectoryPoint(
            run_id=run_id,
            scope_level="system",
            scope_ref="system",
            timestep_index=t,
            timestamp=now,
            direct_loss=round(direct, 4),
            propagated_loss=round(propagated, 4),
            cumulative_loss=round(cumulative, 4),
            revenue_at_risk=round(revenue_at_risk, 4),
            loss_velocity=round(velocity, 4),
            loss_acceleration=round(acceleration, 4),
            status=status,
        ))
        prev_velocity = velocity
        prev_step_loss = step_loss

    # Peak
    peak_day = 0
    peak_loss = 0.0
    for pt in trajectory:
        if pt.cumulative_loss > peak_loss:
            peak_loss = pt.cumulative_loss
            peak_day = pt.timestep_index

    # Time-to-failure estimates (v4 canonical fields)
    failures: List[TimeToFailure] = []
    for bs in banking_stresses:
        if bs.breach_flags.lcr_breach:
            ttf_h = max(24, int(168 / max(0.1, scenario.shock_intensity)))
            failures.append(TimeToFailure(
                run_id=run_id, scope_level="entity", scope_ref=bs.entity_id,
                failure_type="liquidity_failure",
                failure_threshold_value=LCR_MIN, current_value_at_t0=bs.lcr,
                predicted_failure_timestep=2, predicted_failure_timestamp=now,
                time_to_failure_hours=float(ttf_h), confidence_score=0.75,
                failure_reached_within_horizon=True,
            ))
        if bs.breach_flags.car_breach:
            failures.append(TimeToFailure(
                run_id=run_id, scope_level="entity", scope_ref=bs.entity_id,
                failure_type="capital_failure",
                failure_threshold_value=CAR_MIN, current_value_at_t0=bs.capital_adequacy_ratio,
                predicted_failure_timestep=4, predicted_failure_timestamp=now,
                time_to_failure_hours=float(max(48, int(168 / max(0.1, scenario.shock_intensity)))),
                confidence_score=0.70, failure_reached_within_horizon=True,
            ))
    for ins in insurance_stresses:
        if ins.breach_flags.solvency_breach:
            failures.append(TimeToFailure(
                run_id=run_id, scope_level="entity", scope_ref=ins.entity_id,
                failure_type="solvency_failure",
                failure_threshold_value=SOLVENCY_MIN, current_value_at_t0=ins.solvency_ratio,
                predicted_failure_timestep=3, predicted_failure_timestamp=now,
                time_to_failure_hours=float(max(72, int(240 / max(0.1, scenario.shock_intensity)))),
                confidence_score=0.65, failure_reached_within_horizon=True,
            ))
    for ft in fintech_stresses:
        if ft.breach_flags.availability_breach:
            failures.append(TimeToFailure(
                run_id=run_id, scope_level="entity", scope_ref=ft.entity_id,
                failure_type="availability_failure",
                failure_threshold_value=0.995, current_value_at_t0=ft.service_availability,
                predicted_failure_timestep=1, predicted_failure_timestamp=now,
                time_to_failure_hours=float(max(12, int(48 / max(0.1, scenario.shock_intensity)))),
                confidence_score=0.80, failure_reached_within_horizon=True,
            ))

    # Regulatory breach events (v4 canonical fields)
    breach_events: List[RegulatoryBreachEvent] = []
    for bs in banking_stresses:
        if bs.breach_flags.lcr_breach:
            breach_events.append(RegulatoryBreachEvent(
                run_id=run_id, timestep_index=2, timestamp=now,
                scope_level="entity", scope_ref=bs.entity_id,
                metric_name="lcr", metric_value=bs.lcr, threshold_value=LCR_MIN,
                breach_direction="below_minimum", breach_level="major",
                first_breach=True, reportable=True,
            ))
        if bs.breach_flags.car_breach:
            breach_events.append(RegulatoryBreachEvent(
                run_id=run_id, timestep_index=4, timestamp=now,
                scope_level="entity", scope_ref=bs.entity_id,
                metric_name="capital_adequacy_ratio", metric_value=bs.capital_adequacy_ratio,
                threshold_value=CAR_MIN,
                breach_direction="below_minimum", breach_level="critical",
                first_breach=True, reportable=True,
            ))
    for ins in insurance_stresses:
        if ins.breach_flags.solvency_breach:
            breach_events.append(RegulatoryBreachEvent(
                run_id=run_id, timestep_index=3, timestamp=now,
                scope_level="entity", scope_ref=ins.entity_id,
                metric_name="solvency_ratio", metric_value=ins.solvency_ratio,
                threshold_value=SOLVENCY_MIN,
                breach_direction="below_minimum", breach_level="major",
                first_breach=True, reportable=True,
            ))

    # Business severity
    if peak_loss >= 500:
        biz_severity = "severe"
    elif peak_loss >= 200:
        biz_severity = "high"
    elif peak_loss >= 50:
        biz_severity = "medium"
    else:
        biz_severity = "low"

    executive_status = SEVERITY_MAPPING[biz_severity]

    # First failure time
    first_failure_hours: Optional[float] = None
    first_failure_type: Optional[str] = None
    first_failure_ref: Optional[str] = None
    if failures:
        first = min(failures, key=lambda f: f.time_to_failure_hours or 9999)
        first_failure_hours = first.time_to_failure_hours
        first_failure_type = first.failure_type
        first_failure_ref = first.scope_ref

    critical_count = sum(1 for b in breach_events if b.breach_level == "critical")
    reportable_count = sum(1 for b in breach_events if b.reportable)

    return BusinessImpactSummary(
        run_id=run_id,
        currency=scenario.currency,
        peak_cumulative_loss=round(peak_loss, 4),
        peak_loss_timestep=peak_day,
        peak_loss_timestamp=now,
        system_time_to_first_failure_hours=first_failure_hours,
        first_failure_type=first_failure_type,
        first_failure_scope_ref=first_failure_ref,
        critical_breach_count=critical_count,
        reportable_breach_count=reportable_count,
        business_severity=biz_severity,
        executive_status=executive_status,
    )
