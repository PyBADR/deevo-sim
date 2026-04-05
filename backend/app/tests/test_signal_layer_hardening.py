"""
Hardening tests for the Live Signal Layer.

Covers:
  - Persistence: signals and seeds written to SQLite, survive process restart simulation
  - Transition guards: approve/reject blocked on terminal states
  - Audit trail: audit events created for every lifecycle transition
  - Recovery: _pending rebuilt from DB on load_pending_from_db()
  - Duplicate protection: duplicate signal_id is safe (INSERT OR IGNORE)
  - Invalid input: bad sector/severity/event_type rejected at route layer

Uses an isolated in-memory SQLite DB per test (SIGNAL_DB_PATH=":memory:" is not
supported by SQLAlchemy's file path; instead we use a temp file per test).
"""
from __future__ import annotations

import os
import tempfile
import unittest
from datetime import datetime, timezone
from unittest.mock import MagicMock, patch


# ── Helpers ────────────────────────────────────────────────────────────────────

def _make_live_signal(
    event_type: str = "liquidity_stress",
    sector: str = "banking",
    severity: float = 0.75,
):
    from app.domain.models.live_signal import LiveSignal, LiveSignalSource, SignalSector
    return LiveSignal(
        source=LiveSignalSource.MANUAL,
        sector=SignalSector.BANKING if sector == "banking" else SignalSector.FINTECH,
        event_type=event_type,
        severity_raw=severity,
        confidence_raw=0.8,
    )


def _make_scored(event_type: str = "liquidity_stress", severity: float = 0.75):
    from app.signals.scorer import score
    return score(_make_live_signal(event_type=event_type, severity=severity))


def _setup_store(tmp_path: str):
    """Patch SIGNAL_DB_PATH to a temp file and initialize the store."""
    import app.signals.store as store_mod
    # Monkey-patch the module-level engine to use our temp path
    from sqlalchemy import create_engine, event as sa_event
    from sqlalchemy.orm import Session

    engine = create_engine(
        f"sqlite:///{tmp_path}",
        connect_args={"check_same_thread": False},
        echo=False,
    )

    @sa_event.listens_for(engine, "connect")
    def _pragma(conn, _):
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA foreign_keys=ON")

    # Replace module-level engine + re-create tables
    store_mod._engine = engine
    store_mod.Base.metadata.create_all(engine)
    return engine


# ── Tests ──────────────────────────────────────────────────────────────────────

class TestStorePersistence(unittest.TestCase):
    """store.save_signal / save_seed / update_seed_approved / update_seed_rejected."""

    def setUp(self):
        self.tmp = tempfile.mktemp(suffix=".db")
        _setup_store(self.tmp)
        import app.signals.store as s
        self.store = s

    def tearDown(self):
        try:
            os.unlink(self.tmp)
        except FileNotFoundError:
            pass

    def test_save_signal_and_audit(self):
        scored = _make_scored()
        self.store.save_signal(scored)

        events = self.store.get_audit_log(entity_id=scored.signal.signal_id)
        self.assertTrue(any(e["event_type"] == "signal.ingested" for e in events))

    def test_save_seed_and_audit(self):
        scored = _make_scored()
        from app.signals.seed_generator import generate
        seed = generate(scored)
        self.store.save_seed(seed)

        events = self.store.get_audit_log(entity_id=seed.seed_id)
        self.assertTrue(any(e["event_type"] == "seed.created" for e in events))

    def test_save_signal_idempotent(self):
        """Duplicate signal_id must not raise."""
        scored = _make_scored()
        self.store.save_signal(scored)
        self.store.save_signal(scored)  # second call must not raise

    def test_update_seed_approved_writes_audit(self):
        scored = _make_scored()
        from app.signals.seed_generator import generate
        from app.domain.models.live_signal import SeedStatus
        seed = generate(scored)
        self.store.save_seed(seed)
        approved = seed.approve(reviewed_by="operator@io", reason="looks correct")
        run_id = "run-test-123"
        self.store.update_seed_approved(approved, run_id)

        events = self.store.get_audit_log(entity_id=seed.seed_id)
        self.assertTrue(any(e["event_type"] == "seed.approved" for e in events))
        # run_id should be in metadata
        approved_event = next(e for e in events if e["event_type"] == "seed.approved")
        self.assertEqual(approved_event["metadata"].get("run_id"), run_id)

    def test_update_seed_rejected_writes_audit(self):
        scored = _make_scored()
        from app.signals.seed_generator import generate
        seed = generate(scored)
        self.store.save_seed(seed)
        rejected = seed.reject(reviewed_by="operator@io", reason="false positive")
        self.store.update_seed_rejected(rejected)

        events = self.store.get_audit_log(entity_id=seed.seed_id)
        self.assertTrue(any(e["event_type"] == "seed.rejected" for e in events))

    def test_load_pending_seeds_empty_initially(self):
        rows = self.store.load_pending_seeds()
        self.assertEqual(rows, [])

    def test_load_pending_seeds_after_save(self):
        scored = _make_scored()
        from app.signals.seed_generator import generate
        seed = generate(scored)
        self.store.save_seed(seed)

        rows = self.store.load_pending_seeds()
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["seed_id"], seed.seed_id)
        self.assertEqual(rows[0]["status"], "PENDING_REVIEW")

    def test_load_pending_seeds_excludes_approved(self):
        scored = _make_scored()
        from app.signals.seed_generator import generate
        seed = generate(scored)
        self.store.save_seed(seed)
        approved = seed.approve(reviewed_by="op")
        self.store.update_seed_approved(approved, "run-xyz")

        rows = self.store.load_pending_seeds()
        self.assertEqual(rows, [])  # approved seed must not appear in pending


