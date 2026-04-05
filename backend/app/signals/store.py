"""signals.store — SQLite-backed persistence for the Live Signal Layer.

Uses Python's built-in sqlite3 via SQLAlchemy 2.0 (already in requirements.txt).
Zero new pip dependencies.

Tables:
    signal_records   — one row per ingested ScoredSignal (append-only)
    seed_records     — one row per ScenarioSeed (mutable: status/review updated in-place)
    run_records      — one row per pipeline run (metadata; source-of-truth for run state)
    run_result_records — one row per run result (large JSON blob, loaded on-demand)
    signal_audit_log — append-only audit trail for all lifecycle transitions

Source of truth for:
    - Which signals were received and scored
    - Which seeds were created, approved, rejected, or expired
    - Which pipeline runs were triggered, from which seed/signal
    - Full run metadata and result payloads
    - Every lifecycle transition with actor, reason, and timestamp

DB PATH CONFIGURATION
    Priority order (highest first):
        1. Explicit path passed to init_db(path=...)
        2. IO_SIGNAL_DB_PATH environment variable  (Settings env_prefix)
        3. SIGNAL_DB_PATH environment variable     (legacy / backward compat)
        4. Default: ./signals.db                   (cwd — works in dev + Docker WORKDIR /app)

    For Docker deployments, mount a durable volume at /data and set either:
        IO_SIGNAL_DB_PATH=/data/signals.db
    or pass the path explicitly in the lifespan hook.

    init_db() logs the active path at INFO level and emits a WARNING if the
    path appears ephemeral (starts with /tmp or /var/folders).  The system
    will not block on an ephemeral path — but the warning is real.

ENGINE LIFECYCLE
    The SQLAlchemy engine is created lazily inside init_db().
    All read/write helpers call _get_engine() which raises RuntimeError if
    init_db() has not been called.  This prevents silent no-op writes.
"""

from __future__ import annotations

import json
import logging
import os
from datetime import datetime, timezone, timedelta
from typing import Any

from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer, String, Text, text
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, declarative_base

logger = logging.getLogger(__name__)

# ── Lazy engine ───────────────────────────────────────────────────────────────

_engine = None
_DB_PATH: str | None = None
Base = declarative_base()


def _get_engine():
    if _engine is None:
        raise RuntimeError(
            "Signal store engine is not initialized. "
            "Call app.signals.store.init_db() during application startup."
        )
    return _engine


# ── ORM Models ────────────────────────────────────────────────────────────────

class SignalRecord(Base):
    """Persists one row per ingested ScoredSignal.  Append-only."""
    __tablename__ = "signal_records"

    signal_id       = Column(String(64),  primary_key=True)
    source          = Column(String(32),  nullable=False)
    sector          = Column(String(32),  nullable=False, index=True)
    event_type      = Column(String(128), nullable=False)
    severity_raw    = Column(Float,       nullable=False)
    confidence_raw  = Column(Float,       nullable=False)
    signal_score    = Column(Float,       nullable=True)
    lat             = Column(Float,       nullable=True)
    lng             = Column(Float,       nullable=True)
    description     = Column(Text,        nullable=False, default="")
    entity_ids_json = Column(Text,        nullable=False, default="[]")
    payload_json    = Column(Text,        nullable=False, default="{}")
    received_at     = Column(DateTime(timezone=True), nullable=False)
    created_at      = Column(DateTime(timezone=True), nullable=False)


class SeedRecord(Base):
    """Persists one row per ScenarioSeed.  Status/review fields updated in-place."""
    __tablename__ = "seed_records"

    seed_id                 = Column(String(64),  primary_key=True)
    signal_id               = Column(String(64),  nullable=False, index=True)
    sector                  = Column(String(32),  nullable=False, index=True)
    suggested_template_id   = Column(String(128), nullable=False)
    suggested_severity      = Column(Float,       nullable=False)
    suggested_horizon_hours = Column(Integer,     nullable=False)
    rationale               = Column(Text,        nullable=False)
    status                  = Column(String(32),  nullable=False, default="PENDING_REVIEW", index=True)
    created_at              = Column(DateTime(timezone=True), nullable=False)
    reviewed_by             = Column(String(256), nullable=True)
    reviewed_at             = Column(DateTime(timezone=True), nullable=True)
    review_reason           = Column(Text,        nullable=True)
    run_id                  = Column(String(64),  nullable=True)


class RunRecord(Base):
    """Persists run metadata for every pipeline run.

    Written immediately when a run starts (status=running) and updated on
    completion or failure.  Source of truth for run state after restart.
    Linked back to seed/signal via seed_id / signal_id (both nullable — runs
    created directly via POST /runs have no seed linkage).
    """
    __tablename__ = "run_records"

    run_id            = Column(String(64),  primary_key=True)
    scenario_id       = Column(String(128), nullable=False, index=True)
    status            = Column(String(32),  nullable=False, default="running", index=True)
    severity          = Column(Float,       nullable=True)
    horizon_hours     = Column(Integer,     nullable=True)
    label             = Column(Text,        nullable=True)
    seed_id           = Column(String(64),  nullable=True, index=True)
    signal_id         = Column(String(64),  nullable=True)
    reviewed_by       = Column(String(256), nullable=True)
    model_version     = Column(String(64),  nullable=True)
    stages_completed  = Column(Integer,     nullable=True)
    stages_total      = Column(Integer,     nullable=True, default=13)
    computed_in_ms    = Column(Float,       nullable=True)
    error             = Column(Text,        nullable=True)
    created_at        = Column(DateTime(timezone=True), nullable=False, index=True)
    completed_at      = Column(DateTime(timezone=True), nullable=True)


class RunResultRecord(Base):
    """Persists full pipeline result payload as a JSON blob.

    Stored separately from RunRecord to avoid loading large blobs during
    startup or status polls.  Loaded on-demand only when GET /runs/{id} is called.
    """
    __tablename__ = "run_result_records"

    run_id     = Column(String(64),  primary_key=True)
    result_json = Column(Text,       nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False)


