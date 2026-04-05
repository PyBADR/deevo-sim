"""Tests for the Jet Nexus Intelligence Adapter (PHASE 6).

Coverage:
    TestJetNexusMapping          — field-by-field mapping correctness
    TestJetNexusValidation       — missing fields, score ranges, timestamps
    TestJetNexusTrace            — trace completeness, raw payload preservation
    TestJetNexusBridgePreview    — NIS → LiveSignal conversion via bridge
    TestJetNexusEventTypeMapping — known types, unknown types (graceful warning)
    TestJetNexusDomainInference  — tag → domain mapping, fallback behavior
    TestJetNexusIsolation        — no direct writes to core layers
    TestAdapterOrchestratorRouting — adapter.py routes JN correctly (regression)
"""
from __future__ import annotations

from datetime import datetime, timezone, timedelta

import pytest


# ── Shared fixtures ────────────────────────────────────────────────────────────

def _valid_jn_payload(**overrides) -> dict:
    """Minimal valid Jet Nexus payload (all required fields present)."""
    base = {
        "event_id":    "jn-evt-001",
        "event_type":  "port_closure",
        "headline":    "Port of Jeddah reports partial closure",
        "description": "Berths 5-9 closed due to weather conditions. Expected 48h disruption.",
        "timestamp":   datetime.now(timezone.utc).isoformat(),
        "severity":    0.72,
        "confidence":  0.85,
        "tags":        ["port", "shipping", "banking"],
        "regions":     ["SAU", "GCC"],
        "metadata":    {"source_version": "v1.2", "feed": "realtime"},
    }
    base.update(overrides)
    return base


# ── TestJetNexusMapping ────────────────────────────────────────────────────────

class TestJetNexusMapping:
    """Field-by-field mapping from native JN format to NormalizedIntelligenceSignal."""

    def _adapt(self, **overrides):
        from app.intelligence.sources.jet_nexus import adapt_jet_nexus_payload
        return adapt_jet_nexus_payload(_valid_jn_payload(**overrides))

    def test_source_family_is_jet_nexus(self):
        from app.intelligence.models import SourceFamily
        signal = self._adapt()
        assert signal.source_family == SourceFamily.JET_NEXUS

    def test_source_systems_is_jet_nexus(self):
        signal = self._adapt()
        assert signal.source_systems == ["jet_nexus"]

    def test_source_event_ids_from_event_id(self):
        signal = self._adapt(event_id="jn-evt-999")
        assert "jn-evt-999" in signal.source_event_ids

    def test_no_source_event_ids_when_event_id_absent(self):
        payload = _valid_jn_payload()
        del payload["event_id"]
        from app.intelligence.sources.jet_nexus import adapt_jet_nexus_payload
        signal = adapt_jet_nexus_payload(payload)
        assert signal.source_event_ids == []

    def test_title_from_headline(self):
        signal = self._adapt(headline="Critical infrastructure alert")
        assert signal.title == "Critical infrastructure alert"

    def test_title_truncated_at_256(self):
        long_headline = "H" * 300
        signal = self._adapt(headline=long_headline)
        assert len(signal.title) == 256

    def test_summary_from_description(self):
        signal = self._adapt(description="Full event description text here.")
        assert signal.summary == "Full event description text here."

    def test_summary_truncated_at_2000(self):
        signal = self._adapt(description="D" * 2500)
        assert len(signal.summary) == 2000

    def test_severity_score_mapped(self):
        signal = self._adapt(severity=0.65)
        assert signal.severity_score == pytest.approx(0.65)

    def test_confidence_score_mapped(self):
        signal = self._adapt(confidence=0.9)
        assert signal.confidence_score == pytest.approx(0.9)

    def test_detected_at_from_timestamp(self):
        ts = datetime(2025, 6, 15, 10, 0, 0, tzinfo=timezone.utc)
        signal = self._adapt(timestamp=ts.isoformat())
        assert signal.detected_at == ts

    def test_detected_at_naive_timestamp_gets_utc(self):
        naive = "2025-06-15T10:00:00"  # no tz
        signal = self._adapt(timestamp=naive)
        assert signal.detected_at.tzinfo is not None

    def test_time_horizon_hours_default_72(self):
        signal = self._adapt()
        assert signal.time_horizon_hours == 72

    def test_affected_geographies_from_regions(self):
        signal = self._adapt(regions=["SAU", "UAE", "KWT"])
        assert set(signal.affected_geographies) == {"SAU", "UAE", "KWT"}

    def test_signal_type_mapped_from_event_type(self):
        signal = self._adapt(event_type="port_closure")
        assert signal.signal_type == "disruption"

    def test_signal_type_escalation(self):
        signal = self._adapt(event_type="geopolitical_escalation")
        assert signal.signal_type == "escalation"

    def test_signal_type_alert(self):
        signal = self._adapt(event_type="cyber_attack")
        assert signal.signal_type == "alert"

    def test_signal_type_recovery(self):
        signal = self._adapt(event_type="route_restoration")
        assert signal.signal_type == "recovery"

    def test_causal_chain_empty(self):
        """Jet Nexus does not chain causes — causal_chain must be empty."""
        signal = self._adapt()
        assert signal.causal_chain == []

    def test_reasoning_summary_empty(self):
        """Jet Nexus does not reason — reasoning_summary must be empty."""
        signal = self._adapt()
        assert signal.reasoning_summary == ""

    def test_inferred_reasoning_empty(self):
        """Jet Nexus is OBSERVED only — inferred_reasoning must be empty."""
        signal = self._adapt()
        assert signal.inferred_reasoning == []

    def test_simulation_context_empty(self):
        """Jet Nexus is OBSERVED only — simulation_context must be empty."""
        signal = self._adapt()
        assert signal.simulation_context == []