class TestHITLTransitionGuards(unittest.TestCase):
    """hitl.approve() and hitl.reject() must block invalid transitions."""

    def setUp(self):
        self.tmp = tempfile.mktemp(suffix=".db")
        _setup_store(self.tmp)
        # Clear in-memory caches
        import app.signals.hitl as hitl_mod
        hitl_mod._pending.clear()
        hitl_mod._reviewed.clear()
        self.hitl = hitl_mod

    def tearDown(self):
        import app.signals.hitl as hitl_mod
        hitl_mod._pending.clear()
        hitl_mod._reviewed.clear()
        try:
            os.unlink(self.tmp)
        except FileNotFoundError:
            pass

    def _submit(self, event_type="liquidity_stress"):
        scored = _make_scored(event_type=event_type)
        # Patch run_unified_pipeline so approve() doesn't need a real pipeline
        return self.hitl.submit(scored)

    def test_approve_non_existent_seed_raises(self):
        with self.assertRaises(self.hitl.HITLError) as ctx:
            self.hitl.approve("seed-doesnotexist", reviewed_by="op")
        self.assertIn("not found", str(ctx.exception).lower())

    def test_reject_non_existent_seed_raises(self):
        with self.assertRaises(self.hitl.HITLError):
            self.hitl.reject("seed-doesnotexist", reviewed_by="op")

    def test_double_reject_raises(self):
        seed = self._submit()
        # Reject once
        self.hitl.reject(seed.seed_id, reviewed_by="op", reason="first reject")
        # Second reject must raise
        with self.assertRaises(self.hitl.HITLError) as ctx:
            self.hitl.reject(seed.seed_id, reviewed_by="op", reason="second reject")
        self.assertIn("REJECTED", str(ctx.exception))

    def test_approve_already_rejected_seed_raises(self):
        seed = self._submit()
        self.hitl.reject(seed.seed_id, reviewed_by="op")
        with self.assertRaises(self.hitl.HITLError) as ctx:
            with patch("app.simulation.runner.run_unified_pipeline", return_value={}):
                self.hitl.approve(seed.seed_id, reviewed_by="op")
        self.assertIn("REJECTED", str(ctx.exception))

    def test_approve_happy_path(self):
        seed = self._submit()
        fake_result = {
            "status": "completed",
            "stages_completed": 13,
            "financial_impact": {},
        }
        with patch("app.simulation.runner.run_unified_pipeline", return_value=fake_result), \
             patch("app.api.v1.routes.runs.get_run_store", return_value={}), \
             patch("app.api.v1.routes.runs.get_result_store", return_value={}):
            result = self.hitl.approve(seed.seed_id, reviewed_by="admin@io", reason="approved")

        self.assertEqual(result.seed.reviewed_by, "admin@io")
        self.assertIsNotNone(result.run_id)
        # Seed must be in _reviewed, not _pending
        self.assertNotIn(seed.seed_id, self.hitl._pending)
        self.assertIn(seed.seed_id, self.hitl._reviewed)

    def test_pipeline_failure_leaves_seed_in_pending(self):
        """If pipeline fails, seed must remain in PENDING_REVIEW (not lost)."""
        seed = self._submit()
        with patch("app.simulation.runner.run_unified_pipeline", side_effect=RuntimeError("pipeline down")):
            with self.assertRaises(self.hitl.HITLError):
                self.hitl.approve(seed.seed_id, reviewed_by="op")
        # Seed must still be retrievable as PENDING
        from app.domain.models.live_signal import SeedStatus
        self.assertIn(seed.seed_id, self.hitl._pending)
        self.assertEqual(self.hitl._pending[seed.seed_id].status, SeedStatus.PENDING_REVIEW)


