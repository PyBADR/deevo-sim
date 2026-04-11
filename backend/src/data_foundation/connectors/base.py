"""Base connector — full pipeline from HTTP fetch to canonical observations.

Pipeline stages:
  1. Create SourceFetchRun (PENDING → RUNNING)
  2. fetch_raw()  — subclass HTTP call, returns raw JSON payload
  3. Persist RawSourceRecord with SHA-256 content_hash
  4. Duplicate detection via content_hash lookup
  5. normalize() — subclass maps raw → list of CanonicalObservation dicts
  6. Revision handling: find existing obs, bump revision_number, compute delta
  7. Persist CanonicalObservationORM rows
  8. Create NormalizationRun with metrics
  9. Update SourceFetchRun (COMPLETED / FAILED)
  10. Return ConnectorResult summary
"""

from __future__ import annotations

import hashlib
import json
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import date, datetime, timezone
from typing import Any, Dict, List, Optional, Sequence
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.data_foundation.models.reality_tables import (
    CanonicalObservationORM,
    NormalizationRunORM,
    RawSourceRecordORM,
    SourceFetchRunORM,
    SourceTruthRegistryORM,
)

logger = logging.getLogger(__name__)


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _uuid() -> str:
    return str(uuid4())


def _content_hash(payload: Any) -> str:
    """SHA-256 of canonical JSON serialization."""
    canonical = json.dumps(payload, sort_keys=True, default=str)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


@dataclass
class ConnectorResult:
    """Summary returned after a full connector run."""
    source_id: str
    fetch_run_id: str
    normalization_run_id: str
    status: str  # COMPLETED, FAILED, PARTIAL
    records_fetched: int = 0
    records_new: int = 0
    records_duplicate: int = 0
    observations_created: int = 0
    observations_updated: int = 0
    observations_skipped: int = 0
    validation_errors: int = 0
    error_message: Optional[str] = None
    errors: list = field(default_factory=list)


@dataclass
class NormalizedRecord:
    """A single normalized observation ready for persistence."""
    indicator_code: str
    indicator_id: str
    value: float
    unit: str
    country: str
    period_start: date
    period_end: date
    frequency: str
    observation_date: date
    entity_id: Optional[str] = None
    confidence_score: float = 0.8
    confidence_method: str = "SOURCE_DECLARED"
    is_provisional: bool = False


