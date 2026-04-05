"""Tests for the Intelligence Adapter Foundation.

Coverage:
    TestAdapterModels            — NormalizedIntelligenceSignal construction + helpers
    TestRawValidation            — validate_raw_payload: missing fields, score range, timestamp
    TestTraceBuilder             — TraceBuilder accumulates warnings/violations, derives status
    TestAdapterNormalization     — normalize_intelligence_payload: MANUAL_INTELLIGENCE path
    TestAdapterRejection         — malformed payloads raise AdapterError with violations
    TestAdapterSourceFamilyEnum  — unknown source_family rejected
    TestBridgeContract           — bridge eligibility gate + field mapping
    TestSemanticSeparation       — observed / inferred / simulated never collapsed
    TestSourceStubs              — Jet Nexus / TREK / Observatory stubs raise NotImplementedError
"""
from __future__ import annotations

from datetime import datetime, timezone, timedelta

import pytest


# ── Shared fixtures ────────────────────────────────────────────────────────────

def _minimal_valid_payload(**overrides) -> dict:
    """Return the smallest payload that passes all validation rules."""
    base = {
        "source_family":    "manual_intelligence",
        "source_systems":   ["test-system-01"],
        "source_event_ids": ["evt-001"],
        "signal_type":      "disruption",
        "title":            "Test signal",
        "summary":          "Minimal test payload for unit tests.",
        "severity_score":   0.6,
        "confidence_score": 0.8,
        "detected_at":      datetime.now(timezone.utc).isoformat(),
        "time_horizon_hours": 48,
        "affected_domains": ["banking"],
        "observed_evidence": [
            {
                "evidence_id":    "ev-001",
                "evidence_type":  "OBSERVED",
                "source_system":  "test-system-01",
                "source_event_id": "evt-001",
                "description":    "Port congestion detected.",
                "observed_at":    datetime.now(timezone.utc).isoformat(),
                "confidence":     0.9,
            }
        ],
    }
    base.update(overrides)
    return base


# ── TestAdapterModels ──────────────────────────────────────────────────────────

class TestAdapterModels:
    """NormalizedIntelligenceSignal construction and helper methods."""

    def test_normalized_signal_is_frozen(self):
        from app.intelligence.adapter import normalize_intelligence_payload
        signal = normalize_intelligence_payload(_minimal_valid_payload())
        with pytest.raises(Exception):  # frozen pydantic model raises on setattr
            signal.title = "mutated"  # type: ignore[misc]

    def test_semantic_summary_counts(self):
        from app.intelligence.adapter import normalize_intelligence_payload
        now = datetime.now(timezone.utc).isoformat()
        payload = _minimal_valid_payload(
            inferred_reasoning=[
                {
                    "reasoning_type":  "LIQUIDITY_STRESS",
                    "source_system":   "trek",
                    "inferred_at":     now,
                    "confidence":      0.7,
                    "summary":         "Liquidity stress inferred.",
                    "inferred_severity": 0.6,
                }
            ],
            simulation_context=[
                {
                    "simulation_type": "SCENARIO_PROPAGATION",
                    "source_system":   "observatory",
                    "simulated_at":    now,
                    "model_version":   "v1.0",
                    "confidence":      0.65,
                    "horizon_hours":   48,
                    "summary":         "Scenario spread projected.",
                    "projected_severity": 0.55,
                }
            ],
        )
        signal = normalize_intelligence_payload(payload)
        summary = signal.semantic_summary()
        assert summary["observed"]  == 1
        assert summary["inferred"]  == 1
        assert summary["simulated"] == 1

    def test_has_observed_inferred_simulated_flags(self):
        from app.intelligence.adapter import normalize_intelligence_payload
        signal = normalize_intelligence_payload(_minimal_valid_payload())
        assert signal.has_observed()
        assert not signal.has_inferred()
        assert not signal.has_simulated()

    def test_normalized_signal_id_prefix(self):
        from app.intelligence.adapter import normalize_intelligence_payload
        signal = normalize_intelligence_payload(_minimal_valid_payload())
        assert signal.normalized_signal_id.startswith("nis-")

    def test_adapter_version_present(self):
        from app.intelligence.adapter import normalize_intelligence_payload
        from app.intelligence.models import ADAPTER_VERSION
        signal = normalize_intelligence_payload(_minimal_valid_payload())
        assert signal.adapter_version == ADAPTER_VERSION


# ── TestRawValidation ─────────────────────────────────────────────────────────

