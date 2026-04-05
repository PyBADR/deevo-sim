"""domain.models.decision_value — ROI / Decision Value domain model.

A DecisionValue is a first-class entity that answers:
  "Given the confirmed outcome of this decision, what was the measurable value?"

It sits one level above the Outcome layer:
    signal → seed → run → decision → outcome → value

No ROI is computed without a linked Outcome.
No numbers are fabricated — every field in net_value is stored and traceable.

Formula:
    net_value = avoided_loss - total_cost
    total_cost = operational_cost + decision_cost + latency_cost

    where:
      avoided_loss  — explicit input OR outcome.expected_value (if available)
      operational_cost — cost of running the underlying pipeline
      decision_cost    — cost of the decision action itself
      latency_cost     — cost due to response latency (slower response = more exposure)

Computation is deterministic and recomputable from calculation_trace inputs alone.

This module does NOT touch the Outcome layer.  It reads from it read-only.
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field


def _now_utc() -> datetime:
    return datetime.now(timezone.utc)


def _value_id() -> str:
    return f"val-{uuid.uuid4().hex[:12]}"


# ── Enums ──────────────────────────────────────────────────────────────────────

class ValueClassification(StrEnum):
    """Classification of a computed decision value.

    Derived deterministically from net_value using fixed thresholds.
    Thresholds are applied per-computation and stored in calculation_trace.
    """
    HIGH_VALUE     = "HIGH_VALUE"      # net_value ≥  1_000_000
    POSITIVE_VALUE = "POSITIVE_VALUE"  # 0 < net_value < 1_000_000
    NEUTRAL        = "NEUTRAL"         # net_value == 0 (within ±1 tolerance)
    NEGATIVE_VALUE = "NEGATIVE_VALUE"  # -1_000_000 < net_value < 0
    LOSS_INDUCING  = "LOSS_INDUCING"   # net_value ≤ -1_000_000


# ── Domain model ──────────────────────────────────────────────────────────────

class DecisionValue(BaseModel):
    """A deterministic, auditable ROI entity derived from a confirmed Outcome.

    Immutable — follows the frozen Pydantic pattern used throughout this system.
    State changes (e.g., recomputation) produce new objects; the old record is
    superseded (not updated in-place) by writing a new row with the same
    source_outcome_id and emitting a value.recomputed audit event.

    Linkage:
      source_outcome_id is REQUIRED.  source_decision_id and source_run_id
      are copied from the source Outcome for fast denormalized lookup — they
      are not independently enforced here because the engine validates them.

    Traceability:
      calculation_trace stores every input, intermediate step, and outcome
      context at the moment of computation.  Re-running the formula against
      the trace inputs should reproduce net_value exactly.
    """
    value_id:               str             = Field(default_factory=_value_id)

    # Linkage — source_outcome_id is the primary foreign key for this layer
    source_outcome_id:      str             # REQUIRED — engine-enforced
    source_decision_id:     str | None      = None  # denormalized from Outcome
    source_run_id:          str | None      = None  # denormalized from Outcome

    # Who computed this and when
    computed_at:            datetime        = Field(default_factory=_now_utc)
    computed_by:            str             # system identity or actor ID

    # Outcome context — copied for reference without touching the Outcome entity
    expected_value:         float | None    = None
    realized_value:         float | None    = None

    # Cost inputs (all default to 0.0 if not applicable)
    avoided_loss:           float           = 0.0  # primary value input
    operational_cost:       float           = 0.0
    decision_cost:          float           = 0.0
    latency_cost:           float           = 0.0

    # Computed outputs
    total_cost:             float           = 0.0  # sum of all cost inputs
    net_value:              float           = 0.0  # avoided_loss - total_cost
    value_confidence_score: float           = 0.0  # 0.0–1.0
    value_classification:   ValueClassification

    # Traceability — must allow full recomputation from this dict alone
    calculation_trace:      dict[str, Any]  = Field(default_factory=dict)

    # Human notes
    notes:                  str | None      = Field(None, max_length=1000)

    model_config = {"frozen": True}
