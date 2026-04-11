"""Rule spec validator — check specs against indicator catalog and source registry.

Validates:
  1. Structural: required fields, valid operators, valid actions
  2. Referential: indicator_codes exist in catalog, datasets exist
  3. Threshold: values are sane for the indicator's unit and normal range
  4. Uniqueness: no duplicate rule_ids across a spec set
  5. Governance: active rules must have an approved_by
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Set

from src.data_foundation.rules.spec import (
    VALID_ACTIONS,
    VALID_DATASETS,
    VALID_ESCALATION_LEVELS,
    VALID_OPERATORS,
    ConditionSpec,
    RuleSpec,
)

logger = logging.getLogger(__name__)

_SEED_DIR = Path(__file__).parent.parent / "seed"


@dataclass
class ValidationIssue:
    """A single validation issue found in a rule spec."""
    rule_id: str
    field: str
    message: str
    severity: str  # "error" or "warning"


@dataclass
class ValidationResult:
    """Result of validating one or more rule specs."""
    specs_checked: int = 0
    valid: int = 0
    invalid: int = 0
    issues: List[ValidationIssue] = field(default_factory=list)

    @property
    def passed(self) -> bool:
        return self.invalid == 0 and not any(i.severity == "error" for i in self.issues)

    def errors(self) -> List[ValidationIssue]:
        return [i for i in self.issues if i.severity == "error"]

    def warnings(self) -> List[ValidationIssue]:
        return [i for i in self.issues if i.severity == "warning"]


def _load_indicator_codes() -> Dict[str, dict]:
    """Load indicator catalog for referential validation."""
    catalog_path = _SEED_DIR / "indicator_catalog.json"
    if not catalog_path.exists():
        return {}
    with open(catalog_path) as f:
        catalog = json.load(f)
    return {entry["indicator_code"]: entry for entry in catalog}


def _load_source_ids() -> Set[str]:
    """Load source IDs from source truth registry."""
    registry_path = _SEED_DIR / "source_truth_registry.json"
    if not registry_path.exists():
        return set()
    with open(registry_path) as f:
        registry = json.load(f)
    return {entry["source_id"] for entry in registry}


def validate_spec(
    spec: RuleSpec,
    *,
    indicator_catalog: Optional[Dict[str, dict]] = None,
) -> ValidationResult:
    """Validate a single rule spec.

    Args:
        spec: The rule spec to validate.
        indicator_catalog: Pre-loaded catalog. Loaded from seed if None.

    Returns:
        ValidationResult with any issues found.
    """
    if indicator_catalog is None:
        indicator_catalog = _load_indicator_codes()

    result = ValidationResult(specs_checked=1)
    issues = result.issues

    # 1. Structural: rule_id format
    if not spec.rule_id or len(spec.rule_id) > 128:
        issues.append(ValidationIssue(spec.rule_id, "rule_id", "Must be 1-128 characters", "error"))

    # 2. Conditions validation
    for i, cond in enumerate(spec.conditions):
        _validate_condition(spec.rule_id, i, cond, indicator_catalog, issues)

    # 3. Action validation (already checked by Pydantic, but double-check)
    if spec.action not in VALID_ACTIONS:
        issues.append(ValidationIssue(spec.rule_id, "action", f"Invalid action '{spec.action}'", "error"))

    # 4. Escalation level
    if spec.escalation_level not in VALID_ESCALATION_LEVELS:
        issues.append(ValidationIssue(spec.rule_id, "escalation_level", f"Invalid level '{spec.escalation_level}'", "error"))

    # 5. Governance: active rules should have approval
    if spec.is_active and not spec.approved_by:
        issues.append(ValidationIssue(spec.rule_id, "approved_by", "Active rule has no approved_by", "warning"))

    # 6. Cooldown sanity
    if spec.cooldown_minutes > 43200:  # 30 days
        issues.append(ValidationIssue(spec.rule_id, "cooldown_minutes", f"Cooldown {spec.cooldown_minutes}m seems excessive (>30d)", "warning"))

    # 7. Expiry date format
    if spec.expiry_date:
        try:
            from datetime import date as _date
            _date.fromisoformat(spec.expiry_date)
        except ValueError:
            issues.append(ValidationIssue(spec.rule_id, "expiry_date", f"Invalid ISO date: '{spec.expiry_date}'", "error"))

    if any(i.severity == "error" for i in issues):
        result.invalid = 1
    else:
        result.valid = 1

    return result


def _validate_condition(
    rule_id: str,
    index: int,
    cond: ConditionSpec,
    catalog: Dict[str, dict],
    issues: List[ValidationIssue],
) -> None:
    """Validate a single condition within a rule spec."""
    prefix = f"conditions[{index}]"

    # Operator already validated by Pydantic, but check anyway
    if cond.operator not in VALID_OPERATORS:
        issues.append(ValidationIssue(rule_id, f"{prefix}.operator", f"Invalid operator '{cond.operator}'", "error"))

    # Must have either dataset or indicator_code
    if not cond.dataset and not cond.indicator_code:
        # Allow bare field names with dot notation (dataset.field)
        if "." not in cond.field:
            issues.append(ValidationIssue(
                rule_id, f"{prefix}.field",
                "Must specify 'dataset' or 'indicator_code', or use dot notation (dataset.field)",
                "error",
            ))

    # Validate dataset reference
    if cond.dataset and cond.dataset not in VALID_DATASETS:
        issues.append(ValidationIssue(
            rule_id, f"{prefix}.dataset",
            f"Unknown dataset '{cond.dataset}'. Valid: {sorted(VALID_DATASETS)}",
            "error",
        ))

    # Validate indicator_code against catalog
    if cond.indicator_code and catalog:
        if cond.indicator_code not in catalog:
            issues.append(ValidationIssue(
                rule_id, f"{prefix}.indicator_code",
                f"Indicator '{cond.indicator_code}' not found in catalog",
                "error",
            ))
        else:
            # Check threshold sanity against normal range
            entry = catalog[cond.indicator_code]
            _validate_threshold_range(rule_id, prefix, cond, entry, issues)

    # Validate threshold type matches operator
    if cond.operator in ("in", "not_in"):
        if not isinstance(cond.threshold, list):
            issues.append(ValidationIssue(
                rule_id, f"{prefix}.threshold",
                f"Operator '{cond.operator}' requires a list threshold",
                "error",
            ))
    elif cond.operator == "between":
        if not isinstance(cond.threshold, list) or len(cond.threshold) != 2:
            issues.append(ValidationIssue(
                rule_id, f"{prefix}.threshold",
                "Operator 'between' requires a [min, max] list",
                "error",
            ))

    # Threshold must not be None
    if cond.threshold is None:
        issues.append(ValidationIssue(rule_id, f"{prefix}.threshold", "Threshold cannot be null", "error"))


def _validate_threshold_range(
    rule_id: str,
    prefix: str,
    cond: ConditionSpec,
    catalog_entry: dict,
    issues: List[ValidationIssue],
) -> None:
    """Check if threshold is within a plausible range for the indicator."""
    if cond.operator in ("in", "not_in", "between"):
        return  # Skip range check for list operators

    if not isinstance(cond.threshold, (int, float)):
        return

    normal_min = catalog_entry.get("normal_range_min")
    normal_max = catalog_entry.get("normal_range_max")

    # If the threshold is wildly outside the normal range, warn
    if normal_min is not None and normal_max is not None:
        range_span = abs(normal_max - normal_min)
        if range_span > 0:
            if cond.threshold < normal_min - 3 * range_span:
                issues.append(ValidationIssue(
                    rule_id, f"{prefix}.threshold",
                    f"Threshold {cond.threshold} is far below normal range [{normal_min}, {normal_max}]",
                    "warning",
                ))
            if cond.threshold > normal_max + 3 * range_span:
                issues.append(ValidationIssue(
                    rule_id, f"{prefix}.threshold",
                    f"Threshold {cond.threshold} is far above normal range [{normal_min}, {normal_max}]",
                    "warning",
                ))


def validate_all(specs: List[RuleSpec]) -> ValidationResult:
    """Validate a list of rule specs, including cross-spec checks.

    Cross-spec checks:
      - No duplicate rule_ids
    """
    catalog = _load_indicator_codes()
    combined = ValidationResult()
    seen_ids: Set[str] = set()

    for spec in specs:
        # Duplicate check
        if spec.rule_id in seen_ids:
            combined.issues.append(ValidationIssue(
                spec.rule_id, "rule_id", f"Duplicate rule_id '{spec.rule_id}'", "error",
            ))
            combined.invalid += 1
            combined.specs_checked += 1
            continue
        seen_ids.add(spec.rule_id)

        single = validate_spec(spec, indicator_catalog=catalog)
        combined.specs_checked += single.specs_checked
        combined.valid += single.valid
        combined.invalid += single.invalid
        combined.issues.extend(single.issues)

    return combined