class TestRawValidation:
    """validate_raw_payload: field-level violation detection."""

    def _run(self, raw: dict):
        from app.intelligence.trace import TraceBuilder
        from app.intelligence.validators import validate_raw_payload
        from app.intelligence.models import ADAPTER_VERSION
        tb = TraceBuilder(
            source_family    = str(raw.get("source_family", "")),
            source_systems   = raw.get("source_systems", []),
            adapter_version  = ADAPTER_VERSION,
        )
        validate_raw_payload(raw, tb)
        return tb

    def test_missing_title_is_violation(self):
        raw = _minimal_valid_payload()
        del raw["title"]
        tb = self._run(raw)
        assert tb.has_violations()
        fields = [v.field_name for v in tb.get_violations()]
        assert "title" in fields

    def test_severity_above_one_is_violation(self):
        raw = _minimal_valid_payload(severity_score=1.5)
        tb = self._run(raw)
        assert tb.has_violations()
        assert any(v.field_name == "severity_score" for v in tb.get_violations())

    def test_confidence_below_zero_is_violation(self):
        raw = _minimal_valid_payload(confidence_score=-0.1)
        tb = self._run(raw)
        assert tb.has_violations()
        assert any(v.field_name == "confidence_score" for v in tb.get_violations())

    def test_horizon_zero_is_violation(self):
        raw = _minimal_valid_payload(time_horizon_hours=0)
        tb = self._run(raw)
        assert tb.has_violations()
        assert any(v.field_name == "time_horizon_hours" for v in tb.get_violations())

    def test_horizon_over_8760_is_violation(self):
        raw = _minimal_valid_payload(time_horizon_hours=8761)
        tb = self._run(raw)
        assert tb.has_violations()

    def test_far_future_timestamp_is_violation(self):
        future_ts = (datetime.now(timezone.utc) + timedelta(hours=200)).isoformat()
        raw = _minimal_valid_payload(detected_at=future_ts)
        tb = self._run(raw)
        assert tb.has_violations()
        assert any(v.rule == "FUTURE_TIMESTAMP" for v in tb.get_violations())

    def test_epoch_zero_timestamp_is_violation(self):
        raw = _minimal_valid_payload(detected_at="1970-01-01T00:00:00+00:00")
        tb = self._run(raw)
        assert tb.has_violations()
        assert any(v.rule == "EPOCH_ZERO" for v in tb.get_violations())

    def test_empty_source_systems_is_violation(self):
        raw = _minimal_valid_payload(source_systems=[])
        tb = self._run(raw)
        assert tb.has_violations()
        assert any(v.field_name == "source_systems" for v in tb.get_violations())

    def test_no_semantic_sections_is_warning_not_violation(self):
        raw = _minimal_valid_payload()
        raw.pop("observed_evidence", None)
        # No inferred or simulated either
        tb = self._run(raw)
        # Semantic absence is a WARNING, not a violation (signal is still valid)
        assert not tb.has_violations()
        assert tb.has_warnings()
        assert any(w.field_name == "semantic_sections" for w in tb.get_warnings())

    def test_missing_source_event_ids_is_warning(self):
        raw = _minimal_valid_payload()
        raw.pop("source_event_ids", None)
        tb = self._run(raw)
        assert not tb.has_violations()
        assert any(w.field_name == "source_event_ids" for w in tb.get_warnings())


# ── TestTraceBuilder ──────────────────────────────────────────────────────────

class TestTraceBuilder:
    """TraceBuilder accumulates state and derives normalization status."""

    def _tb(self, **kwargs):
        from app.intelligence.trace import TraceBuilder
        from app.intelligence.models import ADAPTER_VERSION
        return TraceBuilder(
            source_family   = kwargs.get("source_family", "manual_intelligence"),
            source_systems  = kwargs.get("source_systems", ["sys-a"]),
            adapter_version = ADAPTER_VERSION,
        )

    def test_no_events_yields_normalized_status(self):
        tb = self._tb()
        assert tb.derived_status() == "NORMALIZED"

    def test_warning_yields_partial_status(self):
        tb = self._tb()
        tb.warn("some_field", "a warning", severity="LOW")
        assert tb.derived_status() == "PARTIAL"

    def test_violation_yields_rejected_status(self):
        tb = self._tb()
        tb.violation("field_x", "bad value", received_value="x", rule="TEST_RULE")
        assert tb.derived_status() == "REJECTED"

    def test_build_contains_required_keys(self):
        tb = self._tb()
        result = tb.build()
        required = {"trace_id", "normalization_status", "source_family", "source_systems", "adapter_version"}
        assert required.issubset(set(result.keys()))

    def test_get_violations_returns_copy(self):
        tb = self._tb()
        tb.violation("f", "m", received_value="v", rule="R")
        v1 = tb.get_violations()
        v1.clear()
        assert len(tb.get_violations()) == 1  # original is not mutated

    def test_get_warnings_returns_copy(self):
        tb = self._tb()
        tb.warn("f", "m", severity="LOW")
        w1 = tb.get_warnings()
        w1.clear()
        assert len(tb.get_warnings()) == 1


