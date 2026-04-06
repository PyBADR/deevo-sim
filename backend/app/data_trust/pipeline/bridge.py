"""
Impact Observatory | مرصد الأثر — Intelligence Engine Bridge

Insertion point between the Data Trust Layer and the existing
intelligence pipeline. Only validated + scored data flows through here.

CRITICAL: This module does NOT rewrite the intelligence engine.
It adapts a TrustedEventContract into the shape expected by
app.ingestion.ingest.ingest_raw_event(), then passes it into
the existing quality pipeline stages.

Flow
----
    TrustedEventContract (validated + scored)
        ↓
    ingest_to_intelligence()
        ↓
    ingest_raw_event() [existing, unmodified]
        ↓
    validate_event()   [existing, unmodified]
        ↓
    normalize_event()  [existing, unmodified]
        → NormalizedEvent available for full pipeline use

The bridge stops at normalize_event() output and returns a structured result.
Callers that need the full 13-stage pipeline can call run_unified_pipeline()
after confirming the template_id is present in the contract's normalized_payload.

Domain → event_type mapping
----------------------------
    "government"  → "geopolitical"
    "real_estate" → "economic"
    "energy"      → "geopolitical"
    "banking"     → "economic"
    "maritime"    → "geopolitical"
    "aviation"    → "geopolitical"
    "cyber"       → "cyber"
    (default)     → "economic"

Bridge result shape
-------------------
    {
        "ok":          bool,
        "event_id":    str,
        "source":      str,
        "domain":      str,
        "confidence":  float,
        "error":       str | None,       # present when ok=False
        "ingest_id":   str | None,       # RawEvent.source_id
        "validated":   bool,             # True if validate_event passed
        "normalized":  bool,             # True if normalize_event ran
    }
"""

from __future__ import annotations

import logging
from typing import Optional

from ..contracts.event import TrustedEventContract

logger = logging.getLogger(__name__)

# ── Domain → event_type mapping ───────────────────────────────────────────────
_DOMAIN_TO_EVENT_TYPE: dict[str, str] = {
    "government":   "geopolitical",
    "real_estate":  "economic",
    "energy":       "geopolitical",
    "banking":      "economic",
    "insurance":    "economic",
    "maritime":     "geopolitical",
    "aviation":     "geopolitical",
    "logistics":    "economic",
    "cyber":        "cyber",
}
_DEFAULT_EVENT_TYPE = "economic"


