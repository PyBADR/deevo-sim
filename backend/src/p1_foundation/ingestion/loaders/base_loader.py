"""P1 Data Foundation — Base Loader.

Abstract base for all ingestion loaders. Provides the common pipeline:
load raw → apply field mappings → validate quality gates → attach provenance → emit result.
"""

from __future__ import annotations

import hashlib
import json
import logging
from abc import ABC, abstractmethod
from datetime import datetime, timezone
from typing import Any

from pydantic import BaseModel, Field, ValidationError

from p1_foundation.ingestion.contracts import FieldMapping, IngestionContract, QualityGate
from p1_foundation.models.enums import DataQuality

logger = logging.getLogger(__name__)


class IngestionResult(BaseModel):
    """Result of ingesting a batch of records."""

    contract_id: str
    total_raw: int = 0
    accepted: int = 0
    rejected: int = 0
    warnings: int = 0
    records: list[dict] = Field(default_factory=list)
    errors: list[dict] = Field(default_factory=list)
    provenance_hash: str = ""
    ingested_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class BaseLoader(ABC):
    """Abstract base loader. Subclasses implement `fetch_raw`."""

    def __init__(self, contract: IngestionContract):
        self.contract = contract

    @abstractmethod
    def fetch_raw(self, **kwargs: Any) -> list[dict]:
        """Fetch raw records from the source. Returns list of dicts."""
        ...

    def ingest(self, **kwargs: Any) -> IngestionResult:
        """Full ingestion pipeline: fetch → map → validate → provenance."""
        raw_records = self.fetch_raw(**kwargs)
        result = IngestionResult(contract_id=self.contract.contract_id, total_raw=len(raw_records))

        for i, raw in enumerate(raw_records):
            mapped = self._apply_mappings(raw)
            gate_errors, gate_warnings = self._check_quality_gates(mapped)

            if gate_errors:
                result.rejected += 1
                result.errors.append({
                    "index": i,
                    "raw": raw,
                    "errors": gate_errors,
                })
                continue

            if gate_warnings:
                result.warnings += len(gate_warnings)

            mapped["provenance_hash"] = self._hash_record(raw)
            mapped["ingested_at"] = datetime.now(timezone.utc).isoformat()
            mapped["data_quality"] = self.contract.output_quality.value
            result.accepted += 1
            result.records.append(mapped)

        result.provenance_hash = self._hash_batch(raw_records)
        logger.info(
            "Ingestion %s: %d accepted, %d rejected, %d warnings",
            self.contract.contract_id,
            result.accepted,
            result.rejected,
            result.warnings,
        )
        return result

    def _apply_mappings(self, raw: dict) -> dict:
        """Apply field mappings from contract."""
        if not self.contract.field_mappings:
            return dict(raw)

        mapped: dict[str, Any] = {}
        for fm in self.contract.field_mappings:
            value = raw.get(fm.source_field, fm.default)
            if value is None and fm.required:
                continue
            if fm.transform and value is not None:
                value = self._transform(value, fm.transform)
            mapped[fm.target_field] = value
        return mapped

    def _transform(self, value: Any, transform: str) -> Any:
        """Apply a named transform to a value."""
        transforms = {
            "to_float": lambda v: float(v),
            "to_int": lambda v: int(v),
            "to_str": lambda v: str(v),
            "strip": lambda v: str(v).strip(),
            "upper": lambda v: str(v).upper(),
            "lower": lambda v: str(v).lower(),
        }
        fn = transforms.get(transform)
        if fn is None:
            logger.warning("Unknown transform '%s', returning raw value", transform)
            return value
        try:
            return fn(value)
        except (ValueError, TypeError):
            return value

    def _check_quality_gates(self, record: dict) -> tuple[list[str], list[str]]:
        """Evaluate quality gates. Returns (errors, warnings)."""
        errors: list[str] = []
        warnings: list[str] = []

        for gate in self.contract.quality_gates:
            msg = self._evaluate_gate(record, gate)
            if msg:
                if gate.severity == "error":
                    errors.append(msg)
                else:
                    warnings.append(msg)

        return errors, warnings

    def _evaluate_gate(self, record: dict, gate: QualityGate) -> str | None:
        """Evaluate a single quality gate. Returns error message or None."""
        value = record.get(gate.field)

        if gate.check == "not_null":
            if value is None:
                return f"{gate.field}: must not be null"

        elif gate.check == "range":
            if value is not None:
                lo = gate.params.get("min")
                hi = gate.params.get("max")
                try:
                    v = float(value)
                    if lo is not None and v < lo:
                        return f"{gate.field}: {v} below minimum {lo}"
                    if hi is not None and v > hi:
                        return f"{gate.field}: {v} above maximum {hi}"
                except (ValueError, TypeError):
                    return f"{gate.field}: cannot convert to number"

        elif gate.check == "regex":
            import re
            pattern = gate.params.get("pattern", "")
            if value is not None and not re.match(pattern, str(value)):
                return f"{gate.field}: '{value}' does not match pattern '{pattern}'"

        elif gate.check == "in_set":
            allowed = gate.params.get("values", [])
            if value is not None and value not in allowed:
                return f"{gate.field}: '{value}' not in allowed set"

        return None

    @staticmethod
    def _hash_record(record: dict) -> str:
        raw = json.dumps(record, sort_keys=True, default=str)
        return hashlib.sha256(raw.encode()).hexdigest()

    @staticmethod
    def _hash_batch(records: list[dict]) -> str:
        raw = json.dumps(records, sort_keys=True, default=str)
        return hashlib.sha256(raw.encode()).hexdigest()
