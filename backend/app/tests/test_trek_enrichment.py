"""
TREK Enrichment Adapter — Integration Tests

Tests for the TREK enrichment pipeline as specified in the TREK integration brief.

Required coverage (6 specified scenarios):
    1. TREK adds inferred_reasoning when enabled
    2. Observed data unchanged after TREK enrichment
    3. causal_chain populated with TREK reasoning steps
    4. trace_payload shows INFERRED entries from TREK
    5. Enriched signal passes bridge validation
    6. Bridge preview works end-to-end with TREK

Additional coverage:
    - All TREK reasoning rules (7 rules)
    - Score adjustment logic
    - Multi-rule firing (contagion + liquidity)
    - TREK with low-severity signal (no inferences)
    - TREK stub backward compat (adapt_trek_payload raises NotImplementedError)
    - TREK rejects REJECTED signals
    - API enable_trek flag (via adapter.normalize_for_preview)
    - normalize_with_trek pipeline
    - validate_trek_payload stub
    - Frozen model — enrichment returns new object
    - Semantic separation enforced (observed untouched)
    - Reasoning summary populated
"""

from __future__ import annotations

import pytest
from datetime import datetime, timezone, timedelta
from unittest.mock import patch

from app.intelligence.models import (
    NormalizedIntelligenceSignal,
    NormalizationStatus,
    ObservedEvidence,
    InferredReasoning,
    ReasoningType,
    SourceFamily,
    EvidenceType,
)
from app.intelligence.sources.trek import (
    enrich_with_trek,
    adapt_trek_payload,
    validate_trek_payload,
    TREKAdapterError,
    TREK_CONFIDENCE_WEIGHT,
    _SEV_HIGH,
    _SEV_MEDIUM,
    _SEV_MINIMUM,
    TREK_REQUIRED_FIELDS,
)
from app.intelligence.sources.jet_nexus import adapt_jet_nexus_payload
from app.intelligence.adapter import normalize_with_trek, normalize_for_preview
from app.intelligence.bridge import SignalBridge
from app.intelligence.validators import assert_bridge_eligible


# ─── Fixtures ─────────────────────────────────────────────────────────────────

def _ts(offset_hours: int = 0) -> str:
    """ISO 8601 timestamp offset from now."""
    return (datetime.now(timezone.utc) - timedelta(hours=offset_hours)).isoformat()


def _make_jn_payload(
    severity: float = 0.75,
    confidence: float = 0.80,
    event_type: str = "supply_disruption",
    tags: list[str] | None = None,
    headline: str = "Major port closure disrupts trade finance",
    description: str = "Port operations suspended due to industrial action",
) -> dict:
    return {
        "event_id":    "jn-test-001",
        "event_type":  event_type,
        "headline":    headline,
        "description": description,
        "timestamp":   _ts(1),
        "severity":    severity,
        "confidence":  confidence,
        "tags":        tags if tags is not None else ["banking", "port", "trade"],
        "regions":     ["AE", "SA"],
        "metadata":    {"source": "jet_nexus_feed"},
    }


def _jn_signal(
    severity: float = 0.75,
    confidence: float = 0.80,
    event_type: str = "supply_disruption",
    tags: list[str] | None = None,
    headline: str = "Major port closure disrupts trade finance",
) -> NormalizedIntelligenceSignal:
    """Create a normalized JN signal for enrichment tests."""
    return adapt_jet_nexus_payload(_make_jn_payload(
        severity=severity,
        confidence=confidence,
        event_type=event_type,
        tags=tags,
        headline=headline,
    ))


def _multi_domain_signal(severity: float = 0.75) -> NormalizedIntelligenceSignal:
    """JN signal touching banking + fintech + insurance."""
    return _jn_signal(
        severity=severity,
        tags=["banking", "fintech", "insurance", "payment"],
    )


def _low_severity_signal() -> NormalizedIntelligenceSignal:
    return _jn_signal(severity=0.10, confidence=0.50)


# ─── Scenario 1: TREK adds inferred_reasoning when enabled ────────────────────