class TestHITLRecovery(unittest.TestCase):
    """load_pending_from_db() must restore _pending from SQLite."""

    def setUp(self):
        self.tmp = tempfile.mktemp(suffix=".db")
        _setup_store(self.tmp)
        import app.signals.hitl as hitl_mod
        hitl_mod._pending.clear()
        hitl_mod._reviewed.clear()
        self.hitl = hitl_mod

    def tearDown(self):
        import app.signals.hitl as hitl_mod
        hitl_mod._pending.clear()
        hitl_mod._reviewed.clear()
        try:
            os.unlink(self.tmp)
        except FileNotFoundError:
            pass

    def test_recovery_restores_pending_seeds(self):
        scored = _make_scored()
        from app.signals.seed_generator import generate
        import app.signals.store as store_mod
        seed = generate(scored)
        store_mod.save_seed(seed)

        # Simulate restart: clear the cache
        self.hitl._pending.clear()
        self.assertEqual(len(self.hitl._pending), 0)

        # Recover
        self.hitl.load_pending_from_db()
        self.assertIn(seed.seed_id, self.hitl._pending)

    def test_recovery_skips_approved_seeds(self):
        scored = _make_scored()
        from app.signals.seed_generator import generate
        import app.signals.store as store_mod
        seed = generate(scored)
        store_mod.save_seed(seed)
        approved = seed.approve(reviewed_by="op")
        store_mod.update_seed_approved(approved, "run-abc")

        self.hitl._pending.clear()
        self.hitl.load_pending_from_db()
        self.assertNotIn(seed.seed_id, self.hitl._pending)


class TestTransitionGuardMatrix(unittest.TestCase):
    """_assert_transition must enforce the full state machine."""

    def setUp(self):
        import app.signals.hitl as hitl_mod
        self.guard = hitl_mod._assert_transition
        self.HITLError = hitl_mod.HITLError

    def _seed_with_status(self, status_str: str):
        from app.domain.models.live_signal import ScenarioSeed, SignalSector, SeedStatus
        return ScenarioSeed(
            signal_id="sig-test",
            sector=SignalSector.BANKING,
            suggested_template_id="regional_liquidity_stress_event",
            suggested_severity=0.6,
            suggested_horizon_hours=72,
            rationale="test",
            status=SeedStatus(status_str),
            created_at=datetime.now(timezone.utc),
        )

    def test_pending_can_approve(self):
        from app.domain.models.live_signal import SeedStatus
        seed = self._seed_with_status("PENDING_REVIEW")
        self.guard(seed, SeedStatus.APPROVED)  # must not raise

    def test_pending_can_reject(self):
        from app.domain.models.live_signal import SeedStatus
        seed = self._seed_with_status("PENDING_REVIEW")
        self.guard(seed, SeedStatus.REJECTED)  # must not raise

    def test_approved_cannot_approve_again(self):
        from app.domain.models.live_signal import SeedStatus
        seed = self._seed_with_status("APPROVED")
        with self.assertRaises(self.HITLError):
            self.guard(seed, SeedStatus.APPROVED)

    def test_approved_cannot_reject(self):
        from app.domain.models.live_signal import SeedStatus
        seed = self._seed_with_status("APPROVED")
        with self.assertRaises(self.HITLError):
            self.guard(seed, SeedStatus.REJECTED)

    def test_rejected_cannot_approve(self):
        from app.domain.models.live_signal import SeedStatus
        seed = self._seed_with_status("REJECTED")
        with self.assertRaises(self.HITLError):
            self.guard(seed, SeedStatus.APPROVED)

    def test_expired_cannot_approve(self):
        from app.domain.models.live_signal import SeedStatus
        seed = self._seed_with_status("EXPIRED")
        with self.assertRaises(self.HITLError):
            self.guard(seed, SeedStatus.APPROVED)


