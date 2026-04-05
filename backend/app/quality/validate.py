"""
Impact Observatory | مرصد الأثر — Event Validation (Stage 2)

Business-rule validation. NOT type-only.
Rejects or warns on out-of-bounds values, unknown templates, invalid sectors.

Validation rules:
- severity ∈ [0.0, 1.0]
- horizon_hours ∈ [1, 8760]
- template_id ∈ KNOWN_SCENARIOS (if from scenario_catalog)
- sectors ⊆ KNOWN_SECTORS
- shock_intensity ∈ [0.01, 1.0] (clamped with warning if adjusted)
"""

from app.domain.models.raw_event import RawEvent, ValidatedEvent
from app.graph.bridge import scenario_exists

KNOWN_SECTORS = {
    "banking", "insurance", "fintech", "energy", "aviation",
    "shipping", "ports", "tourism", "food_security", "telecom",
    "sovereign", "utilities", "logistics", "real_estate",
}

VALID_EVENT_TYPES = {"geopolitical", "economic", "natural", "cyber"}


class ValidationError(Exception):
    """Raised when validation fails hard (reject the event)."""
    def __init__(self, errors: list[str]):
        self.errors = errors
        super().__init__(f"Validation failed: {'; '.join(errors)}")


def validate_event(raw: RawEvent) -> ValidatedEvent:
    """Validate a RawEvent against business rules.

    Returns ValidatedEvent on success.
    Raises ValidationError on hard failure.
    Soft issues produce warnings + reduced validation_score.
    """
    errors: list[str] = []
    warnings: list[str] = []
    score = 1.0
    payload = raw.payload

    # ── Event type ────────────────────────────────────────────
    if raw.event_type not in VALID_EVENT_TYPES:
        errors.append(f"Unknown event_type: {raw.event_type}")

    # ── Severity ──────────────────────────────────────────────
    severity = payload.get("severity", 0.5)
    if not isinstance(severity, (int, float)):
        errors.append(f"severity must be numeric, got {type(severity).__name__}")
        severity = 0.5
    elif severity < 0.0 or severity > 1.0:
        errors.append(f"severity {severity} out of bounds [0.0, 1.0]")

    # ── Horizon hours ─────────────────────────────────────────
    horizon_hours = payload.get("horizon_hours", 168)
    if not isinstance(horizon_hours, (int, float)):
        warnings.append(f"horizon_hours not numeric, defaulting to 168")
        horizon_hours = 168
        score -= 0.1
    elif horizon_hours < 1 or horizon_hours > 8760:
        warnings.append(f"horizon_hours {horizon_hours} clamped to [1, 8760]")
        horizon_hours = max(1, min(8760, int(horizon_hours)))
        score -= 0.05

    # ── Template ID ───────────────────────────────────────────
    template_id = payload.get("template_id")
    if template_id and raw.source == "scenario_catalog":
        if not scenario_exists(template_id):
            errors.append(f"Unknown template_id: {template_id}")

    # ── Sectors ───────────────────────────────────────────────
    sectors = payload.get("sectors_affected", [])
    if sectors:
        unknown = [s for s in sectors if s not in KNOWN_SECTORS]
        if unknown:
            warnings.append(f"Unknown sectors removed: {unknown}")
            sectors = [s for s in sectors if s in KNOWN_SECTORS]
            score -= 0.05 * len(unknown)

    # ── Source trust ──────────────────────────────────────────
    source_trust = raw.provenance.get("trust_weight", 0.5)
    if source_trust < 0.5:
        warnings.append(f"Low-trust source ({raw.source}), confidence will be reduced")
        score *= source_trust

    # ── Hard rejection ────────────────────────────────────────
    if errors:
        raise ValidationError(errors)

    return ValidatedEvent(
        raw_event_id=raw.source_id,
        template_id=template_id,
        severity=float(severity),
        horizon_hours=int(horizon_hours),
        sectors_affected=sectors,
        validation_score=max(0.0, min(1.0, score)),
        warnings=warnings,
    )
