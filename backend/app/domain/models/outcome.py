"""domain.models.outcome — Outcome Intelligence domain model.

First-class outcome entity for tracking realized results of decisions and runs.
This is NOT the OperatorDecision.outcome_status field (execution result).
This is a standalone entity that answers: "what actually happened after we acted?"

Lifecycle:
    PENDING_OBSERVATION → OBSERVED → CONFIRMED → CLOSED
    PENDING_OBSERVATION → OBSERVED → DISPUTED  → CLOSED
    PENDING_OBSERVATION → FAILED   → CLOSED
    (OBSERVED → FAILED) also permitted

Linkage requirement:
    At least one of source_decision_id, source_run_id must be non-null.
    source_signal_id and source_seed_id are optional enrichment.

This layer does NOT compute ROI. It stores the raw truth that ROI needs later:
    - What did we expect?
    - What did we observe?
    - Is the observation confirmed or disputed?
    - How long did resolution take?
    - What evidence supports the classification?
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field


def _now_utc() -> datetime:
    return datetime.now(timezone.utc)


def _outcome_id() -> str:
    return f"out-{uuid.uuid4().hex[:12]}"


# ── Enums ──────────────────────────────────────────────────────────────────────

class OutcomeStatus(StrEnum):
    """Full lifecycle of an Outcome entity.

    Separate from OperatorDecision.outcome_status (which reflects execution result).
    This tracks the epistemic state of what actually happened after action.
    """
    PENDING_OBSERVATION = "PENDING_OBSERVATION"  # action taken, no observation yet
    OBSERVED            = "OBSERVED"             # evidence observed, not yet classified
    CONFIRMED           = "CONFIRMED"            # classified and confirmed
    DISPUTED            = "DISPUTED"             # observed but classification contested
    CLOSED              = "CLOSED"               # terminal — lifecycle complete
    FAILED              = "FAILED"               # observation or confirmation failed


class OutcomeClassification(StrEnum):
    """Signal-detection classification of the outcome.

    Answers: was the action correct given what actually happened?
    """
    TRUE_POSITIVE           = "TRUE_POSITIVE"           # action warranted + impact materialized
    FALSE_POSITIVE          = "FALSE_POSITIVE"          # action taken, but impact did not materialize
    TRUE_NEGATIVE           = "TRUE_NEGATIVE"           # no action taken, impact did not materialize
    FALSE_NEGATIVE          = "FALSE_NEGATIVE"          # no action taken, but impact did materialize
    PARTIALLY_REALIZED      = "PARTIALLY_REALIZED"      # action taken, impact partially materialized
    NO_MATERIAL_IMPACT      = "NO_MATERIAL_IMPACT"      # action had no measurable effect
    OPERATIONALLY_SUCCESSFUL = "OPERATIONALLY_SUCCESSFUL"  # action executed correctly, outcome TBD
    OPERATIONALLY_FAILED    = "OPERATIONALLY_FAILED"    # action execution failed operationally


# ── Domain model ──────────────────────────────────────────────────────────────

class Outcome(BaseModel):
    """A first-class outcome entity linked to a decision and/or run.

    Immutable — state transitions produce new objects via model_copy() following
    the frozen Pydantic pattern used throughout this system.

    Fields are explicit. No ad-hoc dicts masquerading as outcome state.
    """
    outcome_id:                 str                          = Field(default_factory=_outcome_id)

    # Source linkage — at least one of decision_id or run_id required (engine-enforced)
    source_decision_id:         str | None                   = None
    source_run_id:              str | None                   = None
    source_signal_id:           str | None                   = None
    source_seed_id:             str | None                   = None

    # Lifecycle
    outcome_status:             OutcomeStatus                = OutcomeStatus.PENDING_OBSERVATION
    outcome_classification:     OutcomeClassification | None = None

    # Timestamps
    observed_at:                datetime | None              = None
    recorded_at:                datetime                     = Field(default_factory=_now_utc)
    updated_at:                 datetime                     = Field(default_factory=_now_utc)
    closed_at:                  datetime | None              = None

    # Actor
    recorded_by:                str

    # Value fields — explicit, optional until captured
    expected_value:             float | None                 = None
    realized_value:             float | None                 = None

    # Quality flags
    error_flag:                 bool                         = False
    time_to_resolution_seconds: int | None                   = None

    # Evidence — structured JSON, not ad-hoc text
    evidence_payload:           dict[str, Any]               = Field(default_factory=dict)

    # Human notes
    notes:                      str | None                   = Field(None, max_length=1000)

    model_config = {"frozen": True}

    # ── Transition methods ────────────────────────────────────────────────────

    def to_observed(
        self,
        evidence_payload: dict[str, Any] | None = None,
        realized_value:   float | None          = None,
        notes:            str | None            = None,
    ) -> "Outcome":
        now = _now_utc()
        return self.model_copy(update={
            "outcome_status":   OutcomeStatus.OBSERVED,
            "observed_at":      now,
            "updated_at":       now,
            "evidence_payload": {**self.evidence_payload, **(evidence_payload or {})},
            "realized_value":   realized_value if realized_value is not None else self.realized_value,
            "notes":            notes or self.notes,
        })

    def to_confirmed(
        self,
        classification:  OutcomeClassification,
        realized_value:  float | None = None,
        notes:           str | None   = None,
    ) -> "Outcome":
        now = _now_utc()
        observed_at = self.observed_at or now
        elapsed_s = int((now - observed_at).total_seconds()) if observed_at else None
        return self.model_copy(update={
            "outcome_status":          OutcomeStatus.CONFIRMED,
            "outcome_classification":  classification,
            "updated_at":              now,
            "realized_value":          realized_value if realized_value is not None else self.realized_value,
            "time_to_resolution_seconds": elapsed_s,
            "notes":                   notes or self.notes,
        })

    def to_disputed(
        self,
        reason: str,
        notes:  str | None = None,
    ) -> "Outcome":
        now = _now_utc()
        return self.model_copy(update={
            "outcome_status": OutcomeStatus.DISPUTED,
            "updated_at":     now,
            "error_flag":     True,
            "notes":          f"[DISPUTED] {reason}" + (f" | {notes}" if notes else ""),
        })

    def to_failed(self, reason: str) -> "Outcome":
        now = _now_utc()
        return self.model_copy(update={
            "outcome_status": OutcomeStatus.FAILED,
            "updated_at":     now,
            "error_flag":     True,
            "notes":          f"[FAILED] {reason}",
        })

    def to_closed(self, notes: str | None = None) -> "Outcome":
        now = _now_utc()
        recorded_at_ts = self.recorded_at
        elapsed_s = int((now - recorded_at_ts).total_seconds())
        return self.model_copy(update={
            "outcome_status":              OutcomeStatus.CLOSED,
            "closed_at":                   now,
            "updated_at":                  now,
            "time_to_resolution_seconds":  elapsed_s,
            "notes":                       notes or self.notes,
        })
