"""
Intelligence Adapter — Jet Nexus Source Adapter

INTEGRATION STATUS: IMPLEMENTED (v1.0.0)

Jet Nexus is the first external intelligence source integrated into the platform.
It produces OBSERVED evidence only — Jet Nexus observes and reports operational
events. It does NOT infer financial risk or run projections. Those layers belong
to TREK and Impact Observatory respectively.

CONTRACT:
    All Jet Nexus data enters the platform ONLY through adapt_jet_nexus_payload().
    No direct writes to Signal / Decision / Outcome / Value layers are permitted.
    Full raw payload is preserved in ObservedEvidence.raw_value for audit.

Jet Nexus native payload shape (v1):
    {
        "event_id":    str,       # unique JN event identifier (strongly recommended)
        "event_type":  str,       # operational event classification (see EVENT_TYPE_MAP)
        "headline":    str,       # brief human-readable title            [REQUIRED]
        "description": str,       # full event description
        "timestamp":   str,       # ISO 8601 event datetime               [REQUIRED]
        "severity":    float,     # JN severity [0.0, 1.0]               [REQUIRED]
        "confidence":  float,     # JN confidence [0.0, 1.0]             [REQUIRED]
        "tags":        list[str], # free-form topic / domain tags
        "regions":     list[str], # affected geographic regions (ISO or label)
        "metadata":    dict,      # verbatim source metadata — preserved in evidence
    }

Mapping rules:
    source_family         → jet_nexus (SourceFamily.JET_NEXUS)
    source_systems        → ["jet_nexus"]
    source_event_ids      → [event_id] if present, else []
    signal_type           → mapped from event_type via EVENT_TYPE_MAP
    title                 → headline[:256] (fallback: event_type)
    summary               → description[:2000] (fallback: headline)
    severity_score        → severity (validated [0,1])
    confidence_score      → confidence (validated [0,1])
    detected_at           → timestamp (ISO 8601 required)
    time_horizon_hours    → 72 (JN does not publish a horizon — default 3 days)
    affected_domains      → inferred from tags via TAG_DOMAIN_MAP
    affected_geographies  → regions (verbatim)
    observed_evidence     → [ObservedEvidence] with raw_value = full raw payload
    inferred_reasoning    → [] (JN does not infer)
    simulation_context    → [] (JN does not simulate)
    causal_chain          → [] (JN does not chain)
    reasoning_summary     → "" (JN does not reason)
"""

from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone, timedelta
from typing import Any

from app.intelligence.models import (
    ADAPTER_VERSION,
    NormalizationStatus,
    NormalizedIntelligenceSignal,
    ObservedEvidence,
    SourceFamily,
    _norm_signal_id,
    _now_utc,
)
from app.intelligence.trace import AdapterError, NormalizationViolation, TraceBuilder

logger = logging.getLogger("observatory.intelligence.jet_nexus")


# ─── Error ────────────────────────────────────────────────────────────────────

class JetNexusAdapterError(AdapterError):
    """Raised when a Jet Nexus payload fails adapter validation."""


# ─── Mapping tables ───────────────────────────────────────────────────────────

# Jet Nexus event_type → NIS signal_type
# Covers the known JN event taxonomy.  Unknown types generate a MEDIUM warning
# and default to "disruption" — never a crash.
JET_NEXUS_EVENT_TYPE_MAP: dict[str, str] = {
    # Operational disruptions
    "supply_disruption":       "disruption",
    "port_closure":            "disruption",
    "port_congestion":         "disruption",
    "shipping_delay":          "disruption",
    "flight_disruption":       "disruption",
    "road_closure":            "disruption",
    "border_closure":          "disruption",
    "infrastructure_failure":  "disruption",
    "weather_event":           "disruption",
    "natural_disaster":        "disruption",
    "power_outage":            "disruption",
    # Escalation / risk events
    "geopolitical_escalation": "escalation",
    "conflict":                "escalation",
    "sanctions":               "escalation",
    "protest":                 "escalation",
    "civil_unrest":            "escalation",
    "strike":                  "escalation",
    "coup":                    "escalation",
    # Alerts (requiring watch, not immediate disruption)
    "market_volatility":       "alert",
    "cyber_attack":            "alert",
    "regulatory_change":       "alert",
    "trade_restriction":       "alert",
    "currency_pressure":       "alert",
    "leadership_change":       "alert",
    # Recovery / normalization
    "recovery":                "recovery",
    "normalization":           "recovery",
    "route_restoration":       "recovery",
    "sanction_lifted":         "recovery",
    "ceasefire":               "recovery",
}

_DEFAULT_SIGNAL_TYPE: str = "disruption"