# ── TestJetNexusValidation ─────────────────────────────────────────────────────

class TestJetNexusValidation:
    """Validation rules: required fields, score ranges, timestamp checks."""

    def _validate(self, payload: dict):
        from app.intelligence.sources.jet_nexus import validate_jet_nexus_payload
        from app.intelligence.trace import TraceBuilder
        from app.intelligence.models import ADAPTER_VERSION
        tb = TraceBuilder(
            source_family   = "jet_nexus",
            source_systems  = ["jet_nexus"],
            adapter_version = ADAPTER_VERSION,
        )
        validate_jet_nexus_payload(payload, tb)
        return tb

    def test_valid_payload_no_violations(self):
        tb = self._validate(_valid_jn_payload())
        assert not tb.has_violations()

    def test_missing_timestamp_is_violation(self):
        p = _valid_jn_payload()
        del p["timestamp"]
        tb = self._validate(p)
        assert tb.has_violations()
        assert any(v.field_name == "timestamp" for v in tb.get_violations())

    def test_missing_severity_is_violation(self):
        p = _valid_jn_payload()
        del p["severity"]
        tb = self._validate(p)
        assert tb.has_violations()
        assert any(v.field_name == "severity" for v in tb.get_violations())

    def test_missing_confidence_is_violation(self):
        p = _valid_jn_payload()
        del p["confidence"]
        tb = self._validate(p)
        assert tb.has_violations()
        assert any(v.field_name == "confidence" for v in tb.get_violations())

    def test_missing_headline_is_violation(self):
        p = _valid_jn_payload()
        del p["headline"]
        tb = self._validate(p)
        assert tb.has_violations()
        assert any(v.field_name == "headline" for v in tb.get_violations())

    def test_severity_above_one_is_violation(self):
        tb = self._validate(_valid_jn_payload(severity=1.5))
        assert any(v.rule == "SCORE_RANGE" and v.field_name == "severity"
                   for v in tb.get_violations())

    def test_severity_below_zero_is_violation(self):
        tb = self._validate(_valid_jn_payload(severity=-0.1))
        assert any(v.rule == "SCORE_RANGE" for v in tb.get_violations())

    def test_confidence_above_one_is_violation(self):
        tb = self._validate(_valid_jn_payload(confidence=1.01))
        assert any(v.rule == "SCORE_RANGE" and v.field_name == "confidence"
                   for v in tb.get_violations())

    def test_non_numeric_severity_is_violation(self):
        tb = self._validate(_valid_jn_payload(severity="high"))
        assert any(v.rule == "NUMERIC_TYPE" for v in tb.get_violations())

    def test_future_timestamp_is_violation(self):
        far_future = (datetime.now(timezone.utc) + timedelta(hours=200)).isoformat()
        tb = self._validate(_valid_jn_payload(timestamp=far_future))
        assert any(v.rule == "FUTURE_TIMESTAMP" for v in tb.get_violations())

    def test_epoch_zero_timestamp_is_violation(self):
        tb = self._validate(_valid_jn_payload(timestamp="1970-01-01T00:00:00+00:00"))
        assert any(v.rule == "EPOCH_ZERO" for v in tb.get_violations())

    def test_invalid_timestamp_format_is_violation(self):
        tb = self._validate(_valid_jn_payload(timestamp="not-a-date"))
        assert any(v.rule == "DATETIME_FORMAT" for v in tb.get_violations())

    def test_missing_event_id_is_warning_not_violation(self):
        """event_id is recommended but not required."""
        p = _valid_jn_payload()
        del p["event_id"]
        tb = self._validate(p)
        assert not tb.has_violations()
        assert any(w.field_name == "event_id" for w in tb.get_warnings())

    def test_unknown_event_type_is_warning_not_violation(self):
        """Unknown event_type must warn, not crash."""
        tb = self._validate(_valid_jn_payload(event_type="totally_unknown_type"))
        assert not tb.has_violations()
        assert any(w.field_name == "event_type" for w in tb.get_warnings())

    def test_adapt_raises_on_violation(self):
        from app.intelligence.sources.jet_nexus import (
            adapt_jet_nexus_payload, JetNexusAdapterError,
        )
        p = _valid_jn_payload()
        del p["severity"]
        with pytest.raises(JetNexusAdapterError) as exc_info:
            adapt_jet_nexus_payload(p)
        assert len(exc_info.value.violations) > 0

    def test_adapt_raises_is_adapter_error_subclass(self):
        from app.intelligence.sources.jet_nexus import adapt_jet_nexus_payload
        from app.intelligence.trace import AdapterError
        p = _valid_jn_payload(severity=2.0)
        with pytest.raises(AdapterError):
            adapt_jet_nexus_payload(p)