class DecisionRecord(Base):
    """Persists one row per OperatorDecision. Status/outcome updated in-place.

    Source linkage: at least one of source_signal_id, source_seed_id, source_run_id
    should be non-null (enforced at the engine layer, not the DB level).
    """
    __tablename__ = "decision_records"

    decision_id      = Column(String(64),  primary_key=True)
    source_signal_id = Column(String(64),  nullable=True, index=True)
    source_seed_id   = Column(String(64),  nullable=True, index=True)
    source_run_id    = Column(String(64),  nullable=True, index=True)
    decision_type    = Column(String(32),  nullable=False, index=True)
    decision_status  = Column(String(32),  nullable=False, default="CREATED", index=True)
    decision_payload = Column(Text,        nullable=False, default="{}")
    rationale        = Column(Text,        nullable=True)
    confidence_score = Column(Float,       nullable=True)
    created_by       = Column(String(256), nullable=False)
    outcome_status   = Column(String(32),  nullable=False, default="PENDING")
    outcome_payload  = Column(Text,        nullable=False, default="{}")
    created_at       = Column(DateTime(timezone=True), nullable=False, index=True)
    updated_at       = Column(DateTime(timezone=True), nullable=False)
    closed_at        = Column(DateTime(timezone=True), nullable=True)


class OutcomeRecord(Base):
    """Persists one row per Outcome entity.  Status fields updated in-place.

    Source linkage: at least one of source_decision_id, source_run_id must be
    non-null (enforced at the engine layer).

    evidence_json stores structured evidence payload as a JSON blob.
    error_flag stored as 0/1 INTEGER (SQLite has no native bool).
    """
    __tablename__ = "outcome_records"

    outcome_id                 = Column(String(64),  primary_key=True)
    source_decision_id         = Column(String(64),  nullable=True, index=True)
    source_run_id              = Column(String(64),  nullable=True, index=True)
    source_signal_id           = Column(String(64),  nullable=True, index=True)
    source_seed_id             = Column(String(64),  nullable=True, index=True)
    outcome_status             = Column(String(32),  nullable=False, default="PENDING_OBSERVATION", index=True)
    outcome_classification     = Column(String(32),  nullable=True)
    observed_at                = Column(DateTime(timezone=True), nullable=True)
    recorded_at                = Column(DateTime(timezone=True), nullable=False, index=True)
    updated_at                 = Column(DateTime(timezone=True), nullable=False)
    closed_at                  = Column(DateTime(timezone=True), nullable=True)
    recorded_by                = Column(String(256), nullable=False)
    expected_value             = Column(Float,       nullable=True)
    realized_value             = Column(Float,       nullable=True)
    error_flag                 = Column(Integer,     nullable=False, default=0)
    time_to_resolution_secs    = Column(Integer,     nullable=True)
    evidence_json              = Column(Text,        nullable=False, default="{}")
    notes                      = Column(Text,        nullable=True)


