"""P1 Data Foundation — Decision Rules.

Deterministic rules that map signal conditions to proposed actions.
Rules are evaluated by the decision engine against incoming data.
"""

from __future__ import annotations

from pydantic import Field

from p1_foundation.models.base import ConfidenceMixin, P1BaseModel
from p1_foundation.models.enums import DecisionAction, Severity


class RuleCondition(P1BaseModel):
    """A single condition within a decision rule."""

    field: str = Field(..., description="Data field to evaluate (e.g., 'oil_price_usd')")
    operator: str = Field(..., description="Comparison operator: gt, gte, lt, lte, eq, neq, in, not_in, between")
    value: float | str | list = Field(..., description="Threshold value or list for in/between")
    dataset: str = Field(..., description="Source dataset for this field")


class DecisionRuleRecord(P1BaseModel, ConfidenceMixin):
    """A decision rule that maps conditions to actions."""

    rule_id: str = Field(..., description="Unique rule identifier (e.g., 'RULE-OIL-001')")
    rule_name: str = Field(..., description="Human-readable rule name")
    description: str = Field(..., description="What this rule detects and why")
    conditions: list[RuleCondition] = Field(..., min_length=1, description="Conditions (all must match)")
    logic: str = Field(default="AND", description="Condition logic: AND or OR")
    action: DecisionAction = Field(..., description="Proposed action when triggered")
    severity: Severity = Field(..., description="Severity of the situation this rule detects")
    affected_sectors: list[str] = Field(default_factory=list, description="Sectors impacted")
    affected_countries: list[str] = Field(default_factory=list, description="Countries impacted")
    cooldown_hours: int = Field(default=24, ge=0, description="Minimum hours between triggers")
    expiry_date: str | None = Field(default=None, description="Rule expiry date (ISO)")
    is_active: bool = Field(default=True, description="Whether rule is enabled")
    priority: int = Field(default=5, ge=1, le=10, description="Priority 1 (highest) to 10 (lowest)")
    dataset_id: str | None = Field(default=None, description="FK to DatasetRegistryEntry.id")
