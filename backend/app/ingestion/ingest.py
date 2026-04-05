"""
Impact Observatory | مرصد الأثر — Ingestion Layer

Stage 1: Accept raw events from scenario catalog or external feeds.
Converts incoming requests into RawEvent objects for the quality pipeline.

Rules:
- Source must be in KNOWN_SOURCES (or default to low-trust)
- Payload must be parseable
- Malformed inputs are rejected immediately
"""

import uuid
from datetime import datetime, timezone

from app.domain.models.raw_event import RawEvent
from .sources import KNOWN_SOURCES, get_source_trust_weight


def ingest_scenario(
    template_id: str,
    severity: float,
    horizon_hours: int,
    label: str = "",
) -> RawEvent:
    """Ingest from the built-in scenario catalog (highest trust)."""
    return RawEvent(
        source="scenario_catalog",
        source_id=f"catalog_{template_id}_{uuid.uuid4().hex[:8]}",
        event_type="geopolitical",
        payload={
            "template_id": template_id,
            "severity": severity,
            "horizon_hours": horizon_hours,
            "label": label,
        },
        received_at=datetime.now(timezone.utc),
        provenance={
            "source": "scenario_catalog",
            "trust_weight": 1.0,
            "template_id": template_id,
        },
    )


def ingest_raw_event(
    source: str,
    source_id: str,
    event_type: str,
    payload: dict,
) -> RawEvent:
    """Ingest from any external source (variable trust).

    Parameters
    ----------
    source : str
        Source identifier (e.g. "crucix", "manual", "external_api").
    source_id : str
        Original ID from the source system.
    event_type : str
        Event category: "geopolitical", "economic", "natural", "cyber".
    payload : dict
        Raw event payload — will be validated in quality layer.

    Returns
    -------
    RawEvent
        Unvalidated event ready for the quality pipeline.

    Raises
    ------
    ValueError
        If payload is not a dict or event_type is empty.
    """
    if not isinstance(payload, dict):
        raise ValueError("Payload must be a dict")
    if not event_type:
        raise ValueError("event_type is required")

    trust_weight = get_source_trust_weight(source)

    return RawEvent(
        source=source,
        source_id=source_id or f"{source}_{uuid.uuid4().hex[:8]}",
        event_type=event_type,
        payload=payload,
        received_at=datetime.now(timezone.utc),
        provenance={
            "source": source,
            "trust_weight": trust_weight,
            "known_source": source in KNOWN_SOURCES,
        },
    )
