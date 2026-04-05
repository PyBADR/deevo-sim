"""domain.sources — Canonical source trust weight registry for the Live Signal Layer.

Single source of truth for how much to trust each signal origin.
Used by signals/scorer.py.

Trust weight semantics:
    0.90 — proprietary / verified intelligence feed
    0.85 — UN-affiliated conflict database (ACLED)
    0.80 — real-time AIS vessel tracking
    0.75 — civil aviation transponder data (OpenSky)
    0.70 — operator-entered manual signal
    0.40 — unknown / unconfigured source (heavy penalty)

Sector sensitivity (MVP: banking + fintech only):
    banking → 1.15  higher regulatory exposure, faster contagion
    fintech → 1.05  payment corridor disruption, slightly lower systemic risk

Scoring formula (used by scorer.py):
    event_impact = severity_norm × 0.45
                 + confidence_norm × 0.30
                 + source_weight   × 0.25
    signal_score = event_impact × sector_weight   (clamped [0, 1])
"""

from __future__ import annotations

from app.domain.models.live_signal import LiveSignalSource, SignalSector

# ── Source trust weights ──────────────────────────────────────────────────────

SOURCE_TRUST: dict[LiveSignalSource, float] = {
    LiveSignalSource.CRUCIX:    0.90,
    LiveSignalSource.ACLED:     0.85,
    LiveSignalSource.AISSTREAM: 0.80,
    LiveSignalSource.OPENSKY:   0.75,
    LiveSignalSource.MANUAL:    0.70,
}

_FALLBACK_TRUST: float = 0.40  # unknown / not in registry

# ── Sector sensitivity (MVP: banking + fintech) ───────────────────────────────

SECTOR_SENSITIVITY: dict[SignalSector, float] = {
    SignalSector.BANKING: 1.15,
    SignalSector.FINTECH: 1.05,
}

_FALLBACK_SENSITIVITY: float = 1.00  # neutral — for future sectors


# ── Public accessors ──────────────────────────────────────────────────────────

def get_source_weight(source: LiveSignalSource) -> float:
    """Return the trust weight for a LiveSignalSource."""
    return SOURCE_TRUST.get(source, _FALLBACK_TRUST)


def get_sector_weight(sector: SignalSector) -> float:
    """Return the sector sensitivity multiplier for a SignalSector."""
    return SECTOR_SENSITIVITY.get(sector, _FALLBACK_SENSITIVITY)


def resolve_weights(
    source: LiveSignalSource,
    sector: SignalSector,
) -> tuple[float, float]:
    """Convenience: return (source_weight, sector_weight) in one call."""
    return get_source_weight(source), get_sector_weight(sector)