# ── TestAdapterNormalization ──────────────────────────────────────────────────

class TestAdapterNormalization:
    """normalize_intelligence_payload: correct output for MANUAL_INTELLIGENCE."""

    def test_valid_payload_produces_normalized_status(self):
        from app.intelligence.adapter import normalize_intelligence_payload
        from app.intelligence.models import NormalizationStatus
        signal = normalize_intelligence_payload(_minimal_valid_payload())
        assert signal.normalization_status == NormalizationStatus.NORMALIZED

    def test_payload_with_warning_produces_partial_status(self):
        from app.intelligence.adapter import normalize_intelligence_payload
        from app.intelligence.models import NormalizationStatus
        # No source_event_ids → warning → PARTIAL
        payload = _minimal_valid_payload()
        payload.pop("source_event_ids", None)
        signal = normalize_intelligence_payload(payload)
        assert signal.normalization_status == NormalizationStatus.PARTIAL

    def test_source_family_preserved(self):
        from app.intelligence.adapter import normalize_intelligence_payload
        from app.intelligence.models import SourceFamily
        signal = normalize_intelligence_payload(_minimal_valid_payload())
        assert signal.source_family == SourceFamily.MANUAL_INTELLIGENCE

    def test_title_truncated_at_256(self):
        from app.intelligence.adapter import normalize_intelligence_payload
        long_title = "T" * 300
        signal = normalize_intelligence_payload(_minimal_valid_payload(title=long_title))
        assert len(signal.title) == 256

    def test_summary_truncated_at_2000(self):
        from app.intelligence.adapter import normalize_intelligence_payload
        long_summary = "S" * 2500
        signal = normalize_intelligence_payload(_minimal_valid_payload(summary=long_summary))
        assert len(signal.summary) == 2000

    def test_detected_at_naive_string_gets_utc(self):
        from app.intelligence.adapter import normalize_intelligence_payload
        naive_ts = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")  # no tzinfo
        signal = normalize_intelligence_payload(_minimal_valid_payload(detected_at=naive_ts))
        assert signal.detected_at.tzinfo is not None

    def test_trace_payload_embedded_in_signal(self):
        from app.intelligence.adapter import normalize_intelligence_payload
        signal = normalize_intelligence_payload(_minimal_valid_payload())
        assert isinstance(signal.trace_payload, dict)
        assert "trace_id" in signal.trace_payload

    def test_evidence_payload_is_copy_of_raw(self):
        from app.intelligence.adapter import normalize_intelligence_payload
        raw = _minimal_valid_payload()
        signal = normalize_intelligence_payload(raw)
        # evidence_payload must contain the source fields
        assert signal.evidence_payload.get("source_family") == "manual_intelligence"


# ── TestAdapterRejection ──────────────────────────────────────────────────────

class TestAdapterRejection:
    """Malformed payloads raise AdapterError with violations list."""

    def test_missing_required_fields_raises_adapter_error(self):
        from app.intelligence.adapter import normalize_intelligence_payload
        from app.intelligence.trace import AdapterError
        # Empty payload — missing all required fields
        with pytest.raises(AdapterError) as exc_info:
            normalize_intelligence_payload({"source_family": "manual_intelligence"})
        err = exc_info.value
        assert len(err.violations) > 0

    def test_adapter_error_has_to_dict(self):
        from app.intelligence.adapter import normalize_intelligence_payload
        from app.intelligence.trace import AdapterError
        with pytest.raises(AdapterError) as exc_info:
            normalize_intelligence_payload({"source_family": "manual_intelligence"})
        d = exc_info.value.to_dict()
        assert "violations" in d
        assert isinstance(d["violations"], list)

    def test_out_of_range_severity_raises_adapter_error(self):
        from app.intelligence.adapter import normalize_intelligence_payload
        from app.intelligence.trace import AdapterError
        with pytest.raises(AdapterError) as exc_info:
            normalize_intelligence_payload(_minimal_valid_payload(severity_score=2.5))
        fields = [v.field_name for v in exc_info.value.violations]
        assert "severity_score" in fields

    def test_normalize_for_preview_never_raises(self):
        from app.intelligence.adapter import normalize_for_preview
        # Even a completely empty payload should return a dict, never raise
        result = normalize_for_preview({})
        assert isinstance(result, dict)
        assert result.get("success") is False