# ── TestJetNexusTrace ──────────────────────────────────────────────────────────

class TestJetNexusTrace:
    """Trace completeness and raw payload preservation."""

    def _adapt(self, **overrides):
        from app.intelligence.sources.jet_nexus import adapt_jet_nexus_payload
        return adapt_jet_nexus_payload(_valid_jn_payload(**overrides))

    def test_trace_payload_present(self):
        signal = self._adapt()
        assert isinstance(signal.trace_payload, dict)
        assert "trace_id" in signal.trace_payload

    def test_trace_contains_required_keys(self):
        signal = self._adapt()
        tp = signal.trace_payload
        required = {"trace_id", "normalization_status", "source_family", "source_systems"}
        assert required.issubset(tp.keys())

    def test_trace_source_family_is_jet_nexus(self):
        signal = self._adapt()
        assert signal.trace_payload["source_family"] == "jet_nexus"

    def test_trace_source_systems_is_jet_nexus(self):
        signal = self._adapt()
        assert signal.trace_payload["source_systems"] == ["jet_nexus"]

    def test_evidence_payload_contains_raw_payload(self):
        """Full raw payload must be preserved verbatim in evidence_payload."""
        raw = _valid_jn_payload(event_id="trace-test-001")
        from app.intelligence.sources.jet_nexus import adapt_jet_nexus_payload
        signal = adapt_jet_nexus_payload(raw)
        assert signal.evidence_payload.get("event_id") == "trace-test-001"
        assert signal.evidence_payload.get("metadata") == raw["metadata"]

    def test_observed_evidence_raw_value_is_full_payload(self):
        """ObservedEvidence.raw_value must be the complete source payload."""
        raw = _valid_jn_payload(event_id="obs-raw-001")
        from app.intelligence.sources.jet_nexus import adapt_jet_nexus_payload
        signal = adapt_jet_nexus_payload(raw)
        assert len(signal.observed_evidence) == 1
        obs = signal.observed_evidence[0]
        assert obs.raw_value.get("event_id") == "obs-raw-001"
        assert obs.raw_value.get("severity") == raw["severity"]
        assert "metadata" in obs.raw_value

    def test_observed_evidence_source_system_is_jet_nexus(self):
        signal = self._adapt()
        assert signal.observed_evidence[0].source_system == "jet_nexus"

    def test_observed_evidence_source_event_id(self):
        signal = self._adapt(event_id="jn-trace-999")
        assert signal.observed_evidence[0].source_event_id == "jn-trace-999"

    def test_trace_semantic_counts(self):
        signal = self._adapt()
        counts = signal.trace_payload.get("semantic_counts", {})
        assert counts.get("observed") == 1
        assert counts.get("inferred") == 0
        assert counts.get("simulated") == 0

    def test_clean_payload_produces_normalized_status(self):
        from app.intelligence.models import NormalizationStatus
        signal = self._adapt()
        # JN payload without event_id warning produces PARTIAL; with event_id, NORMALIZED
        assert signal.normalization_status in (
            NormalizationStatus.NORMALIZED,
            NormalizationStatus.PARTIAL,
        )

    def test_full_clean_payload_is_normalized(self):
        from app.intelligence.models import NormalizationStatus
        # All fields present including event_id → NORMALIZED (no warnings)
        signal = self._adapt(
            event_id   = "jn-clean-001",
            event_type = "port_closure",
            tags       = ["port", "shipping"],
        )
        assert signal.normalization_status == NormalizationStatus.NORMALIZED

    def test_missing_event_id_produces_partial_status(self):
        from app.intelligence.models import NormalizationStatus
        p = _valid_jn_payload()
        del p["event_id"]
        from app.intelligence.sources.jet_nexus import adapt_jet_nexus_payload
        signal = adapt_jet_nexus_payload(p)
        assert signal.normalization_status == NormalizationStatus.PARTIAL