class TestTREKAddsInferredReasoning:
    """Required scenario 1: TREK adds inferred_reasoning when enabled."""

    def test_trek_adds_inferred_reasoning_items(self):
        """Basic: high-severity banking signal → at least one InferredReasoning."""
        signal = _jn_signal(severity=0.75, tags=["banking", "trade"])
        assert len(signal.inferred_reasoning) == 0, "JN should produce no inferences"

        enriched = enrich_with_trek(signal)

        assert len(enriched.inferred_reasoning) >= 1
        assert all(isinstance(i, InferredReasoning) for i in enriched.inferred_reasoning)

    def test_trek_inferences_are_typed(self):
        """Each InferredReasoning has a valid ReasoningType."""
        enriched = enrich_with_trek(_jn_signal(severity=0.75, tags=["banking"]))
        for item in enriched.inferred_reasoning:
            assert item.evidence_type == EvidenceType.INFERRED
            assert isinstance(item.reasoning_type, ReasoningType)

    def test_trek_inferences_have_trek_source_system(self):
        """All TREK-generated InferredReasoning items have source_system='trek'."""
        enriched = enrich_with_trek(_jn_signal(severity=0.75, tags=["banking"]))
        trek_items = [i for i in enriched.inferred_reasoning if i.source_system == "trek"]
        assert len(trek_items) >= 1

    def test_no_inference_below_minimum_threshold(self):
        """Severity below _SEV_MINIMUM → no TREK inferences."""
        signal   = _jn_signal(severity=_SEV_MINIMUM - 0.01, tags=["banking"])
        enriched = enrich_with_trek(signal)
        assert len(enriched.inferred_reasoning) == 0

    def test_liquidity_stress_fires_at_high_severity_banking(self):
        """LIQUIDITY_STRESS fires when severity >= _SEV_HIGH and banking domain."""
        signal   = _jn_signal(severity=_SEV_HIGH + 0.05, tags=["banking"])
        enriched = enrich_with_trek(signal)
        rtypes   = {i.reasoning_type for i in enriched.inferred_reasoning}
        assert ReasoningType.LIQUIDITY_STRESS in rtypes

    def test_credit_exposure_fires_at_medium_severity_banking(self):
        """CREDIT_EXPOSURE fires when severity >= _SEV_MEDIUM and banking + disruption."""
        signal   = _jn_signal(severity=_SEV_MEDIUM + 0.05, event_type="supply_disruption", tags=["banking"])
        enriched = enrich_with_trek(signal)
        rtypes   = {i.reasoning_type for i in enriched.inferred_reasoning}
        assert ReasoningType.CREDIT_EXPOSURE in rtypes

    def test_counterparty_risk_fires_for_insurance_domain(self):
        """COUNTERPARTY_RISK fires when insurance domain at medium+ severity."""
        signal   = _jn_signal(severity=0.55, tags=["insurance", "reinsur"])
        enriched = enrich_with_trek(signal)
        rtypes   = {i.reasoning_type for i in enriched.inferred_reasoning}
        assert ReasoningType.COUNTERPARTY_RISK in rtypes

    def test_market_disruption_fires_for_fintech_domain(self):
        """MARKET_DISRUPTION fires when fintech domain at medium+ severity."""
        signal   = _jn_signal(severity=0.55, tags=["fintech", "payment"])
        enriched = enrich_with_trek(signal)
        rtypes   = {i.reasoning_type for i in enriched.inferred_reasoning}
        assert ReasoningType.MARKET_DISRUPTION in rtypes

    def test_contagion_risk_fires_for_multi_domain_high_severity(self):
        """CONTAGION_RISK fires for multi-domain exposure at high severity."""
        signal   = _multi_domain_signal(severity=_SEV_HIGH + 0.05)
        enriched = enrich_with_trek(signal)
        rtypes   = {i.reasoning_type for i in enriched.inferred_reasoning}
        assert ReasoningType.CONTAGION_RISK in rtypes

    def test_regulatory_signal_fires_for_alert_with_regulatory_keyword(self):
        """REGULATORY_SIGNAL fires for alert type with regulatory keyword."""
        signal   = _jn_signal(
            severity=0.55,
            event_type="regulatory_change",
            headline="New compliance directive issued for trade finance",
            tags=["banking"],
        )
        enriched = enrich_with_trek(signal)
        rtypes   = {i.reasoning_type for i in enriched.inferred_reasoning}
        assert ReasoningType.REGULATORY_SIGNAL in rtypes

    def test_generic_inference_fires_as_fallback(self):
        """GENERIC_INFERENCE fires when no specific rule matches but severity is medium+.

        Conditions that avoid all specific rules:
          - event_type="recovery"  → not disruption/escalation (blocks LIQUIDITY+CREDIT)
          -                        → not alert (blocks REGULATORY_SIGNAL)
          - tags=["energy"]        → maps to banking only (single domain → blocks CONTAGION)
          - no fintech              → blocks MARKET_DISRUPTION
          - no insurance            → blocks COUNTERPARTY_RISK
        Only GENERIC_INFERENCE (fallback) should fire.
        """
        signal   = _jn_signal(severity=0.50, event_type="recovery", tags=["energy"])
        enriched = enrich_with_trek(signal)
        rtypes   = {i.reasoning_type for i in enriched.inferred_reasoning}
        assert ReasoningType.GENERIC_INFERENCE in rtypes