# Jet Nexus tag → NIS affected_domain
# Case-insensitive substring match: if the tag contains the key, the domain
# is added. First match per domain prevents duplicates.
JET_NEXUS_TAG_DOMAIN_MAP: list[tuple[str, str]] = [
    ("bank",       "banking"),
    ("trade",      "banking"),
    ("credit",     "banking"),
    ("finance",    "banking"),
    ("shipping",   "banking"),
    ("port",       "banking"),
    ("logistics",  "banking"),
    ("energy",     "banking"),
    ("oil",        "banking"),
    ("gas",        "banking"),
    ("commodity",  "banking"),
    ("fintech",    "fintech"),
    ("payment",    "fintech"),
    ("remittance", "fintech"),
    ("digital",    "fintech"),
    ("crypto",     "fintech"),
    ("aviation",   "fintech"),
    ("insurance",  "insurance"),
    ("reinsur",    "insurance"),
    ("underwr",    "insurance"),
]

_DEFAULT_DOMAINS: list[str] = ["banking"]

# Plausibility window for JN timestamps
_MAX_FUTURE_HOURS: int = 72
_MAX_PAST_YEARS:   int = 5
_EPOCH_ZERO: datetime  = datetime(1970, 1, 2, tzinfo=timezone.utc)

# Default forecast horizon (JN does not publish a time horizon)
_DEFAULT_HORIZON_HOURS: int = 72

# Required JN fields (used by adapter and validate_jet_nexus_payload)
JET_NEXUS_REQUIRED_FIELDS: tuple[str, ...] = (
    "timestamp",
    "severity",
    "confidence",
    "headline",
)

JET_NEXUS_SOURCE_FAMILY: SourceFamily = SourceFamily.JET_NEXUS


# ─── Validation ───────────────────────────────────────────────────────────────

def validate_jet_nexus_payload(
    raw: dict[str, Any],
    tb: TraceBuilder,
) -> None:
    """Validate a raw Jet Nexus payload and record issues into tb.

    Violations (fatal — cause REJECTED status and raise):
        - missing timestamp
        - missing or out-of-range severity
        - missing or out-of-range confidence
        - missing headline
        - unparseable timestamp

    Warnings (non-fatal — cause PARTIAL status):
        - missing event_id (traceability reduced)
        - unknown event_type (defaults to "disruption")
        - empty tags (domain scope defaulted to ["banking"])
        - timestamp far in the past (> 5 years)

    Does not raise — caller checks tb.has_violations().
    """
    # ── Required fields ───────────────────────────────────────────────────────
    for field_name in JET_NEXUS_REQUIRED_FIELDS:
        val = raw.get(field_name)
        if val is None or (isinstance(val, str) and not val.strip()):
            tb.violation(
                field_name=field_name,
                message=f"Jet Nexus required field '{field_name}' is missing or blank",
                received_value=val,
                rule="REQUIRED_FIELD",
            )

    # ── Severity range ────────────────────────────────────────────────────────
    severity = raw.get("severity")
    if severity is not None:
        try:
            fval = float(severity)
            if not (0.0 <= fval <= 1.0):
                tb.violation(
                    field_name="severity",
                    message=f"severity must be in [0.0, 1.0], got {fval}",
                    received_value=severity,
                    rule="SCORE_RANGE",
                )
        except (TypeError, ValueError):
            tb.violation(
                field_name="severity",
                message=f"severity is not numeric: {severity!r}",
                received_value=severity,
                rule="NUMERIC_TYPE",
            )

    # ── Confidence range ──────────────────────────────────────────────────────
    confidence = raw.get("confidence")
    if confidence is not None:
        try:
            fval = float(confidence)
            if not (0.0 <= fval <= 1.0):
                tb.violation(
                    field_name="confidence",
                    message=f"confidence must be in [0.0, 1.0], got {fval}",
                    received_value=confidence,
                    rule="SCORE_RANGE",
                )
        except (TypeError, ValueError):
            tb.violation(
                field_name="confidence",
                message=f"confidence is not numeric: {confidence!r}",
                received_value=confidence,
                rule="NUMERIC_TYPE",
            )

    # ── Timestamp plausibility ────────────────────────────────────────────────
    timestamp = raw.get("timestamp")
    if timestamp is not None and isinstance(timestamp, str) and timestamp.strip():
        _validate_jn_timestamp("timestamp", timestamp, tb)

    # ── Soft warnings ─────────────────────────────────────────────────────────
    if not raw.get("event_id"):
        tb.warn(
            field_name="event_id",
            message="event_id not provided — downstream traceability is reduced",
            severity="MEDIUM",
        )

    event_type = raw.get("event_type", "")
    if event_type not in JET_NEXUS_EVENT_TYPE_MAP:
        tb.warn(
            field_name="event_type",
            message=(
                f"Unknown event_type '{event_type}' — "
                f"signal_type will default to '{_DEFAULT_SIGNAL_TYPE}'. "
                f"Known types: {sorted(JET_NEXUS_EVENT_TYPE_MAP)}"
            ),
            original_value=event_type,
            resolved_value=_DEFAULT_SIGNAL_TYPE,
            severity="LOW",
        )

    tags = raw.get("tags", [])
    if not isinstance(tags, list) or len(tags) == 0:
        tb.warn(
            field_name="tags",
            message=(
                "tags is empty — affected_domains will default to "
                f"{_DEFAULT_DOMAINS}"
            ),
            original_value=tags,
            resolved_value=_DEFAULT_DOMAINS,
            severity="LOW",
        )