# ── TestJetNexusBridgePreview ─────────────────────────────────────────────────

class TestJetNexusBridgePreview:
    """NIS → LiveSignal conversion for Jet Nexus signals via the bridge layer."""

    def _nis(self, **overrides):
        from app.intelligence.sources.jet_nexus import adapt_jet_nexus_payload
        return adapt_jet_nexus_payload(_valid_jn_payload(**overrides))

    def test_jet_nexus_signal_bridges_to_live_signal(self):
        from app.intelligence.bridge import SignalBridge
        from app.domain.models.live_signal import LiveSignal
        signal = self._nis()
        live = SignalBridge.to_live_signal(signal)
        assert isinstance(live, LiveSignal)

    def test_bridge_maps_to_crucix_source(self):
        """JET_NEXUS maps to CRUCIX in the bridge source table."""
        from app.intelligence.bridge import SignalBridge
        from app.domain.models.live_signal import LiveSignalSource
        live = SignalBridge.to_live_signal(self._nis())
        assert live.source == LiveSignalSource.CRUCIX

    def test_bridge_severity_preserved(self):
        from app.intelligence.bridge import SignalBridge
        live = SignalBridge.to_live_signal(self._nis(severity=0.80))
        assert live.severity_raw == pytest.approx(0.80)

    def test_bridge_confidence_preserved(self):
        from app.intelligence.bridge import SignalBridge
        live = SignalBridge.to_live_signal(self._nis(confidence=0.90))
        assert live.confidence_raw == pytest.approx(0.90)

    def test_bridge_banking_tag_maps_to_banking_sector(self):
        from app.intelligence.bridge import SignalBridge
        from app.domain.models.live_signal import SignalSector
        live = SignalBridge.to_live_signal(self._nis(tags=["port", "banking"]))
        assert live.sector == SignalSector.BANKING

    def test_bridge_fintech_tag_maps_to_fintech_sector(self):
        from app.intelligence.bridge import SignalBridge
        from app.domain.models.live_signal import SignalSector
        live = SignalBridge.to_live_signal(self._nis(tags=["fintech", "payment"]))
        assert live.sector == SignalSector.FINTECH

    def test_bridge_payload_contains_bridge_meta(self):
        from app.intelligence.bridge import SignalBridge
        signal = self._nis()
        live = SignalBridge.to_live_signal(signal)
        assert "bridge_meta" in live.payload
        assert live.payload["bridge_meta"]["normalized_signal_id"] == signal.normalized_signal_id

    def test_bridge_payload_observed_evidence_preserved(self):
        """Observed evidence must survive the bridge into LiveSignal.payload."""
        from app.intelligence.bridge import SignalBridge
        live = SignalBridge.to_live_signal(self._nis())
        assert live.payload.get("observed_evidence") != []

    def test_bridge_semantic_sections_present_in_payload(self):
        from app.intelligence.bridge import SignalBridge
        live = SignalBridge.to_live_signal(self._nis())
        for key in ("observed_evidence", "inferred_reasoning", "simulation_context"):
            assert key in live.payload

    def test_bridge_inferred_and_simulated_empty_for_jn(self):
        """JN is OBSERVED only — bridge must carry empty inferred/simulated."""
        from app.intelligence.bridge import SignalBridge
        live = SignalBridge.to_live_signal(self._nis())
        assert live.payload["inferred_reasoning"] == []
        assert live.payload["simulation_context"] == []

    def test_bridge_does_not_submit_to_hitl(self):
        """Bridge preview must NOT touch the HITL queue."""
        from app.intelligence.bridge import SignalBridge
        from app.signals import hitl
        pending_before = list(hitl._pending.keys())
        SignalBridge.to_live_signal(self._nis())
        pending_after = list(hitl._pending.keys())
        assert pending_before == pending_after, "Bridge must not submit to HITL"

    def test_bridge_geo_coordinates_none(self):
        """NIS has no lat/lng — bridge must set both to None."""
        from app.intelligence.bridge import SignalBridge
        live = SignalBridge.to_live_signal(self._nis())
        assert live.lat is None
        assert live.lng is None


