"""
Impact Observatory | مرصد الأثر — Data Trust Layer Unit Tests

Tests cover:
    1. TrustedEventContract construction and field validation
    2. ValidationStatus enum values
    3. Centralized validator (8 rules)
    4. SourceMetrics + compute_source_score (formula, tiers, edge cases)
    5. GovernmentAdapter (fetch, normalize, source_metrics)
    6. RealEstateAdapter (fetch, normalize, source_metrics)
    7. Quarantine store (write + read round-trip, lazy init)
    8. Pipeline orchestrator (PipelineResult shape, record routing)
    9. Bridge (domain → event_type mapping, import-failure path)

All tests are deterministic — no ML, no network, no external dependencies.
The quarantine store tests use a tmp_path SQLite DB (pytest fixture).
"""

from __future__ import annotations

import sys
import types
from datetime import datetime, timezone, timedelta
from unittest.mock import MagicMock, patch

import pytest


# ──────────────────────────────────────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────────────────────────────────────

def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _make_contract(**kwargs):
    """Build a minimal valid TrustedEventContract, overrideable via kwargs."""
    from app.data_trust.contracts.event import TrustedEventContract

    defaults = dict(
        timestamp=_utcnow(),
        source="test_source",
        domain="government",
        geo={"country": "SA", "region": "Riyadh"},
        raw_payload={"raw": True},
        normalized_payload={"indicator": "gdp", "value": 3.5},
    )
    defaults.update(kwargs)
    return TrustedEventContract(**defaults)


# ──────────────────────────────────────────────────────────────────────────────
# 1. TrustedEventContract
# ──────────────────────────────────────────────────────────────────────────────

class TestTrustedEventContract:

    def test_auto_event_id(self):
        c = _make_contract()
        assert c.event_id.startswith("te_")
        assert len(c.event_id) > 3

    def test_auto_received_at_utc(self):
        c = _make_contract()
        assert c.received_at.tzinfo is not None

    def test_source_stripped(self):
        c = _make_contract(source="  gov_data  ")
        assert c.source == "gov_data"

    def test_domain_stripped(self):
        c = _make_contract(domain="  real_estate  ")
        assert c.domain == "real_estate"

    def test_geo_must_be_nonempty(self):
        from pydantic import ValidationError
        with pytest.raises(ValidationError, match="non-empty"):
            _make_contract(geo={})

    def test_impact_score_bounds(self):
        from pydantic import ValidationError
        with pytest.raises(ValidationError):
            _make_contract(impact_score=1.5)
        with pytest.raises(ValidationError):
            _make_contract(impact_score=-0.1)

    def test_confidence_bounds(self):
        from pydantic import ValidationError
        with pytest.raises(ValidationError):
            _make_contract(confidence=2.0)

    def test_defaults(self):
        from app.data_trust.contracts.event import ValidationStatus
        c = _make_contract()
        assert c.impact_score is None
        assert c.confidence is None
        # use_enum_values=True — stored as string
        assert c.validation_status == "pending"
        assert c.validation_errors == []

    def test_mutable_confidence(self):
        c = _make_contract()
        c.confidence = 0.77
        assert c.confidence == 0.77


# ──────────────────────────────────────────────────────────────────────────────
# 2. ValidationStatus enum
# ──────────────────────────────────────────────────────────────────────────────

class TestValidationStatus:

    def test_enum_values(self):
        from app.data_trust.contracts.event import ValidationStatus
        assert ValidationStatus.PENDING.value    == "pending"
        assert ValidationStatus.VALID.value      == "valid"
        assert ValidationStatus.INVALID.value    == "invalid"
        assert ValidationStatus.QUARANTINED.value == "quarantined"


# ──────────────────────────────────────────────────────────────────────────────
# 3. Centralized validator — 8 rules
# ──────────────────────────────────────────────────────────────────────────────

