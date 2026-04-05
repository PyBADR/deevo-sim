"""
Impact Observatory | مرصد الأثر — Simulation State

Accumulator for stage outputs during a unified pipeline run.
Every stage writes its output here; the final result is built from this state.
"""

import time
from dataclasses import dataclass, field
from typing import Any, Optional

from app.domain.models.raw_event import RawEvent, ValidatedEvent, NormalizedEvent, EnrichedEvent
from app.domain.models.signal import Signal, SignalCluster
from app.domain.models.graph_snapshot import GraphSnapshot
from app.domain.models.trust_metadata import TrustMetadata


@dataclass
class StageRecord:
    """Per-stage execution metadata."""
    status: str = "pending"  # pending | completed | skipped | failed
    duration_ms: float = 0.0
    detail: str = ""
    confidence: float = 1.0


@dataclass
class SimulationState:
    """Accumulates all stage outputs during a pipeline run."""

    # Identifiers
    run_id: str = ""
    scenario_id: str = ""
    scenario_label: str = ""
    severity: float = 0.0
    horizon_hours: int = 168

    # Stage outputs
    raw_event: Optional[RawEvent] = None
    validated_event: Optional[ValidatedEvent] = None
    normalized_event: Optional[NormalizedEvent] = None
    enriched_event: Optional[EnrichedEvent] = None
    signal_clusters: list[SignalCluster] = field(default_factory=list)
    signal: Optional[Signal] = None
    graph_snapshot: Optional[GraphSnapshot] = None

    # Existing pipeline outputs (from intelligence/ engines)
    propagation_result: Optional[dict] = None
    financial_impacts: list[dict] = field(default_factory=list)
    banking_stress: Optional[dict] = None
    insurance_stress: Optional[dict] = None
    fintech_stress: Optional[dict] = None
    risk_scores: Optional[dict] = None
    decisions: Optional[dict] = None
    explanation: Optional[dict] = None

    # Trust
    trust: Optional[TrustMetadata] = None

    # Stage log
    stage_log: dict[str, dict] = field(default_factory=dict)
    warnings: list[str] = field(default_factory=list)
    data_sources: list[str] = field(default_factory=list)

    # Timing
    start_time: float = field(default_factory=time.time)

    def record_stage(self, stage_id: str, status: str = "completed",
                     duration_ms: float = 0.0, detail: str = "",
                     confidence: float = 1.0):
        """Record a stage's execution result."""
        self.stage_log[stage_id] = {
            "status": status,
            "duration_ms": round(duration_ms, 1),
            "detail": detail,
        }

    def get_stages_completed(self) -> list[str]:
        """Return list of stage IDs that completed successfully."""
        return [
            sid for sid, info in self.stage_log.items()
            if info.get("status") == "completed"
        ]

    def get_stage_confidences(self) -> list[float]:
        """Collect confidence scores from quality stages."""
        confidences = []
        if self.validated_event:
            confidences.append(self.validated_event.validation_score)
        if self.enriched_event:
            confidences.append(self.enriched_event.enrichment_completeness)
        if self.signal:
            confidences.append(self.signal.confidence)
        return confidences

    def elapsed_ms(self) -> float:
        return round((time.time() - self.start_time) * 1000, 1)