# ─── Scenario 2: Observed data unchanged after TREK enrichment ────────────────

class TestObservedDataPreserved:
    """Required scenario 2: Observed data unchanged after TREK enrichment."""

    def test_observed_evidence_count_unchanged(self):
        """TREK must not add or remove observed_evidence items."""
        signal   = _jn_signal(severity=0.75, tags=["banking"])
        enriched = enrich_with_trek(signal)
        assert len(enriched.observed_evidence) == len(signal.observed_evidence)

    def test_observed_evidence_content_identical(self):
        """The single JN ObservedEvidence item is byte-identical after enrichment."""
        signal   = _jn_signal(severity=0.75, tags=["banking"])
        enriched = enrich_with_trek(signal)
        assert enriched.observed_evidence[0] == signal.observed_evidence[0]

    def test_observed_evidence_raw_value_unchanged(self):
        """raw_value inside ObservedEvidence is identical after enrichment."""
        signal   = _jn_signal(severity=0.75, tags=["banking"])
        enriched = enrich_with_trek(signal)
        assert enriched.observed_evidence[0].raw_value == signal.observed_evidence[0].raw_value

    def test_source_family_unchanged(self):
        """source_family stays jet_nexus — TREK does not reclassify the source."""
        signal   = _jn_signal()
        enriched = enrich_with_trek(signal)
        assert enriched.source_family == SourceFamily.JET_NEXUS

    def test_source_systems_contains_original(self):
        """Original source system is still present (trek is APPENDED, not replaced)."""
        signal   = _jn_signal()
        enriched = enrich_with_trek(signal)
        assert "jet_nexus" in enriched.source_systems

    def test_evidence_payload_unchanged(self):
        """evidence_payload (verbatim JN payload) is preserved exactly."""
        signal   = _jn_signal()
        enriched = enrich_with_trek(signal)
        assert enriched.evidence_payload == signal.evidence_payload

    def test_source_event_ids_unchanged(self):
        """source_event_ids from JN are not modified by TREK."""
        signal   = _jn_signal()
        enriched = enrich_with_trek(signal)
        assert enriched.source_event_ids == signal.source_event_ids

    def test_enrichment_returns_new_object(self):
        """Frozen model — enrich_with_trek must return a new NIS, not mutate in place."""
        signal   = _jn_signal()
        enriched = enrich_with_trek(signal)
        assert enriched is not signal
        assert enriched.normalized_signal_id == signal.normalized_signal_id

    def test_simulation_context_unchanged(self):
        """simulation_context (always empty from JN) stays empty after TREK."""
        signal   = _jn_signal()
        enriched = enrich_with_trek(signal)
        assert enriched.simulation_context == []


# ─── Scenario 3: causal_chain populated with TREK reasoning steps ─────────────