class BaseConnector(ABC):
    """Abstract base for all data source connectors.

    Subclasses implement:
      - source_id: str — matches source_truth_registry.source_id
      - fetch_raw() → raw JSON payload from the real API
      - normalize(raw_payload) → list of NormalizedRecord
      - source_url property — the URL being fetched
    """

    source_id: str
    _session: AsyncSession

    def __init__(self, session: AsyncSession):
        self._session = session

    @property
    @abstractmethod
    def source_url(self) -> str:
        """The URL from which data is fetched."""

    @abstractmethod
    async def fetch_raw(self) -> Dict[str, Any]:
        """Make the real HTTP call and return the raw JSON payload.

        Raises on network/parse errors — the pipeline catches and records them.
        """

    @abstractmethod
    def normalize(self, raw_payload: Dict[str, Any]) -> List[NormalizedRecord]:
        """Map raw API payload into a list of NormalizedRecord objects.

        Must validate that required fields are present and values are sane.
        Returns only valid records; logs and counts validation errors.
        """

    def validate_record(self, rec: NormalizedRecord) -> List[str]:
        """Validate a normalized record. Returns list of error strings (empty = valid)."""
        errors = []
        if not rec.indicator_code:
            errors.append("indicator_code is empty")
        if not rec.indicator_id:
            errors.append("indicator_id is empty")
        if not rec.country:
            errors.append("country is empty")
        if not rec.unit:
            errors.append("unit is empty")
        if rec.period_start > rec.period_end:
            errors.append(f"period_start {rec.period_start} > period_end {rec.period_end}")
        if rec.confidence_score < 0.0 or rec.confidence_score > 1.0:
            errors.append(f"confidence_score {rec.confidence_score} out of [0,1]")
        return errors

    # ── Full pipeline ────────────────────────────────────────────────────

    async def run(self, *, trigger_type: str = "SCHEDULED", triggered_by: Optional[str] = None) -> ConnectorResult:
        """Execute the full fetch → persist → normalize → observe pipeline."""
        fetch_run_id = f"fr-{self.source_id}-{_uuid()[:8]}"
        norm_run_id = f"nr-{self.source_id}-{_uuid()[:8]}"
        now = _utcnow()

        result = ConnectorResult(
            source_id=self.source_id,
            fetch_run_id=fetch_run_id,
            normalization_run_id=norm_run_id,
            status="PENDING",
        )

        # Step 1: Create fetch run (RUNNING)
        fetch_run = SourceFetchRunORM(
            run_id=fetch_run_id,
            source_id=self.source_id,
            source_url=self.source_url,
            fetch_timestamp=now,
            period_start=date.today(),
            period_end=date.today(),
            status="RUNNING",
            started_at=now,
            trigger_type=trigger_type,
            triggered_by=triggered_by,
        )
        self._session.add(fetch_run)
        await self._session.flush()

        try:
            # Step 2: Fetch raw data
            raw_payload = await self.fetch_raw()
            payload_bytes = len(json.dumps(raw_payload, default=str).encode("utf-8"))
            content_hash = _content_hash(raw_payload)

            # Determine period from payload (subclasses can override)
            period_start, period_end = self._extract_period(raw_payload)
            fetch_run.period_start = period_start
            fetch_run.period_end = period_end
            fetch_run.content_hash = content_hash
            fetch_run.payload_size_bytes = payload_bytes

            # Step 3: Check duplicate via content_hash
            dup_stmt = select(RawSourceRecordORM).where(
                RawSourceRecordORM.content_hash == content_hash,
                RawSourceRecordORM.source_id == self.source_id,
            )
            dup_result = await self._session.execute(dup_stmt)
            existing_raw = dup_result.scalar_one_or_none()

            record_id = f"raw-{self.source_id}-{_uuid()[:8]}"
            is_duplicate = existing_raw is not None

            # Step 4: Persist raw record
            raw_record = RawSourceRecordORM(
                record_id=record_id,
                source_id=self.source_id,
                fetch_run_id=fetch_run_id,
                source_url=self.source_url,
                fetch_timestamp=now,
                content_hash=content_hash,
                period_start=period_start,
                period_end=period_end,
                raw_payload=raw_payload,
                content_type="application/json",
                payload_size_bytes=payload_bytes,
                is_duplicate=is_duplicate,
                duplicate_of_record_id=existing_raw.record_id if existing_raw else None,
                normalization_status="PENDING" if not is_duplicate else "SKIPPED",
            )
            self._session.add(raw_record)
            result.records_fetched = 1

            if is_duplicate:
                result.records_duplicate = 1
                logger.info("Duplicate payload detected for %s (hash=%s)", self.source_id, content_hash[:16])
            else:
                result.records_new = 1

            # Step 5: Normalize (even if duplicate — revisions may apply)
            norm_run = NormalizationRunORM(
                run_id=norm_run_id,
                fetch_run_id=fetch_run_id,
                source_id=self.source_id,
                started_at=_utcnow(),
                status="RUNNING",
                raw_records_input=1,
                field_mappings_used={"connector": type(self).__name__},
            )
            self._session.add(norm_run)

            normalized_records = self.normalize(raw_payload)

            obs_created = 0
            obs_updated = 0
            obs_skipped = 0
            validation_errors = 0
            quality_gates: List[Dict[str, Any]] = []

            for rec in normalized_records:
                # Step 6: Validate
                errors = self.validate_record(rec)
                if errors:
                    validation_errors += 1
                    quality_gates.append({"indicator": rec.indicator_code, "errors": errors})
                    logger.warning("Validation failed for %s: %s", rec.indicator_code, errors)
                    result.errors.append({"indicator": rec.indicator_code, "errors": errors})
                    continue

                # Step 7: Check for existing observation (revision handling)
                existing_obs = await self._find_existing_observation(
                    rec.indicator_code, rec.country, rec.period_start
                )

                if existing_obs is not None:
                    if is_duplicate and abs(existing_obs.value - rec.value) < 1e-10:
                        obs_skipped += 1
                        continue

                    # Revision: update existing observation
                    prev_value = existing_obs.value
                    existing_obs.previous_value = prev_value
                    existing_obs.value = rec.value
                    existing_obs.change_absolute = round(rec.value - prev_value, 6)
                    if abs(prev_value) > 1e-10:
                        existing_obs.change_pct = round(
                            ((rec.value - prev_value) / abs(prev_value)) * 100, 4
                        )
                    existing_obs.revision_number += 1
                    existing_obs.fetch_timestamp = now
                    existing_obs.content_hash = content_hash
                    existing_obs.source_url = self.source_url
                    existing_obs.raw_record_id = record_id
                    existing_obs.normalization_run_id = norm_run_id
                    existing_obs.is_provisional = rec.is_provisional
                    obs_updated += 1
                else:
                    # New observation
                    obs = CanonicalObservationORM(
                        observation_id=f"obs-{rec.indicator_code}-{_uuid()[:8]}",
                        indicator_id=rec.indicator_id,
                        indicator_code=rec.indicator_code,
                        value=rec.value,
                        unit=rec.unit,
                        country=rec.country,
                        entity_id=rec.entity_id,
                        period_start=rec.period_start,
                        period_end=rec.period_end,
                        frequency=rec.frequency,
                        observation_date=rec.observation_date,
                        source_id=self.source_id,
                        source_url=self.source_url,
                        fetch_timestamp=now,
                        content_hash=content_hash,
                        raw_record_id=record_id,
                        normalization_run_id=norm_run_id,
                        confidence_score=rec.confidence_score,
                        confidence_method=rec.confidence_method,
                        is_provisional=rec.is_provisional,
                        revision_number=0,
                    )
                    self._session.add(obs)
                    obs_created += 1

            # Step 8: Finalize normalization run
            norm_end = _utcnow()
            norm_run.completed_at = norm_end
            norm_run.duration_seconds = (norm_end - norm_run.started_at).total_seconds()
            norm_run.status = "COMPLETED"
            norm_run.observations_created = obs_created
            norm_run.observations_updated = obs_updated
            norm_run.observations_skipped = obs_skipped
            norm_run.validation_errors = validation_errors
            norm_run.quality_gates_applied = quality_gates if quality_gates else None

            # Update raw record status
            raw_record.normalization_status = "COMPLETED" if validation_errors == 0 else "PARTIAL"

            # Step 9: Finalize fetch run
            fetch_end = _utcnow()
            fetch_run.completed_at = fetch_end
            fetch_run.duration_seconds = (fetch_end - fetch_run.started_at).total_seconds()
            fetch_run.status = "COMPLETED"
            fetch_run.records_fetched = result.records_fetched
            fetch_run.records_new = result.records_new
            fetch_run.records_duplicate = result.records_duplicate

            # Update source registry
            await self._update_source_registry(success=True)

            await self._session.flush()

            result.status = "COMPLETED" if validation_errors == 0 else "PARTIAL"
            result.observations_created = obs_created
            result.observations_updated = obs_updated
            result.observations_skipped = obs_skipped
            result.validation_errors = validation_errors

        except Exception as exc:
            logger.exception("Connector %s failed: %s", self.source_id, exc)
            result.status = "FAILED"
            result.error_message = str(exc)

            fetch_run.status = "FAILED"
            fetch_run.error_message = str(exc)[:2000]
            fetch_run.error_code = type(exc).__name__
            fetch_run.completed_at = _utcnow()
            if fetch_run.started_at:
                fetch_run.duration_seconds = (fetch_run.completed_at - fetch_run.started_at).total_seconds()

            await self._update_source_registry(success=False)
            await self._session.flush()

        return result

    # ── Helpers ───────────────────────────────────────────────────────────

    async def _find_existing_observation(
        self, indicator_code: str, country: str, period_start: date
    ) -> Optional[CanonicalObservationORM]:
        """Find the latest observation for this indicator+country+period."""
        stmt = (
            select(CanonicalObservationORM)
            .where(CanonicalObservationORM.indicator_code == indicator_code)
            .where(CanonicalObservationORM.country == country)
            .where(CanonicalObservationORM.period_start == period_start)
            .order_by(CanonicalObservationORM.revision_number.desc())
            .limit(1)
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def _update_source_registry(self, *, success: bool) -> None:
        """Update last_successful_fetch and consecutive_failures on the source."""
        stmt = select(SourceTruthRegistryORM).where(
            SourceTruthRegistryORM.source_id == self.source_id
        )
        result = await self._session.execute(stmt)
        source = result.scalar_one_or_none()
        if source is None:
            return
        if success:
            source.last_successful_fetch = _utcnow()
            source.consecutive_failures = 0
        else:
            source.consecutive_failures = (source.consecutive_failures or 0) + 1

    def _extract_period(self, raw_payload: Dict[str, Any]) -> tuple[date, date]:
        """Extract period_start and period_end from raw payload.

        Default: today. Subclasses override for source-specific logic.
        """
        today = date.today()
        return today, today
