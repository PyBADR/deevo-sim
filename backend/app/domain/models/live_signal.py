"""domain.models.live_signal — Core domain types for the Live Signal Layer.

MVP scope: banking + fintech signals only.

Flow:
    raw source data
      → LiveSignal          (inbound, unscored)
      → ScoredSignal        (after normalizer + scorer)
      → ScenarioSeed        (HITL-gated, proposed pipeline trigger)
      → run_unified_pipeline (only after human APPROVAL)

ScenarioSeed is the central object.  Nothing enters the pipeline without
an APPROVED seed.  HITL is the only gate.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field


# ── Enums ─────────────────────────────────────────────────────────────────────

class LiveSignalSource(StrEnum):
    """Where the raw signal originated."""
    ACLED      = "acled"      # conflict / geopolitical
    AISSTREAM  = "aisstream"  # maritime vessel positions
    OPENSKY    = "opensky"    # aviation positions
    CRUCIX     = "crucix"     # proprietary intelligence feed
    MANUAL     = "manual"     # operator-entered signal


class SignalSector(StrEnum):
    """MVP: banking and fintech only.

    Extensible — add sectors here when scope expands.
    Normalizer enforces this enum; unknown sectors are rejected.
    """
    BANKING = "banking"
    FINTECH = "fintech"


class SeedStatus(StrEnum):
    """HITL lifecycle of a ScenarioSeed."""
    PENDING_REVIEW = "PENDING_REVIEW"
    APPROVED       = "APPROVED"
    REJECTED       = "REJECTED"
    EXPIRED        = "EXPIRED"  # never reviewed within TTL


# ── Core domain models ────────────────────────────────────────────────────────

def _now_utc() -> datetime:
    return datetime.now(timezone.utc)


def _signal_id() -> str:
    return f"sig-{uuid.uuid4().hex[:12]}"


def _seed_id() -> str:
    return f"seed-{uuid.uuid4().hex[:12]}"


class LiveSignal(BaseModel):
    """Raw inbound signal from an external or manual source.

    Created by the ingestor.  Not yet scored or validated for pipeline use.
    Immutable after creation — downstream steps produce new objects.
    """
    signal_id:      str           = Field(default_factory=_signal_id)
    source:         LiveSignalSource
    sector:         SignalSector
    event_type:     str           = Field(..., max_length=128)
    severity_raw:   float         = Field(..., ge=0.0, le=1.0)
    confidence_raw: float         = Field(0.7, ge=0.0, le=1.0)
    entity_ids:     list[str]     = Field(default_factory=list)
    lat:            float | None  = None
    lng:            float | None  = None
    description:    str           = Field("", max_length=500)
    received_at:    datetime      = Field(default_factory=_now_utc)
    payload:        dict[str, Any] = Field(default_factory=dict)

    model_config = {"frozen": True}


class ScoredSignal(BaseModel):
    """A LiveSignal after normalization and scoring.

    Produced by signals/scorer.py.  Contains the original signal plus
    derived scores used by seed_generator to propose a ScenarioSeed.

    signal_score formula:
        event_impact  = severity_norm × 0.45
                      + confidence_norm × 0.30
                      + source_weight   × 0.25
        signal_score  = event_impact × sector_weight
    """
    signal:          LiveSignal
    severity_norm:   float    = Field(..., ge=0.0, le=1.0)
    confidence_norm: float    = Field(..., ge=0.0, le=1.0)
    source_weight:   float    = Field(..., ge=0.0, le=1.0)
    sector_weight:   float    = Field(..., ge=0.0)
    signal_score:    float    = Field(..., ge=0.0, le=1.0)
    scoring_version: str      = "v1"
    scored_at:       datetime = Field(default_factory=_now_utc)

    model_config = {"frozen": True}


class ScenarioSeed(BaseModel):
    """HITL-gated proposal to trigger a pipeline run.

    Created by signals/seed_generator.py from a ScoredSignal.
    Transitions:  PENDING_REVIEW → APPROVED → pipeline run
                  PENDING_REVIEW → REJECTED → discarded

    Only APPROVED seeds produce pipeline inputs for run_unified_pipeline().
    """
    seed_id:                str        = Field(default_factory=_seed_id)
    signal_id:              str
    sector:                 SignalSector
    suggested_template_id:  str
    suggested_severity:     float      = Field(..., ge=0.0, le=1.0)
    suggested_horizon_hours: int       = Field(72, ge=1, le=8760)
    rationale:              str        = Field(..., max_length=300)
    status:                 SeedStatus = SeedStatus.PENDING_REVIEW
    created_at:             datetime   = Field(default_factory=_now_utc)
    reviewed_by:            str | None = None
    reviewed_at:            datetime | None = None
    review_reason:          str | None = None

    def approve(self, reviewed_by: str, reason: str | None = None) -> "ScenarioSeed":
        """Return a new APPROVED seed (immutability preserved via copy)."""
        return self.model_copy(update={
            "status":        SeedStatus.APPROVED,
            "reviewed_by":   reviewed_by,
            "reviewed_at":   _now_utc(),
            "review_reason": reason,
        })

    def reject(self, reviewed_by: str, reason: str | None = None) -> "ScenarioSeed":
        """Return a new REJECTED seed."""
        return self.model_copy(update={
            "status":        SeedStatus.REJECTED,
            "reviewed_by":   reviewed_by,
            "reviewed_at":   _now_utc(),
            "review_reason": reason,
        })

    def to_pipeline_kwargs(self) -> dict:
        """Return kwargs for run_unified_pipeline() — only valid on APPROVED seeds."""
        if self.status != SeedStatus.APPROVED:
            raise ValueError(
                f"Seed {self.seed_id} is {self.status} — only APPROVED seeds enter the pipeline"
            )
        return {
            "template_id":   self.suggested_template_id,
            "severity":      self.suggested_severity,
            "horizon_hours": self.suggested_horizon_hours,
            "label":         f"[Signal] {self.sector.value} · {self.seed_id}",
        }
