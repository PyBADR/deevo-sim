"""
Impact Observatory | مرصد الأثر
Utility functions — formatting, classification, math helpers.
"""
from __future__ import annotations

import math
import uuid
from datetime import datetime, timezone
from typing import Sequence


# ---------------------------------------------------------------------------
# Financial formatting
# ---------------------------------------------------------------------------

def format_loss_usd(usd: float) -> str:
    """Format a USD value into human-readable string: '$3.2B', '$450M', '$12K'."""
    if usd is None or math.isnan(usd):
        return "$0"
    usd = abs(usd)
    if usd >= 1_000_000_000:
        return f"${usd / 1_000_000_000:.1f}B"
    if usd >= 1_000_000:
        return f"${usd / 1_000_000:.1f}M"
    if usd >= 1_000:
        return f"${usd / 1_000:.1f}K"
    return f"${usd:.0f}"


# ---------------------------------------------------------------------------
# Risk classification
# ---------------------------------------------------------------------------

RISK_THRESHOLDS: dict[str, tuple[float, float]] = {
    "NOMINAL":  (0.00, 0.20),
    "LOW":      (0.20, 0.35),
    "GUARDED":  (0.35, 0.50),
    "ELEVATED": (0.50, 0.65),
    "HIGH":     (0.65, 0.80),
    "SEVERE":   (0.80, 1.01),
}


def classify_stress(score: float) -> str:
    """Map a 0-1 score to a risk classification label."""
    score = clamp(score, 0.0, 1.0)
    for label, (lo, hi) in RISK_THRESHOLDS.items():
        if lo <= score < hi:
            return label
    return "SEVERE"


classify_risk = classify_stress  # alias


# ---------------------------------------------------------------------------
# Math helpers
# ---------------------------------------------------------------------------

def clamp(value: float, lo: float, hi: float) -> float:
    """Clamp *value* to the closed interval [lo, hi]."""
    return max(lo, min(hi, float(value)))


def weighted_average(values: Sequence[float], weights: Sequence[float]) -> float:
    """Compute a weighted average. Weights need not be normalised."""
    if not values:
        return 0.0
    total_weight = sum(weights)
    if total_weight == 0:
        return sum(values) / len(values)
    return sum(v * w for v, w in zip(values, weights)) / total_weight


def safe_divide(numerator: float, denominator: float, fallback: float = 0.0) -> float:
    """Division that returns *fallback* when denominator is zero."""
    if denominator == 0:
        return fallback
    return numerator / denominator


def normalize(value: float, lo: float, hi: float) -> float:
    """Min-max normalise *value* into [0, 1] given the expected range [lo, hi]."""
    if hi == lo:
        return 0.0
    return clamp((value - lo) / (hi - lo), 0.0, 1.0)


# ---------------------------------------------------------------------------
# ID / timestamp helpers
# ---------------------------------------------------------------------------

def generate_run_id() -> str:
    """Return a UUID4 hex string (no dashes), used as run_id."""
    return uuid.uuid4().hex


def now_utc() -> str:
    """Return the current UTC time as an ISO 8601 string with timezone."""
    return datetime.now(timezone.utc).isoformat()


# ---------------------------------------------------------------------------
# Severity label helpers
# ---------------------------------------------------------------------------

def severity_label(severity: float) -> str:
    """Human-readable severity band label."""
    if severity < 0.20:
        return "Minimal"
    if severity < 0.40:
        return "Low"
    if severity < 0.60:
        return "Moderate"
    if severity < 0.75:
        return "High"
    if severity < 0.90:
        return "Very High"
    return "Catastrophic"


def severity_label_ar(severity: float) -> str:
    """Arabic severity band label."""
    if severity < 0.20:
        return "طفيف"
    if severity < 0.40:
        return "منخفض"
    if severity < 0.60:
        return "متوسط"
    if severity < 0.75:
        return "مرتفع"
    if severity < 0.90:
        return "مرتفع جداً"
    return "كارثي"


def risk_label_ar(level: str) -> str:
    """Arabic risk level label."""
    mapping = {
        "NOMINAL":  "طبيعي",
        "LOW":      "منخفض",
        "GUARDED":  "محدود",
        "ELEVATED": "مرتفع",
        "HIGH":     "عالٍ",
        "SEVERE":   "شديد",
    }
    return mapping.get(level, "غير محدد")
