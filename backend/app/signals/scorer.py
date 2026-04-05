"""signals.scorer — LiveSignal → ScoredSignal.

Formula:
    event_impact = severity_norm  × 0.45
                 + confidence_norm × 0.30
                 + source_weight   × 0.25

    signal_score = event_impact × sector_weight   (clamped [0.0, 1.0])

No state, no I/O, no side effects.
"""

from __future__ import annotations

from app.domain.models.live_signal import LiveSignal, ScoredSignal
from app.domain.sources import resolve_weights

_W_SEVERITY:   float = 0.45
_W_CONFIDENCE: float = 0.30
_W_SOURCE:     float = 0.25
_SCORING_VERSION = "v1"


def score(signal: LiveSignal) -> ScoredSignal:
    """Score a LiveSignal and return a ScoredSignal."""
    source_weight, sector_weight = resolve_weights(signal.source, signal.sector)

    severity_norm   = signal.severity_raw
    confidence_norm = signal.confidence_raw

    event_impact = (
        severity_norm   * _W_SEVERITY
        + confidence_norm * _W_CONFIDENCE
        + source_weight   * _W_SOURCE
    )

    signal_score = min(event_impact * sector_weight, 1.0)
    signal_score = max(signal_score, 0.0)

    return ScoredSignal(
        signal=signal,
        severity_norm=severity_norm,
        confidence_norm=confidence_norm,
        source_weight=source_weight,
        sector_weight=sector_weight,
        signal_score=round(signal_score, 4),
        scoring_version=_SCORING_VERSION,
    )