def ingest_to_intelligence(
    contract: TrustedEventContract,
    *,
    run_id: Optional[str] = None,
) -> dict:
    """
    Pass a validated+scored TrustedEventContract into the existing quality pipeline.

    Adapts the contract into a RawEvent, runs validate_event() and
    normalize_event() from the existing quality layer.

    Does NOT trigger the full 13-stage run_unified_pipeline(). That pipeline
    is designed for scenario-catalog runs with a canonical template_id.
    External trust-layer events are validated and normalized here; full
    pipeline execution requires operator review (HITL gate) unless
    the event carries a known template_id.

    Parameters
    ----------
    contract : TrustedEventContract
        Validated and scored contract from the orchestrator.
    run_id : str, optional
        Orchestrator run ID for log correlation.

    Returns
    -------
    dict
        Bridge result with ok, event_id, error, ingest_id, validated, normalized.
    """
    tag = f"[{run_id}] " if run_id else ""
    event_id = contract.event_id

    # ── Import existing pipeline modules ──────────────────────────────────────
    # Imported here (not at module top) to keep the trust layer decoupled.
    # If the existing pipeline fails to import, the error surfaces immediately.
    try:
        from app.ingestion.ingest import ingest_raw_event
        from app.quality.validate import validate_event, ValidationError
        from app.quality.normalize import normalize_event
    except ImportError as exc:
        logger.error(
            "%sBridge import failed — existing intelligence pipeline unavailable: %s",
            tag, exc,
        )
        return {
            "ok": False,
            "event_id": event_id,
            "source": contract.source,
            "domain": contract.domain,
            "confidence": contract.confidence,
            "error": f"Intelligence pipeline import failed: {exc}",
            "ingest_id": None,
            "validated": False,
            "normalized": False,
        }

    # ── Build payload for ingest_raw_event() ─────────────────────────────────
    # Merge normalized_payload with geo, trust metadata, and any available fields.
    event_type = _DOMAIN_TO_EVENT_TYPE.get(contract.domain.lower(), _DEFAULT_EVENT_TYPE)

    ingest_payload = {
        **contract.normalized_payload,
        # Trust layer metadata — passed through for audit trail
        "_trust_event_id":   contract.event_id,
        "_trust_source":     contract.source,
        "_trust_domain":     contract.domain,
        "_trust_confidence": contract.confidence,
        "_trust_score":      contract.confidence,   # same value, explicit alias
        # Geo for pipeline context
        "_geo_country": contract.geo.get("country", ""),
        "_geo_region":  contract.geo.get("region", ""),
    }

    # Forward impact_score as severity if no explicit severity in payload
    if "severity" not in ingest_payload and contract.impact_score is not None:
        ingest_payload["severity"] = contract.impact_score

    # ── Stage 1 (existing): Ingest ────────────────────────────────────────────
    try:
        raw_event = ingest_raw_event(
            source=contract.source,
            source_id=contract.event_id,
            event_type=event_type,
            payload=ingest_payload,
        )
        ingest_id = raw_event.source_id
        logger.info(
            "%sBridge ingest OK event_id=%s ingest_id=%s event_type=%s",
            tag, event_id, ingest_id, event_type,
        )
    except Exception as exc:
        logger.error("%sBridge ingest_raw_event failed event_id=%s: %s", tag, event_id, exc)
        return {
            "ok": False,
            "event_id": event_id,
            "source": contract.source,
            "domain": contract.domain,
            "confidence": contract.confidence,
            "error": f"ingest_raw_event() failed: {exc}",
            "ingest_id": None,
            "validated": False,
            "normalized": False,
        }

    # ── Stage 2 (existing): Validate ──────────────────────────────────────────
    validated_event = None
    try:
        validated_event = validate_event(raw_event)
        logger.info(
            "%sBridge validate OK event_id=%s score=%.3f",
            tag, event_id, validated_event.validation_score,
        )
    except ValidationError as exc:
        # The existing validator raised — the record has structural issues
        # beyond what the trust layer already checked (e.g. unknown template_id).
        # Return partial success: ingest succeeded, validation failed.
        logger.warning(
            "%sBridge validate FAILED event_id=%s errors=%s",
            tag, event_id, exc.errors,
        )
        return {
            "ok": False,
            "event_id": event_id,
            "source": contract.source,
            "domain": contract.domain,
            "confidence": contract.confidence,
            "error": f"Existing validate_event() rejected: {exc.errors}",
            "ingest_id": ingest_id,
            "validated": False,
            "normalized": False,
        }
    except Exception as exc:
        logger.error("%sBridge validate unexpected error event_id=%s: %s", tag, event_id, exc)
        return {
            "ok": False,
            "event_id": event_id,
            "source": contract.source,
            "domain": contract.domain,
            "confidence": contract.confidence,
            "error": f"validate_event() unexpected: {exc}",
            "ingest_id": ingest_id,
            "validated": False,
            "normalized": False,
        }

    # ── Stage 3 (existing): Normalize ─────────────────────────────────────────
    try:
        normalized_event = normalize_event(validated_event)
        logger.info(
            "%sBridge normalize OK event_id=%s normalized_id=%s",
            tag, event_id, normalized_event.event_id,
        )
    except ValueError as exc:
        # normalize_event raises ValueError for HARD_FAIL (unknown template_id etc.)
        logger.warning(
            "%sBridge normalize HARD_FAIL event_id=%s: %s", tag, event_id, exc
        )
        # Validated but not normalized — still a partial pass.
        # Return ok=True with normalized=False so the orchestrator knows this record
        # reached the intelligence boundary but needs a template_id to go further.
        return {
            "ok": True,
            "event_id": event_id,
            "source": contract.source,
            "domain": contract.domain,
            "confidence": contract.confidence,
            "error": None,
            "ingest_id": ingest_id,
            "validated": True,
            "normalized": False,
            "normalize_note": (
                "normalize_event() raised (likely missing template_id in payload). "
                "Record is validated; full pipeline requires template_id."
            ),
        }
    except Exception as exc:
        logger.error("%sBridge normalize unexpected error event_id=%s: %s", tag, event_id, exc)
        return {
            "ok": False,
            "event_id": event_id,
            "source": contract.source,
            "domain": contract.domain,
            "confidence": contract.confidence,
            "error": f"normalize_event() unexpected: {exc}",
            "ingest_id": ingest_id,
            "validated": True,
            "normalized": False,
        }

    # ── Full pass ─────────────────────────────────────────────────────────────
    return {
        "ok":           True,
        "event_id":     event_id,
        "source":       contract.source,
        "domain":       contract.domain,
        "confidence":   contract.confidence,
        "error":        None,
        "ingest_id":    ingest_id,
        "validated":    True,
        "normalized":   True,
        "normalized_id": normalized_event.event_id,
        "geo_scope":    normalized_event.geographic_scope,
    }
