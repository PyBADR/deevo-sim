"""
Intelligence Adapter Foundation — Adapter Orchestration

PHASE 3: Main entry point for all external intelligence normalization.

This module is the ONLY authorized normalization entry point for external
intelligence. No external system may write directly to core layers.

Dispatches to source-specific adapters based on source_family.
Jet Nexus:          IMPLEMENTED (v1.0.0) — full native format normalization.
TREK:               IMPLEMENTED (v1.0.0) — enrichment: inferred reasoning.
Impact Observatory: IMPLEMENTED (v1.0.0) — enrichment: simulated projections.
The generic normalization path is fully functional for MANUAL_INTELLIGENCE.

Public API:
    normalize_intelligence_payload(raw)
        → NormalizedIntelligenceSignal  (raises AdapterError on failure)

    normalize_for_preview(raw, enable_trek, enable_simulation)
        → dict  (always returns, even on failure — for API preview endpoints)

    normalize_with_trek(raw)
        → NormalizedIntelligenceSignal  (normalizes + TREK enrichment)

    normalize_with_simulation(raw, enable_trek)
        → NormalizedIntelligenceSignal  (normalizes + optional TREK + simulation)

    get_adapter_for_family(source_family)
        → callable  (returns the source-specific adapter function)

Full pipeline (all layers enabled):
    normalize_intelligence_payload(raw)   → NIS
        → enrich_with_trek(NIS)           → NIS + inferred
        → enrich_with_simulation(NIS)     → NIS + inferred + simulated
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any, Callable

from .models import (
    ADAPTER_VERSION,
    NormalizationStatus,
    NormalizedIntelligenceSignal,
    ObservedEvidence,
    InferredReasoning,
    SimulatedProjection,
    SourceFamily,
    _now_utc,
    _norm_signal_id,
)
from .trace import AdapterError, TraceBuilder
from .validators import validate_raw_payload, assert_bridge_eligible

logger = logging.getLogger("observatory.intelligence.adapter")

# ─── Source family → adapter mapping ─────────────────────────────────────────

def _get_source_adapters() -> dict[str, Callable[[dict[str, Any]], NormalizedIntelligenceSignal]]:
    """Lazy import of source adapters to avoid circular imports.

    Returns mapping of source_family value → adapter function.
    Stubs raise NotImplementedError — this is intentional until each
    integration phase is complete.
    """
    from .sources.jet_nexus import adapt_jet_nexus_payload
    from .sources.trek import adapt_trek_payload
    from .sources.impact_observatory import adapt_impact_observatory_payload

    return {
        SourceFamily.JET_NEXUS:          adapt_jet_nexus_payload,
        SourceFamily.TREK:               adapt_trek_payload,
        SourceFamily.IMPACT_OBSERVATORY: adapt_impact_observatory_payload,
        # MANUAL_INTELLIGENCE uses the generic path below
    }


def get_adapter_for_family(
    source_family: str,
) -> Callable[[dict[str, Any]], NormalizedIntelligenceSignal] | None:
    """Return the source-specific adapter for a given family, or None if generic.

    Returns None for MANUAL_INTELLIGENCE (uses generic normalization).
    Returns the stub function for Jet Nexus / TREK / Observatory (will raise
    NotImplementedError until those integration phases are complete).
    """
    adapters = _get_source_adapters()
    return adapters.get(source_family)


# ─── Generic normalization ────────────────────────────────────────────────────

def _normalize_generic(
    raw: dict[str, Any],
    tb: TraceBuilder,
) -> NormalizedIntelligenceSignal:
    """Generic normalization path for MANUAL_INTELLIGENCE payloads.

    Also used as the reference implementation for adapter unit tests.
    Fully implemented — not a stub.
    """
    # Parse observed_evidence
    observed: list[ObservedEvidence] = []
    for item in raw.get("observed_evidence", []):
        try:
            observed.append(ObservedEvidence(**item))
            tb.note("observed_evidence", f"Parsed item from {item.get('source_system', '?')}")
        except Exception as exc:
            tb.warn("observed_evidence", f"Could not parse item: {exc}", severity="MEDIUM")

    # Parse inferred_reasoning
    inferred: list[InferredReasoning] = []
    for item in raw.get("inferred_reasoning", []):
        try:
            inferred.append(InferredReasoning(**item))
            tb.note("inferred_reasoning", f"Parsed item from {item.get('source_system', '?')}")
        except Exception as exc:
            tb.warn("inferred_reasoning", f"Could not parse item: {exc}", severity="MEDIUM")

    # Parse simulation_context
    simulated: list[SimulatedProjection] = []
    for item in raw.get("simulation_context", []):
        try:
            simulated.append(SimulatedProjection(**item))
            tb.note("simulation_context", f"Parsed item from {item.get('source_system', '?')}")
        except Exception as exc:
            tb.warn("simulation_context", f"Could not parse item: {exc}", severity="MEDIUM")

    tb.set_semantic_counts(len(observed), len(inferred), len(simulated))

    # Parse detected_at
    detected_at_raw = raw.get("detected_at")
    if isinstance(detected_at_raw, datetime):
        detected_at = detected_at_raw if detected_at_raw.tzinfo else detected_at_raw.replace(tzinfo=timezone.utc)
    elif isinstance(detected_at_raw, str):
        try:
            detected_at = datetime.fromisoformat(detected_at_raw)
            if detected_at.tzinfo is None:
                detected_at = detected_at.replace(tzinfo=timezone.utc)
        except ValueError:
            tb.violation(  # type: ignore[attr-defined]  # already called on tb
                "detected_at",
                f"Could not parse detected_at: {detected_at_raw!r}",
                received_value=detected_at_raw,
                rule="DATETIME_FORMAT",
            )
            detected_at = _now_utc()
    else:
        detected_at = _now_utc()
        tb.warn("detected_at", "Missing detected_at — defaulted to now", severity="MEDIUM")

    # Determine status from trace
    status_str = tb.derived_status()
    status = NormalizationStatus(status_str)

    trace_payload = tb.build()

    return NormalizedIntelligenceSignal(
        normalized_signal_id  = _norm_signal_id(),
        adapter_version       = ADAPTER_VERSION,
        normalization_status  = status,
        source_family         = SourceFamily(raw["source_family"]),
        source_systems        = list(raw.get("source_systems", [])),
        source_event_ids      = list(raw.get("source_event_ids", [])),
        signal_type           = str(raw.get("signal_type", "disruption")),
        title                 = str(raw.get("title", ""))[:256],
        summary               = str(raw.get("summary", ""))[:2000],
        severity_score        = float(raw.get("severity_score", 0.0)),
        confidence_score      = float(raw.get("confidence_score", 0.5)),
        detected_at           = detected_at,
        time_horizon_hours    = int(raw.get("time_horizon_hours", 72)),
        affected_domains      = list(raw.get("affected_domains", [])),
        affected_geographies  = list(raw.get("affected_geographies", [])),
        observed_evidence     = observed,
        inferred_reasoning    = inferred,
        simulation_context    = simulated,
        causal_chain          = list(raw.get("causal_chain", [])),
        reasoning_summary     = str(raw.get("reasoning_summary", ""))[:2000],
        evidence_payload      = dict(raw),
        trace_payload         = trace_payload,
    )


# ─── Public entry point ───────────────────────────────────────────────────────

def normalize_intelligence_payload(raw: dict[str, Any]) -> NormalizedIntelligenceSignal:
    """Normalize a raw external intelligence payload.

    This is the ONLY authorized entry point for all external intelligence.

    Dispatch logic:
        JET_NEXUS           → adapt_jet_nexus_payload (source adapter, own validation)
        TREK                → stub (NotImplementedError until integration)
        IMPACT_OBSERVATORY  → stub (NotImplementedError until integration)
        MANUAL_INTELLIGENCE → generic normalization (generic validation applied)

    SOURCE ADAPTER DISPATCH (before generic validation):
        Source-specific adapters (Jet Nexus, TREK, Observatory) receive native
        payloads in their own field schema. Generic validation (which checks for
        source_systems, signal_type, title, etc.) does NOT apply to native format
        payloads. Each source adapter runs its own validation internally.

        The `source_family` field in the raw payload is used ONLY for routing —
        the adapter itself is responsible for validating all other fields.

    Raises:
        AdapterError  — when payload is malformed or fails validation
        NotImplementedError — when source family adapter is not yet implemented

    Returns:
        NormalizedIntelligenceSignal — always NORMALIZED or PARTIAL status
        (REJECTED signals raise AdapterError instead of returning)
    """
    source_family = raw.get("source_family", "")
    source_systems = raw.get("source_systems", [])
    if not isinstance(source_systems, list):
        source_systems = [str(source_systems)]

    tb = TraceBuilder(
        source_family=str(source_family),
        source_systems=source_systems,
        adapter_version=ADAPTER_VERSION,
    )

    # Validate source_family enum membership
    try:
        sf = SourceFamily(source_family)
    except ValueError:
        tb.violation(
            field_name="source_family",
            message=(
                f"Unknown source_family '{source_family}'. "
                f"Accepted values: {[f.value for f in SourceFamily]}"
            ),
            received_value=source_family,
            rule="ENUM_MEMBERSHIP",
        )
        raise AdapterError(
            f"Invalid source_family '{source_family}'",
            violations=tb.get_violations(),
        )

    # ── Source-specific dispatch (BEFORE generic validation) ──────────────────
    # Source adapters use native payload formats (event_id, headline, etc.)
    # Generic validation checks for normalized-format fields and MUST NOT run
    # against native formats. Each source adapter handles its own validation.
    if sf != SourceFamily.MANUAL_INTELLIGENCE:
        adapter_fn = get_adapter_for_family(sf.value)
        if adapter_fn is not None:
            logger.info(
                "Dispatching to source adapter for family=%s (skipping generic validation)",
                sf.value,
            )
            return adapter_fn(raw)

    # ── Generic path (MANUAL_INTELLIGENCE or family with no registered adapter) ──
    # Run standard validation before generic normalization.
    validate_raw_payload(raw, tb)

    if tb.has_violations():
        raise AdapterError(
            f"Payload from '{source_family}' failed validation with "
            f"{len(tb.get_violations())} violation(s)",
            violations=tb.get_violations(),
        )

    signal = _normalize_generic(raw, tb)

    logger.info(
        "Normalized intelligence signal id=%s family=%s status=%s "
        "observed=%d inferred=%d simulated=%d",
        signal.normalized_signal_id,
        signal.source_family,
        signal.normalization_status,
        len(signal.observed_evidence),
        len(signal.inferred_reasoning),
        len(signal.simulation_context),
    )

    return signal


def normalize_with_trek(raw: dict[str, Any]) -> NormalizedIntelligenceSignal:
    """Normalize a raw payload and then enrich it with TREK reasoning.

    Pipeline:
        normalize_intelligence_payload(raw) → NIS → enrich_with_trek(NIS) → enriched NIS

    Intended for the Jet Nexus → TREK combined pipeline.
    Can also be used with MANUAL_INTELLIGENCE payloads.

    Raises:
        AdapterError        — payload validation failed (source step)
        NotImplementedError — source family adapter not yet implemented
        TREKAdapterError    — TREK enrichment failed (post-normalization)
    """
    from .sources.trek import enrich_with_trek

    signal   = normalize_intelligence_payload(raw)
    enriched = enrich_with_trek(signal)

    logger.info(
        "trek.pipeline completed id=%s family=%s inferences=%d",
        enriched.normalized_signal_id,
        enriched.source_family,
        len(enriched.inferred_reasoning),
    )
    return enriched


def normalize_with_simulation(
    raw: dict[str, Any],
    enable_trek: bool = True,
) -> NormalizedIntelligenceSignal:
    """Normalize a raw payload, optionally enrich with TREK, then apply simulation.

    Full pipeline (enable_trek=True):
        normalize_intelligence_payload(raw)  → NIS
        → enrich_with_trek(NIS)              → NIS + inferred reasoning
        → enrich_with_simulation(NIS)        → NIS + inferred + simulated projections

    Abbreviated pipeline (enable_trek=False):
        normalize_intelligence_payload(raw)  → NIS
        → enrich_with_simulation(NIS)        → NIS + simulated projections

    Note: TREK is recommended before simulation — simulation benefits from
    inferred_reasoning context, though it is not strictly required.

    Args:
        raw:         Raw payload dict.
        enable_trek: When True (default), apply TREK enrichment before simulation.

    Raises:
        AdapterError                    — payload validation failed
        NotImplementedError             — source adapter not implemented
        TREKAdapterError                — TREK enrichment failed
        ImpactObservatoryAdapterError   — simulation enrichment failed
    """
    from .sources.trek import enrich_with_trek
    from .sources.impact_observatory import enrich_with_simulation

    signal = normalize_intelligence_payload(raw)

    if enable_trek:
        signal = enrich_with_trek(signal)

    enriched = enrich_with_simulation(signal)

    logger.info(
        "simulation.pipeline completed id=%s family=%s "
        "inferred=%d simulated=%d",
        enriched.normalized_signal_id,
        enriched.source_family,
        len(enriched.inferred_reasoning),
        len(enriched.simulation_context),
    )
    return enriched


def normalize_for_preview(
    raw: dict[str, Any],
    enable_trek: bool = False,
    enable_simulation: bool = False,
) -> dict[str, Any]:
    """Normalize a payload and return a preview dict — never raises.

    Used by POST /api/v1/intelligence/normalize for safe preview.
    Returns either the normalized signal representation or an error report.

    Args:
        raw:               Raw payload dict.
        enable_trek:       When True, apply TREK enrichment after normalization.
        enable_simulation: When True, apply simulation enrichment (after TREK if enabled).
                           Simulation runs independently even if enable_trek=False.
    """
    try:
        if enable_simulation:
            signal = normalize_with_simulation(raw, enable_trek=enable_trek)
        elif enable_trek:
            signal = normalize_with_trek(raw)
        else:
            signal = normalize_intelligence_payload(raw)
        return {
            "success": True,
            "normalized_signal_id": signal.normalized_signal_id,
            "normalization_status": signal.normalization_status,
            "source_family":        signal.source_family,
            "source_systems":       signal.source_systems,
            "signal_type":          signal.signal_type,
            "title":                signal.title,
            "severity_score":       signal.severity_score,
            "confidence_score":     signal.confidence_score,
            "detected_at":          signal.detected_at.isoformat(),
            "time_horizon_hours":   signal.time_horizon_hours,
            "affected_domains":     signal.affected_domains,
            "semantic_summary":     signal.semantic_summary(),
            "trace_payload":        signal.trace_payload,
        }
    except NotImplementedError as exc:
        return {
            "success": False,
            "error": "NOT_IMPLEMENTED",
            "detail": str(exc),
            "source_family": raw.get("source_family"),
        }
    except AdapterError as exc:
        return {
            "success":    False,
            "error":      "ADAPTER_ERROR",
            "detail":     str(exc),
            "violations": exc.to_dict().get("violations", []),
        }
    except Exception as exc:
        logger.exception("Unexpected error during normalize_for_preview")
        return {
            "success": False,
            "error":   "INTERNAL_ERROR",
            "detail":  str(exc),
        }
