"""
Quality Control Layer — backend/app/quality/

Stages 2-7: Validate → Normalize → Deduplicate → Enrich → Cluster → Signal.
Garbage-in/garbage-out control. Raw data NEVER bypasses this layer.
"""

from .validate import validate_event
from .normalize import normalize_event
from .deduplicate import deduplicate_event
from .enrich import enrich_event
from .cluster import cluster_signals
from .signal import generate_signal, score_signal

__all__ = [
    "validate_event",
    "normalize_event",
    "deduplicate_event",
    "enrich_event",
    "cluster_signals",
    "generate_signal",
    "score_signal",
]
