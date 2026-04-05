"""domain.models.operator_decision — Operator Layer decision domain model.

NOT to be confused with domain.models.decision (DecisionAction/DecisionPlan),
which is the pipeline engine's output model for recommended actions from runs.

This model represents deliberate, human-driven decisions made by operators in
response to system state (signals, seeds, runs) — the Operator Layer.

Flow:
    signal/seed/run state
      → OperatorDecision (CREATED)
      → OperatorDecision (IN_REVIEW → EXECUTED | FAILED)
      → OperatorDecision (CLOSED)

Linkage requirement: at least one of source_signal_id, source_seed_id,
source_run_id must be non-null (enforced by the engine layer).
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field


def _now_utc() -> datetime:
    return datetime.now(timezone.utc)


def _decision_id() -> str:
    return f"dec-{uuid.uuid4().hex[:12]}"


class DecisionType(StrEnum):
    """Operator action classification."""
    APPROVE_ACTION      = "APPROVE_ACTION"      # approve a recommended action from a run decision plan
    REJECT_ACTION       = "REJECT_ACTION"       # reject a recommended action
    ESCALATE            = "ESCALATE"            # escalate a situation to higher authority
    IGNORE              = "IGNORE"              # consciously ignore a signal/seed/run
    TRIGGER_RUN         = "TRIGGER_RUN"         # manually trigger a new pipeline run
    OVERRIDE_RUN_RESULT = "OVERRIDE_RUN_RESULT" # override automated assessment with manual judgment


class DecisionStatus(StrEnum):
    """Operator decision lifecycle state."""
    CREATED   = "CREATED"   # decision record exists, not yet reviewed
    IN_REVIEW = "IN_REVIEW" # operator is actively reviewing
    EXECUTED  = "EXECUTED"  # decision has been acted upon
    FAILED    = "FAILED"    # execution raised an error
    CLOSED    = "CLOSED"    # terminal — decision lifecycle complete


class OutcomeStatus(StrEnum):
    """Result of executing the decision."""
    PENDING = "PENDING"  # execution in progress or not yet started
    SUCCESS = "SUCCESS"  # action completed successfully
    FAILURE = "FAILURE"  # action failed
    PARTIAL = "PARTIAL"  # action partially completed


class OperatorDecision(BaseModel):
    """A deliberate, human-driven decision in the Operator Layer.

    Immutable after creation — downstream state transitions produce new objects
    via model_copy() following the same pattern as ScenarioSeed.
    """
    decision_id:       str             = Field(default_factory=_decision_id)
    # Source linkage (at least one required, enforced by engine)
    source_signal_id:  str | None      = None
    source_seed_id:    str | None      = None
    source_run_id:     str | None      = None
    # Classification
    decision_type:     DecisionType
    decision_status:   DecisionStatus  = DecisionStatus.CREATED
    # Content
    decision_payload:  dict[str, Any]  = Field(default_factory=dict)
    rationale:         str | None      = Field(None, max_length=500)
    confidence_score:  float | None    = Field(None, ge=0.0, le=1.0)
    # Actor
    created_by:        str
    # Outcome
    outcome_status:    OutcomeStatus   = OutcomeStatus.PENDING
    outcome_payload:   dict[str, Any]  = Field(default_factory=dict)
    # Timestamps
    created_at:        datetime        = Field(default_factory=_now_utc)
    updated_at:        datetime        = Field(default_factory=_now_utc)
    closed_at:         datetime | None = None

    model_config = {"frozen": True}

    def to_review(self) -> "OperatorDecision":
        return self.model_copy(update={
            "decision_status": DecisionStatus.IN_REVIEW,
            "updated_at": _now_utc(),
        })

    def to_executed(self, outcome_payload: dict[str, Any]) -> "OperatorDecision":
        return self.model_copy(update={
            "decision_status": DecisionStatus.EXECUTED,
            "outcome_status":  OutcomeStatus.SUCCESS,
            "outcome_payload": outcome_payload,
            "updated_at":      _now_utc(),
        })

    def to_failed(self, error: str) -> "OperatorDecision":
        return self.model_copy(update={
            "decision_status": DecisionStatus.FAILED,
            "outcome_status":  OutcomeStatus.FAILURE,
            "outcome_payload": {"error": error},
            "updated_at":      _now_utc(),
        })

    def to_closed(self, outcome_status: OutcomeStatus = OutcomeStatus.SUCCESS) -> "OperatorDecision":
        now = _now_utc()
        return self.model_copy(update={
            "decision_status": DecisionStatus.CLOSED,
            "outcome_status":  outcome_status,
            "closed_at":       now,
            "updated_at":      now,
        })