class TestValidator:

    def _validate(self, **kwargs):
        from app.data_trust.validation.validator import validate_trusted_event
        return validate_trusted_event(_make_contract(**kwargs))

    def test_valid_contract_passes(self):
        result = self._validate()
        assert result["valid"] is True
        assert result["errors"] == []

    def test_rule1_empty_event_id(self):
        from app.data_trust.validation.validator import validate_trusted_event
        from app.data_trust.contracts.event import TrustedEventContract
        c = _make_contract()
        c.event_id = ""
        result = validate_trusted_event(c)
        assert not result["valid"]
        assert any("RULE_1" in e for e in result["errors"])

    def test_rule3_impact_score_out_of_range(self):
        from app.data_trust.validation.validator import validate_trusted_event
        from app.data_trust.contracts.event import TrustedEventContract
        c = _make_contract()
        # Bypass Pydantic by setting directly after construction
        object.__setattr__(c, "impact_score", 1.5)
        result = validate_trusted_event(c)
        assert any("RULE_3" in e for e in result["errors"])

    def test_rule4_unknown_domain_warns(self):
        # RULE_4 is a warning-only policy: unknown domains are flagged but not rejected.
        # The contract is still valid so the record can proceed; the operator is warned.
        result = self._validate(domain="unknown_xyz")
        assert result["valid"] is True
        assert any("RULE_4_WARN" in e for e in result["errors"])

    def test_rule5_source_too_short(self):
        result = self._validate(source="ab")
        assert any("RULE_5" in e for e in result["errors"])

    def test_rule6_thin_normalized_payload(self):
        result = self._validate(normalized_payload={"only_one": "key"})
        assert any("RULE_6" in e for e in result["errors"])

    def test_rule7_geo_missing_country(self):
        result = self._validate(geo={"region": "Riyadh"})
        assert any("RULE_7" in e for e in result["errors"])

    def test_rule8_warn_old_timestamp(self):
        old_ts = _utcnow() - timedelta(days=45)
        result = self._validate(timestamp=old_ts)
        # Rule 8 issues a _WARN for old timestamps — contract is still valid
        assert result["valid"] is True
        assert any("RULE_8_WARN" in e for e in result["errors"])

    def test_rule8_future_timestamp_hard_fail(self):
        future_ts = _utcnow() + timedelta(minutes=10)
        result = self._validate(timestamp=future_ts)
        assert not result["valid"]
        assert any("RULE_8" in e and "_WARN" not in e for e in result["errors"])


# ──────────────────────────────────────────────────────────────────────────────
# 4. Trust scorer
# ──────────────────────────────────────────────────────────────────────────────

class TestTrustScorer:

    def _score(self, **metric_overrides):
        from app.data_trust.scoring.trust_scorer import SourceMetrics, compute_source_score
        defaults = dict(
            reliability=0.90,
            freshness=0.65,
            coverage=0.90,
            consistency=0.88,
            latency=0.70,
            event_timestamp=_utcnow(),
            received_at=_utcnow(),
            normalized_payload={"a": 1, "b": 2, "c": 3},
        )
        defaults.update(metric_overrides)
        return compute_source_score(SourceMetrics(**defaults))

    def test_weights_sum_to_one(self):
        from app.data_trust.scoring.trust_scorer import _WEIGHTS
        assert abs(sum(_WEIGHTS.values()) - 1.0) < 1e-9

    def test_result_fields(self):
        r = self._score()
        assert 0.0 <= r.source_score <= 1.0
        assert 0.0 <= r.confidence  <= 1.0
        assert r.trust_tier in ("TIER_1_HIGH", "TIER_2_MEDIUM", "TIER_3_LOW", "TIER_4_UNTRUSTED")
        assert r.formula

    def test_high_metrics_yield_tier1(self):
        r = self._score(reliability=1.0, event_timestamp=_utcnow() - timedelta(minutes=30))
        assert r.trust_tier == "TIER_1_HIGH"

    def test_low_metrics_yield_low_tier(self):
        r = self._score(
            reliability=0.10,
            event_timestamp=_utcnow() - timedelta(days=90),
            received_at=_utcnow(),
            normalized_payload={"a": 1},   # thin payload
        )
        assert r.trust_tier in ("TIER_3_LOW", "TIER_4_UNTRUSTED")

    def test_score_is_deterministic(self):
        ts = _utcnow() - timedelta(hours=2)
        r1 = self._score(event_timestamp=ts)
        r2 = self._score(event_timestamp=ts)
        assert r1.source_score == r2.source_score