def _validate_jn_timestamp(field_name: str, val: str, tb: TraceBuilder) -> None:
    """Parse and plausibility-check a Jet Nexus timestamp string."""
    now = datetime.now(timezone.utc)
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

    if ts <= _EPOCH_ZERO:
        tb.violation(
            field_name=field_name,
            message=f"{field_name} looks like epoch zero — likely a missing/unset value",
            received_value=val,
            rule="EPOCH_ZERO",
        )
    elif ts > now + timedelta(hours=_MAX_FUTURE_HOURS):
        tb.violation(
            field_name=field_name,
            message=f"{field_name} is more than {_MAX_FUTURE_HOURS}h in the future",
            received_value=val,
            rule="FUTURE_TIMESTAMP",
        )
    elif ts < now - timedelta(days=_MAX_PAST_YEARS * 365):
        tb.warn(
            field_name=field_name,
            message=f"{field_name} is more than {_MAX_PAST_YEARS} years in the past",
            original_value=val,
            severity="MEDIUM",
        )


# ─── Private mappers ──────────────────────────────────────────────────────────

def _map_signal_type(event_type: str, tb: TraceBuilder) -> str:
    """Map JN event_type to NIS signal_type. Warns on unknown type."""
    mapped = JET_NEXUS_EVENT_TYPE_MAP.get(event_type)
    if mapped is None:
        # Warning already recorded in validate_jet_nexus_payload
        return _DEFAULT_SIGNAL_TYPE
    return mapped


def _map_domains(tags: list[str], tb: TraceBuilder) -> list[str]:
    """Infer affected_domains from JN tags using TAG_DOMAIN_MAP.

    Checks each tag (lowercase) against each key in TAG_DOMAIN_MAP.
    Collects unique domains in order of first match.
    Falls back to _DEFAULT_DOMAINS if no match found.
    """
    if not isinstance(tags, list) or not tags:
        # Warning already recorded in validate_jet_nexus_payload
        return list(_DEFAULT_DOMAINS)

    seen: set[str] = set()
    domains: list[str] = []
    for tag in tags:
        tag_lower = str(tag).lower()
        for key, domain in JET_NEXUS_TAG_DOMAIN_MAP:
            if key in tag_lower and domain not in seen:
                domains.append(domain)
                seen.add(domain)

    if not domains:
        tb.warn(
            field_name="tags",
            message=(
                f"No recognized domain keywords in tags={tags!r} — "
                f"defaulting to {_DEFAULT_DOMAINS}"
            ),
            original_value=tags,
            resolved_value=_DEFAULT_DOMAINS,
            severity="LOW",
        )
        return list(_DEFAULT_DOMAINS)

    tb.note("affected_domains", f"Inferred from tags: {domains}")
    return domains


def _parse_jn_timestamp(timestamp_str: str | None, tb: TraceBuilder) -> datetime:
    """Parse JN timestamp string to datetime. Defaults to now on parse failure."""
    if not timestamp_str:
        # Violation already recorded — return now as safe fallback
        return _now_utc()

    try:
        ts = datetime.fromisoformat(str(timestamp_str))
        if ts.tzinfo is None:
            ts = ts.replace(tzinfo=timezone.utc)
        return ts
    except ValueError:
        # Violation already recorded in validation — return now as fallback
        return _now_utc()


def _build_event_id(raw: dict[str, Any]) -> str:
    """Return event_id from raw, or generate a synthetic traceable ID."""
    eid = raw.get("event_id")
    if eid:
        return str(eid)[:128]
    synthetic = f"jn-synthetic-{uuid.uuid4().hex[:12]}"
    return synthetic


# ─── Main adapter ─────────────────────────────────────────────────────────────