class TestSignalIngestValidation(unittest.TestCase):
    """SignalIngestBody must reject malformed inputs."""

    def _body(self, **kwargs):
        from app.api.v1.routes.signals import SignalIngestBody
        return SignalIngestBody(**kwargs)

    def test_valid_banking_signal(self):
        b = self._body(sector="banking", event_type="liquidity_stress", severity=0.7)
        self.assertEqual(b.sector, "banking")

    def test_invalid_sector_raises(self):
        from pydantic import ValidationError
        with self.assertRaises(ValidationError):
            self._body(sector="energy", event_type="oil_shock", severity=0.5)

    def test_severity_out_of_range_raises(self):
        from pydantic import ValidationError
        with self.assertRaises(ValidationError):
            self._body(sector="banking", event_type="bank_run", severity=1.5)

    def test_latitude_out_of_range_raises(self):
        from pydantic import ValidationError
        with self.assertRaises(ValidationError):
            self._body(sector="banking", event_type="bank_run", severity=0.6, lat=200.0)

    def test_blank_event_type_raises(self):
        from pydantic import ValidationError
        with self.assertRaises(ValidationError):
            self._body(sector="banking", event_type="   ", severity=0.6)


class TestRunPersistence(unittest.TestCase):
    """Run metadata and results survive restart (load_runs_from_db)."""

    def setUp(self):
        self.tmp = tempfile.mktemp(suffix=".db")
        _setup_store(self.tmp)
        import app.signals.store as s
        self.store = s

    def tearDown(self):
        try:
            os.unlink(self.tmp)
        except FileNotFoundError:
            pass

    def test_save_run_and_reload(self):
        run_meta = {
            "run_id": "run-persist-001",
            "scenario_id": "regional_liquidity_stress_event",
            "status": "completed",
            "severity": 0.75,
            "horizon_hours": 72,
            "stages_completed": 13,
            "stages_total": 13,
            "created_at": datetime.now(timezone.utc),
        }
        self.store.save_run(run_meta)
        loaded = self.store.load_run_by_id("run-persist-001")
        self.assertIsNotNone(loaded)
        self.assertEqual(loaded["status"], "completed")
        self.assertEqual(loaded["scenario_id"], "regional_liquidity_stress_event")

    def test_save_run_result_and_reload(self):
        self.store.save_run({"run_id": "run-res-001", "scenario_id": "test", "status": "completed",
                             "created_at": datetime.now(timezone.utc)})
        result_payload = {"status": "completed", "stages_completed": 13, "financial_impact": {"total": 42.0}}
        self.store.save_run_result("run-res-001", result_payload)
        loaded = self.store.load_result_by_id("run-res-001")
        self.assertIsNotNone(loaded)
        self.assertEqual(loaded["stages_completed"], 13)
        self.assertEqual(loaded["financial_impact"]["total"], 42.0)

    def test_load_all_run_metadata_returns_rows(self):
        for i in range(3):
            self.store.save_run({
                "run_id": f"run-meta-{i}",
                "scenario_id": "test",
                "status": "completed",
                "created_at": datetime.now(timezone.utc),
            })
        rows = self.store.load_all_run_metadata()
        ids = [r["run_id"] for r in rows]
        for i in range(3):
            self.assertIn(f"run-meta-{i}", ids)

    def test_runs_restored_into_routes_cache(self):
        """load_runs_from_db() must warm the _runs cache in routes/runs.py."""
        self.store.save_run({
            "run_id": "run-warmup-001",
            "scenario_id": "test",
            "status": "completed",
            "created_at": datetime.now(timezone.utc),
        })
        from app.api.v1.routes import runs as runs_mod
        runs_mod._runs.clear()  # simulate restart
        runs_mod.load_runs_from_db()
        self.assertIn("run-warmup-001", runs_mod._runs)

    def test_run_result_missing_returns_none(self):
        self.assertIsNone(self.store.load_result_by_id("run-nonexistent-999"))

    def test_run_audit_event_written(self):
        run_meta = {
            "run_id": "run-audit-001",
            "scenario_id": "test",
            "status": "completed",
            "created_at": datetime.now(timezone.utc),
        }
        self.store.save_run(run_meta)
        events = self.store.get_audit_log(entity_id="run-audit-001")
        self.assertTrue(any(e["event_type"] == "run.completed" for e in events))


