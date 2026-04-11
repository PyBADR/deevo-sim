"""P1 Data Foundation — Decision Logs.

Immutable audit trail of every decision proposed, approved, rejected,
or executed by the system. Links back to the rule that triggered it
and the data state at trigger time.
"""

from __future__ import annotations

from pydantic import Field

from p1_foundation.models.base import P1BaseModel
from p1_foundation.models.enums import DecisionAction, DecisionStatus, Severity


class DecisionLogRecord(P1BaseModel):
    """An immutable decision audit entry."""

    log_id: str = Field(..., description="Unique log entry identifier")
    rule_id: str = Field(..., description="FK to DecisionRuleRecord.rule_id that triggered this")
    rule_name: str = Field(..., description="Rule name at trigger time (denormalized for audit)")
    action: DecisionAction = Field(..., description="Action proposed")
    status: DecisionStatus = Field(..., description="Current lifecycle status")
    severity: Severity = Field(..., description="Severity at trigger time")
    trigger_data_hash: str = Field(..., description="SHA-256 hash of the data state that triggered the rule")
    trigger_summary: str = Field(..., description="Human-readable summary of trigger conditions")
    affected_entities: list[str] = Field(default_factory=list, description="Entity IDs affected")
    affected_sectors: list[str] = Field(default_factory=list, description="Sectors affected")
    affected_countries: list[str] = Field(default_factory=list, description="Countries affected")
    reviewer: str | None = Field(default=None, description="Who reviewed this decision")
    reviewer_notes: str | None = Field(default=None, description="Reviewer comments")
    reviewed_at: str | None = Field(default=None, description="Review timestamp (ISO)")
    executed_at: str | None = Field(default=None, description="Execution timestamp (ISO)")
    dataset_id: str | None = Field(default=None, description="FK to DatasetRegistryEntry.id")