class TestCausalChainPopulated:
    """Required scenario 3: causal_chain populated with TREK reasoning steps."""

    def test_causal_chain_not_empty_after_trek(self):
        """Enriched signal has a non-empty causal_chain."""
        enriched = enrich_with_trek(_jn_signal(severity=0.75, tags=["banking"]))
        assert len(enriched.causal_chain) >= 1

    def test_causal_chain_starts_with_observed_anchor(self):
        """First causal step is the 'OBSERVED' anchor from the source signal."""
        enriched = enrich_with_trek(_jn_signal(severity=0.75, tags=["banking"]))
        assert enriched.causal_chain[0].startswith("OBSERVED [JET_NEXUS]")

    def test_causal_chain_includes_inferred_steps(self):
        """Each TREK inference appears as an 'INFERRED [TREK/...]' step."""
        enriched = enrich_with_trek(_jn_signal(severity=0.75, tags=["banking"]))
        inferred_steps = [s for s in enriched.causal_chain if s.startswith("INFERRED [TREK/")]
        assert len(inferred_steps) >= 1

    def test_causal_chain_step_count_matches_inferences(self):
        """Number of INFERRED steps == number of InferredReasoning items from TREK."""
        enriched = enrich_with_trek(_jn_signal(severity=0.75, tags=["banking"]))
        trek_items    = [i for i in enriched.inferred_reasoning if i.source_system == "trek"]
        inferred_steps = [s for s in enriched.causal_chain if s.startswith("INFERRED [TREK/")]
        assert len(inferred_steps) == len(trek_items)

    def test_causal_chain_reasoning_type_in_step_label(self):
        """TREK step labels include the reasoning type for traceability."""
        enriched = enrich_with_trek(_jn_signal(severity=0.75, tags=["banking"]))
        trek_items = [i for i in enriched.inferred_reasoning if i.source_system == "trek"]
        for item in trek_items:
            matching = [s for s in enriched.causal_chain if item.reasoning_type.value in s]
            assert len(matching) >= 1, f"No chain step for {item.reasoning_type.value}"

    def test_causal_chain_includes_title_in_observed_anchor(self):
        """Observed anchor in causal_chain contains the signal title."""
        signal   = _jn_signal(headline="Port closure affects Gulf trade", severity=0.75)
        enriched = enrich_with_trek(signal)
        assert "Port closure affects Gulf trade" in enriched.causal_chain[0]

    def test_causal_chain_empty_when_no_trek_inferences(self):
        """When TREK generates no inferences, causal_chain has only the observed anchor."""
        signal   = _jn_signal(severity=_SEV_MINIMUM - 0.01)
        enriched = enrich_with_trek(signal)
        # Should have exactly 1 item: the observed anchor (no TREK steps)
        assert len(enriched.causal_chain) == 1
        assert "OBSERVED" in enriched.causal_chain[0]


# ─── Scenario 4: trace_payload shows INFERRED entries from TREK ───────────────

class TestTracePayloadInferred:
    """Required scenario 4: trace_payload shows INFERRED entries from TREK."""

    def test_trace_payload_has_trek_enrichment_section(self):
        """Enriched signal trace_payload contains 'trek_enrichment' key."""
        enriched = enrich_with_trek(_jn_signal(severity=0.75, tags=["banking"]))
        assert "trek_enrichment" in enriched.trace_payload

    def test_trek_enrichment_trace_has_expected_keys(self):
        """TREK enrichment trace section has the standard TraceBuilder fields."""
        enriched     = enrich_with_trek(_jn_signal(severity=0.75, tags=["banking"]))
        trek_section = enriched.trace_payload["trek_enrichment"]
        for key in ("trace_id", "adapter_version", "notes", "warnings", "violations"):
            assert key in trek_section, f"Missing key '{key}' in trek_enrichment trace"

    def test_trek_enrichment_trace_has_notes(self):
        """TREK trace section contains adapter notes (rule engine fired messages)."""
        enriched     = enrich_with_trek(_jn_signal(severity=0.75, tags=["banking"]))
        trek_section = enriched.trace_payload["trek_enrichment"]
        assert len(trek_section["notes"]) >= 1

    def test_original_source_trace_preserved(self):
        """Original JN trace in trace_payload is preserved (not overwritten)."""
        signal   = _jn_signal()
        original_trace_id = signal.trace_payload.get("trace_id")
        enriched = enrich_with_trek(signal)
        assert enriched.trace_payload.get("trace_id") == original_trace_id

    def test_trek_trace_source_family_includes_plus_trek(self):
        """TREK trace source_family includes '+trek' suffix to identify enrichment."""
        enriched     = enrich_with_trek(_jn_signal())
        trek_section = enriched.trace_payload["trek_enrichment"]
        assert "+trek" in trek_section["source_family"]

    def test_trek_trace_records_rule_fires(self):
        """Notes in the TREK trace mention the rules that fired."""
        enriched     = enrich_with_trek(_jn_signal(severity=0.75, tags=["banking"]))
        trek_section = enriched.trace_payload["trek_enrichment"]
        note_texts   = " ".join(n.get("message", "") for n in trek_section["notes"])
        # Rule engine completion note must be present
        assert "Rule engine completed" in note_texts or "fired" in note_texts


