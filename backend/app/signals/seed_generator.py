"""signals.seed_generator — ScoredSignal → ScenarioSeed.

Maps a scored signal to a HITL-gated ScenarioSeed using template IDs
from the main scenario catalog (app.scenarios.catalog).

Template IDs used here MUST exist in app.scenarios.catalog.SCENARIO_CATALOG.

MVP scope: banking + fintech sectors only.
No state, no I/O, no side effects.
"""

from __future__ import annotations

import logging
from typing import Final

from app.domain.models.live_signal import ScenarioSeed, ScoredSignal

logger = logging.getLogger(__name__)

# ── Event-type → catalog template-id registry ─────────────────────────────────
#
# All template IDs must exist in app.scenarios.catalog.SCENARIO_CATALOG.
# Keys are lowercased; normalizer already lower-strips event_type values.

EVENT_TYPE_TO_TEMPLATE: Final[dict[str, str]] = {
    # ── Banking ───────────────────────────────────────────────────────────────
    "liquidity_stress":         "regional_liquidity_stress_event",
    "bank_run":                 "regional_liquidity_stress_event",
    "interbank_freeze":         "regional_liquidity_stress_event",
    "interbank_stress":         "regional_liquidity_stress_event",
    "fx_volatility":            "regional_liquidity_stress_event",
    "credit_squeeze":           "regional_liquidity_stress_event",
    "capital_flight":           "regional_liquidity_stress_event",
    "regulatory_action":        "regional_liquidity_stress_event",
    "capital_controls":         "regional_liquidity_stress_event",
    # ── Fintech / Cyber ───────────────────────────────────────────────────────
    "cyber_attack":             "financial_infrastructure_cyber_disruption",
    "payment_disruption":       "financial_infrastructure_cyber_disruption",
    "infrastructure_outage":    "financial_infrastructure_cyber_disruption",
    "system_outage":            "financial_infrastructure_cyber_disruption",
    "data_breach":              "financial_infrastructure_cyber_disruption",
    "ransomware":               "financial_infrastructure_cyber_disruption",
    # ── Cross-sector (banking + fintech) ─────────────────────────────────────
    "sanctions_escalation":     "cross_border_sanctions_escalation",
    "sanctions_announcement":   "cross_border_sanctions_escalation",
    "cross_border_restriction": "cross_border_sanctions_escalation",
    "payment_corridor_block":   "cross_border_sanctions_escalation",
}

# ── Horizon thresholds ────────────────────────────────────────────────────────

_HORIZON_HIGH:   int = 168   # 7 days  — signal_score >= 0.7
_HORIZON_MEDIUM: int = 72    # 3 days  — signal_score >= 0.4
_HORIZON_LOW:    int = 24    # 1 day   — signal_score < 0.4

_THRESHOLD_HIGH:   float = 0.70
_THRESHOLD_MEDIUM: float = 0.40


# ── Public entry point ────────────────────────────────────────────────────────

class SeedGenerationError(ValueError):
    """Raised when a ScoredSignal cannot produce a valid ScenarioSeed."""


def generate(scored: ScoredSignal) -> ScenarioSeed:
    """Generate a ScenarioSeed from a ScoredSignal.

    Raises SeedGenerationError if:
    - event_type has no template mapping
    - the mapped template_id is not in the main catalog
    - derived params are out of valid range

    Returns a ScenarioSeed in PENDING_REVIEW status — no pipeline run triggered.
    """
    signal = scored.signal

    # ── 1. event_type → template_id ──────────────────────────────────────────
    event_type_key = signal.event_type.lower().strip()
    if not event_type_key:
        raise SeedGenerationError("event_type is empty — cannot map to a scenario template")

    template_id = EVENT_TYPE_TO_TEMPLATE.get(event_type_key)
    if template_id is None:
        supported = sorted(EVENT_TYPE_TO_TEMPLATE.keys())
        raise SeedGenerationError(
            f"event_type '{signal.event_type}' has no template mapping. "
            f"Supported types: {supported}"
        )

    # ── 2. Validate template against catalog ─────────────────────────────────
    try:
        from app.scenarios.catalog import get_scenario_by_id
        get_scenario_by_id(template_id)
    except ValueError as exc:
        raise SeedGenerationError(
            f"Template '{template_id}' not found in scenario catalog: {exc}"
        ) from exc

    # ── 3. Derive severity and horizon ────────────────────────────────────────
    suggested_severity = round(scored.signal_score, 4)

    if scored.signal_score >= _THRESHOLD_HIGH:
        suggested_horizon_hours = _HORIZON_HIGH
    elif scored.signal_score >= _THRESHOLD_MEDIUM:
        suggested_horizon_hours = _HORIZON_MEDIUM
    else:
        suggested_horizon_hours = _HORIZON_LOW

    # Range guard (should never fail given scoring formula, but explicit is safer)
    if not (0.0 <= suggested_severity <= 1.0):
        raise SeedGenerationError(f"Derived severity out of range: {suggested_severity}")
    if not (1 <= suggested_horizon_hours <= 8760):
        raise SeedGenerationError(f"Derived horizon_hours out of range: {suggested_horizon_hours}")

    # ── 4. Deterministic rationale ────────────────────────────────────────────
    sector_label = signal.sector.value
    source_label = signal.source.value
    rationale = (
        f"{sector_label.capitalize()} signal '{signal.event_type}' "
        f"(score={scored.signal_score:.3f}, src={source_label}) "
        f"→ template '{template_id}', severity={suggested_severity:.3f}, "
        f"horizon={suggested_horizon_hours}h. Awaiting HITL review."
    )

    # ── 5. Build seed ─────────────────────────────────────────────────────────
    seed = ScenarioSeed(
        signal_id=signal.signal_id,
        sector=signal.sector,
        suggested_template_id=template_id,
        suggested_severity=suggested_severity,
        suggested_horizon_hours=suggested_horizon_hours,
        rationale=rationale,
    )

    logger.info(
        "seed_generated seed_id=%s template=%s severity=%.3f horizon=%dh sector=%s",
        seed.seed_id, template_id, suggested_severity, suggested_horizon_hours, sector_label,
    )

    return seed
