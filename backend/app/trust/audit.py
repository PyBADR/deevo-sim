"""
Impact Observatory | مرصد الأثر — Audit Layer

SHA-256 hash generation, trace ID creation, provenance tracking.
"""

import hashlib
import json
import uuid
from datetime import datetime, timezone

from app.domain.models.trust_metadata import TrustMetadata


def generate_trace_id() -> str:
    """Generate a unique trace identifier for a pipeline run."""
    return f"io-{uuid.uuid4().hex}"


def generate_audit_hash(data: dict) -> str:
    """Generate SHA-256 hash of the output data for audit trail.

    The hash covers the entire output payload, ensuring tamper detection.
    """
    serialized = json.dumps(data, sort_keys=True, default=str)
    return hashlib.sha256(serialized.encode("utf-8")).hexdigest()


def build_trust_metadata(
    stages_completed: list[str],
    stage_log: dict,
    data_sources: list[str],
    confidence_score: float,
    warnings: list[str],
    explanations: list[str] | None = None,
    provenance_chain: list[str] | None = None,
    output_payload: dict | None = None,
) -> TrustMetadata:
    """Build a complete TrustMetadata envelope.

    Parameters
    ----------
    stages_completed : list[str]
        List of stage IDs that completed successfully.
    stage_log : dict
        Per-stage execution metadata: {stage_id: {status, duration_ms, detail}}.
    data_sources : list[str]
        Sources that contributed to this output.
    confidence_score : float
        Composite confidence score (0.0-1.0).
    warnings : list[str]
        Accumulated warnings from all stages.
    explanations : list[str] | None
        Human-readable explanations.
    output_payload : dict | None
        Full output dict for audit hash computation.
    """
    trace_id = generate_trace_id()
    audit_hash = generate_audit_hash(output_payload or {})

    return TrustMetadata(
        trace_id=trace_id,
        audit_id=f"audit-{uuid.uuid4().hex[:12]}",
        audit_hash=audit_hash,
        model_version="4.0.0",
        pipeline_version="2.0.0",
        data_sources=data_sources,
        confidence_score=round(max(0.0, min(1.0, confidence_score)), 4),
        warnings=warnings,
        explanations=explanations or [],
        stages_completed=stages_completed,
        stage_log=stage_log,
        provenance_chain=provenance_chain or [],
    )