# ──────────────────────────────────────────────────────────────────────────────
# 5. GovernmentAdapter
# ──────────────────────────────────────────────────────────────────────────────

class TestGovernmentAdapter:

    def setup_method(self):
        from app.data_trust.adapters.government import GovernmentAdapter
        self.adapter = GovernmentAdapter()

    def test_source_id(self):
        assert self.adapter.source_id == "government_open_data"

    def test_domain(self):
        assert self.adapter.domain == "government"

    def test_fetch_returns_list(self):
        records = self.adapter.fetch()
        assert isinstance(records, list)
        assert len(records) >= 1

    def test_fetch_records_have_required_keys(self):
        for r in self.adapter.fetch():
            assert "record_id" in r
            assert "country_code" in r
            assert "indicator_code" in r
            assert "value" in r

    def test_normalize_returns_contract(self):
        from app.data_trust.contracts.event import TrustedEventContract
        raw = self.adapter.fetch()[0]
        contract = self.adapter.normalize(raw)
        assert isinstance(contract, TrustedEventContract)

    def test_normalized_contract_valid(self):
        raw = self.adapter.fetch()[0]
        contract = self.adapter.normalize(raw)
        result = self.adapter.validate(contract)
        assert result["valid"] is True

    def test_source_metrics_keys(self):
        m = self.adapter.source_metrics()
        for key in ("reliability", "freshness", "coverage", "consistency", "latency"):
            assert key in m
            assert 0.0 <= m[key] <= 1.0


# ──────────────────────────────────────────────────────────────────────────────
# 6. RealEstateAdapter
# ──────────────────────────────────────────────────────────────────────────────

class TestRealEstateAdapter:

    def setup_method(self):
        from app.data_trust.adapters.real_estate import RealEstateAdapter
        self.adapter = RealEstateAdapter()

    def test_source_id(self):
        assert self.adapter.source_id == "real_estate_feed"

    def test_domain(self):
        assert self.adapter.domain == "real_estate"

    def test_fetch_returns_list(self):
        records = self.adapter.fetch()
        assert isinstance(records, list)
        assert len(records) >= 1

    def test_normalize_returns_contract(self):
        from app.data_trust.contracts.event import TrustedEventContract
        raw = self.adapter.fetch()[0]
        contract = self.adapter.normalize(raw)
        assert isinstance(contract, TrustedEventContract)

    def test_geo_has_country(self):
        raw = self.adapter.fetch()[0]
        contract = self.adapter.normalize(raw)
        assert "country" in contract.geo

    def test_source_metrics_keys(self):
        m = self.adapter.source_metrics()
        for key in ("reliability", "freshness", "coverage", "consistency", "latency"):
            assert key in m


# ──────────────────────────────────────────────────────────────────────────────
# 7. Quarantine store
# ──────────────────────────────────────────────────────────────────────────────

