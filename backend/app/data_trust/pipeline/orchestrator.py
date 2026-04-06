"""
Impact Observatory | مرصد الأثر — Data Trust Pipeline Orchestrator

Runs the complete trust pipeline for a given adapter:

    fetch → normalize → validate → score → quarantine OR pass → intelligence bridge

Design rules
------------
- No heavy framework. Plain Python with explicit control flow.
- No silent failures. Every failure is logged and recorded.
- No partial processing. If normalize() fails for one record, it is quarantined;
  the rest of the batch continues.
- Retries: fetch() is retried once on AdapterFetchError (network transience).
  normalize() is NOT retried — a normalization failure indicates a structural
  problem with the source data that retrying won't fix.
- Logging: every stage transition is logged at INFO level.
  Validation errors are logged at WARNING. Quarantine writes at WARNING.
  Bridge failures at ERROR.

Result shape
------------
    PipelineResult:
        run_id          str
        adapter         str
        total           int     Records fetched
        passed          int     Records passed to intelligence engine
        quarantined     int     Records sent to quarantine
        failed          int     Records failed at normalize or bridge stage
        records         list[RecordResult]  Per-record trace

    RecordResult:
        event_id        str
        status          "passed" | "quarantined" | "failed"
        errors          list[str]   Empty when status="passed"
        source_score    float | None
        trust_tier      str | None
        bridge_result   dict | None   Intelligence engine output (if passed)
"""

from __future__ import annotations

import logging
import time
import uuid
from dataclasses import dataclass, field
from typing import Optional

from ..adapters.base import BaseAdapter, AdapterFetchError, AdapterNormalizeError
from ..contracts.event import TrustedEventContract, ValidationStatus
from ..scoring.trust_scorer import SourceMetrics, compute_source_score
from ..quarantine.store import quarantine_record
from .bridge import ingest_to_intelligence

logger = logging.getLogger(__name__)


@dataclass
class RecordResult:
    """Per-record outcome from the trust pipeline."""
    event_id:     str
    status:       str                   # "passed" | "quarantined" | "failed"
    errors:       list[str]             = field(default_factory=list)
    source_score: Optional[float]       = None
    trust_tier:   Optional[str]         = None
    bridge_result: Optional[dict]       = None

    def to_dict(self) -> dict:
        return {
            "event_id":     self.event_id,
            "status":       self.status,
            "errors":       self.errors,
            "source_score": self.source_score,
            "trust_tier":   self.trust_tier,
            "bridge_ok":    self.bridge_result is not None and self.bridge_result.get("ok", False),
        }


@dataclass
class PipelineResult:
    """Aggregate outcome for one orchestrator run (one adapter, N records)."""
    run_id:      str
    adapter:     str
    total:       int = 0
    passed:      int = 0
    quarantined: int = 0
    failed:      int = 0
    duration_ms: float = 0.0
    records:     list[RecordResult] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        """True if at least one record passed and none failed catastrophically."""
        return self.passed > 0

    def to_dict(self) -> dict:
        return {
            "run_id":      self.run_id,
            "adapter":     self.adapter,
            "total":       self.total,
            "passed":      self.passed,
            "quarantined": self.quarantined,
            "failed":      self.failed,
            "duration_ms": self.duration_ms,
            "ok":          self.ok,
            "records":     [r.to_dict() for r in self.records],
        }


def run_pipeline(adapter: BaseAdapter) -> PipelineResult:
    """
    Execute the data trust pipeline for one adapter.

    Flow per record
    ---------------
    1. fetch()       → list[dict]  (retried once on AdapterFetchError)
    2. normalize()   → TrustedEventContract
    3. validate()    → {"valid": bool, "errors": list[str]}
    4. If invalid    → quarantine()  → RecordResult(status="quarantined")
    5. If valid      → compute_source_score()
    6.               → ingest_to_intelligence()
    7.               → RecordResult(status="passed")

    Parameters
    ----------
    adapter : BaseAdapter
        Concrete adapter instance (GovernmentAdapter, RealEstateAdapter, etc.)

    Returns
    -------
    PipelineResult
        Aggregate result with per-record traces.
    """
    run_id = f"dtp_{uuid.uuid4().hex[:12]}"
    t_start = time.time()

    logger.info(
        "[%s] Starting data trust pipeline — adapter=%s",
        run_id, adapter.source_id,
    )

    result = PipelineResult(run_id=run_id, adapter=adapter.source_id)

    # ── Stage 1: Fetch ────────────────────────────────────────────────────────
    raw_records: list[dict] = []
    try:
        raw_records = adapter.fetch()
        logger.info("[%s] Fetched %d records from %s", run_id, len(raw_records), adapter.source_id)
    except AdapterFetchError as exc:
        logger.warning("[%s] fetch() failed: %s — retrying once", run_id, exc)
        try:
            raw_records = adapter.fetch()
            logger.info("[%s] Retry fetch succeeded: %d records", run_id, len(raw_records))
        except AdapterFetchError as exc2:
            logger.error("[%s] fetch() retry failed: %s — aborting pipeline", run_id, exc2)
            result.duration_ms = round((time.time() - t_start) * 1000, 1)
            return result

    result.total = len(raw_records)
    if result.total == 0:
        logger.warning("[%s] Adapter %s returned 0 records", run_id, adapter.source_id)
        result.duration_ms = round((time.time() - t_start) * 1000, 1)
        return result

    # ── Stage 2–6: Per-record processing ─────────────────────────────────────
    adapter_metrics = adapter.source_metrics()

    for raw in raw_records:
        rec = _process_record(
            run_id=run_id,
            raw=raw,
            adapter=adapter,
            adapter_metrics=adapter_metrics,
        )
        result.records.append(rec)
        if rec.status == "passed":
            result.passed += 1
        elif rec.status == "quarantined":
            result.quarantined += 1
        else:
            result.failed += 1

    result.duration_ms = round((time.time() - t_start) * 1000, 1)
    logger.info(
        "[%s] Pipeline complete — total=%d passed=%d quarantined=%d failed=%d %.1fms",
        run_id, result.total, result.passed, result.quarantined, result.failed,
        result.duration_ms,
    )
    return result


