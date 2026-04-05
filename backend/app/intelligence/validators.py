"""
Intelligence Adapter Foundation — Validation Layer

PHASE 1 (contract) + PHASE 2 (trace): validation rules for external payloads
before and after normalization.

Validates:
    - required fields present
    - score ranges [0.0, 1.0]
    - timestamp plausibility (not far future, not epoch zero)
    - source trace completeness (at least one source_system, at least one event_id)
    - semantic completeness (at least one of observed / inferred / simulated)
    - normalization_status coherence (REJECTED signals must not bridge)

All validation functions are pure — no I/O, no side effects.
They either return None (pass) or raise AdapterError / populate TraceBuilder.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone, timedelta
from typing import Any

from .models import NormalizedIntelligenceSignal, NormalizationStatus
from .trace import AdapterError, NormalizationViolation, TraceBuilder

logger = logging.getLogger("observatory.intelligence.validators")

# ─── Plausibility windows ─────────────────────────────────────────────────────

_MAX_FUTURE_HOURS: int   = 72          # detected_at may not be > 72h in the future
_MAX_PAST_YEARS:   int   = 5           # detected_at may not be > 5 years in the past
_EPOCH_ZERO: datetime    = datetime(1970, 1, 2, tzinfo=timezone.utc)  # guard against literal epoch 0

# ─── Raw payload validation (pre-normalization) ───────────────────────────────

REQUIRED_RAW_FIELDS: tuple[str, ...] = (
    "source_family",
    "source_systems",
    "signal_type",
    "title",
    "summary",
    "severity_score",
    "confidence_score",
    "detected_at",
    "time_horizon_hours",
    "affected_domains",
)


def validate_raw_payload(
    raw: dict[str, Any],
    tb: TraceBuilder,
) -> None:
    """Validate a raw external payload before normalization.

    Records violations into tb for all missing/invalid fields.
    Does NOT raise — caller checks tb.has_violations() and raises if needed.
    """
    # Required fields presence
    for field_name in REQUIRED_RAW_FIELDS:
        if field_name not in raw or raw[field_name] is None:
            tb.violation(
                field_name=field_name,
                message=f"Required field '{field_name}' is missing or null",
                received_value=raw.get(field_name),
                rule="REQUIRED_FIELD",
            )

    # source_systems must be a non-empty list
    ss = raw.get("source_systems")
    if ss is not None:
        if not isinstance(ss, list) or len(ss) == 0:
            tb.violation(
                field_name="source_systems",
                message="source_systems must be a non-empty list of source system names",
                received_value=ss,
                rule="NON_EMPTY_LIST",
            )

    # Score range checks
    for score_field in ("severity_score", "confidence_score"):
        val = raw.get(score_field)
        if val is not None:
            try:
                fval = float(val)
                if not (0.0 <= fval <= 1.0):
                    tb.violation(
                        field_name=score_field,
                        message=f"{score_field} must be in [0.0, 1.0], got {fval}",
                        received_value=val,
                        rule="SCORE_RANGE",
                    )
            except (TypeError, ValueError):
                tb.violation(
                    field_name=score_field,
                    message=f"{score_field} is not numeric: {val!r}",
                    received_value=val,
                    rule="NUMERIC_TYPE",
                )

    # time_horizon_hours range
    thr = raw.get("time_horizon_hours")
    if thr is not None:
        try:
            ithr = int(thr)
            if not (1 <= ithr <= 8760):
                tb.violation(
                    field_name="time_horizon_hours",
                    message=f"time_horizon_hours must be in [1, 8760], got {ithr}",
                    received_value=thr,
                    rule="HORIZON_RANGE",
                )
        except (TypeError, ValueError):
            tb.violation(
                field_name="time_horizon_hours",
                message=f"time_horizon_hours is not an integer: {thr!r}",
                received_value=thr,
                rule="NUMERIC_TYPE",
            )

    # detected_at plausibility
    dat = raw.get("detected_at")
    if dat is not None:
        _validate_timestamp_field("detected_at", dat, tb)

    # affected_domains non-empty list
    ad = raw.get("affected_domains")
    if ad is not None:
        if not isinstance(ad, list) or len(ad) == 0:
            tb.warn(
                field_name="affected_domains",
                message="affected_domains is empty — signal has no domain scope",
                original_value=ad,
                severity="MEDIUM",
            )

    # source_event_ids — warn if empty (not required, but strongly encouraged)
    se = raw.get("source_event_ids", [])
    if not isinstance(se, list) or len(se) == 0:
        tb.warn(
            field_name="source_event_ids",
            message="source_event_ids is empty — traceability to source events is reduced",
            original_value=se,
            severity="MEDIUM",
        )

    # Semantic section presence — at least one of the three must exist
    has_observed  = bool(raw.get("observed_evidence"))
    has_inferred  = bool(raw.get("inferred_reasoning"))
    has_simulated = bool(raw.get("simulation_context"))
    if not (has_observed or has_inferred or has_simulated):
        tb.warn(
            field_name="semantic_sections",
            message=(
                "No semantic evidence sections provided "
                "(observed_evidence / inferred_reasoning / simulation_context are all empty). "
                "Signal is valid but has no traceable evidence."
            ),
            severity="HIGH",
        )


def _validate_timestamp_field(field_name: str, val: Any, tb: TraceBuilder) -> None:
    """Parse and range-check a timestamp field. Records violations into tb."""
    now = datetime.now(timezone.utc)
    ts: datetime | None = None

    if isinstance(val, datetime):
        ts = val if val.tzinfo else val.replace(tzinfo=timezone.utc)
    elif isinstance(val, str):
        try:
            ts = datetime.fromisoformat(val)
            if ts.tzinfo is None:
                ts = ts.replace(tzinfo=timezone.utc)
        except ValueError:
            tb.violation(
                field_name=field_name,
                message=f"{field_name} is not a valid ISO 8601 datetime: {val!r}",
                received_value=val,
                rule="DATETIME_FORMAT",
            )
            return
    else:
        tb.violation(
            field_name=field_name,
            message=f"{field_name} must be a datetime or ISO 8601 string, got {type(val).__name__}",
            received_value=type(val).__name__,
            rule="DATETIME_TYPE",
        )
        return

    if ts <= _EPOCH_ZERO:
        tb.violation(
            field_name=field_name,
            message=f"{field_name} looks like epoch zero — likely a missing value",
            received_value=val,
            rule="EPOCH_ZERO",
        )
    elif ts > now + timedelta(hours=_MAX_FUTURE_HOURS):
        tb.violation(
            field_name=field_name,
            message=f"{field_name} is more than {_MAX_FUTURE_HOURS}h in the future",
            received_value=str(val),
            rule="FUTURE_TIMESTAMP",
        )
    elif ts < now - timedelta(days=_MAX_PAST_YEARS * 365):
        tb.warn(
            field_name=field_name,
            message=f"{field_name} is more than {_MAX_PAST_YEARS} years in the past",
            original_value=str(val),
            severity="MEDIUM",
        )


# ─── Post-normalization validation ────────────────────────────────────────────

def validate_normalized_signal(signal: NormalizedIntelligenceSignal) -> list[str]:
    """Validate a fully normalized NormalizedIntelligenceSignal.

    Returns a list of error messages. Empty list = valid.
    Used as a final gate before the signal bridge.
    """
    errors: list[str] = []

    if signal.normalization_status == NormalizationStatus.REJECTED:
        errors.append(
            f"Signal {signal.normalized_signal_id} has REJECTED normalization status "
            "— it must not enter the bridge"
        )

    if not signal.source_systems:
        errors.append("source_systems is empty — provenance cannot be established")

    if not (0.0 <= signal.severity_score <= 1.0):
        errors.append(f"severity_score out of range: {signal.severity_score}")

    if not (0.0 <= signal.confidence_score <= 1.0):
        errors.append(f"confidence_score out of range: {signal.confidence_score}")

    if not signal.affected_domains:
        errors.append("affected_domains is empty — no domain scope established")

    if not signal.title.strip():
        errors.append("title is blank")

    if not signal.summary.strip():
        errors.append("summary is blank")

    # Trace payload must be present and contain mandatory keys
    required_trace_keys = {"trace_id", "normalization_status", "source_family", "source_systems"}
    missing_trace = required_trace_keys - set(signal.trace_payload.keys())
    if missing_trace:
        errors.append(f"trace_payload is missing required keys: {sorted(missing_trace)}")

    return errors


def assert_bridge_eligible(signal: NormalizedIntelligenceSignal) -> None:
    """Raise AdapterError if the signal is not eligible to enter the signal bridge.

    Called immediately before SignalBridge.to_live_signal().
    """
    errors = validate_normalized_signal(signal)
    if errors:
        violations = [
            NormalizationViolation(field_name="normalized_signal", message=e, rule="BRIDGE_ELIGIBILITY")
            for e in errors
        ]
        raise AdapterError(
            f"Signal {signal.normalized_signal_id} is not bridge-eligible: "
            + "; ".join(errors),
            violations=violations,
        )