# ─── Scenario 5: Enriched signal passes bridge validation ─────────────────────

class TestEnrichedSignalPassesBridgeValidation:
    """Required scenario 5: Enriched signal passes bridge validation."""

    def test_enriched_signal_passes_assert_bridge_eligible(self):
        """assert_bridge_eligible does not raise for TREK-enriched signal."""
        enriched = enrich_with_trek(_jn_signal(severity=0.75, tags=["banking"]))
        assert_bridge_eligible(enriched)  # must not raise

    def test_enriched_signal_bridge_eligible_status(self):
        """Enriched signal has NORMALIZED or PARTIAL status (not REJECTED)."""
        enriched = enrich_with_trek(_jn_signal(severity=0.75, tags=["banking"]))
        assert enriched.normalization_status.value in ("NORMALIZED", "PARTIAL")

    def test_enriched_signal_has_required_bridge_fields(self):
        """Bridge-required fields are all present on the enriched signal."""
        enriched = enrich_with_trek(_jn_signal())
        assert enriched.source_family is not None
        assert enriched.signal_type
        assert enriched.severity_score >= 0.0
        assert len(enriched.affected_domains) >= 1

    def test_multiple_inferred_reasonings_still_bridge_eligible(self):
        """Multi-rule fired signal (contagion + liquidity) still passes bridge."""
        signal   = _multi_domain_signal(severity=0.80)
        enriched = enrich_with_trek(signal)
        assert len(enriched.inferred_reasoning) >= 2
        assert_bridge_eligible(enriched)  # must not raise


# ─── Scenario 6: Bridge preview works end-to-end with TREK ───────────────────