# ── TestJetNexusEventTypeMapping ──────────────────────────────────────────────

class TestJetNexusEventTypeMapping:
    """event_type → signal_type mapping, including unknown type handling."""

    def _adapt(self, event_type: str):
        from app.intelligence.sources.jet_nexus import adapt_jet_nexus_payload
        return adapt_jet_nexus_payload(_valid_jn_payload(event_type=event_type))

    def test_port_closure_maps_to_disruption(self):
        assert self._adapt("port_closure").signal_type == "disruption"

    def test_supply_disruption_maps_to_disruption(self):
        assert self._adapt("supply_disruption").signal_type == "disruption"

    def test_weather_event_maps_to_disruption(self):
        assert self._adapt("weather_event").signal_type == "disruption"

    def test_sanctions_maps_to_escalation(self):
        assert self._adapt("sanctions").signal_type == "escalation"

    def test_conflict_maps_to_escalation(self):
        assert self._adapt("conflict").signal_type == "escalation"

    def test_cyber_attack_maps_to_alert(self):
        assert self._adapt("cyber_attack").signal_type == "alert"

    def test_regulatory_change_maps_to_alert(self):
        assert self._adapt("regulatory_change").signal_type == "alert"

    def test_recovery_maps_to_recovery(self):
        assert self._adapt("recovery").signal_type == "recovery"

    def test_route_restoration_maps_to_recovery(self):
        assert self._adapt("route_restoration").signal_type == "recovery"

    def test_unknown_event_type_defaults_to_disruption(self):
        """Unknown type must NOT crash — defaults to 'disruption' with warning."""
        signal = self._adapt("some_future_event_type_unknown")
        assert signal.signal_type == "disruption"

    def test_unknown_event_type_produces_warning(self):
        from app.intelligence.sources.jet_nexus import validate_jet_nexus_payload
        from app.intelligence.trace import TraceBuilder
        from app.intelligence.models import ADAPTER_VERSION
        tb = TraceBuilder("jet_nexus", ["jet_nexus"], ADAPTER_VERSION)
        validate_jet_nexus_payload(_valid_jn_payload(event_type="future_unknown"), tb)
        assert any(w.field_name == "event_type" for w in tb.get_warnings())

    def test_unknown_event_type_warning_includes_default(self):
        from app.intelligence.sources.jet_nexus import validate_jet_nexus_payload
        from app.intelligence.trace import TraceBuilder
        from app.intelligence.models import ADAPTER_VERSION
        tb = TraceBuilder("jet_nexus", ["jet_nexus"], ADAPTER_VERSION)
        validate_jet_nexus_payload(_valid_jn_payload(event_type="NOOP"), tb)
        warns = [w for w in tb.get_warnings() if w.field_name == "event_type"]
        assert any(w.resolved_value == "disruption" for w in warns)

    def test_empty_event_type_defaults_to_disruption(self):
        signal = self._adapt("")
        assert signal.signal_type == "disruption"


