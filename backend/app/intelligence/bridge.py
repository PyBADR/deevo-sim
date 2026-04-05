"""
Intelligence Adapter Foundation — Signal Bridge Contract

PHASE 5: Typed bridge from NormalizedIntelligenceSignal → LiveSignal.

The bridge is the ONLY authorized path from normalized external intelligence
into the core signal pipeline. It enforces:

    1. Bridge eligibility gate (assert_bridge_eligible must pass)
    2. Explicit field-by-field mapping — no implicit coercion
    3. Provenance preservation — source_family + normalized_signal_id carried
       into the payload field of the resulting LiveSignal
    4. Semantic separation enforced — observed / inferred / simulated sections
       are never collapsed; they are packaged into the payload for downstream use

CONTRACT GUARANTEES:
    - Sector defaults: if affected_domains contains "banking" → BANKING
                       if affected_domains contains "fintech"  → FINTECH
                       otherwise                               → BANKING (default with warning)
    - Source mapping: jet_nexus → CRUCIX (proprietary external feed)
                      trek / impact_observatory / manual_intelligence → MANUAL
    - description: signal.summary[:500] — matches LiveSignal.description max_length
    - payload: contains bridge_meta + semantic sections from signal
    - entity_ids: signal.source_systems — operator-meaningful provenance IDs

LIMITATIONS (explicit — not defects):
    - Only BANKING and FINTECH sectors are supported in the current LiveSignal
      contract. Insurance and other domains are logged and the bridge falls back
      to BANKING. This restriction belongs to LiveSignal, not to this bridge.
    - Geo coordinates are not mapped: NormalizedIntelligenceSignal carries no
      lat/lng fields. The bridge sets lat=None, lng=None.
    - The bridge does NOT submit the resulting LiveSignal to the HITL queue.
      Callers are responsible for downstream submission (signals.hitl.submit).

Usage:
    from app.intelligence.bridge import SignalBridge

    live = SignalBridge.to_live_signal(normalized_signal)
    # → then submit to HITL:
    # from app.signals.hitl import submit
    # seed = submit(live)
"""

from __future__ import annotations

import logging
from typing import Any

from app.domain.models.live_signal import LiveSignal, LiveSignalSource, SignalSector
from app.intelligence.models import NormalizedIntelligenceSignal, SourceFamily
from app.intelligence.trace import AdapterError
from app.intelligence.validators import assert_bridge_eligible

logger = logging.getLogger("observatory.intelligence.bridge")

# ─── Mapping tables ───────────────────────────────────────────────────────────

# SourceFamily → LiveSignalSource
# CRUCIX is used for external intelligence feeds (Jet Nexus) since it is
# defined as "proprietary intelligence feed" in LiveSignalSource.
# Full source type extension is deferred to the per-family integration phase.
_SOURCE_FAMILY_TO_SIGNAL_SOURCE: dict[str, LiveSignalSource] = {
    SourceFamily.JET_NEXUS:           LiveSignalSource.CRUCIX,
    SourceFamily.TREK:                LiveSignalSource.MANUAL,
    SourceFamily.IMPACT_OBSERVATORY:  LiveSignalSource.MANUAL,
    SourceFamily.MANUAL_INTELLIGENCE: LiveSignalSource.MANUAL,
}

# Domain strings that map to supported SignalSector values.
# Checked in order — first match wins.
_DOMAIN_TO_SECTOR: list[tuple[str, SignalSector]] = [
    ("banking",  SignalSector.BANKING),
    ("fintech",  SignalSector.FINTECH),
]

_DEFAULT_SECTOR = SignalSector.BANKING


# ─── Bridge ───────────────────────────────────────────────────────────────────

class SignalBridgeError(AdapterError):
    """Raised when the bridge cannot produce a valid LiveSignal."""


