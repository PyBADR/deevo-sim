"""
Impact Observatory | مرصد الأثر — Quarantine Store

SQLite-backed quarantine for rejected TrustedEventContract records.

Design
------
- Uses Python's built-in sqlite3 (no new pip dependencies).
- Same SQLAlchemy 2.0 pattern as app/signals/store.py for consistency.
- Separate database file (trust_quarantine.db) to keep concerns isolated.
  The existing signals.db is not modified.
- Append-only: quarantined records are never updated; reprocessing creates
  a new record with status "reprocessed".
- All fields needed for later reprocessing are stored:
    raw_payload, normalized_payload (if available), error reasons,
    source, domain, event_id, timestamps.

DB PATH CONFIGURATION
    Priority order (highest first):
        1. Explicit path passed to init_quarantine_db(path=...)
        2. TRUST_QUARANTINE_DB_PATH environment variable
        3. Default: ./trust_quarantine.db (cwd — works in dev + Docker WORKDIR /app)

Reprocessing support
--------------------
    load_quarantine(source=None, domain=None, status="quarantined")
    Returns list[dict] of quarantined records matching filters.
    The orchestrator can reload and replay these through run_pipeline().
"""

from __future__ import annotations

import json
import logging
import os
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import (
    Column, DateTime, Integer, String, Text,
    create_engine, text,
)
from sqlalchemy.orm import Session, declarative_base

logger = logging.getLogger(__name__)

_engine = None
_DB_PATH: str | None = None
Base = declarative_base()


# ── ORM Model ─────────────────────────────────────────────────────────────────

class QuarantineRecord(Base):
    """One row per quarantined TrustedEventContract. Append-only."""
    __tablename__ = "quarantine_records"

    id                  = Column(Integer, primary_key=True, autoincrement=True)
    event_id            = Column(String(64),  nullable=False, index=True)
    source              = Column(String(64),  nullable=False, index=True)
    domain              = Column(String(64),  nullable=False, index=True)
    quarantined_at      = Column(DateTime,    nullable=False, index=True)
    event_timestamp     = Column(DateTime,    nullable=True)
    error_reasons       = Column(Text,        nullable=False)   # JSON list[str]
    raw_payload         = Column(Text,        nullable=False)   # JSON dict
    normalized_payload  = Column(Text,        nullable=False)   # JSON dict (may be {})
    impact_score        = Column(Text,        nullable=True)    # str(float) or NULL
    confidence          = Column(Text,        nullable=True)    # str(float) or NULL
    status              = Column(String(32),  nullable=False, default="quarantined", index=True)
    # "quarantined" | "reprocessed" | "dismissed"
    pipeline_run_id     = Column(String(64),  nullable=True)    # Links to orchestrator run


# ── Lifecycle ─────────────────────────────────────────────────────────────────

def _get_engine():
    if _engine is None:
        raise RuntimeError(
            "Quarantine store engine is not initialized. "
            "Call data_trust.quarantine.store.init_quarantine_db() during startup."
        )
    return _engine


def init_quarantine_db(path: Optional[str] = None) -> str:
    """
    Initialize the quarantine SQLite database and create tables.

    Call once during application startup (e.g. in main.py lifespan).

    Parameters
    ----------
    path : str, optional
        Explicit file path for the SQLite database.
        If None, uses TRUST_QUARANTINE_DB_PATH env var or ./trust_quarantine.db.

    Returns
    -------
    str
        Resolved database path (for logging).
    """
    global _engine, _DB_PATH

    resolved = (
        path
        or os.environ.get("TRUST_QUARANTINE_DB_PATH")
        or "trust_quarantine.db"
    )
    _DB_PATH = resolved

    if resolved.startswith(("/tmp", "/var/folders")):
        logger.warning(
            "Quarantine DB at ephemeral path %s — data will not survive container restart",
            resolved,
        )

    _engine = create_engine(
        f"sqlite:///{resolved}",
        connect_args={"check_same_thread": False},
        echo=False,
    )
    Base.metadata.create_all(_engine)
    logger.info("Quarantine DB initialized at %s", resolved)
    return resolved


# ── Write ─────────────────────────────────────────────────────────────────────

