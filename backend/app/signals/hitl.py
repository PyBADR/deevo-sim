"""signals.hitl — Human-in-the-Loop adapter for the Live Signal Layer.

This is the ONLY place in the live signal layer that calls run_unified_pipeline().
A human operator (ADMIN or OPERATOR role) must approve a seed explicitly.
No automation, no background job, no retry, no queue.

Lifecycle:
    submit(scored_signal)
        → generates ScenarioSeed via seed_generator.generate()
        → persists signal + seed to SQLite (store.py)
        → caches seed in _pending dict (PENDING_REVIEW)
        → returns seed

    approve(seed_id, reviewed_by, reason=None)
        → retrieves seed from _pending (falls back to DB if missing from cache)
        → validates: must be PENDING_REVIEW
        → transitions seed: PENDING_REVIEW → APPROVED
        → calls run_unified_pipeline() — the ONLY call site in this layer
        → persists approval + run_id to store (audit event written)
        → stores run result in the canonical run/result stores from runs.py
        → moves seed from _pending to _reviewed
        → returns ApproveResult(seed, run_id, run_result)

    reject(seed_id, reviewed_by, reason=None)
        → retrieves seed from _pending
        → transitions seed: PENDING_REVIEW → REJECTED
        → persists rejection to store (audit event written)
        → moves seed from _pending to _reviewed
        → returns rejected ScenarioSeed

State transition guard matrix:
    PENDING_REVIEW → APPROVED    (via approve())  ✓ allowed
    PENDING_REVIEW → REJECTED    (via reject())   ✓ allowed
    APPROVED       → any         HITLError         ✗ blocked
    REJECTED       → any         HITLError         ✗ blocked
    EXPIRED        → any         HITLError         ✗ blocked

PERSISTENCE MODEL
    Source of truth:  SQLite via store.py (survives process restart)
    In-memory cache:  _pending / _reviewed dicts (fast lookup, rebuilt on startup)
    Recovery:         load_pending_from_db() must be called during app lifespan startup

AUDIT TRAIL
    Every state transition writes an audit event via store.write_audit() or
    the dedicated update_* helpers.  Failure paths (pipeline error) also write
    an audit event before raising.
"""

from __future__ import annotations

import uuid
import logging
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

from app.domain.models.live_signal import ScenarioSeed, ScoredSignal, SeedStatus, SignalSector
from app.signals import seed_generator

logger = logging.getLogger(__name__)


# ── In-memory cache (not source of truth — see store.py) ─────────────────────

_pending:  dict[str, ScenarioSeed] = {}   # PENDING_REVIEW seeds
_reviewed: dict[str, ScenarioSeed] = {}   # APPROVED | REJECTED seeds


# ── Result type ───────────────────────────────────────────────────────────────

@dataclass(frozen=True)
class ApproveResult:
    """Returned by approve() — carries the approved seed and the run_id."""
    seed:       ScenarioSeed
    run_id:     str
    run_result: dict[str, Any]


# ── Exception ─────────────────────────────────────────────────────────────────

class HITLError(ValueError):
    """Raised for invalid HITL operations (bad transition, not found, etc.)."""


# ── Transition guard ──────────────────────────────────────────────────────────

_VALID_TRANSITIONS: dict[SeedStatus, set[SeedStatus]] = {
    SeedStatus.PENDING_REVIEW: {SeedStatus.APPROVED, SeedStatus.REJECTED},
    SeedStatus.APPROVED:       set(),   # terminal
    SeedStatus.REJECTED:       set(),   # terminal
    SeedStatus.EXPIRED:        set(),   # terminal
}


def _assert_transition(seed: ScenarioSeed, target: SeedStatus) -> None:
    """Raise HITLError if the seed→target transition is not permitted."""
    if target not in _VALID_TRANSITIONS.get(seed.status, set()):
        raise HITLError(
            f"Seed {seed.seed_id}: transition {seed.status.value} → {target.value} is not allowed. "
            f"Current status is {seed.status.value}."
        )