class SignalBridge:
    """Typed bridge: NormalizedIntelligenceSignal → LiveSignal.

    All methods are class-level — no instance state.
    """

    @classmethod
    def to_live_signal(
        cls,
        signal: NormalizedIntelligenceSignal,
    ) -> LiveSignal:
        """Convert a normalized intelligence signal to a LiveSignal.

        Enforces bridge eligibility before mapping.
        The returned LiveSignal is ready for submission to signals.hitl.submit().

        Args:
            signal: A NormalizedIntelligenceSignal in NORMALIZED or PARTIAL status.

        Returns:
            LiveSignal — fully typed, ready for HITL submission.

        Raises:
            SignalBridgeError / AdapterError — if signal fails bridge eligibility.
        """
        # Gate 1: bridge eligibility (status, scores, domains, trace completeness)
        assert_bridge_eligible(signal)

        source     = cls._map_source(signal.source_family)
        sector     = cls._map_sector(signal.affected_domains, signal.normalized_signal_id)
        event_type = cls._map_event_type(signal.signal_type)
        description = signal.summary[:500]
        payload    = cls._build_payload(signal)

        live = LiveSignal(
            source         = source,
            sector         = sector,
            event_type     = event_type,
            severity_raw   = signal.severity_score,
            confidence_raw = signal.confidence_score,
            entity_ids     = list(signal.source_systems),
            lat            = None,
            lng            = None,
            description    = description,
            payload        = payload,
        )

        logger.info(
            "Bridge: NIS %s → LiveSignal %s  source=%s sector=%s severity=%.3f",
            signal.normalized_signal_id,
            live.signal_id,
            source.value,
            sector.value,
            signal.severity_score,
        )

        return live

    # ── Private helpers ────────────────────────────────────────────────────────

    @classmethod
    def _map_source(cls, source_family: SourceFamily) -> LiveSignalSource:
        """Map SourceFamily → LiveSignalSource.

        Explicit mapping table — never falls through to a default silently.
        All four families have entries; missing families raise SignalBridgeError.
        """
        mapped = _SOURCE_FAMILY_TO_SIGNAL_SOURCE.get(source_family)
        if mapped is None:
            raise SignalBridgeError(
                f"No LiveSignalSource mapping for source_family '{source_family}'. "
                "Update bridge._SOURCE_FAMILY_TO_SIGNAL_SOURCE to add the mapping.",
                violations=[],
            )
        return mapped

    @classmethod
    def _map_sector(
        cls,
        affected_domains: list[str],
        signal_id: str,
    ) -> SignalSector:
        """Derive SignalSector from affected_domains.

        Checks each domain string (case-insensitive) against _DOMAIN_TO_SECTOR.
        First match wins.  Falls back to BANKING with a warning if no match.

        Bridge limitation: LiveSignal.sector is currently BANKING | FINTECH only.
        Insurance, regulatory, and other domains will be supported when LiveSignal
        is extended in the sector-expansion integration phase.
        """
        lower_domains = [d.lower() for d in affected_domains]
        for domain_key, sector in _DOMAIN_TO_SECTOR:
            if any(domain_key in d for d in lower_domains):
                return sector

        logger.warning(
            "Bridge %s: no recognized sector in affected_domains=%r — defaulting to BANKING. "
            "This is a LiveSignal contract limitation (only BANKING/FINTECH supported).",
            signal_id,
            affected_domains,
        )
        return _DEFAULT_SECTOR

    @classmethod
    def _map_event_type(cls, signal_type: str) -> str:
        """Map signal_type to LiveSignal.event_type (max 128 chars)."""
        return str(signal_type)[:128]

    @classmethod
    def _build_payload(cls, signal: NormalizedIntelligenceSignal) -> dict[str, Any]:
        """Build the LiveSignal.payload dict from the normalized signal.

        Preserves full provenance and semantic sections.
        The trace_payload is EXCLUDED from the bridge payload (it is large and
        belongs to the intelligence adapter layer, not the signal layer).

        Payload structure:
            bridge_meta     — bridge provenance (normalized_signal_id, adapter_version, status)
            signal_type     — original signal_type string
            title           — signal title (not available on LiveSignal directly)
            time_horizon_hours — original horizon
            affected_geographies — from signal
            causal_chain    — causal chain list from signal
            reasoning_summary — from signal
            semantic_summary — observed/inferred/simulated counts
            observed_evidence — list of dicts (OBSERVED facts)
            inferred_reasoning — list of dicts (INFERRED reasoning)
            simulation_context — list of dicts (SIMULATED projections)
            source_event_ids — original event IDs for traceability
        """
        return {
            "bridge_meta": {
                "normalized_signal_id": signal.normalized_signal_id,
                "adapter_version":      signal.adapter_version,
                "normalization_status": signal.normalization_status,
                "source_family":        signal.source_family,
                "normalized_at":        signal.normalized_at.isoformat(),
            },
            "signal_type":            signal.signal_type,
            "title":                  signal.title,
            "time_horizon_hours":     signal.time_horizon_hours,
            "affected_geographies":   signal.affected_geographies,
            "causal_chain":           signal.causal_chain,
            "reasoning_summary":      signal.reasoning_summary,
            "semantic_summary":       signal.semantic_summary(),
            "observed_evidence":      [e.model_dump() for e in signal.observed_evidence],
            "inferred_reasoning":     [r.model_dump() for r in signal.inferred_reasoning],
            "simulation_context":     [p.model_dump() for p in signal.simulation_context],
            "source_event_ids":       signal.source_event_ids,
        }


# ─── Convenience function ─────────────────────────────────────────────────────

def bridge_to_live_signal(signal: NormalizedIntelligenceSignal) -> LiveSignal:
    """Module-level convenience wrapper for SignalBridge.to_live_signal().

    Equivalent to SignalBridge.to_live_signal(signal).
    """
    return SignalBridge.to_live_signal(signal)