class DecisionValueRecord(Base):
    """Persists one row per DecisionValue (ROI) computation.

    Each row is append-only in intent — recomputations write a NEW row rather
    than updating in-place, allowing full audit history of value changes.

    calculation_json stores the full calculation trace (inputs + formula steps)
    as a JSON blob, ensuring every computation is replayable.
    """
    __tablename__ = "decision_value_records"

    value_id               = Column(String(64),  primary_key=True)
    source_outcome_id      = Column(
        String(64),
        ForeignKey("outcome_records.outcome_id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    source_decision_id     = Column(String(64),  nullable=True, index=True)
    source_run_id          = Column(String(64),  nullable=True, index=True)
    computed_at            = Column(DateTime(timezone=True), nullable=False, index=True)
    computed_by            = Column(String(256), nullable=False)
    expected_value         = Column(Float,       nullable=True)
    realized_value         = Column(Float,       nullable=True)
    avoided_loss           = Column(Float,       nullable=False, default=0.0)
    operational_cost       = Column(Float,       nullable=False, default=0.0)
    decision_cost          = Column(Float,       nullable=False, default=0.0)
    latency_cost           = Column(Float,       nullable=False, default=0.0)
    total_cost             = Column(Float,       nullable=False, default=0.0)
    net_value              = Column(Float,       nullable=False, default=0.0)
    value_confidence_score = Column(Float,       nullable=False, default=0.0)
    value_classification   = Column(String(32),  nullable=False)
    calculation_json       = Column(Text,        nullable=False, default="{}")
    notes                  = Column(Text,        nullable=True)


class AuditEvent(Base):
    """Append-only audit trail.

    event_type vocabulary:
        signal.ingested         — raw signal received and scored
        seed.created            — ScenarioSeed created from ScoredSignal
        seed.approved           — operator approved seed, pipeline triggered
        seed.rejected           — operator rejected seed, no pipeline
        seed.expired            — seed TTL elapsed, auto-transitioned to EXPIRED
        seed.pipeline_failed    — pipeline raised after HITL approval
        seed.load_error         — recovery row failed to reconstruct on startup
        run.started             — pipeline run began
        run.completed           — pipeline run completed successfully
        run.failed              — pipeline run failed
        decision.created        — operator decision record created
        decision.executed       — decision executed (action taken)
        decision.failed         — decision execution failed
        decision.closed         — decision lifecycle closed
        outcome.created         — new Outcome entity recorded
        outcome.observed        — evidence observed for an Outcome
        outcome.confirmed       — Outcome confirmed with classification
        outcome.disputed        — Outcome classification disputed
        outcome.failed          — Outcome recording/observation failed
        outcome.closed          — Outcome lifecycle closed
        value.computed          — DecisionValue computed from an Outcome
        value.recomputed        — DecisionValue recomputed with updated inputs
    """
    __tablename__ = "signal_audit_log"

    id            = Column(Integer,     primary_key=True, autoincrement=True)
    event_type    = Column(String(64),  nullable=False, index=True)
    entity_id     = Column(String(64),  nullable=False, index=True)
    entity_kind   = Column(String(16),  nullable=False)
    actor         = Column(String(256), nullable=True)
    reason        = Column(Text,        nullable=True)
    metadata_json = Column(Text,        nullable=False, default="{}")
    created_at    = Column(DateTime(timezone=True), nullable=False, index=True)


# ── Ephemeral path detection ──────────────────────────────────────────────────

_EPHEMERAL_PREFIXES = ("/tmp", "/var/folders", "/private/var/folders")


def _is_ephemeral(path: str) -> bool:
    return any(path.startswith(p) for p in _EPHEMERAL_PREFIXES)


# ── Init (lazy — call once during app startup) ────────────────────────────────

def init_db(path: str | None = None) -> str:
    """Create SQLAlchemy engine, configure WAL, create all tables.

    Must be called once during application startup before any read/write
    helper is used.  Safe to call multiple times — subsequent calls are no-ops
    if the engine is already initialized (returns the active DB path).

    Args:
        path: explicit DB file path.  If None, resolves from env vars.

    Returns:
        The resolved DB file path (useful for startup logging).

    Env vars (first match wins):
        IO_SIGNAL_DB_PATH   — Settings-prefixed (preferred)
        SIGNAL_DB_PATH      — legacy / backward compat
        default: ./signals.db
    """
    global _engine, _DB_PATH

    if _engine is not None:
        return _DB_PATH  # already initialized

    resolved = (
        path
        or os.environ.get("IO_SIGNAL_DB_PATH")
        or os.environ.get("SIGNAL_DB_PATH")
        or "./signals.db"
    )
    _DB_PATH = resolved

    if _is_ephemeral(resolved):
        logger.warning(
            "SIGNAL STORE DURABILITY WARNING: DB path '%s' appears ephemeral. "
            "Data will be lost on container/host restart. "
            "Set IO_SIGNAL_DB_PATH to a mounted durable volume path (e.g. /data/signals.db).",
            resolved,
        )
    else:
        logger.info("signal store: DB path=%s", resolved)

    engine = create_engine(
        f"sqlite:///{resolved}",
        connect_args={"check_same_thread": False},
        echo=False,
    )

    # Register connection hook AFTER engine creation
    from sqlalchemy import event as sa_event

    @sa_event.listens_for(engine, "connect")
    def _on_connect(conn, _):
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA foreign_keys=ON")
        conn.execute("PRAGMA synchronous=NORMAL")

    Base.metadata.create_all(engine)
    _engine = engine

    logger.info("signal store: initialized (tables created/verified)")
    return _DB_PATH


# ── Internal helpers ──────────────────────────────────────────────────────────

def _now() -> datetime:
    return datetime.now(timezone.utc)


def _j(obj: Any) -> str:
    return json.dumps(obj, default=str)


def _with_session(fn) -> None:
    """Execute fn(db: Session) inside a commit/rollback guard."""
    with Session(_get_engine()) as db:
        try:
            fn(db)
            db.commit()
        except Exception:
            db.rollback()
            raise


# ── Signal persistence ────────────────────────────────────────────────────────

def save_signal(scored) -> None:
    """Persist a ScoredSignal and write signal.ingested audit event.  Idempotent."""
    sig = scored.signal
    now = _now()

    def _write(db: Session) -> None:
        db.execute(
            text(
                "INSERT OR IGNORE INTO signal_records "
                "(signal_id, source, sector, event_type, severity_raw, confidence_raw, "
                " signal_score, lat, lng, description, entity_ids_json, payload_json, "
                " received_at, created_at) "
                "VALUES (:sig_id, :src, :sec, :ev, :sev, :conf, :score, :lat, :lng, "
                "        :desc, :eids, :payload, :recv, :created)"
            ),
            {
                "sig_id":  sig.signal_id, "src": sig.source.value, "sec": sig.sector.value,
                "ev":      sig.event_type, "sev": sig.severity_raw, "conf": sig.confidence_raw,
                "score":   scored.signal_score, "lat": sig.lat, "lng": sig.lng,
                "desc":    sig.description, "eids": _j(sig.entity_ids),
                "payload": _j(sig.payload), "recv": sig.received_at, "created": now,
            },
        )
        db.add(AuditEvent(
            event_type    = "signal.ingested",
            entity_id     = sig.signal_id,
            entity_kind   = "signal",
            actor         = sig.source.value,
            metadata_json = _j({"sector": sig.sector.value, "event_type": sig.event_type,
                                 "signal_score": scored.signal_score}),
            created_at    = now,
        ))

    try:
        _with_session(_write)
    except Exception as exc:
        logger.error("store.save_signal FAILED signal_id=%s: %s", sig.signal_id, exc)


# ── Seed persistence ──────────────────────────────────────────────────────────

def save_seed(seed) -> None:
    """Persist a new PENDING_REVIEW ScenarioSeed and write seed.created audit event."""
    now = _now()

    def _write(db: Session) -> None:
        db.execute(
            text(
                "INSERT OR IGNORE INTO seed_records "
                "(seed_id, signal_id, sector, suggested_template_id, suggested_severity, "
                " suggested_horizon_hours, rationale, status, created_at, "
                " reviewed_by, reviewed_at, review_reason, run_id) "
                "VALUES (:sid, :sig_id, :sec, :tmpl, :sev, :horizon, :rat, :status, "
                "        :created, :rb, :rat2, :rr, :rid)"
            ),
            {
                "sid": seed.seed_id, "sig_id": seed.signal_id, "sec": seed.sector.value,
                "tmpl": seed.suggested_template_id, "sev": seed.suggested_severity,
                "horizon": seed.suggested_horizon_hours, "rat": seed.rationale,
                "status": seed.status.value, "created": seed.created_at,
                "rb": seed.reviewed_by, "rat2": seed.reviewed_at,
                "rr": seed.review_reason, "rid": None,
            },
        )
        db.add(AuditEvent(
            event_type    = "seed.created",
            entity_id     = seed.seed_id,
            entity_kind   = "seed",
            metadata_json = _j({"signal_id": seed.signal_id, "sector": seed.sector.value,
                                 "suggested_template_id": seed.suggested_template_id,
                                 "suggested_severity": seed.suggested_severity,
                                 "suggested_horizon_hours": seed.suggested_horizon_hours}),
            created_at    = now,
        ))

    try:
        _with_session(_write)
    except Exception as exc:
        logger.error("store.save_seed FAILED seed_id=%s: %s", seed.seed_id, exc)


def update_seed_approved(seed, run_id: str) -> None:
    """Set seed to APPROVED, link run_id, write seed.approved audit event."""
    now = _now()

    def _write(db: Session) -> None:
        db.execute(
            text(
                "UPDATE seed_records SET status=:status, reviewed_by=:rb, "
                "reviewed_at=:rat, review_reason=:rr, run_id=:rid WHERE seed_id=:sid"
            ),
            {"status": seed.status.value, "rb": seed.reviewed_by, "rat": seed.reviewed_at,
             "rr": seed.review_reason, "rid": run_id, "sid": seed.seed_id},
        )
        db.add(AuditEvent(
            event_type    = "seed.approved",
            entity_id     = seed.seed_id,
            entity_kind   = "seed",
            actor         = seed.reviewed_by,
            reason        = seed.review_reason,
            metadata_json = _j({"run_id": run_id, "sector": seed.sector.value,
                                 "suggested_template_id": seed.suggested_template_id,
                                 "signal_id": seed.signal_id}),
            created_at    = now,
        ))

    try:
        _with_session(_write)
    except Exception as exc:
        logger.error("store.update_seed_approved FAILED seed_id=%s run_id=%s: %s",
                     seed.seed_id, run_id, exc)


def update_seed_rejected(seed) -> None:
    """Set seed to REJECTED, write seed.rejected audit event."""
    now = _now()

    def _write(db: Session) -> None:
        db.execute(
            text(
                "UPDATE seed_records SET status=:status, reviewed_by=:rb, "
                "reviewed_at=:rat, review_reason=:rr WHERE seed_id=:sid"
            ),
            {"status": seed.status.value, "rb": seed.reviewed_by, "rat": seed.reviewed_at,
             "rr": seed.review_reason, "sid": seed.seed_id},
        )
        db.add(AuditEvent(
            event_type    = "seed.rejected",
            entity_id     = seed.seed_id,
            entity_kind   = "seed",
            actor         = seed.reviewed_by,
            reason        = seed.review_reason,
            metadata_json = _j({"sector": seed.sector.value, "signal_id": seed.signal_id}),
            created_at    = now,
        ))

    try:
        _with_session(_write)
    except Exception as exc:
        logger.error("store.update_seed_rejected FAILED seed_id=%s: %s", seed.seed_id, exc)


def expire_stale_seeds(now: datetime | None = None) -> list[str]:
    """Expire all PENDING_REVIEW seeds whose review window has elapsed.

    A seed expires when:  created_at + suggested_horizon_hours * 3600s <= now

    For each expired seed:
    - Updates seed_records.status → 'EXPIRED'
    - Writes a seed.expired audit event

    Returns:
        List of seed_ids that were transitioned to EXPIRED.

    This function is idempotent — re-running it with the same 'now' is safe.
    Seeds already in a terminal state (APPROVED, REJECTED, EXPIRED) are never touched.
    """
    cutoff = now or _now()

    try:
        with Session(_get_engine()) as db:
            # Find all seeds where created_at + horizon has passed
            rows = db.execute(
                text(
                    "SELECT seed_id, created_at, suggested_horizon_hours, sector, signal_id "
                    "FROM seed_records WHERE status='PENDING_REVIEW'"
                )
            ).fetchall()

            expired_ids: list[str] = []
            for row in rows:
                seed_id              = row.seed_id
                created_raw          = row.created_at
                horizon_hours        = row.suggested_horizon_hours

                # Parse created_at (may be string from SQLite)
                if isinstance(created_raw, str):
                    created_at = datetime.fromisoformat(
                        created_raw.replace("Z", "+00:00")
                    )
                else:
                    created_at = created_raw
                if created_at.tzinfo is None:
                    created_at = created_at.replace(tzinfo=timezone.utc)

                expiry_time = created_at + timedelta(hours=horizon_hours)
                if cutoff >= expiry_time:
                    expired_ids.append(seed_id)

            if not expired_ids:
                return []

            # Bulk update to EXPIRED
            for seed_id in expired_ids:
                db.execute(
                    text(
                        "UPDATE seed_records SET status='EXPIRED', reviewed_at=:now "
                        "WHERE seed_id=:sid AND status='PENDING_REVIEW'"
                    ),
                    {"now": cutoff, "sid": seed_id},
                )

            # Write audit events
            for i, seed_id in enumerate(expired_ids):
                row = next(r for r in rows if r.seed_id == seed_id)
                db.add(AuditEvent(
                    event_type    = "seed.expired",
                    entity_id     = seed_id,
                    entity_kind   = "seed",
                    actor         = None,
                    reason        = "Review window elapsed (horizon_hours TTL)",
                    metadata_json = _j({
                        "sector":                  row.sector,
                        "signal_id":               row.signal_id,
                        "suggested_horizon_hours": row.suggested_horizon_hours,
                        "expired_at":              cutoff.isoformat(),
                    }),
                    created_at    = cutoff,
                ))

            db.commit()

            logger.info("store.expire_stale_seeds: expired %d seeds", len(expired_ids))
            return expired_ids

    except Exception as exc:
        logger.error("store.expire_stale_seeds FAILED: %s", exc)
        return []


# ── Run persistence ───────────────────────────────────────────────────────────

def save_run(run_meta: dict) -> None:
    """Persist a run record (INSERT OR REPLACE — supports both create and update).

    run_meta must contain at minimum: run_id, scenario_id, status, created_at.
    Optional fields: severity, horizon_hours, label, seed_id, signal_id,
    reviewed_by, model_version, stages_completed, stages_total, computed_in_ms,
    error, completed_at.
    """
    now = _now()

    def _write(db: Session) -> None:
        db.execute(
            text(
                "INSERT OR REPLACE INTO run_records "
                "(run_id, scenario_id, status, severity, horizon_hours, label, "
                " seed_id, signal_id, reviewed_by, model_version, "
                " stages_completed, stages_total, computed_in_ms, error, "
                " created_at, completed_at) "
                "VALUES (:run_id, :scenario_id, :status, :severity, :horizon_hours, :label, "
                "        :seed_id, :signal_id, :reviewed_by, :model_version, "
                "        :stages_completed, :stages_total, :computed_in_ms, :error, "
                "        :created_at, :completed_at)"
            ),
            {
                "run_id":          run_meta["run_id"],
                "scenario_id":     run_meta.get("scenario_id", run_meta.get("template_id", "")),
                "status":          run_meta.get("status", "running"),
                "severity":        run_meta.get("severity"),
                "horizon_hours":   run_meta.get("horizon_hours"),
                "label":           run_meta.get("label"),
                "seed_id":         run_meta.get("seed_id"),
                "signal_id":       run_meta.get("signal_id"),
                "reviewed_by":     run_meta.get("reviewed_by"),
                "model_version":   run_meta.get("model_version"),
                "stages_completed": run_meta.get("stages_completed"),
                "stages_total":    run_meta.get("stages_total", 13),
                "computed_in_ms":  run_meta.get("computed_in_ms"),
                "error":           run_meta.get("error"),
                "created_at":      run_meta.get("created_at", now),
                "completed_at":    run_meta.get("completed_at"),
            },
        )
        # Audit event: run.started or run.completed / run.failed depending on status
        status = run_meta.get("status", "running")
        event_type = {
            "running":   "run.started",
            "completed": "run.completed",
            "failed":    "run.failed",
        }.get(status, f"run.{status}")
        db.add(AuditEvent(
            event_type    = event_type,
            entity_id     = run_meta["run_id"],
            entity_kind   = "run",
            actor         = run_meta.get("reviewed_by"),
            reason        = run_meta.get("error"),
            metadata_json = _j({
                "scenario_id":   run_meta.get("scenario_id"),
                "seed_id":       run_meta.get("seed_id"),
                "status":        status,
            }),
            created_at    = now,
        ))

    try:
        _with_session(_write)
    except Exception as exc:
        logger.error("store.save_run FAILED run_id=%s: %s", run_meta.get("run_id"), exc)


def save_run_result(run_id: str, result: dict) -> None:
    """Persist the full pipeline result payload for a run.

    Uses INSERT OR REPLACE — safe to call if a result already exists.
    The result dict is serialized to JSON TEXT.  No in-memory caching here.
    """
    now = _now()

    def _write(db: Session) -> None:
        db.execute(
            text(
                "INSERT OR REPLACE INTO run_result_records (run_id, result_json, created_at) "
                "VALUES (:run_id, :result_json, :created_at)"
            ),
            {"run_id": run_id, "result_json": _j(result), "created_at": now},
        )

    try:
        _with_session(_write)
    except Exception as exc:
        logger.error("store.save_run_result FAILED run_id=%s: %s", run_id, exc)


def load_run_by_id(run_id: str) -> dict | None:
    """Return run metadata dict from DB, or None if not found."""
    try:
        with Session(_get_engine()) as db:
            row = db.execute(
                text("SELECT * FROM run_records WHERE run_id=:rid"),
                {"rid": run_id},
            ).fetchone()
            return dict(row._mapping) if row else None
    except Exception as exc:
        logger.error("store.load_run_by_id FAILED run_id=%s: %s", run_id, exc)
        return None


def load_result_by_id(run_id: str) -> dict | None:
    """Return deserialized run result dict from DB, or None if not found."""
    try:
        with Session(_get_engine()) as db:
            row = db.execute(
                text("SELECT result_json FROM run_result_records WHERE run_id=:rid"),
                {"rid": run_id},
            ).fetchone()
            if row is None:
                return None
            return json.loads(row.result_json)
    except Exception as exc:
        logger.error("store.load_result_by_id FAILED run_id=%s: %s", run_id, exc)
        return None


def load_all_run_metadata(limit: int = 2000) -> list[dict]:
    """Return all run metadata rows (newest first) for startup cache warm-up.

    Deliberately does NOT load result payloads — those are large and loaded on demand.
    """
    try:
        with Session(_get_engine()) as db:
            rows = db.execute(
                text("SELECT * FROM run_records ORDER BY created_at DESC LIMIT :lim"),
                {"lim": limit},
            ).fetchall()
            return [dict(row._mapping) for row in rows]
    except Exception as exc:
        logger.error("store.load_all_run_metadata FAILED: %s", exc)
        return []


# ── Seed recovery ─────────────────────────────────────────────────────────────

def load_pending_seeds() -> list[dict]:
    """Return all PENDING_REVIEW seed rows for in-memory cache recovery."""
    try:
        with Session(_get_engine()) as db:
            rows = db.execute(
                text("SELECT * FROM seed_records WHERE status='PENDING_REVIEW' ORDER BY created_at")
            ).fetchall()
            return [dict(row._mapping) for row in rows]
    except Exception as exc:
        logger.error("store.load_pending_seeds FAILED: %s", exc)
        return []


def load_seed_by_id(seed_id: str) -> dict | None:
    """Return a single seed row by ID (any status), or None."""
    try:
        with Session(_get_engine()) as db:
            row = db.execute(
                text("SELECT * FROM seed_records WHERE seed_id=:sid"),
                {"sid": seed_id},
            ).fetchone()
            return dict(row._mapping) if row else None
    except Exception as exc:
        logger.error("store.load_seed_by_id FAILED seed_id=%s: %s", seed_id, exc)
        return None


# ── Audit query ───────────────────────────────────────────────────────────────

def write_audit(
    event_type: str,
    entity_id: str,
    entity_kind: str,
    actor: str | None,
    reason: str | None,
    metadata: dict[str, Any] | None = None,
) -> None:
    """Write a raw audit event.  Used for failure/error paths."""
    now = _now()

    def _write(db: Session) -> None:
        db.add(AuditEvent(
            event_type    = event_type,
            entity_id     = entity_id,
            entity_kind   = entity_kind,
            actor         = actor,
            reason        = reason,
            metadata_json = _j(metadata or {}),
            created_at    = now,
        ))

    try:
        _with_session(_write)
    except Exception as exc:
        logger.error("store.write_audit FAILED event=%s entity=%s: %s",
                     event_type, entity_id, exc)


def get_audit_log(
    entity_id: str | None = None,
    event_type: str | None = None,
    limit: int = 100,
) -> list[dict]:
    """Query the audit log.  Returns newest events first."""
    clauses: list[str] = []
    params: dict[str, Any] = {"lim": min(limit, 500)}

    if entity_id:
        clauses.append("entity_id = :entity_id")
        params["entity_id"] = entity_id
    if event_type:
        clauses.append("event_type = :event_type")
        params["event_type"] = event_type

    where = ("WHERE " + " AND ".join(clauses)) if clauses else ""
    sql = f"SELECT * FROM signal_audit_log {where} ORDER BY created_at DESC LIMIT :lim"

    try:
        with Session(_get_engine()) as db:
            rows = db.execute(text(sql), params).fetchall()
            result = []
            for row in rows:
                d = dict(row._mapping)
                try:
                    d["metadata"] = json.loads(d.get("metadata_json") or "{}")
                except Exception:
                    d["metadata"] = {}
                d.pop("metadata_json", None)
                result.append(d)
            return result
    except Exception as exc:
        logger.error("store.get_audit_log FAILED: %s", exc)
        return []


# ── Decision persistence ──────────────────────────────────────────────────────

def save_decision(decision_dict: dict) -> None:
    """Persist a new OperatorDecision (INSERT OR IGNORE — idempotent).

    Expects a dict with all OperatorDecision fields.
    Writes decision.created audit event on first insert.
    """
    now = _now()

    def _write(db: Session) -> None:
        existing = db.execute(
            text("SELECT decision_id FROM decision_records WHERE decision_id=:did"),
            {"did": decision_dict["decision_id"]},
        ).fetchone()

        if existing is None:
            db.execute(
                text(
                    "INSERT INTO decision_records "
                    "(decision_id, source_signal_id, source_seed_id, source_run_id, "
                    " decision_type, decision_status, decision_payload, rationale, "
                    " confidence_score, created_by, outcome_status, outcome_payload, "
                    " created_at, updated_at, closed_at) "
                    "VALUES (:did, :sig, :seed, :run, :dtype, :dstatus, :payload, "
                    "        :rationale, :conf, :actor, :ostatus, :opayload, "
                    "        :created, :updated, :closed)"
                ),
                {
                    "did":      decision_dict["decision_id"],
                    "sig":      decision_dict.get("source_signal_id"),
                    "seed":     decision_dict.get("source_seed_id"),
                    "run":      decision_dict.get("source_run_id"),
                    "dtype":    decision_dict["decision_type"],
                    "dstatus":  decision_dict.get("decision_status", "CREATED"),
                    "payload":  _j(decision_dict.get("decision_payload", {})),
                    "rationale": decision_dict.get("rationale"),
                    "conf":     decision_dict.get("confidence_score"),
                    "actor":    decision_dict["created_by"],
                    "ostatus":  decision_dict.get("outcome_status", "PENDING"),
                    "opayload": _j(decision_dict.get("outcome_payload", {})),
                    "created":  decision_dict.get("created_at", now),
                    "updated":  decision_dict.get("updated_at", now),
                    "closed":   decision_dict.get("closed_at"),
                },
            )
            db.add(AuditEvent(
                event_type    = "decision.created",
                entity_id     = decision_dict["decision_id"],
                entity_kind   = "decision",
                actor         = decision_dict.get("created_by"),
                reason        = decision_dict.get("rationale"),
                metadata_json = _j({
                    "decision_type":  decision_dict["decision_type"],
                    "source_signal":  decision_dict.get("source_signal_id"),
                    "source_seed":    decision_dict.get("source_seed_id"),
                    "source_run":     decision_dict.get("source_run_id"),
                }),
                created_at    = now,
            ))

    try:
        _with_session(_write)
    except Exception as exc:
        logger.error("store.save_decision FAILED decision_id=%s: %s",
                     decision_dict.get("decision_id"), exc)


def update_decision(decision_dict: dict, audit_event_type: str) -> None:
    """Update an existing decision record with new status/outcome fields.

    Writes an audit event with audit_event_type.
    decision_dict must include decision_id.
    """
    now = _now()

    def _write(db: Session) -> None:
        db.execute(
            text(
                "UPDATE decision_records SET "
                "decision_status=:dstatus, outcome_status=:ostatus, "
                "outcome_payload=:opayload, updated_at=:updated, closed_at=:closed "
                "WHERE decision_id=:did"
            ),
            {
                "dstatus":  decision_dict.get("decision_status"),
                "ostatus":  decision_dict.get("outcome_status"),
                "opayload": _j(decision_dict.get("outcome_payload", {})),
                "updated":  decision_dict.get("updated_at", now),
                "closed":   decision_dict.get("closed_at"),
                "did":      decision_dict["decision_id"],
            },
        )
        db.add(AuditEvent(
            event_type    = audit_event_type,
            entity_id     = decision_dict["decision_id"],
            entity_kind   = "decision",
            actor         = decision_dict.get("created_by"),
            reason        = decision_dict.get("rationale"),
            metadata_json = _j({
                "decision_type":   decision_dict.get("decision_type"),
                "decision_status": decision_dict.get("decision_status"),
                "outcome_status":  decision_dict.get("outcome_status"),
                "outcome_payload": decision_dict.get("outcome_payload", {}),
            }),
            created_at    = now,
        ))

    try:
        _with_session(_write)
    except Exception as exc:
        logger.error("store.update_decision FAILED decision_id=%s event=%s: %s",
                     decision_dict.get("decision_id"), audit_event_type, exc)


def load_decision_by_id(decision_id: str) -> dict | None:
    """Return decision row dict from DB, or None if not found."""
    try:
        with Session(_get_engine()) as db:
            row = db.execute(
                text("SELECT * FROM decision_records WHERE decision_id=:did"),
                {"did": decision_id},
            ).fetchone()
            if row is None:
                return None
            d = dict(row._mapping)
            d["decision_payload"] = json.loads(d.get("decision_payload") or "{}")
            d["outcome_payload"]  = json.loads(d.get("outcome_payload") or "{}")
            return d
    except Exception as exc:
        logger.error("store.load_decision_by_id FAILED decision_id=%s: %s", decision_id, exc)
        return None


def load_decisions(
    status: str | None = None,
    decision_type: str | None = None,
    limit: int = 100,
) -> list[dict]:
    """Return decision rows (newest first), optionally filtered by status and/or type."""
    clauses: list[str] = []
    params: dict = {"lim": min(limit, 500)}

    if status:
        clauses.append("decision_status = :status")
        params["status"] = status
    if decision_type:
        clauses.append("decision_type = :decision_type")
        params["decision_type"] = decision_type

    where = ("WHERE " + " AND ".join(clauses)) if clauses else ""
    sql = f"SELECT * FROM decision_records {where} ORDER BY created_at DESC LIMIT :lim"

    try:
        with Session(_get_engine()) as db:
            rows = db.execute(text(sql), params).fetchall()
            result = []
            for row in rows:
                d = dict(row._mapping)
                d["decision_payload"] = json.loads(d.get("decision_payload") or "{}")
                d["outcome_payload"]  = json.loads(d.get("outcome_payload") or "{}")
                result.append(d)
            return result
    except Exception as exc:
        logger.error("store.load_decisions FAILED: %s", exc)
        return []


# ── Outcome persistence ───────────────────────────────────────────────────────

def save_outcome(outcome_dict: dict) -> None:
    """Persist a new Outcome entity (INSERT OR IGNORE — idempotent).

    Writes outcome.created audit event on first insert.
    Expects a dict with all Outcome fields.
    """
    now = _now()

    def _write(db: Session) -> None:
        existing = db.execute(
            text("SELECT outcome_id FROM outcome_records WHERE outcome_id=:oid"),
            {"oid": outcome_dict["outcome_id"]},
        ).fetchone()

        if existing is None:
            db.execute(
                text(
                    "INSERT INTO outcome_records "
                    "(outcome_id, source_decision_id, source_run_id, source_signal_id, "
                    " source_seed_id, outcome_status, outcome_classification, "
                    " observed_at, recorded_at, updated_at, closed_at, recorded_by, "
                    " expected_value, realized_value, error_flag, "
                    " time_to_resolution_secs, evidence_json, notes) "
                    "VALUES (:oid, :dec, :run, :sig, :seed, :status, :cls, "
                    "        :obs, :rec, :upd, :closed, :actor, "
                    "        :exp, :real, :err, :ttr, :evid, :notes)"
                ),
                {
                    "oid":    outcome_dict["outcome_id"],
                    "dec":    outcome_dict.get("source_decision_id"),
                    "run":    outcome_dict.get("source_run_id"),
                    "sig":    outcome_dict.get("source_signal_id"),
                    "seed":   outcome_dict.get("source_seed_id"),
                    "status": outcome_dict.get("outcome_status", "PENDING_OBSERVATION"),
                    "cls":    outcome_dict.get("outcome_classification"),
                    "obs":    outcome_dict.get("observed_at"),
                    "rec":    outcome_dict.get("recorded_at", now),
                    "upd":    outcome_dict.get("updated_at", now),
                    "closed": outcome_dict.get("closed_at"),
                    "actor":  outcome_dict["recorded_by"],
                    "exp":    outcome_dict.get("expected_value"),
                    "real":   outcome_dict.get("realized_value"),
                    "err":    1 if outcome_dict.get("error_flag") else 0,
                    "ttr":    outcome_dict.get("time_to_resolution_seconds"),
                    "evid":   _j(outcome_dict.get("evidence_payload", {})),
                    "notes":  outcome_dict.get("notes"),
                },
            )
            db.add(AuditEvent(
                event_type    = "outcome.created",
                entity_id     = outcome_dict["outcome_id"],
                entity_kind   = "outcome",
                actor         = outcome_dict.get("recorded_by"),
                reason        = None,
                metadata_json = _j({
                    "source_decision_id": outcome_dict.get("source_decision_id"),
                    "source_run_id":      outcome_dict.get("source_run_id"),
                    "outcome_status":     outcome_dict.get("outcome_status", "PENDING_OBSERVATION"),
                }),
                created_at    = now,
            ))

    try:
        _with_session(_write)
    except Exception as exc:
        logger.error("store.save_outcome FAILED outcome_id=%s: %s",
                     outcome_dict.get("outcome_id"), exc)


def update_outcome(outcome_dict: dict, audit_event_type: str) -> None:
    """Update an existing Outcome record with new status/value fields.

    Writes an audit event with audit_event_type.
    outcome_dict must include outcome_id.
    """
    now = _now()

    def _write(db: Session) -> None:
        db.execute(
            text(
                "UPDATE outcome_records SET "
                "outcome_status=:status, outcome_classification=:cls, "
                "observed_at=:obs, updated_at=:upd, closed_at=:closed, "
                "realized_value=:real, error_flag=:err, "
                "time_to_resolution_secs=:ttr, evidence_json=:evid, notes=:notes "
                "WHERE outcome_id=:oid"
            ),
            {
                "status": outcome_dict.get("outcome_status"),
                "cls":    outcome_dict.get("outcome_classification"),
                "obs":    outcome_dict.get("observed_at"),
                "upd":    outcome_dict.get("updated_at", now),
                "closed": outcome_dict.get("closed_at"),
                "real":   outcome_dict.get("realized_value"),
                "err":    1 if outcome_dict.get("error_flag") else 0,
                "ttr":    outcome_dict.get("time_to_resolution_seconds"),
                "evid":   _j(outcome_dict.get("evidence_payload", {})),
                "notes":  outcome_dict.get("notes"),
                "oid":    outcome_dict["outcome_id"],
            },
        )
        db.add(AuditEvent(
            event_type    = audit_event_type,
            entity_id     = outcome_dict["outcome_id"],
            entity_kind   = "outcome",
            actor         = outcome_dict.get("recorded_by"),
            reason        = outcome_dict.get("notes"),
            metadata_json = _j({
                "outcome_status":         outcome_dict.get("outcome_status"),
                "outcome_classification": outcome_dict.get("outcome_classification"),
                "realized_value":         outcome_dict.get("realized_value"),
                "error_flag":             outcome_dict.get("error_flag", False),
            }),
            created_at    = now,
        ))

    try:
        _with_session(_write)
    except Exception as exc:
        logger.error("store.update_outcome FAILED outcome_id=%s event=%s: %s",
                     outcome_dict.get("outcome_id"), audit_event_type, exc)


def load_outcome_by_id(outcome_id: str) -> dict | None:
    """Return outcome row dict from DB, or None if not found."""
    try:
        with Session(_get_engine()) as db:
            row = db.execute(
                text("SELECT * FROM outcome_records WHERE outcome_id=:oid"),
                {"oid": outcome_id},
            ).fetchone()
            if row is None:
                return None
            d = dict(row._mapping)
            d["evidence_payload"] = json.loads(d.get("evidence_json") or "{}")
            d["error_flag"]       = bool(d.get("error_flag", 0))
            d.pop("evidence_json", None)
            return d
    except Exception as exc:
        logger.error("store.load_outcome_by_id FAILED outcome_id=%s: %s", outcome_id, exc)
        return None


def load_outcomes(
    decision_id: str | None = None,
    run_id:      str | None = None,
    status:      str | None = None,
    limit:       int        = 100,
) -> list[dict]:
    """Return outcome rows (newest first), optionally filtered."""
    clauses: list[str] = []
    params: dict = {"lim": min(limit, 500)}

    if decision_id:
        clauses.append("source_decision_id = :decision_id")
        params["decision_id"] = decision_id
    if run_id:
        clauses.append("source_run_id = :run_id")
        params["run_id"] = run_id
    if status:
        clauses.append("outcome_status = :status")
        params["status"] = status

    where = ("WHERE " + " AND ".join(clauses)) if clauses else ""
    sql = f"SELECT * FROM outcome_records {where} ORDER BY recorded_at DESC LIMIT :lim"

    try:
        with Session(_get_engine()) as db:
            rows = db.execute(text(sql), params).fetchall()
            result = []
            for row in rows:
                d = dict(row._mapping)
                d["evidence_payload"] = json.loads(d.get("evidence_json") or "{}")
                d["error_flag"]       = bool(d.get("error_flag", 0))
                d.pop("evidence_json", None)
                result.append(d)
            return result
    except Exception as exc:
        logger.error("store.load_outcomes FAILED: %s", exc)
        return []


# ── Decision Value (ROI) persistence ─────────────────────────────────────────

def save_value(value_dict: dict) -> None:
    """Persist a new DecisionValue (ROI) record.

    Uses INSERT OR IGNORE — idempotent on value_id.
    Writes value.computed audit event on first insert.
    Recomputations write a NEW row via a new value_id, not an update.
    """
    now = _now()

    def _write(db: Session) -> None:
        # Referential integrity guard — verify outcome exists before insert.
        # Defense-in-depth: engine._resolve_outcome() already validated this,
        # but this prevents orphan rows if save_value is called directly.
        outcome_ref = db.execute(
            text("SELECT outcome_id FROM outcome_records WHERE outcome_id=:oid"),
            {"oid": value_dict["source_outcome_id"]},
        ).fetchone()
        if outcome_ref is None:
            raise ValueError(
                f"Referential integrity violation: outcome {value_dict['source_outcome_id']!r} "
                "does not exist. Cannot persist value row."
            )

        existing = db.execute(
            text("SELECT value_id FROM decision_value_records WHERE value_id=:vid"),
            {"vid": value_dict["value_id"]},
        ).fetchone()

        if existing is None:
            db.execute(
                text(
                    "INSERT INTO decision_value_records "
                    "(value_id, source_outcome_id, source_decision_id, source_run_id, "
                    " computed_at, computed_by, expected_value, realized_value, "
                    " avoided_loss, operational_cost, decision_cost, latency_cost, "
                    " total_cost, net_value, value_confidence_score, "
                    " value_classification, calculation_json, notes) "
                    "VALUES (:vid, :oid, :did, :rid, :cat, :cby, :exp, :real, "
                    "        :avl, :opc, :dec, :lat, :tot, :net, :conf, "
                    "        :cls, :trace, :notes)"
                ),
                {
                    "vid":   value_dict["value_id"],
                    "oid":   value_dict["source_outcome_id"],
                    "did":   value_dict.get("source_decision_id"),
                    "rid":   value_dict.get("source_run_id"),
                    "cat":   value_dict.get("computed_at", now),
                    "cby":   value_dict["computed_by"],
                    "exp":   value_dict.get("expected_value"),
                    "real":  value_dict.get("realized_value"),
                    "avl":   value_dict.get("avoided_loss", 0.0),
                    "opc":   value_dict.get("operational_cost", 0.0),
                    "dec":   value_dict.get("decision_cost", 0.0),
                    "lat":   value_dict.get("latency_cost", 0.0),
                    "tot":   value_dict.get("total_cost", 0.0),
                    "net":   value_dict["net_value"],
                    "conf":  value_dict.get("value_confidence_score", 0.0),
                    "cls":   value_dict["value_classification"],
                    "trace": _j(value_dict.get("calculation_trace", {})),
                    "notes": value_dict.get("notes"),
                },
            )
            audit_event = value_dict.get("_audit_event_type", "value.computed")
            db.add(AuditEvent(
                event_type    = audit_event,
                entity_id     = value_dict["value_id"],
                entity_kind   = "value",
                actor         = value_dict["computed_by"],
                reason        = value_dict.get("notes"),
                metadata_json = _j({
                    "source_outcome_id":  value_dict["source_outcome_id"],
                    "source_decision_id": value_dict.get("source_decision_id"),
                    "net_value":          value_dict["net_value"],
                    "value_classification": value_dict["value_classification"],
                    "value_confidence_score": value_dict.get("value_confidence_score", 0.0),
                }),
                created_at    = now,
            ))

    try:
        _with_session(_write)
    except ValueError as exc:
        # Re-raise ValueError — referential integrity violations must propagate
        # so callers (engine._compute) know the save failed.
        logger.error("store.save_value INTEGRITY VIOLATION value_id=%s: %s",
                     value_dict.get("value_id"), exc)
        raise
    except Exception as exc:
        logger.error("store.save_value FAILED value_id=%s: %s",
                     value_dict.get("value_id"), exc)


def load_value_by_id(value_id: str) -> dict | None:
    """Return decision_value_records row dict, or None if not found."""
    try:
        with Session(_get_engine()) as db:
            row = db.execute(
                text("SELECT * FROM decision_value_records WHERE value_id=:vid"),
                {"vid": value_id},
            ).fetchone()
            if row is None:
                return None
            d = dict(row._mapping)
            d["calculation_trace"] = json.loads(d.get("calculation_json") or "{}")
            d.pop("calculation_json", None)
            return d
    except Exception as exc:
        logger.error("store.load_value_by_id FAILED value_id=%s: %s", value_id, exc)
        return None


def load_values(
    outcome_id:  str | None = None,
    decision_id: str | None = None,
    run_id:      str | None = None,
    limit:       int        = 100,
) -> list[dict]:
    """Return decision_value_records rows (newest first), optionally filtered."""
    clauses: list[str] = []
    params: dict = {"lim": min(limit, 500)}

    if outcome_id:
        clauses.append("source_outcome_id = :outcome_id")
        params["outcome_id"] = outcome_id
    if decision_id:
        clauses.append("source_decision_id = :decision_id")
        params["decision_id"] = decision_id
    if run_id:
        clauses.append("source_run_id = :run_id")
        params["run_id"] = run_id

    where = ("WHERE " + " AND ".join(clauses)) if clauses else ""
    sql = f"SELECT * FROM decision_value_records {where} ORDER BY computed_at DESC LIMIT :lim"

    try:
        with Session(_get_engine()) as db:
            rows = db.execute(text(sql), params).fetchall()
            result = []
            for row in rows:
                d = dict(row._mapping)
                d["calculation_trace"] = json.loads(d.get("calculation_json") or "{}")
                d.pop("calculation_json", None)
                result.append(d)
            return result
    except Exception as exc:
        logger.error("store.load_values FAILED: %s", exc)
        return []