# ── Public API ────────────────────────────────────────────────────────────────

def submit(scored: ScoredSignal) -> ScenarioSeed:
    """Generate a ScenarioSeed from a ScoredSignal, persist it, and queue for review.

    No pipeline run is triggered here.

    Raises:
        seed_generator.SeedGenerationError: if the signal cannot produce a seed.
    """
    seed = seed_generator.generate(scored)

    # Persist signal + seed BEFORE caching (store failure logged, never raises)
    from app.signals import store
    store.save_signal(scored)
    store.save_seed(seed)

    # Cache for fast lookup
    _pending[seed.seed_id] = seed

    logger.info(
        "hitl.submit seed_id=%s template=%s sector=%s signal_score=%.3f",
        seed.seed_id,
        seed.suggested_template_id,
        seed.sector.value,
        scored.signal_score,
    )
    return seed


def approve(
    seed_id:     str,
    reviewed_by: str,
    reason:      str | None = None,
) -> ApproveResult:
    """Approve a pending seed and synchronously execute the pipeline.

    This is the ONLY call site for run_unified_pipeline() in the live signal layer.

    Args:
        seed_id:     ID of the ScenarioSeed to approve.
        reviewed_by: identity of the approving operator.
        reason:      optional approval note, preserved in provenance.

    Returns:
        ApproveResult with the approved seed, run_id, and full run_result.

    Raises:
        HITLError: seed not found, invalid transition, or pipeline execution fails.
    """
    seed = _resolve_seed(seed_id, for_action="approve")
    _assert_transition(seed, SeedStatus.APPROVED)

    # Transition → APPROVED (immutable model_copy)
    approved_seed = seed.approve(reviewed_by=reviewed_by, reason=reason)

    # Build pipeline kwargs — raises ValueError if seed is not APPROVED (belt-and-suspenders)
    kwargs = approved_seed.to_pipeline_kwargs()

    # Execute pipeline — synchronous, blocking
    try:
        from app.simulation.runner import run_unified_pipeline
        result = run_unified_pipeline(
            template_id=kwargs["template_id"],
            severity=kwargs["severity"],
            horizon_hours=kwargs["horizon_hours"],
            label=kwargs["label"],
        )
    except Exception as exc:
        # Audit the failure before raising — the seed stays in PENDING in the cache
        # (approved_seed is a local copy; _pending[seed_id] is unchanged).
        from app.signals import store
        store.write_audit(
            event_type  = "seed.pipeline_failed",
            entity_id   = seed_id,
            entity_kind = "seed",
            actor       = reviewed_by,
            reason      = f"Pipeline exception: {exc}",
            metadata    = {
                "template_id": kwargs["template_id"],
                "severity":    kwargs["severity"],
                "error":       str(exc),
            },
        )
        logger.error("hitl.approve pipeline failed seed_id=%s: %s", seed_id, exc)
        raise HITLError(f"Pipeline execution failed for seed {seed_id}: {exc}") from exc

    # Assign canonical run_id and annotate with seed provenance
    run_id = str(uuid.uuid4())
    result["run_id"]       = run_id
    result["seed_id"]      = approved_seed.seed_id
    result["seed_sector"]  = approved_seed.sector.value
    result["reviewed_by"]  = approved_seed.reviewed_by

    # Store in the canonical run + result stores (same dicts used by POST /runs)
    now = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    run_meta = {
        "run_id":           run_id,
        "scenario_id":      kwargs["template_id"],
        "status":           result.get("status", "completed"),
        "severity":         kwargs.get("severity"),
        "horizon_hours":    kwargs.get("horizon_hours"),
        "label":            kwargs.get("label", ""),
        "seed_id":          approved_seed.seed_id,
        "signal_id":        approved_seed.signal_id,
        "reviewed_by":      approved_seed.reviewed_by,
        "stages_completed": result.get("stages_completed", 0),
        "stages_total":     13,
        "computed_in_ms":   result.get("duration_ms"),
        "created_at":       now,
        "completed_at":     now,
    }

    try:
        from app.api.v1.routes.runs import get_run_store, get_result_store
        get_run_store()[run_id]    = run_meta
        get_result_store()[run_id] = result
    except Exception as exc:
        logger.error("hitl.approve run store write failed seed_id=%s: %s", seed_id, exc)
        raise HITLError(f"Failed to write run for seed {seed_id}: {exc}") from exc

    # Persist run metadata + result to SQLite (fire-and-forget — store functions log errors)
    from app.signals import store
    store.save_run(run_meta)
    store.save_run_result(run_id, result)

    # Persist approval + run_id linkage to SQLite (audit event included)
    from app.signals import store
    store.update_seed_approved(approved_seed, run_id)

    # Move seed from pending → reviewed in cache
    _pending.pop(seed_id, None)
    _reviewed[approved_seed.seed_id] = approved_seed

    logger.info(
        "hitl.approve seed_id=%s run_id=%s reviewed_by=%s",
        approved_seed.seed_id, run_id, reviewed_by,
    )
    return ApproveResult(seed=approved_seed, run_id=run_id, run_result=result)