def quarantine_record(
    *,
    event_id:           str,
    source:             str,
    domain:             str,
    event_timestamp:    Optional[datetime],
    error_reasons:      list[str],
    raw_payload:        dict,
    normalized_payload: dict,
    impact_score:       Optional[float] = None,
    confidence:         Optional[float] = None,
    pipeline_run_id:    Optional[str]   = None,
) -> int:
    """
    Write a rejected record to the quarantine store.

    Parameters
    ----------
    event_id            Unique ID from TrustedEventContract.event_id
    source              Source identifier (e.g. "government_open_data")
    domain              Business domain (e.g. "government")
    event_timestamp     Original event timestamp (from contract.timestamp)
    error_reasons       List of validation error strings from validator
    raw_payload         Original unmodified payload from source
    normalized_payload  Adapter-normalized payload (may be {} if normalization failed)
    impact_score        If populated by adapter
    confidence          If populated by scorer before quarantine
    pipeline_run_id     Orchestrator run ID for traceability

    Returns
    -------
    int
        Auto-incremented row ID of the quarantine record.
    """
    now = datetime.now(timezone.utc)

    try:
        engine = _get_engine()
    except RuntimeError:
        # Store not initialized — init lazily with default path
        logger.warning(
            "Quarantine store was not pre-initialized. Initializing now with default path."
        )
        init_quarantine_db()
        engine = _get_engine()

    record = QuarantineRecord(
        event_id           = event_id,
        source             = source,
        domain             = domain,
        quarantined_at     = now,
        event_timestamp    = event_timestamp,
        error_reasons      = json.dumps(error_reasons),
        raw_payload        = json.dumps(raw_payload, default=str),
        normalized_payload = json.dumps(normalized_payload, default=str),
        impact_score       = str(impact_score) if impact_score is not None else None,
        confidence         = str(confidence)   if confidence  is not None else None,
        status             = "quarantined",
        pipeline_run_id    = pipeline_run_id,
    )

    with Session(engine) as session:
        session.add(record)
        session.commit()
        row_id = record.id
        logger.info(
            "Quarantined event_id=%s source=%s domain=%s errors=%d row_id=%d",
            event_id, source, domain, len(error_reasons), row_id,
        )
        return row_id


# ── Read ──────────────────────────────────────────────────────────────────────

def load_quarantine(
    source: Optional[str] = None,
    domain: Optional[str] = None,
    status: str = "quarantined",
    limit:  int = 500,
) -> list[dict]:
    """
    Load quarantined records for review or reprocessing.

    Parameters
    ----------
    source : str, optional
        Filter by source identifier.
    domain : str, optional
        Filter by domain.
    status : str
        "quarantined" | "reprocessed" | "dismissed" | all (pass empty string)
    limit : int
        Maximum records to return (default 500).

    Returns
    -------
    list[dict]
        Each dict contains all columns of QuarantineRecord plus:
        - error_reasons_parsed: list[str]
        - raw_payload_parsed: dict
        - normalized_payload_parsed: dict
    """
    try:
        engine = _get_engine()
    except RuntimeError:
        logger.warning("Quarantine store not initialized; returning empty list")
        return []

    with Session(engine) as session:
        query = session.query(QuarantineRecord)
        if source:
            query = query.filter(QuarantineRecord.source == source)
        if domain:
            query = query.filter(QuarantineRecord.domain == domain)
        if status:
            query = query.filter(QuarantineRecord.status == status)
        records = query.order_by(QuarantineRecord.quarantined_at.desc()).limit(limit).all()

    results = []
    for r in records:
        results.append({
            "id":                       r.id,
            "event_id":                 r.event_id,
            "source":                   r.source,
            "domain":                   r.domain,
            "quarantined_at":           r.quarantined_at.isoformat() if r.quarantined_at else None,
            "event_timestamp":          r.event_timestamp.isoformat() if r.event_timestamp else None,
            "error_reasons":            r.error_reasons,
            "error_reasons_parsed":     _safe_json(r.error_reasons, []),
            "raw_payload":              r.raw_payload,
            "raw_payload_parsed":       _safe_json(r.raw_payload, {}),
            "normalized_payload":       r.normalized_payload,
            "normalized_payload_parsed": _safe_json(r.normalized_payload, {}),
            "impact_score":             float(r.impact_score) if r.impact_score else None,
            "confidence":               float(r.confidence)   if r.confidence   else None,
            "status":                   r.status,
            "pipeline_run_id":          r.pipeline_run_id,
        })
    return results


def _safe_json(value: Optional[str], default):
    """Parse JSON string; return default on failure."""
    if not value:
        return default
    try:
        return json.loads(value)
    except (json.JSONDecodeError, TypeError):
        return default