# ── TestAdapterSourceFamilyEnum ───────────────────────────────────────────────

class TestAdapterSourceFamilyEnum:
    """Unknown source_family values are rejected before validation runs."""

    def test_unknown_family_raises_adapter_error(self):
        from app.intelligence.adapter import normalize_intelligence_payload
        from app.intelligence.trace import AdapterError
        payload = _minimal_valid_payload(source_family="unknown_external_system")
        with pytest.raises(AdapterError) as exc_info:
            normalize_intelligence_payload(payload)
        err_msg = str(exc_info.value)
        assert "unknown_external_system" in err_msg

    def test_unknown_family_violation_rule_is_enum_membership(self):
        from app.intelligence.adapter import normalize_intelligence_payload
        from app.intelligence.trace import AdapterError
        with pytest.raises(AdapterError) as exc_info:
            normalize_intelligence_payload(_minimal_valid_payload(source_family="bad_family"))
        rules = [v.rule for v in exc_info.value.violations]
        assert "ENUM_MEMBERSHIP" in rules


# ── TestBridgeContract ────────────────────────────────────────────────────────

class TestBridgeContract:
    """Bridge eligibility gate + field mapping."""

    def _normalized(self, **overrides):
        from app.intelligence.adapter import normalize_intelligence_payload
        return normalize_intelligence_payload(_minimal_valid_payload(**overrides))

    def test_valid_signal_bridges_to_live_signal(self):
        from app.intelligence.bridge import SignalBridge
        from app.domain.models.live_signal import LiveSignal
        signal = self._normalized()
        live = SignalBridge.to_live_signal(signal)
        assert isinstance(live, LiveSignal)

    def test_severity_score_mapped_correctly(self):
        from app.intelligence.bridge import SignalBridge
        signal = self._normalized(severity_score=0.75)
        live = SignalBridge.to_live_signal(signal)
        assert live.severity_raw == pytest.approx(0.75)

    def test_confidence_score_mapped_correctly(self):
        from app.intelligence.bridge import SignalBridge
        signal = self._normalized(confidence_score=0.9)
        live = SignalBridge.to_live_signal(signal)
        assert live.confidence_raw == pytest.approx(0.9)

    def test_source_systems_become_entity_ids(self):
        from app.intelligence.bridge import SignalBridge
        signal = self._normalized(source_systems=["sys-a", "sys-b"])
        live = SignalBridge.to_live_signal(signal)
        assert set(live.entity_ids) == {"sys-a", "sys-b"}

    def test_summary_truncated_for_description(self):
        from app.intelligence.bridge import SignalBridge
        long_summary = "X" * 600
        signal = self._normalized(summary=long_summary)
        live = SignalBridge.to_live_signal(signal)
        assert len(live.description) == 500

    def test_banking_domain_maps_to_banking_sector(self):
        from app.intelligence.bridge import SignalBridge
        from app.domain.models.live_signal import SignalSector
        signal = self._normalized(affected_domains=["banking", "insurance"])
        live = SignalBridge.to_live_signal(signal)
        assert live.sector == SignalSector.BANKING

    def test_fintech_domain_maps_to_fintech_sector(self):
        from app.intelligence.bridge import SignalBridge
        from app.domain.models.live_signal import SignalSector
        signal = self._normalized(affected_domains=["fintech"])
        live = SignalBridge.to_live_signal(signal)
        assert live.sector == SignalSector.FINTECH

    def test_unknown_domain_defaults_to_banking(self):
        from app.intelligence.bridge import SignalBridge
        from app.domain.models.live_signal import SignalSector
        signal = self._normalized(affected_domains=["regulatory", "infrastructure"])
        live = SignalBridge.to_live_signal(signal)
        # Falls back to BANKING (bridge limitation; logged as warning)
        assert live.sector == SignalSector.BANKING

    def test_manual_intelligence_maps_to_manual_source(self):
        from app.intelligence.bridge import SignalBridge
        from app.domain.models.live_signal import LiveSignalSource
        signal = self._normalized()  # manual_intelligence
        live = SignalBridge.to_live_signal(signal)
        assert live.source == LiveSignalSource.MANUAL

    def test_bridge_payload_contains_bridge_meta(self):
        from app.intelligence.bridge import SignalBridge
        signal = self._normalized()
        live = SignalBridge.to_live_signal(signal)
        assert "bridge_meta" in live.payload
        meta = live.payload["bridge_meta"]
        assert meta["normalized_signal_id"] == signal.normalized_signal_id

    def test_bridge_payload_contains_semantic_sections(self):
        from app.intelligence.bridge import SignalBridge
        signal = self._normalized()
        live = SignalBridge.to_live_signal(signal)
        payload = live.payload
        assert "observed_evidence"  in payload
        assert "inferred_reasoning" in payload
        assert "simulation_context" in payload

    def test_geo_coordinates_are_none(self):
        from app.intelligence.bridge import SignalBridge
        signal = self._normalized()
        live = SignalBridge.to_live_signal(signal)
        assert live.lat is None
        assert live.lng is None

    def test_convenience_function_equivalent_to_class_method(self):
        from app.intelligence.bridge import SignalBridge, bridge_to_live_signal
        signal = self._normalized()
        live_class  = SignalBridge.to_live_signal(signal)
        live_fn     = bridge_to_live_signal(signal)
        # Different signal_ids (uuid), same shape
        assert live_class.source == live_fn.source
        assert live_class.sector == live_fn.sector
        assert live_class.severity_raw == live_fn.severity_raw


