"""P1 Data Foundation — Validation Layer.

Schema validation, referential integrity checks, and batch validation
across all P1 datasets.
"""

from __future__ import annotations

import logging
from typing import Any, Type

from pydantic import BaseModel, Field, ValidationError

from p1_foundation.models.base import P1BaseModel

logger = logging.getLogger(__name__)


class ValidationIssue(BaseModel):
    """A single validation issue."""
    field: str
    message: str
    severity: str = "error"  # error | warning
    record_index: int | None = None


class ValidationReport(BaseModel):
    """Result of validating a dataset."""
    dataset_name: str
    total_records: int = 0
    valid_records: int = 0
    invalid_records: int = 0
    issues: list[ValidationIssue] = Field(default_factory=list)
    passed: bool = True

    @property
    def error_count(self) -> int:
        return sum(1 for i in self.issues if i.severity == "error")

    @property
    def warning_count(self) -> int:
        return sum(1 for i in self.issues if i.severity == "warning")


def validate_record(record: dict, model_class: Type[P1BaseModel]) -> tuple[bool, list[ValidationIssue]]:
    """Validate a single record against a Pydantic model.

    Returns (is_valid, issues).
    """
    issues: list[ValidationIssue] = []
    try:
        model_class.model_validate(record)
        return True, issues
    except ValidationError as e:
        for err in e.errors():
            field = ".".join(str(loc) for loc in err["loc"]) if err["loc"] else "root"
            issues.append(ValidationIssue(
                field=field,
                message=err["msg"],
                severity="error",
            ))
        return False, issues


def validate_batch(
    records: list[dict],
    model_class: Type[P1BaseModel],
    dataset_name: str,
) -> ValidationReport:
    """Validate a batch of records against a model."""
    report = ValidationReport(dataset_name=dataset_name, total_records=len(records))

    for i, record in enumerate(records):
        is_valid, issues = validate_record(record, model_class)
        for issue in issues:
            issue.record_index = i
        report.issues.extend(issues)
        if is_valid:
            report.valid_records += 1
        else:
            report.invalid_records += 1

    report.passed = report.invalid_records == 0
    return report


def validate_referential_integrity(
    records: list[dict],
    field: str,
    valid_ids: set[str],
    dataset_name: str,
) -> list[ValidationIssue]:
    """Check that FK values in `field` exist in `valid_ids`."""
    issues: list[ValidationIssue] = []
    for i, record in enumerate(records):
        value = record.get(field)
        if value is None:
            continue
        # Handle list fields (e.g., affected_entities)
        if isinstance(value, list):
            for v in value:
                if v not in valid_ids:
                    issues.append(ValidationIssue(
                        field=field,
                        message=f"FK violation: '{v}' not found in reference set",
                        severity="error",
                        record_index=i,
                    ))
        elif value not in valid_ids:
            issues.append(ValidationIssue(
                field=field,
                message=f"FK violation: '{value}' not found in reference set",
                severity="error",
                record_index=i,
            ))
    return issues


def validate_all_datasets(datasets: dict[str, tuple[list[dict], Type[P1BaseModel]]]) -> dict[str, ValidationReport]:
    """Validate all provided datasets.

    Args:
        datasets: mapping of dataset_name → (records, model_class)

    Returns:
        mapping of dataset_name → ValidationReport
    """
    reports: dict[str, ValidationReport] = {}
    for name, (records, model_class) in datasets.items():
        report = validate_batch(records, model_class, name)
        reports[name] = report
        status = "PASS" if report.passed else "FAIL"
        logger.info(
            "Validation [%s] %s: %d/%d valid",
            status,
            name,
            report.valid_records,
            report.total_records,
        )
    return reports