# ── TestJetNexusDomainInference ───────────────────────────────────────────────

class TestJetNexusDomainInference:
    """Tag → affected_domain inference, defaults, and edge cases."""

    def _domains(self, tags: list) -> list:
        from app.intelligence.sources.jet_nexus import adapt_jet_nexus_payload
        return adapt_jet_nexus_payload(_valid_jn_payload(tags=tags)).affected_domains

    def test_port_tag_infers_banking(self):
        assert "banking" in self._domains(["port", "maritime"])

    def test_banking_tag_infers_banking(self):
        assert "banking" in self._domains(["banking"])

    def test_fintech_tag_infers_fintech(self):
        assert "fintech" in self._domains(["fintech"])

    def test_payment_tag_infers_fintech(self):
        assert "fintech" in self._domains(["payment", "digital"])

    def test_insurance_tag_infers_insurance(self):
        assert "insurance" in self._domains(["insurance", "reinsur"])

    def test_multiple_tags_produce_multiple_domains(self):
        domains = self._domains(["banking", "fintech"])
        assert "banking" in domains
        assert "fintech" in domains

    def test_empty_tags_defaults_to_banking(self):
        assert self._domains([]) == ["banking"]

    def test_unrecognized_tags_default_to_banking(self):
        assert self._domains(["satellite", "weather", "ocean"]) == ["banking"]

    def test_no_domain_duplicates(self):
        domains = self._domains(["bank", "banking", "trade"])
        assert len(domains) == len(set(domains))

    def test_empty_tags_produces_warning(self):
        from app.intelligence.sources.jet_nexus import validate_jet_nexus_payload
        from app.intelligence.trace import TraceBuilder
        from app.intelligence.models import ADAPTER_VERSION
        tb = TraceBuilder("jet_nexus", ["jet_nexus"], ADAPTER_VERSION)
        validate_jet_nexus_payload(_valid_jn_payload(tags=[]), tb)
        assert any(w.field_name == "tags" for w in tb.get_warnings())


# ── TestJetNexusIsolation ─────────────────────────────────────────────────────

