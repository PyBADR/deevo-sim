"""Rule Specification schema — the declarative format for decision rules.

A RuleSpec is a human-readable, version-controlled definition of a decision
rule. It declares what data to watch, what conditions trigger the rule,
what action to take, and who must approve it.

Every field is deterministic and auditable. No ML, no fuzzy logic.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator

# Valid operators for condition evaluation.
VALID_OPERATORS = frozenset({
    "gt", "gte", "lt", "lte", "eq", "neq",
    "in", "not_in",
    "between",
    "change_gt", "change_lt",        # absolute change
    "change_pct_gt", "change_pct_lt",  # percentage change
})

# Valid datasets that conditions can reference.
VALID_DATASETS = frozenset({
    "canonical_observations",
    "macro_indicators",
    "interest_rate_signals",
    "oil_energy_signals",
    "fx_signals",
    "cbk_indicators",
    "banking_profiles",
    "insurance_profiles",
    "logistics_nodes",
    "event_signals",
})

# Valid actions — matches DecisionAction enum values.
VALID_ACTIONS = frozenset({
    "ALERT", "ESCALATE", "HEDGE", "REBALANCE",
    "MONITOR", "PAUSE", "DIVEST", "INCREASE_RESERVES",
    "ACTIVATE_CONTINGENCY", "NO_ACTION",
})

# Valid escalation levels — matches RiskLevel enum values.
VALID_ESCALATION_LEVELS = frozenset({
    "NOMINAL", "LOW", "GUARDED", "ELEVATED", "HIGH", "SEVERE", "CRITICAL",
})

# Valid GCC country codes.
VALID_COUNTRIES = frozenset({"SA", "AE", "KW", "QA", "BH", "OM"})


class ConditionSpec(BaseModel):
    """A single condition in a rule specification.

    Conditions are deterministic predicates evaluated against data fields.
    The field uses dot notation: {dataset}.{column} or {indicator_code}.
    """

    field: str = Field(
        ...,
        description=(
            "Data field to evaluate. Use dot notation for dataset fields "
            "(e.g., 'oil_energy_signals.value', 'banking_profiles.npl_ratio_pct') "
            "or indicator codes for canonical observations (e.g., 'BRENT_SPOT')."
        ),
    )
    operator: str = Field(
        ...,
        description="Comparison operator: gt, gte, lt, lte, eq, neq, in, not_in, between, change_gt, change_lt, change_pct_gt, change_pct_lt.",
    )
    threshold: Any = Field(
        ...,
        description="Threshold value. Scalar for gt/lt/eq, list for in/not_in, [min, max] for between.",
    )
    unit: Optional[str] = Field(
        default=None,
        description="Unit of the threshold for documentation (e.g., 'USD_per_bbl', 'percent', 'bps').",
    )
    dataset: Optional[str] = Field(
        default=None,
        description="Source dataset. Required for dataset.field references. Omit for indicator_code references.",
    )
    indicator_code: Optional[str] = Field(
        default=None,
        description="Indicator code from indicator_catalog. Alternative to dataset.field.",
    )
    description: Optional[str] = Field(
        default=None,
        description="Human-readable explanation of this condition.",
    )

    model_config = ConfigDict(extra="forbid")

    @field_validator("operator")
    @classmethod
    def _check_operator(cls, v: str) -> str:
        if v not in VALID_OPERATORS:
            raise ValueError(f"Invalid operator '{v}'. Must be one of: {sorted(VALID_OPERATORS)}")
        return v


class RuleSpec(BaseModel):
    """A complete, declarative rule specification.

    This is the source-of-truth format for decision rules. Rule specs are
    stored as JSON or YAML files, validated against the indicator catalog
    and source registry, and compiled into DecisionRuleORM objects.
    """

    # ── Identity ─────────────────────────────────────────────────────────
    spec_version: str = Field(
        default="1.0.0",
        description="Version of the spec format itself.",
    )
    rule_id: str = Field(
        ...,
        description="Unique rule identifier (e.g., 'RULE-OIL-SHOCK-001').",
    )
    rule_name: str = Field(
        ...,
        max_length=256,
        description="Human-readable rule name.",
    )
    rule_name_ar: Optional[str] = Field(
        default=None,
        max_length=256,
        description="Arabic rule name.",
    )
    description: str = Field(
        ...,
        description="What this rule detects and why it matters.",
    )
    version: int = Field(
        default=1,
        ge=1,
        description="Rule version. Increment on any change to conditions or action.",
    )

    # ── Conditions ───────────────────────────────────────────────────────
    conditions: List[ConditionSpec] = Field(
        ...,
        min_length=1,
        description="One or more conditions. All must be met (AND) or any (OR).",
    )
    condition_logic: Literal["AND", "OR"] = Field(
        default="AND",
        description="How conditions combine: AND (all must match) or OR (any match).",
    )

    # ── Action ───────────────────────────────────────────────────────────
    action: str = Field(
        ...,
        description="Action to take when conditions are met.",
    )
    action_params: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Parameters for the action (e.g., alert recipients, hedge ratio).",
    )
    escalation_level: str = Field(
        default="ELEVATED",
        description="Risk level for this rule.",
    )

    # ── Scope ────────────────────────────────────────────────────────────
    applicable_countries: List[str] = Field(
        default_factory=list,
        description="GCC country codes. Empty = all GCC.",
    )
    applicable_sectors: List[str] = Field(
        default_factory=list,
        description="Sector codes. Empty = all sectors.",
    )
    applicable_scenarios: List[str] = Field(
        default_factory=list,
        description="Scenario IDs this rule is relevant for.",
    )

    # ── Governance ───────────────────────────────────────────────────────
    requires_human_approval: bool = Field(
        default=True,
        description="Whether action requires human sign-off before execution.",
    )
    cooldown_minutes: int = Field(
        default=60,
        ge=0,
        description="Minimum minutes between consecutive triggers.",
    )
    is_active: bool = Field(
        default=False,
        description="Whether this rule is live. Starts inactive; activation requires approval.",
    )
    expiry_date: Optional[str] = Field(
        default=None,
        description="ISO date after which this rule auto-deactivates.",
    )

    # ── Provenance ───────────────────────────────────────────────────────
    author: Optional[str] = Field(
        default=None,
        description="Who wrote this spec.",
    )
    approved_by: Optional[str] = Field(
        default=None,
        description="Who approved this spec for activation.",
    )
    source_dataset_ids: List[str] = Field(
        default_factory=list,
        description="Dataset IDs this rule depends on for evaluation.",
    )
    tags: List[str] = Field(
        default_factory=list,
        description="Classification tags for discovery.",
    )

    model_config = ConfigDict(extra="forbid")

    @field_validator("action")
    @classmethod
    def _check_action(cls, v: str) -> str:
        if v not in VALID_ACTIONS:
            raise ValueError(f"Invalid action '{v}'. Must be one of: {sorted(VALID_ACTIONS)}")
        return v

    @field_validator("escalation_level")
    @classmethod
    def _check_escalation(cls, v: str) -> str:
        if v not in VALID_ESCALATION_LEVELS:
            raise ValueError(f"Invalid escalation_level '{v}'. Must be one of: {sorted(VALID_ESCALATION_LEVELS)}")
        return v

    @field_validator("applicable_countries")
    @classmethod
    def _check_countries(cls, v: List[str]) -> List[str]:
        invalid = set(v) - VALID_COUNTRIES
        if invalid:
            raise ValueError(f"Invalid country codes: {invalid}. Must be GCC: {sorted(VALID_COUNTRIES)}")
        return v