class TestQuarantineStore:

    def _init(self, tmp_path):
        from app.data_trust.quarantine import store as qs
        # Reset module-level state for test isolation
        qs._engine = None
        qs._DB_PATH = None
        db_file = str(tmp_path / "test_quarantine.db")
        qs.init_quarantine_db(path=db_file)
        return qs

    def test_init_returns_path(self, tmp_path):
        from app.data_trust.quarantine import store as qs
        qs._engine = None
        path = qs.init_quarantine_db(path=str(tmp_path / "q.db"))
        assert "q.db" in path

    def test_write_and_read(self, tmp_path):
        qs = self._init(tmp_path)
        row_id = qs.quarantine_record(
            event_id="te_test_001",
            source="test_source",
            domain="government",
            event_timestamp=_utcnow(),
            error_reasons=["RULE_4: unknown domain"],
            raw_payload={"raw": True},
            normalized_payload={"n": 1, "k": 2},
        )
        assert row_id > 0

        records = qs.load_quarantine(source="test_source")
        assert len(records) == 1
        r = records[0]
        assert r["event_id"] == "te_test_001"
        assert r["status"] == "quarantined"
        assert r["error_reasons_parsed"] == ["RULE_4: unknown domain"]
        assert r["raw_payload_parsed"] == {"raw": True}

    def test_multiple_records_ordering(self, tmp_path):
        qs = self._init(tmp_path)
        for i in range(5):
            qs.quarantine_record(
                event_id=f"te_test_{i:03d}",
                source="bulk_source",
                domain="government",
                event_timestamp=_utcnow(),
                error_reasons=[f"error_{i}"],
                raw_payload={},
                normalized_payload={"a": i, "b": i},
            )
        records = qs.load_quarantine(source="bulk_source", limit=10)
        assert len(records) == 5
        # Most recent first
        assert records[0]["event_id"] == "te_test_004"

    def test_filter_by_domain(self, tmp_path):
        qs = self._init(tmp_path)
        qs.quarantine_record(
            event_id="te_gov", source="s1", domain="government",
            event_timestamp=_utcnow(), error_reasons=["e"],
            raw_payload={}, normalized_payload={"a": 1, "b": 2},
        )
        qs.quarantine_record(
            event_id="te_re", source="s2", domain="real_estate",
            event_timestamp=_utcnow(), error_reasons=["e"],
            raw_payload={}, normalized_payload={"a": 1, "b": 2},
        )
        gov_records = qs.load_quarantine(domain="government")
        assert all(r["domain"] == "government" for r in gov_records)

    def test_uninitialised_returns_empty(self, tmp_path):
        from app.data_trust.quarantine import store as qs
        qs._engine = None
        result = qs.load_quarantine()
        assert result == []


# ──────────────────────────────────────────────────────────────────────────────
# 8. Pipeline orchestrator
# ──────────────────────────────────────────────────────────────────────────────

class TestOrchestrator:

    def _run_with_mock_bridge(self, adapter, bridge_ok=True, tmp_path=None):
        """Run the pipeline with a mocked intelligence bridge."""
        from app.data_trust.quarantine import store as qs
        if tmp_path:
            qs._engine = None
            qs.init_quarantine_db(path=str(tmp_path / "orch_q.db"))

        bridge_result = {
            "ok": bridge_ok,
            "event_id": "te_x",
            "source": adapter.source_id,
            "domain": adapter.domain,
            "confidence": 0.80,
            "error": None if bridge_ok else "bridge error",
            "ingest_id": "te_x",
            "validated": True,
            "normalized": False,
        }

        with patch(
            "app.data_trust.pipeline.orchestrator.ingest_to_intelligence",
            return_value=bridge_result,
        ):
            from app.data_trust.pipeline.orchestrator import run_pipeline
            return run_pipeline(adapter)

    def test_government_adapter_full_run(self, tmp_path):
        from app.data_trust.adapters.government import GovernmentAdapter
        result = self._run_with_mock_bridge(GovernmentAdapter(), tmp_path=tmp_path)

        assert result.run_id.startswith("dtp_")
        assert result.total >= 1
        assert result.passed + result.quarantined + result.failed == result.total

    def test_real_estate_adapter_full_run(self, tmp_path):
        from app.data_trust.adapters.real_estate import RealEstateAdapter
        result = self._run_with_mock_bridge(RealEstateAdapter(), tmp_path=tmp_path)
        assert result.total >= 1

    def test_passed_records_have_bridge_result(self, tmp_path):
        from app.data_trust.adapters.government import GovernmentAdapter
        result = self._run_with_mock_bridge(GovernmentAdapter(), bridge_ok=True, tmp_path=tmp_path)
        passed = [r for r in result.records if r.status == "passed"]
        for rec in passed:
            assert rec.bridge_result is not None
            assert rec.source_score is not None
            assert rec.trust_tier is not None

    def test_bridge_failure_routes_to_failed(self, tmp_path):
        from app.data_trust.adapters.government import GovernmentAdapter
        result = self._run_with_mock_bridge(GovernmentAdapter(), bridge_ok=False, tmp_path=tmp_path)
        failed = [r for r in result.records if r.status == "failed"]
        assert len(failed) >= 1
        for rec in failed:
            assert rec.errors

    def test_pipeline_result_to_dict(self, tmp_path):
        from app.data_trust.adapters.government import GovernmentAdapter
        result = self._run_with_mock_bridge(GovernmentAdapter(), tmp_path=tmp_path)
        d = result.to_dict()
        for key in ("run_id", "adapter", "total", "passed", "quarantined", "failed", "duration_ms", "ok", "records"):
            assert key in d

    def test_fetch_retry_on_error(self, tmp_path):
        """Verify that a failing fetch is retried once and the pipeline aborts on second failure."""
        from app.data_trust.quarantine import store as qs
        qs._engine = None
        qs.init_quarantine_db(path=str(tmp_path / "retry_q.db"))

        from app.data_trust.adapters.base import BaseAdapter, AdapterFetchError
        from app.data_trust.contracts.event import TrustedEventContract

        class AlwaysFailAdapter(BaseAdapter):
            source_id = "always_fail"
            domain = "government"
            fetch_calls = 0

            def fetch(self) -> list[dict]:
                AlwaysFailAdapter.fetch_calls += 1
                raise AdapterFetchError("simulated failure")

            def normalize(self, raw: dict) -> TrustedEventContract:
                raise NotImplementedError

        adapter = AlwaysFailAdapter()
        from app.data_trust.pipeline.orchestrator import run_pipeline
        result = run_pipeline(adapter)

        assert AlwaysFailAdapter.fetch_calls == 2   # one try + one retry
        assert result.total == 0
        assert result.passed == 0