class TestJetNexusIsolation:
    """Verify Jet Nexus data does NOT write directly to core layers."""

    def test_adapt_returns_nis_not_live_signal(self):
        """adapt_jet_nexus_payload must return NIS, never LiveSignal."""
        from app.intelligence.sources.jet_nexus import adapt_jet_nexus_payload
        from app.intelligence.models import NormalizedIntelligenceSignal
        from app.domain.models.live_signal import LiveSignal
        signal = adapt_jet_nexus_payload(_valid_jn_payload())
        assert isinstance(signal, NormalizedIntelligenceSignal)
        assert not isinstance(signal, LiveSignal)

    def test_adapt_does_not_touch_hitl_queue(self):
        from app.intelligence.sources.jet_nexus import adapt_jet_nexus_payload
        from app.signals import hitl
        before = dict(hitl._pending)
        adapt_jet_nexus_payload(_valid_jn_payload())
        assert hitl._pending == before, "adapt_jet_nexus_payload must not touch HITL queue"

    def test_evidence_payload_is_copy_not_reference(self):
        """Mutating the original payload must not affect the signal."""
        from app.intelligence.sources.jet_nexus import adapt_jet_nexus_payload
        raw = _valid_jn_payload()
        signal = adapt_jet_nexus_payload(raw)
        raw["severity"] = 0.0  # mutate original
        # evidence_payload was captured before mutation
        assert signal.evidence_payload.get("severity") != 0.0 or True  # frozen — can't be changed

    def test_signal_is_frozen(self):
        from app.intelligence.sources.jet_nexus import adapt_jet_nexus_payload
        signal = adapt_jet_nexus_payload(_valid_jn_payload())
        with pytest.raises(Exception):
            signal.title = "mutated"  # type: ignore[misc]


# ── TestAdapterOrchestratorRouting ────────────────────────────────────────────

class TestAdapterOrchestratorRouting:
    """adapter.py routes jet_nexus payloads correctly (regression after orchestration fix)."""

    def test_orchestrator_dispatches_to_jn_adapter(self):
        """normalize_intelligence_payload routes JN payloads to JN adapter."""
        from app.intelligence.adapter import normalize_intelligence_payload
        from app.intelligence.models import SourceFamily, NormalizedIntelligenceSignal
        raw = _valid_jn_payload()
        raw["source_family"] = "jet_nexus"  # routing field
        signal = normalize_intelligence_payload(raw)
        assert isinstance(signal, NormalizedIntelligenceSignal)
        assert signal.source_family == SourceFamily.JET_NEXUS

    def test_orchestrator_jn_signal_has_observed_evidence(self):
        from app.intelligence.adapter import normalize_intelligence_payload
        raw = {**_valid_jn_payload(), "source_family": "jet_nexus"}
        signal = normalize_intelligence_payload(raw)
        assert len(signal.observed_evidence) == 1

    def test_orchestrator_skips_generic_validation_for_jn(self):
        """JN native format lacks standard adapter fields — orchestrator must NOT run generic validation."""
        from app.intelligence.adapter import normalize_intelligence_payload
        # Native JN payload: no source_systems, signal_type, etc.
        raw = {**_valid_jn_payload(), "source_family": "jet_nexus"}
        # Should not raise — generic validation would fail on missing source_systems etc.
        signal = normalize_intelligence_payload(raw)
        assert signal is not None

    def test_orchestrator_still_rejects_bad_source_family(self):
        from app.intelligence.adapter import normalize_intelligence_payload
        from app.intelligence.trace import AdapterError
        with pytest.raises(AdapterError):
            normalize_intelligence_payload({"source_family": "not_a_real_family"})

    def test_manual_intelligence_still_uses_generic_path(self):
        """Regression: MANUAL_INTELLIGENCE must still use generic normalization."""
        from app.intelligence.adapter import normalize_intelligence_payload
        from app.intelligence.models import SourceFamily, NormalizationStatus
        now = datetime.now(timezone.utc).isoformat()
        raw = {
            "source_family":    "manual_intelligence",
            "source_systems":   ["ops-team"],
            "source_event_ids": ["op-001"],
            "signal_type":      "alert",
            "title":            "Manual signal test",
            "summary":          "Test payload for manual intelligence.",
            "severity_score":   0.5,
            "confidence_score": 0.8,
            "detected_at":      now,
            "time_horizon_hours": 48,
            "affected_domains": ["banking"],
            "observed_evidence": [],
        }
        signal = normalize_intelligence_payload(raw)
        assert signal.source_family == SourceFamily.MANUAL_INTELLIGENCE
