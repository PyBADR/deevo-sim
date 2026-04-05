"""
Impact Observatory | مرصد الأثر — Trust Metadata Model

Data contract for Stage 12: Trust / Audit / Governance layer.
Every major output MUST include this metadata.
"""

from pydantic import Field, ConfigDict
from .base import VersionedModel


class TrustMetadata(VersionedModel):
    """Trust envelope attached to every simulation output."""
    model_config = ConfigDict(protected_namespaces=())
    trace_id: str = Field(default="", description="Unique trace identifier")
    audit_id: str = Field(default="", description="Audit record identifier")
    audit_hash: str = Field(default="", description="SHA-256 hash of full output")
    model_version: str = Field(default="4.0.0")
    pipeline_version: str = Field(default="2.0.0", description="Unified pipeline version")
    data_sources: list[str] = Field(default_factory=list, description="Sources that contributed to this output")
    confidence_score: float = Field(default=0.0, ge=0.0, le=1.0, description="Composite confidence")
    warnings: list[str] = Field(default_factory=list)
    explanations: list[str] = Field(default_factory=list)
    stages_completed: list[str] = Field(default_factory=list)
    stage_log: dict = Field(default_factory=dict, description="{stage_id: {status, duration_ms, detail}}")
    provenance_chain: list[str] = Field(default_factory=list, description="Full provenance trail")