class TestBridgePreviewWithTREK:
    """Required scenario 6: Bridge preview works end-to-end with TREK."""

    def test_bridge_preview_produces_live_signal_from_trek_enriched_nis(self):
        """Full pipeline: JN → NIS → TREK enriched NIS → LiveSignal bridge."""
        signal   = adapt_jet_nexus_payload(_make_jn_payload(severity=0.75))
        enriched = enrich_with_trek(signal)
        live     = SignalBridge.to_live_signal(enriched)

        assert live.signal_id.startswith("sig-")
        assert live.severity_raw == enriched.severity_score
        assert live.confidence_raw == enriched.confidence_score

    def test_bridge_live_signal_payload_contains_trek_inferred(self):
        """LiveSignal payload preserves TREK inferred_reasoning section."""
        enriched = enrich_with_trek(_jn_signal(severity=0.75, tags=["banking"]))
        live     = SignalBridge.to_live_signal(enriched)
        assert "inferred_reasoning" in live.payload
        assert len(live.payload["inferred_reasoning"]) >= 1

    def test_bridge_live_signal_payload_contains_observed(self):
        """LiveSignal payload preserves observed section (JN observed_evidence)."""
        enriched = enrich_with_trek(_jn_signal())
        live     = SignalBridge.to_live_signal(enriched)
        assert "observed_evidence" in live.payload

    def test_bridge_live_signal_has_bridge_meta(self):
        """LiveSignal payload has bridge_meta section."""
        enriched = enrich_with_trek(_jn_signal())
        live     = SignalBridge.to_live_signal(enriched)
        assert "bridge_meta" in live.payload

    def test_bridge_does_not_submit_to_hitl_even_with_trek(self):
        """Bridge preview does NOT submit to HITL — TREK enrichment doesn't change this."""
        from app.signals import hitl
        pending_before = list(hitl._pending.keys())
        enriched = enrich_with_trek(_jn_signal(severity=0.75))
        SignalBridge.to_live_signal(enriched)
        pending_after = list(hitl._pending.keys())
        assert pending_before == pending_after, "Bridge must not touch HITL"

    def test_normalize_with_trek_pipeline_produces_bridge_eligible_signal(self):
        """normalize_with_trek (adapter convenience) → bridge eligible."""
        raw      = _make_jn_payload(severity=0.75)
        raw["source_family"] = "jet_nexus"  # add for generic path routing
        enriched = normalize_with_trek({"source_family": "jet_nexus", **raw})
        assert_bridge_eligible(enriched)

    def test_normalize_for_preview_with_enable_trek_flag(self):
        """normalize_for_preview(enable_trek=True) returns success with inferences."""
        raw = {"source_family": "jet_nexus", **_make_jn_payload(severity=0.75)}
        result = normalize_for_preview(raw, enable_trek=True)
        assert result["success"] is True
        semantic = result["semantic_summary"]
        assert semantic["inferred"] >= 1

    def test_normalize_for_preview_without_trek_has_no_inferences(self):
        """normalize_for_preview(enable_trek=False) returns 0 inferred (JN only)."""
        raw    = {"source_family": "jet_nexus", **_make_jn_payload(severity=0.75)}
        result = normalize_for_preview(raw, enable_trek=False)
        assert result["success"] is True
        assert result["semantic_summary"]["inferred"] == 0


# ─── Score adjustment tests ───────────────────────────────────────────────────

class TestScoreAdjustment:
    """TREK score adjustment logic — severity raised, confidence discounted."""

    def test_severity_raised_when_trek_infers_higher(self):
        """When TREK infers severity > original, enriched severity is raised."""
        signal = _jn_signal(severity=_SEV_HIGH + 0.01, tags=["banking"])
        enriched = enrich_with_trek(signal)
        if enriched.inferred_reasoning:
            max_inferred = max(i.inferred_severity for i in enriched.inferred_reasoning)
            assert enriched.severity_score >= signal.severity_score
            assert enriched.severity_score <= 1.0

    def test_severity_never_exceeds_1(self):
        """Enriched severity is always clamped to [0.0, 1.0]."""
        signal   = _jn_signal(severity=0.99, tags=["banking", "fintech", "insurance"])
        enriched = enrich_with_trek(signal)
        assert enriched.severity_score <= 1.0

    def test_confidence_discounted_after_trek(self):
        """When TREK generates inferences, confidence is discounted (TREK_CONFIDENCE_WEIGHT)."""
        signal   = _jn_signal(severity=0.75, tags=["banking"])
        enriched = enrich_with_trek(signal)
        if enriched.inferred_reasoning:
            assert enriched.confidence_score <= signal.confidence_score

    def test_scores_unchanged_when_no_trek_inferences(self):
        """When no TREK inferences fire, scores are identical to original."""
        signal   = _jn_signal(severity=_SEV_MINIMUM - 0.01)
        enriched = enrich_with_trek(signal)
        assert enriched.severity_score  == signal.severity_score
        assert enriched.confidence_score == signal.confidence_score

    def test_reasoning_summary_populated(self):
        """reasoning_summary is non-empty when TREK fires inferences."""
        signal   = _jn_signal(severity=0.75, tags=["banking"])
        enriched = enrich_with_trek(signal)
        if enriched.inferred_reasoning:
            assert len(enriched.reasoning_summary) > 0

    def test_reasoning_summary_empty_when_no_inferences(self):
        """reasoning_summary is empty when TREK fires no inferences."""
        signal   = _jn_signal(severity=_SEV_MINIMUM - 0.01)
        enriched = enrich_with_trek(signal)
        assert enriched.reasoning_summary == ""


# ─── Stub / backward compat tests ────────────────────────────────────────────