def reject(
    seed_id:     str,
    reviewed_by: str,
    reason:      str | None = None,
) -> ScenarioSeed:
    """Reject a pending seed.  No pipeline run is triggered.

    Raises:
        HITLError: seed not found or invalid transition.
    """
    seed = _resolve_seed(seed_id, for_action="reject")
    _assert_transition(seed, SeedStatus.REJECTED)

    rejected_seed = seed.reject(reviewed_by=reviewed_by, reason=reason)

    # Persist rejection to SQLite (audit event included)
    from app.signals import store
    store.update_seed_rejected(rejected_seed)

    # Move seed from pending → reviewed in cache
    _pending.pop(seed_id, None)
    _reviewed[rejected_seed.seed_id] = rejected_seed

    logger.info(
        "hitl.reject seed_id=%s reviewed_by=%s reason=%r",
        rejected_seed.seed_id, reviewed_by, reason,
    )
    return rejected_seed


# ── Query helpers ─────────────────────────────────────────────────────────────

def get_seed(seed_id: str) -> ScenarioSeed | None:
    """Return a seed from cache.  Falls back to DB if not in either dict."""
    if seed_id in _pending:
        return _pending[seed_id]
    if seed_id in _reviewed:
        return _reviewed[seed_id]
    # DB fallback (handles seeds from prior process lifecycle)
    return _load_seed_from_db(seed_id)


def list_pending() -> list[ScenarioSeed]:
    return list(_pending.values())


def list_reviewed() -> list[ScenarioSeed]:
    return list(_reviewed.values())


# ── Startup recovery ──────────────────────────────────────────────────────────

def reconcile_expired_seeds() -> list[str]:
    """Expire stale seeds in DB and evict them from the _pending cache.

    A seed is expired when: created_at + suggested_horizon_hours * 3600s <= now

    This function is idempotent and safe to call at any time (startup, periodic).
    It does NOT raise — failures are logged and an empty list is returned.

    Returns:
        List of seed_ids that were transitioned to EXPIRED.
    """
    from app.signals import store as _store
    try:
        expired_ids = _store.expire_stale_seeds()
    except Exception as exc:
        logger.error("hitl.reconcile_expired_seeds: store call failed: %s", exc)
        return []

    evicted = 0
    for seed_id in expired_ids:
        if seed_id in _pending:
            _pending.pop(seed_id)
            evicted += 1

    if expired_ids:
        logger.info(
            "hitl.reconcile_expired_seeds: expired=%d seeds in DB, evicted=%d from cache",
            len(expired_ids), evicted,
        )
    return expired_ids