# ── TestSemanticSeparation ────────────────────────────────────────────────────

class TestSemanticSeparation:
    """OBSERVED / INFERRED / SIMULATED are never collapsed."""

    def test_observed_evidence_preserved(self):
        from app.intelligence.adapter import normalize_intelligence_payload
        signal = normalize_intelligence_payload(_minimal_valid_payload())
        assert len(signal.observed_evidence) == 1
        ev = signal.observed_evidence[0]
        assert ev.evidence_type.value == "OBSERVED"

    def test_inferred_reasoning_preserved(self):
        from app.intelligence.adapter import normalize_intelligence_payload
        now = datetime.now(timezone.utc).isoformat()
        payload = _minimal_valid_payload(
            inferred_reasoning=[{
                "reasoning_type":   "CREDIT_EXPOSURE",
                "source_system":    "trek",
                "inferred_at":      now,
                "confidence":       0.7,
                "summary":          "Credit exposure flagged.",
                "inferred_severity": 0.65,
            }]
        )
        signal = normalize_intelligence_payload(payload)
        assert len(signal.inferred_reasoning) == 1
        r = signal.inferred_reasoning[0]
        assert r.reasoning_type.value == "CREDIT_EXPOSURE"

    def test_simulated_projection_preserved(self):
        from app.intelligence.adapter import normalize_intelligence_payload
        now = datetime.now(timezone.utc).isoformat()
        payload = _minimal_valid_payload(
            simulation_context=[{
                "simulation_type":    "MONTE_CARLO_RUN",
                "source_system":      "observatory",
                "simulated_at":       now,
                "model_version":      "v1.0",
                "confidence":         0.6,
                "horizon_hours":      72,
                "summary":            "Monte Carlo run complete.",
                "projected_severity": 0.5,
            }]
        )
        signal = normalize_intelligence_payload(payload)
        assert len(signal.simulation_context) == 1
        p = signal.simulation_context[0]
        assert p.simulation_type.value == "MONTE_CARLO_RUN"

    def test_sections_are_not_merged(self):
        """Each semantic section must remain in its own container."""
        from app.intelligence.adapter import normalize_intelligence_payload
        now = datetime.now(timezone.utc).isoformat()
        payload = _minimal_valid_payload(
            inferred_reasoning=[{
                "reasoning_type":   "CONTAGION_RISK",
                "source_system":    "trek",
                "inferred_at":      now,
                "confidence":       0.55,
                "summary":          "Contagion risk assessed.",
                "inferred_severity": 0.5,
            }],
            simulation_context=[{
                "simulation_type":    "SECTOR_STRESS",
                "source_system":      "observatory",
                "simulated_at":       now,
                "model_version":      "v1.0",
                "confidence":         0.5,
                "horizon_hours":      48,
                "summary":            "Sector stress projected.",
                "projected_severity": 0.45,
            }],
        )
        signal = normalize_intelligence_payload(payload)
        assert len(signal.observed_evidence)  == 1  # from base payload
        assert len(signal.inferred_reasoning) == 1
        assert len(signal.simulation_context) == 1
        # No cross-contamination
        assert signal.observed_evidence[0].evidence_type.value  == "OBSERVED"
        assert signal.inferred_reasoning[0].reasoning_type.value == "CONTAGION_RISK"
        assert signal.simulation_context[0].simulation_type.value == "SECTOR_STRESS"

    def test_bridge_preserves_semantic_sections(self):
        """Bridge must carry all three sections into LiveSignal.payload."""
        from app.intelligence.adapter import normalize_intelligence_payload
        from app.intelligence.bridge import SignalBridge
        now = datetime.now(timezone.utc).isoformat()
        payload = _minimal_valid_payload(
            simulation_context=[{
                "simulation_type":    "ENTITY_IMPACT",
                "source_system":      "observatory",
                "simulated_at":       now,
                "model_version":      "v1.0",
                "confidence":         0.7,
                "horizon_hours":      72,
                "summary":            "Entity impact modelled.",
                "projected_severity": 0.6,
            }]
        )
        signal = normalize_intelligence_payload(payload)
        live   = SignalBridge.to_live_signal(signal)

        assert live.payload["observed_evidence"]  != []
        assert live.payload["simulation_context"] != []
        # inferred_reasoning empty but key must be present
        assert "inferred_reasoning" in live.payload