class TestTREKStubAndBackwardCompat:
    """Backward compat: adapt_trek_payload stub still raises NotImplementedError."""

    def test_adapt_trek_payload_raises_not_implemented(self):
        """adapt_trek_payload(raw_dict) always raises NotImplementedError."""
        with pytest.raises(NotImplementedError) as exc_info:
            adapt_trek_payload({"some": "payload"})
        assert "enrich_with_trek" in str(exc_info.value)

    def test_validate_trek_payload_stub_returns_errors_for_missing_fields(self):
        """validate_trek_payload stub lists errors for missing required fields."""
        errors = validate_trek_payload({})
        assert len(errors) == len(TREK_REQUIRED_FIELDS)
        for field_name in TREK_REQUIRED_FIELDS:
            assert any(field_name in e for e in errors)

    def test_validate_trek_payload_stub_returns_empty_for_valid(self):
        """validate_trek_payload stub returns empty list when all required fields present."""
        payload = {
            "trek_signal_id":     "trek-001",
            "analysis_type":      "liquidity",
            "severity":           0.7,
            "confidence":         0.8,
            "reasoning":          "Elevated liquidity risk detected",
            "analysis_timestamp": "2026-04-04T10:00:00Z",
            "horizon_hours":      72,
            "domain":             "banking",
        }
        errors = validate_trek_payload(payload)
        assert errors == []

    def test_trek_adapter_error_is_adapter_error_subclass(self):
        """TREKAdapterError is a subclass of AdapterError."""
        from app.intelligence.trace import AdapterError
        assert issubclass(TREKAdapterError, AdapterError)

    def test_enrich_rejects_rejected_signal(self):
        """enrich_with_trek raises TREKAdapterError for a REJECTED signal."""
        signal = _jn_signal().model_copy(update={"normalization_status": NormalizationStatus.REJECTED})
        with pytest.raises(TREKAdapterError) as exc_info:
            enrich_with_trek(signal)
        assert "REJECTED" in str(exc_info.value)


# ─── Semantic separation enforcement ─────────────────────────────────────────

class TestSemanticSeparation:
    """TREK must never collapse observed/inferred/simulated into a single blob."""

    def test_inferred_reasoning_has_inferred_evidence_type(self):
        """All TREK-generated items have evidence_type=INFERRED."""
        enriched = enrich_with_trek(_jn_signal(severity=0.75, tags=["banking"]))
        for item in enriched.inferred_reasoning:
            assert item.evidence_type == EvidenceType.INFERRED

    def test_observed_evidence_has_observed_evidence_type(self):
        """Observed evidence items are not affected by TREK (still OBSERVED)."""
        enriched = enrich_with_trek(_jn_signal(severity=0.75))
        for item in enriched.observed_evidence:
            assert item.evidence_type == EvidenceType.OBSERVED

    def test_semantic_summary_counts_are_correct(self):
        """semantic_summary() reflects the actual list lengths after TREK."""
        enriched = enrich_with_trek(_jn_signal(severity=0.75, tags=["banking"]))
        summary = enriched.semantic_summary()
        assert summary["observed"]  == len(enriched.observed_evidence)
        assert summary["inferred"]  == len(enriched.inferred_reasoning)
        assert summary["simulated"] == len(enriched.simulation_context)

    def test_trek_items_have_reasoning_payload_with_rule_key(self):
        """TREK InferredReasoning items carry reasoning_payload with rule identifier."""
        enriched = enrich_with_trek(_jn_signal(severity=0.75, tags=["banking"]))
        for item in [i for i in enriched.inferred_reasoning if i.source_system == "trek"]:
            assert "rule" in item.reasoning_payload
            assert item.reasoning_payload["rule"] == item.reasoning_type.value

    def test_trek_items_carry_original_scores_in_payload(self):
        """TREK items embed original_severity and original_confidence for audit."""
        signal   = _jn_signal(severity=0.75, confidence=0.80)
        enriched = enrich_with_trek(signal)
        for item in [i for i in enriched.inferred_reasoning if i.source_system == "trek"]:
            assert item.reasoning_payload["original_severity"]   == signal.severity_score
            assert item.reasoning_payload["original_confidence"] == signal.confidence_score