def load_pending_from_db() -> None:
    """Reconstruct _pending from the persistent store.

    Must be called during app lifespan startup AFTER store.init_db().
    Any rows that cannot be reconstructed are logged and skipped; a
    seed.load_error audit event is written for each failed row.
    """
    from app.signals import store
    rows = store.load_pending_seeds()
    loaded = 0
    failed = 0

    for row in rows:
        sid = row.get("seed_id", "unknown")
        try:
            seed = _row_to_seed(row)
            _pending[seed.seed_id] = seed
            loaded += 1
        except Exception as exc:
            failed += 1
            logger.error(
                "hitl.load_pending_from_db: could not reconstruct seed_id=%s: %s",
                sid, exc,
            )
            store.write_audit(
                event_type  = "seed.load_error",
                entity_id   = sid,
                entity_kind = "seed",
                actor       = None,
                reason      = str(exc),
                metadata    = {"row": {k: str(v) for k, v in row.items()}},
            )

    logger.info(
        "hitl: startup recovery — loaded=%d failed=%d pending seeds from DB",
        loaded, failed,
    )


# ── Internal helpers ──────────────────────────────────────────────────────────

def _resolve_seed(seed_id: str, *, for_action: str) -> ScenarioSeed:
    """Return seed from cache, raising HITLError with a precise message if missing or terminal."""
    if seed_id in _pending:
        return _pending[seed_id]

    # Check reviewed cache for a precise error message
    if seed_id in _reviewed:
        existing = _reviewed[seed_id]
        raise HITLError(
            f"Seed {seed_id} was already {existing.status.value} "
            f"by {existing.reviewed_by} — cannot {for_action} again."
        )

    # DB fallback: seed may have been loaded into _reviewed from a prior session
    db_seed = _load_seed_from_db(seed_id)
    if db_seed is not None:
        if db_seed.status != SeedStatus.PENDING_REVIEW:
            raise HITLError(
                f"Seed {seed_id} has status {db_seed.status.value} in the persistent store "
                f"— cannot {for_action}."
            )
        # Re-add to _pending cache for this request
        _pending[seed_id] = db_seed
        return db_seed

    raise HITLError(f"Seed {seed_id} not found (checked cache and persistent store).")


def _load_seed_from_db(seed_id: str) -> ScenarioSeed | None:
    """Load a seed from the persistent store and reconstruct as ScenarioSeed."""
    from app.signals import store
    row = store.load_seed_by_id(seed_id)
    if row is None:
        return None
    try:
        return _row_to_seed(row)
    except Exception as exc:
        logger.error("hitl._load_seed_from_db: could not reconstruct seed_id=%s: %s", seed_id, exc)
        return None


def _row_to_seed(row: dict) -> ScenarioSeed:
    """Reconstruct a ScenarioSeed from a DB row dict."""
    return ScenarioSeed(
        seed_id                  = row["seed_id"],
        signal_id                = row["signal_id"],
        sector                   = SignalSector(row["sector"]),
        suggested_template_id    = row["suggested_template_id"],
        suggested_severity       = float(row["suggested_severity"]),
        suggested_horizon_hours  = int(row["suggested_horizon_hours"]),
        rationale                = row["rationale"],
        status                   = SeedStatus(row["status"]),
        created_at               = _coerce_dt(row["created_at"]),
        reviewed_by              = row.get("reviewed_by"),
        reviewed_at              = _coerce_dt(row.get("reviewed_at")) if row.get("reviewed_at") else None,
        review_reason            = row.get("review_reason"),
    )


def _coerce_dt(value) -> datetime:
    """Coerce a DB datetime value (may be string or datetime) to a timezone-aware datetime."""
    if isinstance(value, datetime):
        if value.tzinfo is None:
            return value.replace(tzinfo=timezone.utc)
        return value
    if isinstance(value, str):
        # ISO format from SQLite TEXT
        dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
        if dt.tzinfo is None:
            return dt.replace(tzinfo=timezone.utc)
        return dt
    raise TypeError(f"Cannot coerce {type(value)} to datetime: {value!r}")
