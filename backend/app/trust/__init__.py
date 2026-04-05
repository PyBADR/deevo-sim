"""
Trust / Governance Layer — backend/app/trust/

Stage 12: Attach audit, provenance, confidence, and warnings to outputs.
Every major output MUST pass through this layer.
"""

from .audit import generate_audit_hash, generate_trace_id
from .confidence import aggregate_confidence
from .warnings import collect_warnings

__all__ = [
    "generate_audit_hash",
    "generate_trace_id",
    "aggregate_confidence",
    "collect_warnings",
]