# ── TestSourceStubs ───────────────────────────────────────────────────────────

class TestSourceStubs:
    """TREK and Observatory remain stubs. Jet Nexus is IMPLEMENTED (v1.0.0)."""

    def test_jet_nexus_is_no_longer_a_stub(self):
        """Jet Nexus adapter is implemented — it must not raise NotImplementedError."""
        from app.intelligence.sources.jet_nexus import adapt_jet_nexus_payload
        from app.intelligence.models import NormalizedIntelligenceSignal
        now = datetime.now(timezone.utc).isoformat()
        raw = {
            "event_id":   "nis-test-001",
            "event_type": "port_closure",
            "headline":   "Test event",
            "description": "Test description.",
            "timestamp":  now,
            "severity":   0.5,
            "confidence": 0.7,
            "tags":       ["banking"],
            "regions":    ["SAU"],
            "metadata":   {},
        }
        signal = adapt_jet_nexus_payload(raw)
        assert isinstance(signal, NormalizedIntelligenceSignal)

    def test_trek_stub_raises(self):
        from app.intelligence.sources.trek import adapt_trek_payload
        with pytest.raises(NotImplementedError):
            adapt_trek_payload({})

    def test_impact_observatory_stub_raises(self):
        from app.intelligence.sources.impact_observatory import adapt_impact_observatory_payload
        with pytest.raises(NotImplementedError):
            adapt_impact_observatory_payload({})

    def test_normalize_for_preview_jet_nexus_succeeds(self):
        """Jet Nexus is implemented — normalize_for_preview must return success."""
        from app.intelligence.adapter import normalize_for_preview
        now = datetime.now(timezone.utc).isoformat()
        payload = {
            "source_family": "jet_nexus",
            "event_id":      "preview-001",
            "event_type":    "port_closure",
            "headline":      "Test normalize preview",
            "description":   "Adapter foundation integration test.",
            "timestamp":     now,
            "severity":      0.6,
            "confidence":    0.8,
            "tags":          ["banking"],
            "regions":       ["SAU"],
            "metadata":      {},
        }
        result = normalize_for_preview(payload)
        assert result["success"] is True
        assert result["source_family"] == "jet_nexus"

    def test_adapter_dispatches_to_jn_adapter_not_generic(self):
        """JET_NEXUS payloads dispatch to the JN adapter, not the generic path."""
        from app.intelligence.adapter import normalize_intelligence_payload
        from app.intelligence.models import SourceFamily
        now = datetime.now(timezone.utc).isoformat()
        payload = {
            "source_family": "jet_nexus",
            "event_id":      "dispatch-001",
            "event_type":    "cyber_attack",
            "headline":      "Dispatch test",
            "description":   "Testing adapter dispatch path.",
            "timestamp":     now,
            "severity":      0.7,
            "confidence":    0.9,
            "tags":          ["fintech"],
            "regions":       ["UAE"],
            "metadata":      {},
        }
        signal = normalize_intelligence_payload(payload)
        assert signal.source_family == SourceFamily.JET_NEXUS