def adapt_jet_nexus_payload(raw: dict[str, Any]) -> NormalizedIntelligenceSignal:
    """Convert a Jet Nexus native payload to NormalizedIntelligenceSignal.

    This is the ONLY authorized entry point for Jet Nexus data.
    No Jet Nexus data may enter any other layer of the platform directly.

    The full raw payload is preserved in:
        - evidence_payload  (top-level, for the signal contract)
        - ObservedEvidence.raw_value (inside observed_evidence[0])

    This guarantees complete traceability from the Jet Nexus source event
    all the way through the adapter layer.

    Args:
        raw: Native Jet Nexus payload dict. Must conform to the JN payload shape.

    Returns:
        NormalizedIntelligenceSignal with:
            - normalization_status: NORMALIZED (clean) or PARTIAL (warnings)
            - source_family: jet_nexus
            - observed_evidence: [1 ObservedEvidence] — the raw JN event
            - inferred_reasoning: [] — JN does not infer
            - simulation_context: [] — JN does not simulate

    Raises:
        JetNexusAdapterError: when the payload is missing required fields,
            scores are out of range, or the timestamp is invalid.
    """
    tb = TraceBuilder(
        source_family   = SourceFamily.JET_NEXUS.value,
        source_systems  = ["jet_nexus"],
        adapter_version = ADAPTER_VERSION,
    )
    tb.note("adapter", "Jet Nexus v1 adapter invoked")

    # ── Validate ──────────────────────────────────────────────────────────────
    validate_jet_nexus_payload(raw, tb)

    if tb.has_violations():
        raise JetNexusAdapterError(
            f"Jet Nexus payload failed validation with "
            f"{len(tb.get_violations())} violation(s): "
            + "; ".join(v.message for v in tb.get_violations()),
            violations=tb.get_violations(),
        )

    # ── Map fields ────────────────────────────────────────────────────────────
    event_id      = _build_event_id(raw)
    event_type    = str(raw.get("event_type") or "")
    headline      = str(raw.get("headline") or "").strip()
    description   = str(raw.get("description") or "").strip()
    tags          = raw.get("tags") if isinstance(raw.get("tags"), list) else []
    regions       = [str(r) for r in raw.get("regions", []) if r]
    metadata      = raw.get("metadata") if isinstance(raw.get("metadata"), dict) else {}

    signal_type       = _map_signal_type(event_type, tb)
    title             = (headline or event_type or "Jet Nexus event")[:256]
    summary           = (description or headline or "")[:2000]
    severity_score    = float(raw.get("severity", 0.5))
    confidence_score  = float(raw.get("confidence", 0.5))
    detected_at       = _parse_jn_timestamp(raw.get("timestamp"), tb)
    affected_domains  = _map_domains(tags, tb)

    tb.note(
        "signal_type",
        f"Mapped from event_type='{event_type}' → signal_type='{signal_type}'",
    )

    # ── Build ObservedEvidence ────────────────────────────────────────────────
    # Full raw payload is preserved in raw_value — complete audit trail.
    # Jet Nexus is OBSERVED: it reports facts, not interpretations.
    observed = ObservedEvidence(
        source_system    = "jet_nexus",
        source_event_id  = event_id,
        observed_at      = detected_at,
        entity_refs      = [],   # JN v1 does not carry structured entity refs
        raw_value        = dict(raw),  # complete verbatim source payload
        notes            = (
            f"event_type={event_type or 'unspecified'} "
            f"| tags={tags!r} "
            f"| regions={regions!r}"
        )[:500],
    )

    tb.set_semantic_counts(observed=1, inferred=0, simulated=0)

    # ── Derive status and build trace ─────────────────────────────────────────
    status      = NormalizationStatus(tb.derived_status())
    trace       = tb.build()

    signal = NormalizedIntelligenceSignal(
        normalization_status  = status,
        source_family         = SourceFamily.JET_NEXUS,
        source_systems        = ["jet_nexus"],
        source_event_ids      = [event_id] if raw.get("event_id") else [],
        signal_type           = signal_type,
        title                 = title,
        summary               = summary,
        severity_score        = severity_score,
        confidence_score      = confidence_score,
        detected_at           = detected_at,
        time_horizon_hours    = _DEFAULT_HORIZON_HOURS,
        affected_domains      = affected_domains,
        affected_geographies  = regions,
        observed_evidence     = [observed],
        inferred_reasoning    = [],
        simulation_context    = [],
        causal_chain          = [],
        reasoning_summary     = "",
        evidence_payload      = dict(raw),  # verbatim — never interpreted
        trace_payload         = trace,
    )

    logger.info(
        "jet_nexus.adapt id=%s event_id=%s event_type=%s "
        "signal_type=%s status=%s severity=%.3f domains=%s",
        signal.normalized_signal_id,
        event_id,
        event_type,
        signal_type,
        status.value,
        severity_score,
        affected_domains,
    )

    return signal