def _process_record(
    *,
    run_id:          str,
    raw:             dict,
    adapter:         BaseAdapter,
    adapter_metrics: dict[str, float],
) -> RecordResult:
    """Process one raw record through the full trust pipeline."""

    event_id = f"te_unknown_{uuid.uuid4().hex[:8]}"

    # ── Stage 2: Normalize ────────────────────────────────────────────────────
    contract: Optional[TrustedEventContract] = None
    try:
        contract = adapter.normalize(raw)
        event_id = contract.event_id
        logger.debug("[%s] Normalized event_id=%s", run_id, event_id)
    except AdapterNormalizeError as exc:
        logger.warning("[%s] normalize() failed event_id=%s: %s", run_id, event_id, exc)
        _quarantine_failed_normalization(
            run_id=run_id,
            event_id=event_id,
            source=adapter.source_id,
            domain=adapter.domain,
            raw=raw,
            error=str(exc),
        )
        return RecordResult(
            event_id=event_id,
            status="failed",
            errors=[f"normalize() failed: {exc}"],
        )
    except Exception as exc:
        logger.error("[%s] Unexpected normalize() error event_id=%s: %s", run_id, event_id, exc)
        _quarantine_failed_normalization(
            run_id=run_id,
            event_id=event_id,
            source=adapter.source_id,
            domain=adapter.domain,
            raw=raw,
            error=f"Unexpected: {exc}",
        )
        return RecordResult(
            event_id=event_id,
            status="failed",
            errors=[f"Unexpected normalize() error: {exc}"],
        )

    # ── Stage 3: Validate ─────────────────────────────────────────────────────
    validation = adapter.validate(contract)
    hard_failures = [e for e in validation["errors"] if "_WARN" not in e]

    if not validation["valid"] or hard_failures:
        logger.warning(
            "[%s] Validation failed event_id=%s errors=%s",
            run_id, event_id, validation["errors"],
        )
        contract.validation_status = ValidationStatus.QUARANTINED
        contract.validation_errors = validation["errors"]

        # ── Stage 4: Quarantine ───────────────────────────────────────────────
        quarantine_record(
            event_id=event_id,
            source=contract.source,
            domain=contract.domain,
            event_timestamp=contract.timestamp,
            error_reasons=validation["errors"],
            raw_payload=contract.raw_payload,
            normalized_payload=contract.normalized_payload,
            impact_score=contract.impact_score,
            confidence=contract.confidence,
            pipeline_run_id=run_id,
        )
        return RecordResult(
            event_id=event_id,
            status="quarantined",
            errors=validation["errors"],
        )

    contract.validation_status = ValidationStatus.VALID

    # ── Stage 5: Score ────────────────────────────────────────────────────────
    metrics = SourceMetrics(
        reliability=adapter_metrics.get("reliability", 0.70),
        freshness=adapter_metrics.get("freshness", 0.80),
        coverage=adapter_metrics.get("coverage", 0.75),
        consistency=adapter_metrics.get("consistency", 0.70),
        latency=adapter_metrics.get("latency", 0.80),
        event_timestamp=contract.timestamp,
        received_at=contract.received_at,
        normalized_payload=contract.normalized_payload,
    )
    scoring = compute_source_score(metrics)
    contract.confidence = scoring.confidence

    logger.info(
        "[%s] Scored event_id=%s score=%.4f tier=%s formula=%s",
        run_id, event_id, scoring.source_score, scoring.trust_tier, scoring.formula,
    )

    # ── Stage 6: Intelligence bridge ─────────────────────────────────────────
    bridge_result = ingest_to_intelligence(contract, run_id=run_id)

    if not bridge_result.get("ok"):
        logger.error(
            "[%s] Bridge failed event_id=%s: %s",
            run_id, event_id, bridge_result.get("error"),
        )
        return RecordResult(
            event_id=event_id,
            status="failed",
            errors=[bridge_result.get("error", "Bridge failed")],
            source_score=scoring.source_score,
            trust_tier=scoring.trust_tier,
        )

    return RecordResult(
        event_id=event_id,
        status="passed",
        errors=validation["errors"],   # May contain _WARN entries
        source_score=scoring.source_score,
        trust_tier=scoring.trust_tier,
        bridge_result=bridge_result,
    )


def _quarantine_failed_normalization(
    *,
    run_id:   str,
    event_id: str,
    source:   str,
    domain:   str,
    raw:      dict,
    error:    str,
) -> None:
    """Write a quarantine record for a record that failed normalization."""
    try:
        quarantine_record(
            event_id=event_id,
            source=source,
            domain=domain,
            event_timestamp=None,
            error_reasons=[f"NORMALIZE_FAILED: {error}"],
            raw_payload=raw,
            normalized_payload={},
            pipeline_run_id=run_id,
        )
    except Exception as qe:
        logger.error(
            "[%s] Failed to write quarantine record for failed normalization: %s",
            run_id, qe,
        )
