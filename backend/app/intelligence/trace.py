"""
Intelligence Adapter Foundation — Trace Packaging

PHASE 2: Trace payload builder.

Preserves:
    - source system names
    - source event IDs
    - raw payload references
    - adapter notes
    - normalization warnings
    - semantic separation (observed / inferred / simulated sections)
    - field-level decisions made during normalization

The trace is immutable after build and embedded in NormalizedIntelligenceSignal.
It is NEVER stripped or summarized downstream.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from typing import Any


def _now_utc() -> str:
    return datetime.now(timezone.utc).isoformat()


# ─── Warning / Error records ──────────────────────────────────────────────────

@dataclass(frozen=True)
class NormalizationWarning:
    """A non-fatal issue encountered during normalization.

    Warnings do NOT block normalization. They indicate that a field was
    defaulted, truncated, or inferred rather than explicitly provided.

    status is set to PARTIAL on the resulting signal when any warnings exist.
    """
    field_name: str
    message: str
    original_value: Any = None
    resolved_value: Any = None
    severity: str = "LOW"       # LOW | MEDIUM | HIGH
    at: str = field(default_factory=_now_utc)


@dataclass(frozen=True)
class NormalizationViolation:
    """A fatal error that blocks normalization.

    Violations result in REJECTED status. The signal MUST NOT enter the
    bridge or core system when any violation is present.
    """
    field_name: str
    message: str
    received_value: Any = None
    rule: str = ""
    at: str = field(default_factory=_now_utc)


class AdapterError(ValueError):
    """Raised when normalization fails with one or more violations.

    violations: list of NormalizationViolation objects.
    """
    def __init__(self, message: str, violations: list[NormalizationViolation] | None = None):
        super().__init__(message)
        self.violations: list[NormalizationViolation] = violations or []

    def to_dict(self) -> dict[str, Any]:
        return {
            "error": str(self),
            "violations": [asdict(v) for v in self.violations],
        }


# ─── Trace builder ────────────────────────────────────────────────────────────

class TraceBuilder:
    """Accumulates normalization decisions, warnings, and violations.

    Usage:
        tb = TraceBuilder(source_family="trek", source_systems=["trek_v2"])
        tb.note("severity_score", "clamped from 1.4 to 1.0")
        tb.warn("title", "not provided — defaulted to event_type", severity="MEDIUM")
        tb.build()  # returns dict ready for NormalizedIntelligenceSignal.trace_payload
    """

    def __init__(
        self,
        source_family: str,
        source_systems: list[str],
        adapter_version: str = "1.0.0",
    ):
        self._trace_id = f"trace-{uuid.uuid4().hex[:12]}"
        self._source_family = source_family
        self._source_systems = list(source_systems)
        self._adapter_version = adapter_version
        self._started_at = _now_utc()
        self._notes: list[dict[str, Any]] = []
        self._warnings: list[NormalizationWarning] = []
        self._violations: list[NormalizationViolation] = []
        self._semantic_counts: dict[str, int] = {"observed": 0, "inferred": 0, "simulated": 0}

    # ── Recording ─────────────────────────────────────────────────────────────

    def note(self, field_name: str, message: str, **extra: Any) -> None:
        """Record a neutral adapter decision (no severity)."""
        self._notes.append({"field": field_name, "message": message, **extra, "at": _now_utc()})

    def warn(
        self,
        field_name: str,
        message: str,
        original_value: Any = None,
        resolved_value: Any = None,
        severity: str = "LOW",
    ) -> None:
        """Record a non-fatal normalization warning."""
        self._warnings.append(NormalizationWarning(
            field_name=field_name,
            message=message,
            original_value=original_value,
            resolved_value=resolved_value,
            severity=severity,
        ))

    def violation(
        self,
        field_name: str,
        message: str,
        received_value: Any = None,
        rule: str = "",
    ) -> None:
        """Record a fatal normalization violation."""
        self._violations.append(NormalizationViolation(
            field_name=field_name,
            message=message,
            received_value=received_value,
            rule=rule,
        ))

    def set_semantic_counts(self, observed: int, inferred: int, simulated: int) -> None:
        self._semantic_counts = {"observed": observed, "inferred": inferred, "simulated": simulated}

    # ── Status derivation ─────────────────────────────────────────────────────

    def has_violations(self) -> bool:
        return len(self._violations) > 0

    def has_warnings(self) -> bool:
        return len(self._warnings) > 0

    def derived_status(self) -> str:
        """Derive normalization status from accumulated records.

        REJECTED  — any violations
        PARTIAL   — warnings but no violations
        NORMALIZED — clean
        """
        if self._violations:
            return "REJECTED"
        if self._warnings:
            return "PARTIAL"
        return "NORMALIZED"

    def get_violations(self) -> list[NormalizationViolation]:
        return list(self._violations)

    def get_warnings(self) -> list[NormalizationWarning]:
        return list(self._warnings)

    # ── Build ─────────────────────────────────────────────────────────────────

    def build(self) -> dict[str, Any]:
        """Return the complete trace payload dict.

        This dict is embedded verbatim into NormalizedIntelligenceSignal.trace_payload.
        It is never modified or summarized.
        """
        return {
            "trace_id":          self._trace_id,
            "adapter_version":   self._adapter_version,
            "source_family":     self._source_family,
            "source_systems":    self._source_systems,
            "normalization_status": self.derived_status(),
            "started_at":        self._started_at,
            "completed_at":      _now_utc(),
            "semantic_counts":   self._semantic_counts,
            "warning_count":     len(self._warnings),
            "violation_count":   len(self._violations),
            "notes":             self._notes,
            "warnings":          [asdict(w) for w in self._warnings],
            "violations":        [asdict(v) for v in self._violations],
        }