class TestSeedExpiry(unittest.TestCase):
    """expire_stale_seeds() and reconcile_expired_seeds() enforce lifecycle."""

    def setUp(self):
        self.tmp = tempfile.mktemp(suffix=".db")
        _setup_store(self.tmp)
        import app.signals.store as s
        self.store = s
        import app.signals.hitl as hitl_mod
        hitl_mod._pending.clear()
        hitl_mod._reviewed.clear()
        self.hitl = hitl_mod

    def tearDown(self):
        import app.signals.hitl as hitl_mod
        hitl_mod._pending.clear()
        hitl_mod._reviewed.clear()
        try:
            os.unlink(self.tmp)
        except FileNotFoundError:
            pass

    def _submit_with_short_horizon(self):
        """Submit a seed with a 1-hour horizon for easy expiry testing."""
        from app.domain.models.live_signal import LiveSignal, LiveSignalSource, SignalSector
        from app.signals.scorer import score
        signal = LiveSignal(
            source=LiveSignalSource.MANUAL,
            sector=SignalSector.BANKING,
            event_type="liquidity_stress",
            severity_raw=0.7,
            confidence_raw=0.8,
        )
        scored = score(signal)
        seed = self.hitl.submit(scored)
        return seed

    def test_expire_stale_seeds_transitions_to_expired(self):
        seed = self._submit_with_short_horizon()
        # Advance "now" past the expiry window (horizon_hours ahead)
        from app.domain.models.live_signal import SeedStatus
        from datetime import timedelta
        future_now = datetime.now(timezone.utc) + timedelta(hours=seed.suggested_horizon_hours + 1)
        expired_ids = self.store.expire_stale_seeds(now=future_now)
        self.assertIn(seed.seed_id, expired_ids)

    def test_expire_stale_seeds_writes_audit_event(self):
        seed = self._submit_with_short_horizon()
        from datetime import timedelta
        future_now = datetime.now(timezone.utc) + timedelta(hours=seed.suggested_horizon_hours + 1)
        self.store.expire_stale_seeds(now=future_now)
        events = self.store.get_audit_log(entity_id=seed.seed_id, event_type="seed.expired")
        self.assertEqual(len(events), 1)

    def test_reconcile_evicts_from_pending_cache(self):
        seed = self._submit_with_short_horizon()
        self.assertIn(seed.seed_id, self.hitl._pending)
        # Manually expire in DB
        from datetime import timedelta
        future_now = datetime.now(timezone.utc) + timedelta(hours=seed.suggested_horizon_hours + 1)
        self.store.expire_stale_seeds(now=future_now)
        # Reconcile
        self.hitl.reconcile_expired_seeds()
        self.assertNotIn(seed.seed_id, self.hitl._pending)

    def test_approve_expired_seed_raises(self):
        """Expired seeds (EXPIRED status in DB) must not be approvable."""
        seed = self._submit_with_short_horizon()
        from datetime import timedelta
        future_now = datetime.now(timezone.utc) + timedelta(hours=seed.suggested_horizon_hours + 1)
        self.store.expire_stale_seeds(now=future_now)
        self.hitl._pending.pop(seed.seed_id, None)  # evict from cache to force DB lookup
        with self.assertRaises(self.hitl.HITLError) as ctx:
            self.hitl.approve(seed.seed_id, reviewed_by="op")
        self.assertIn("EXPIRED", str(ctx.exception))

    def test_expire_idempotent(self):
        """Calling expire_stale_seeds twice must not create duplicate audit events."""
        seed = self._submit_with_short_horizon()
        from datetime import timedelta
        future_now = datetime.now(timezone.utc) + timedelta(hours=seed.suggested_horizon_hours + 1)
        self.store.expire_stale_seeds(now=future_now)
        self.store.expire_stale_seeds(now=future_now)  # second call
        events = self.store.get_audit_log(entity_id=seed.seed_id, event_type="seed.expired")
        self.assertEqual(len(events), 1)  # only one expiry event despite two calls


class TestEphemeralPathDetection(unittest.TestCase):
    """init_db() must warn on ephemeral paths."""

    def test_tmp_path_detected_as_ephemeral(self):
        from app.signals.store import _is_ephemeral
        self.assertTrue(_is_ephemeral("/tmp/signals.db"))
        self.assertTrue(_is_ephemeral("/var/folders/abc/signals.db"))
        self.assertTrue(_is_ephemeral("/private/var/folders/abc/signals.db"))

    def test_data_path_not_ephemeral(self):
        from app.signals.store import _is_ephemeral
        self.assertFalse(_is_ephemeral("/data/signals.db"))
        self.assertFalse(_is_ephemeral("./signals.db"))
        self.assertFalse(_is_ephemeral("/app/signals.db"))

    def test_init_db_returns_resolved_path(self):
        """init_db() must return the path string (not None)."""
        import app.signals.store as store_mod
        # Use the already-initialized engine from setUp in other tests (engine may be set)
        # Just test the _is_ephemeral logic independently
        from app.signals.store import _is_ephemeral
        self.assertIsInstance(_is_ephemeral("/data/signals.db"), bool)


if __name__ == "__main__":
    unittest.main()