# ──────────────────────────────────────────────────────────────────────────────
# 9. Bridge — domain → event_type mapping + import-failure path
# ──────────────────────────────────────────────────────────────────────────────

class TestBridge:

    def test_domain_event_type_mapping(self):
        from app.data_trust.pipeline.bridge import _DOMAIN_TO_EVENT_TYPE, _DEFAULT_EVENT_TYPE
        assert _DOMAIN_TO_EVENT_TYPE["government"]  == "geopolitical"
        assert _DOMAIN_TO_EVENT_TYPE["real_estate"] == "economic"
        assert _DOMAIN_TO_EVENT_TYPE["cyber"]       == "cyber"
        assert _DEFAULT_EVENT_TYPE == "economic"

    def test_import_failure_returns_ok_false(self):
        """If the existing pipeline cannot be imported, bridge returns ok=False cleanly."""
        contract = _make_contract()
        contract.confidence = 0.75

        with patch.dict(sys.modules, {
            "app.ingestion.ingest":   None,
            "app.quality.validate":   None,
            "app.quality.normalize":  None,
        }):
            from importlib import import_module
            # Reload bridge to force the import attempt inside the function
            from app.data_trust.pipeline import bridge
            result = bridge.ingest_to_intelligence(contract, run_id="test_run")

        assert result["ok"] is False
        assert "error" in result
        assert result["validated"] is False
        assert result["normalized"] is False

    def test_result_shape_on_success(self):
        """Bridge result must always contain the required keys."""
        contract = _make_contract()
        contract.confidence = 0.80

        mock_raw = MagicMock()
        mock_raw.source_id = "te_bridge_test"

        mock_validated = MagicMock()
        mock_validated.validation_score = 0.90

        mock_normalized = MagicMock()
        mock_normalized.event_id = "norm_001"
        mock_normalized.geographic_scope = "regional"

        # The bridge imports lazily inside ingest_to_intelligence().
        # Inject fake modules into sys.modules so the `from ... import` resolves them.
        fake_ingest = types.ModuleType("app.ingestion.ingest")
        fake_ingest.ingest_raw_event = MagicMock(return_value=mock_raw)

        fake_validate = types.ModuleType("app.quality.validate")
        fake_validate.validate_event = MagicMock(return_value=mock_validated)
        fake_validate.ValidationError = Exception

        fake_normalize = types.ModuleType("app.quality.normalize")
        fake_normalize.normalize_event = MagicMock(return_value=mock_normalized)

        with patch.dict(sys.modules, {
            "app.ingestion.ingest":  fake_ingest,
            "app.quality.validate":  fake_validate,
            "app.quality.normalize": fake_normalize,
        }):
            from app.data_trust.pipeline import bridge as b
            result = b.ingest_to_intelligence(contract, run_id="shape_test")

        required_keys = {"ok", "event_id", "source", "domain", "confidence", "error",
                         "ingest_id", "validated", "normalized"}
        assert required_keys.issubset(result.keys())
