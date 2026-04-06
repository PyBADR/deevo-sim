"""
Impact Observatory | مرصد الأثر — Source Trust Scorer

Deterministic, explainable trust scoring for data sources.
No ML, no probabilistic sampling. Pure formula.

Formula
-------
    source_score =
        0.30 × reliability   +
        0.20 × freshness     +
        0.20 × coverage      +
        0.15 × consistency   +
        0.15 × latency

All dimensions are normalized to [0.0, 1.0] before applying weights.
The weighted sum is the source_score ∈ [0.0, 1.0].
confidence = source_score (identity mapping; explainability is preserved).

Dimensions
----------
reliability   (weight 0.30)
    Historical validation pass rate for this source.
    Computed from: (passed_records / total_records) over the last 30 days.
    Default if no history: 0.70 (conservative — known source without track record).
    Unknown source default: 0.40 (low trust until proven).

freshness     (weight 0.20)
    Age of the event relative to now.
    Score bands:
        < 1 hour    → 1.00
        1–24 hours  → 0.85
        1–7 days    → 0.65
        7–30 days   → 0.40
        > 30 days   → 0.20  (also flagged as RULE_8_WARN in validator)
    Default if not computable: 0.80.

coverage      (weight 0.20)
    Payload completeness: ratio of non-None fields in normalized_payload.
    Computed from: len(non_null_values) / len(normalized_payload).
    Default if normalized_payload empty: 0.00.

consistency   (weight 0.15)
    Variance stability across recent events from this source.
    Computed from: 1 - std_dev(last_N_scores) where N=10.
    Default if no history: 0.70.

latency       (weight 0.15)
    Delivery lag: how quickly the event reached the trust layer
    after its source timestamp.
    Score bands:
        < 1 hour    → 1.00
        1–6 hours   → 0.85
        6–24 hours  → 0.70
        1–7 days    → 0.50
        > 7 days    → 0.25
    Default if not computable: 0.80.

Trust tier mapping (for logging / auditability)
-----------------------------------------------
    0.85–1.00  → TIER_1_HIGH
    0.65–0.85  → TIER_2_MEDIUM
    0.45–0.65  → TIER_3_LOW
    0.00–0.45  → TIER_4_UNTRUSTED
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta
from typing import Optional


# ── Dimension weights (must sum to 1.0) ──────────────────────────────────────
_WEIGHTS: dict[str, float] = {
    "reliability":  0.30,
    "freshness":    0.20,
    "coverage":     0.20,
    "consistency":  0.15,
    "latency":      0.15,
}
assert abs(sum(_WEIGHTS.values()) - 1.0) < 1e-9, "Dimension weights must sum to 1.0"


@dataclass
class SourceMetrics:
    """
    Input metrics for the trust scoring formula.
    All dimensions must be in [0.0, 1.0].

    Prefer passing computed values from the adapter's source_metrics() method.
    If a dimension is unavailable, use the explicit defaults documented below.
    """
    reliability:  float = 0.70   # Default: known source, no history
    freshness:    float = 0.80   # Default: reasonably recent
    coverage:     float = 0.75   # Default: moderate completeness
    consistency:  float = 0.70   # Default: moderate consistency
    latency:      float = 0.80   # Default: acceptable delivery lag

    # Contextual inputs for computed dimensions
    event_timestamp: Optional[datetime] = None    # For freshness computation
    received_at:     Optional[datetime] = None    # For latency computation
    normalized_payload: Optional[dict] = None     # For coverage computation

    def __post_init__(self) -> None:
        for dim, val in {
            "reliability":  self.reliability,
            "freshness":    self.freshness,
            "coverage":     self.coverage,
            "consistency":  self.consistency,
            "latency":      self.latency,
        }.items():
            if not (0.0 <= val <= 1.0):
                raise ValueError(
                    f"SourceMetrics.{dim}={val} is out of bounds [0.0, 1.0]"
                )


@dataclass
class ScoringResult:
    """
    Output of compute_source_score().
    Fully explainable — every dimension contribution is recorded.
    """
    source_score:  float
    confidence:    float
    dimensions:    dict[str, float]     # Raw dimension values
    contributions: dict[str, float]     # Weighted contributions per dimension
    trust_tier:    str                  # TIER_1_HIGH .. TIER_4_UNTRUSTED
    formula:       str                  # Human-readable computation trace


def _compute_freshness(event_timestamp: Optional[datetime]) -> float:
    """Score freshness from event age. Returns default 0.80 if timestamp absent."""
    if event_timestamp is None:
        return 0.80
    now = datetime.now(timezone.utc)
    ts = event_timestamp
    if ts.tzinfo is None:
        ts = ts.replace(tzinfo=timezone.utc)
    age = now - ts
    if   age < timedelta(hours=1):   return 1.00
    elif age < timedelta(hours=24):  return 0.85
    elif age < timedelta(days=7):    return 0.65
    elif age < timedelta(days=30):   return 0.40
    else:                            return 0.20


def _compute_coverage(normalized_payload: Optional[dict]) -> float:
    """Score payload completeness. Returns 0.0 if payload absent."""
    if not normalized_payload:
        return 0.00
    total = len(normalized_payload)
    if total == 0:
        return 0.00
    non_null = sum(1 for v in normalized_payload.values() if v is not None)
    return round(non_null / total, 4)


def _compute_latency(
    event_timestamp: Optional[datetime],
    received_at:     Optional[datetime],
) -> float:
    """Score delivery lag (source timestamp → received_at). Default 0.80."""
    if event_timestamp is None or received_at is None:
        return 0.80
    ts = event_timestamp
    ra = received_at
    if ts.tzinfo is None:
        ts = ts.replace(tzinfo=timezone.utc)
    if ra.tzinfo is None:
        ra = ra.replace(tzinfo=timezone.utc)
    lag = ra - ts
    if   lag < timedelta(hours=1):  return 1.00
    elif lag < timedelta(hours=6):  return 0.85
    elif lag < timedelta(hours=24): return 0.70
    elif lag < timedelta(days=7):   return 0.50
    else:                           return 0.25


def _trust_tier(score: float) -> str:
    if   score >= 0.85: return "TIER_1_HIGH"
    elif score >= 0.65: return "TIER_2_MEDIUM"
    elif score >= 0.45: return "TIER_3_LOW"
    else:               return "TIER_4_UNTRUSTED"


def compute_source_score(metrics: SourceMetrics) -> ScoringResult:
    """
    Compute deterministic source trust score.

    Resolves computed dimensions (freshness, coverage, latency) from
    contextual fields in metrics if they are available, then applies
    the 5-dimension weighted formula.

    Parameters
    ----------
    metrics : SourceMetrics
        Source quality inputs. Adapter provides via source_metrics()
        merged with contract fields for computed dimensions.

    Returns
    -------
    ScoringResult
        Fully explainable scoring output with per-dimension contributions.
    """
    # ── Resolve computed dimensions (override static metrics if context available)
    freshness = (
        _compute_freshness(metrics.event_timestamp)
        if metrics.event_timestamp is not None
        else metrics.freshness
    )
    coverage = (
        _compute_coverage(metrics.normalized_payload)
        if metrics.normalized_payload is not None
        else metrics.coverage
    )
    latency = (
        _compute_latency(metrics.event_timestamp, metrics.received_at)
        if (metrics.event_timestamp is not None and metrics.received_at is not None)
        else metrics.latency
    )

    # ── Clamp all resolved dimensions to [0.0, 1.0] ──────────────────────────
    dims: dict[str, float] = {
        "reliability":  max(0.0, min(1.0, metrics.reliability)),
        "freshness":    max(0.0, min(1.0, freshness)),
        "coverage":     max(0.0, min(1.0, coverage)),
        "consistency":  max(0.0, min(1.0, metrics.consistency)),
        "latency":      max(0.0, min(1.0, latency)),
    }

    # ── Apply weighted formula ────────────────────────────────────────────────
    contributions: dict[str, float] = {
        dim: round(_WEIGHTS[dim] * val, 6)
        for dim, val in dims.items()
    }
    source_score = round(sum(contributions.values()), 6)
    # Clamp to [0.0, 1.0] to absorb any floating-point accumulation
    source_score = max(0.0, min(1.0, source_score))

    # ── Human-readable formula trace ─────────────────────────────────────────
    formula = (
        f"source_score = "
        f"0.30×{dims['reliability']:.3f}(reliability) + "
        f"0.20×{dims['freshness']:.3f}(freshness) + "
        f"0.20×{dims['coverage']:.3f}(coverage) + "
        f"0.15×{dims['consistency']:.3f}(consistency) + "
        f"0.15×{dims['latency']:.3f}(latency) "
        f"= {source_score:.4f}"
    )

    return ScoringResult(
        source_score=source_score,
        confidence=source_score,      # confidence ≡ source_score for explainability
        dimensions=dims,
        contributions=contributions,
        trust_tier=_trust_tier(source_score),
        formula=formula,
    )
