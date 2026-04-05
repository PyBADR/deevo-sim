"""signals.normalizer — Raw input → LiveSignal.

Takes an arbitrary inbound dict (from API, manual entry, or feed adapter)
and produces a validated, typed LiveSignal.

MVP scope: banking + fintech sectors only.
Signals with any other sector are rejected with NormalizationError.

Responsibilities:
1. Validate required fields — reject missing/malformed inputs immediately.
2. Normalize field aliases — handle variant keys from different sources.
3. Clamp numeric ranges — severity and confidence forced into [0, 1].
4. Enforce sector scope — reject anything not banking or fintech.
5. Resolve geo → entity IDs — find nearest finance-layer graph nodes within
   MAX_GEO_RADIUS_DEG. Falls back gracefully if entity graph unavailable.
6. Produce a frozen LiveSignal.

No side effects, no state mutation, no I/O.
"""

from __future__ import annotations

import math
import logging
from typing import Any

from app.domain.models.live_signal import (
    LiveSignal,
    LiveSignalSource,
    SignalSector,
)
from app.domain.sources import get_source_weight

logger = logging.getLogger(__name__)

# ── Constants ─────────────────────────────────────────────────────────────────

MAX_GEO_RADIUS_DEG: float = 5.0  # ~500 km in GCC bounding box
MAX_ENTITY_IDS: int = 5
FINANCE_LAYERS: frozenset[str] = frozenset({"finance", "government"})

_SECTOR_MAP: dict[str, SignalSector] = {
    "banking":  SignalSector.BANKING,
    "bank":     SignalSector.BANKING,
    "fintech":  SignalSector.FINTECH,
    "payments": SignalSector.FINTECH,
    "payment":  SignalSector.FINTECH,
}

_SOURCE_MAP: dict[str, LiveSignalSource] = {
    s.value: s for s in LiveSignalSource
}


# ── Exception ─────────────────────────────────────────────────────────────────

class NormalizationError(ValueError):
    """Raised when an inbound dict cannot be normalized into a LiveSignal."""


# ── Public entry point ────────────────────────────────────────────────────────

def normalize(raw: dict[str, Any]) -> LiveSignal:
    """Normalize a raw inbound dict into a typed LiveSignal.

    Raises NormalizationError if the input cannot be normalized.
    """
    data: dict[str, Any] = {k.lower(): v for k, v in raw.items()}

    sector = _extract_sector(data)
    source = _extract_source(data)
    event_type = _extract_event_type(data)

    severity_raw = _extract_float(
        data, ("severity_raw", "severity_score", "severity"), required=True, field="severity"
    )
    severity_raw = _clamp(severity_raw)

    default_conf = get_source_weight(source) * 0.9
    confidence_raw = _extract_float(
        data, ("confidence_raw", "confidence"), required=False, field="confidence",
        default=default_conf,
    )
    confidence_raw = _clamp(confidence_raw)

    lat = _extract_float(data, ("lat", "latitude"), required=False, field="lat")
    lng = _extract_float(data, ("lng", "longitude"), required=False, field="lng")

    if lat is not None and not (-90.0 <= lat <= 90.0):
        raise NormalizationError(f"latitude out of range: {lat}")
    if lng is not None and not (-180.0 <= lng <= 180.0):
        raise NormalizationError(f"longitude out of range: {lng}")

    entity_ids: list[str] = _resolve_entity_ids(
        lat, lng, data.get("entity_ids", data.get("entity_id"))
    )

    description = str(data.get("description", data.get("notes", "")))[:500]
    payload: dict[str, Any] = dict(raw)

    return LiveSignal(
        source=source,
        sector=sector,
        event_type=event_type,
        severity_raw=severity_raw,
        confidence_raw=confidence_raw,
        entity_ids=entity_ids,
        lat=lat,
        lng=lng,
        description=description,
        payload=payload,
    )


# ── Internal helpers ──────────────────────────────────────────────────────────

def _extract_sector(data: dict[str, Any]) -> SignalSector:
    raw = str(data.get("sector", "")).lower().strip()
    if not raw:
        raise NormalizationError("missing required field 'sector'")
    sector = _SECTOR_MAP.get(raw)
    if sector is None:
        raise NormalizationError(
            f"sector '{raw}' is outside MVP scope — only banking and fintech are accepted"
        )
    return sector


def _extract_source(data: dict[str, Any]) -> LiveSignalSource:
    raw = str(data.get("source", data.get("source_type", "manual"))).lower().strip()
    source = _SOURCE_MAP.get(raw)
    if source is None:
        logger.debug("Unknown source '%s' — treating as MANUAL", raw)
        return LiveSignalSource.MANUAL
    return source


def _extract_event_type(data: dict[str, Any]) -> str:
    ev = str(data.get("event_type", data.get("type", ""))).strip()
    if not ev:
        raise NormalizationError("missing required field 'event_type'")
    return ev[:128]


def _extract_float(
    data: dict[str, Any],
    keys: tuple[str, ...],
    *,
    required: bool,
    field: str,
    default: float | None = None,
) -> float | None:
    for key in keys:
        val = data.get(key)
        if val is not None:
            try:
                return float(val)
            except (TypeError, ValueError):
                raise NormalizationError(f"field '{field}' is not numeric: {val!r}")
    if required:
        raise NormalizationError(f"missing required field '{field}' (tried: {keys})")
    return default


def _clamp(v: float | None, lo: float = 0.0, hi: float = 1.0) -> float:
    if v is None:
        return lo
    return max(lo, min(hi, v))


def _resolve_entity_ids(
    lat: float | None,
    lng: float | None,
    explicit: object,
) -> list[str]:
    if explicit is not None:
        if isinstance(explicit, (list, tuple)):
            return [str(e) for e in explicit][:MAX_ENTITY_IDS]
        if isinstance(explicit, str) and explicit.strip():
            return [explicit.strip()]

    if lat is not None and lng is not None:
        return _geo_resolve(lat, lng)

    return []


def _geo_resolve(lat: float, lng: float) -> list[str]:
    """Find nearest finance/government-layer graph nodes within radius.

    Falls back gracefully if the entity graph is unavailable.
    """
    try:
        from app.graph.registry import get_entities
        entities = get_entities()
    except Exception as exc:
        logger.debug("geo_resolve: entity graph unavailable — %s", exc)
        return []

    candidates: list[tuple[float, str]] = []
    for entity in entities:
        if entity.get("layer") not in FINANCE_LAYERS:
            continue
        e_lat = entity.get("latitude")
        e_lng = entity.get("longitude")
        if e_lat is None or e_lng is None:
            continue
        dist = math.sqrt((lat - e_lat) ** 2 + (lng - e_lng) ** 2)
        if dist <= MAX_GEO_RADIUS_DEG:
            candidates.append((dist, entity["id"]))

    candidates.sort(key=lambda x: x[0])
    return [eid for _, eid in candidates[:MAX_ENTITY_IDS]]
