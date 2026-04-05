"""
Impact Observatory Simulation Enrichment — Integration Tests

Required coverage (6 specified scenarios):
    1. Simulation adds simulation_context
    2. Observed data unchanged after simulation
    3. Inferred data unchanged after simulation
    4. propagation_paths populated
    5. Trace includes SIMULATED entries
    6. Bridge preview still valid

Additional coverage:
    - All simulation types (SCENARIO_PROPAGATION, SECTOR_STRESS, RECOVERY_TRAJECTORY)
    - Propagation graph rules (banking→insurance, banking→fintech, fintech→payments)
    - Impact score computation
    - Exposure estimates per domain
    - Scenario label selection
    - Multi-layer pipeline (JN → TREK → Simulation)
    - Score / status preservation (simulation does not downgrade)
    - normalize_with_simulation() convenience function
    - normalize_for_preview(enable_simulation=True)
    - Stub backward compat (adapt_impact_observatory_payload raises NotImplementedError)
    - Simulation rejects REJECTED signals
    - Simulation works without TREK (single-stage enrichment)
    - Frozen model — returns new object
    - Recovery trajectory not produced for "recovery" signal type
    - Semantic summary counts correct after simulation
"""

from __future__ import annotations

import pytest
from datetime import datetime, timezone, timedelta

from app.intelligence.models import (
    NormalizedIntelligenceSignal,
    NormalizationStatus,
    SimulatedProjection,
    SimulationType,
    EvidenceType,
    SourceFamily,
)
from app.intelligence.sources.impact_observatory import (
    enrich_with_simulation,
    adapt_impact_observatory_payload,
    validate_impact_observatory_payload,
    ImpactObservatoryAdapterError,
    IO_REQUIRED_FIELDS,
    IO_ADAPTER_VERSION,
    _SIM_MINIMUM_SEVERITY,
    _PROPAGATION_GRAPH,
    _DOMAIN_EXPOSURE_WEIGHTS,
)
from app.intelligence.sources.jet_nexus import adapt_jet_nexus_payload
from app.intelligence.sources.trek import enrich_with_trek
from app.intelligence.adapter import normalize_with_simulation, normalize_for_preview
from app.intelligence.bridge import SignalBridge
from app.intelligence.validators import assert_bridge_eligible


# ─── Fixtures ─────────────────────────────────────────────────────────────────

def _ts(offset_hours: int = 1) -> str:
    return (datetime.now(timezone.utc) - timedelta(hours=offset_hours)).isoformat()


def _jn_raw(
    severity: float = 0.75,
    confidence: float = 0.80,
    event_type: str = "supply_disruption",
    tags: list[str] | None = None,
    headline: str = "Major port closure disrupts trade finance",
) -> dict:
    return {
        "event_id":    "jn-sim-test-001",
        "event_type":  event_type,
        "headline":    headline,
        "description": "Port operations suspended due to industrial action",
        "timestamp":   _ts(),
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
    """JN-normalized signal (no TREK enrichment)."""
    return adapt_jet_nexus_payload(_jn_raw(
        severity=severity, confidence=confidence,
        event_type=event_type, tags=tags, headline=headline,
    ))


def _trek_enriched_signal(
    severity: float = 0.75,
    tags: list[str] | None = None,
) -> NormalizedIntelligenceSignal:
    """JN → TREK enriched signal, ready for simulation."""
    return enrich_with_trek(_jn_signal(severity=severity, tags=tags))


def _full_pipeline_signal(
    severity: float = 0.75,
    tags: list[str] | None = None,
) -> NormalizedIntelligenceSignal:
    """Full pipeline: JN → TREK → Simulation."""
    return enrich_with_simulation(_trek_enriched_signal(severity=severity, tags=tags))


def _banking_signal(severity: float = 0.75) -> NormalizedIntelligenceSignal:
    return _trek_enriched_signal(severity=severity, tags=["banking", "port", "trade"])


def _multi_domain_signal(severity: float = 0.75) -> NormalizedIntelligenceSignal:
    return _trek_enriched_signal(severity=severity, tags=["banking", "fintech", "insurance"])


def _low_severity_signal() -> NormalizedIntelligenceSignal:
    return _jn_signal(severity=_SIM_MINIMUM_SEVERITY - 0.01)


# ─── Scenario 1: Simulation adds simulation_context ───────────────────────────

class TestSimulationAddsSimulationContext:
    """Required scenario 1: Simulation adds simulation_context."""

    def test_simulation_context_not_empty_after_enrichment(self):
        """Enriched signal has at least one SimulatedProjection."""
        enriched = enrich_with_simulation(_banking_signal())
        assert len(enriched.simulation_context) >= 1

    def test_simulation_context_items_are_simulated_projections(self):
        """All items in simulation_context are SimulatedProjection instances."""
        enriched = enrich_with_simulation(_banking_signal())
        assert all(isinstance(p, SimulatedProjection) for p in enriched.simulation_context)

    def test_simulation_context_has_scenario_propagation_item(self):
        """Master SCENARIO_PROPAGATION item is always present (above threshold)."""
        enriched = enrich_with_simulation(_banking_signal())
        stypes = {p.simulation_type for p in enriched.simulation_context}
        assert SimulationType.SCENARIO_PROPAGATION in stypes

    def test_simulation_context_has_recovery_trajectory_for_disruption(self):
        """RECOVERY_TRAJECTORY is produced for disruption signal types."""
        enriched = enrich_with_simulation(_banking_signal())
        stypes = {p.simulation_type for p in enriched.simulation_context}
        assert SimulationType.RECOVERY_TRAJECTORY in stypes

    def test_no_recovery_trajectory_for_recovery_signal_type(self):
        """RECOVERY_TRAJECTORY is NOT produced when signal_type is 'recovery'."""
        signal   = _jn_signal(severity=0.75, event_type="recovery")
        enriched = enrich_with_simulation(signal)
        stypes   = [p.simulation_type for p in enriched.simulation_context]
        assert SimulationType.RECOVERY_TRAJECTORY not in stypes

    def test_no_simulation_below_threshold(self):
        """No simulation_context items when severity < _SIM_MINIMUM_SEVERITY."""
        signal   = _low_severity_signal()
        enriched = enrich_with_simulation(signal)
        assert len(enriched.simulation_context) == 0

    def test_simulation_context_items_have_evidence_type_simulated(self):
        """Every SimulatedProjection has evidence_type=SIMULATED."""
        enriched = enrich_with_simulation(_banking_signal())
        for proj in enriched.simulation_context:
            assert proj.evidence_type == EvidenceType.SIMULATED

    def test_simulation_context_items_have_impact_observatory_source(self):
        """Every new SimulatedProjection has source_system='impact_observatory'."""
        enriched = enrich_with_simulation(_banking_signal())
        for proj in enriched.simulation_context:
            assert proj.source_system == "impact_observatory"

    def test_master_projection_has_scenario_label(self):
        """Master SCENARIO_PROPAGATION carries a scenario_label in simulation_payload."""
        enriched = enrich_with_simulation(_banking_signal())
        master   = next(
            p for p in enriched.simulation_context
            if p.simulation_type == SimulationType.SCENARIO_PROPAGATION
        )
        assert "scenario_label" in master.simulation_payload
        assert isinstance(master.simulation_payload["scenario_label"], str)
        assert len(master.simulation_payload["scenario_label"]) > 0

    def test_master_projection_has_impact_score(self):
        """Master SCENARIO_PROPAGATION carries impact_score in [0, 1]."""
        enriched = enrich_with_simulation(_banking_signal())
        master   = next(
            p for p in enriched.simulation_context
            if p.simulation_type == SimulationType.SCENARIO_PROPAGATION
        )
        impact_score = master.simulation_payload["impact_score"]
        assert 0.0 <= impact_score <= 1.0

    def test_master_projection_has_exposure_estimates(self):
        """Master SCENARIO_PROPAGATION carries exposure_estimates dict."""
        enriched = enrich_with_simulation(_banking_signal())
        master   = next(
            p for p in enriched.simulation_context
            if p.simulation_type == SimulationType.SCENARIO_PROPAGATION
        )
        exposure = master.simulation_payload["exposure_estimates"]
        assert isinstance(exposure, dict)
        assert len(exposure) >= 1

    def test_master_projection_has_time_horizon_hours(self):
        """Master SCENARIO_PROPAGATION carries time_horizon_hours."""
        enriched = enrich_with_simulation(_banking_signal())
        master   = next(
            p for p in enriched.simulation_context
            if p.simulation_type == SimulationType.SCENARIO_PROPAGATION
        )
        assert "time_horizon_hours" in master.simulation_payload
        assert master.simulation_payload["time_horizon_hours"] > 0

    def test_projected_severity_in_range(self):
        """All SimulatedProjection items have projected_severity in [0.0, 1.0]."""
        enriched = enrich_with_simulation(_banking_signal())
        for proj in enriched.simulation_context:
            assert 0.0 <= proj.projected_severity <= 1.0

    def test_simulation_confidence_in_range(self):
        """All SimulatedProjection items have confidence in [0.0, 1.0]."""
        enriched = enrich_with_simulation(_banking_signal())
        for proj in enriched.simulation_context:
            assert 0.0 <= proj.confidence <= 1.0


# ─── Scenario 2: Observed data unchanged after simulation ─────────────────────

class TestObservedDataUnchanged:
    """Required scenario 2: Observed data unchanged after simulation."""

    def test_observed_evidence_count_unchanged(self):
        """Simulation does not add or remove observed_evidence items."""
        signal   = _banking_signal()
        enriched = enrich_with_simulation(signal)
        assert len(enriched.observed_evidence) == len(signal.observed_evidence)

    def test_observed_evidence_content_identical(self):
        """ObservedEvidence items are identical after simulation."""
        signal   = _jn_signal()
        enriched = enrich_with_simulation(signal)
        for original, after in zip(signal.observed_evidence, enriched.observed_evidence):
            assert original == after

    def test_observed_raw_value_unchanged(self):
        """raw_value in ObservedEvidence is unchanged by simulation."""
        signal   = _jn_signal()
        enriched = enrich_with_simulation(signal)
        assert enriched.observed_evidence[0].raw_value == signal.observed_evidence[0].raw_value

    def test_evidence_payload_unchanged(self):
        """evidence_payload (verbatim source payload) unchanged by simulation."""
        signal   = _jn_signal()
        enriched = enrich_with_simulation(signal)
        assert enriched.evidence_payload == signal.evidence_payload

    def test_source_family_unchanged(self):
        """source_family is preserved (simulation does not reclassify)."""
        signal   = _jn_signal()
        enriched = enrich_with_simulation(signal)
        assert enriched.source_family == signal.source_family

    def test_source_event_ids_unchanged(self):
        """source_event_ids from original source preserved."""
        signal   = _jn_signal()
        enriched = enrich_with_simulation(signal)
        assert enriched.source_event_ids == signal.source_event_ids

    def test_simulation_returns_new_object(self):
        """Frozen model — enrich_with_simulation returns new NIS, does not mutate."""
        signal   = _jn_signal()
        enriched = enrich_with_simulation(signal)
        assert enriched is not signal
        assert enriched.normalized_signal_id == signal.normalized_signal_id


# ─── Scenario 3: Inferred data unchanged after simulation ─────────────────────

class TestInferredDataUnchanged:
    """Required scenario 3: Inferred data (TREK) unchanged after simulation."""

    def test_inferred_reasoning_count_unchanged(self):
        """Simulation does not add or remove inferred_reasoning items."""
        signal   = _trek_enriched_signal(severity=0.75, tags=["banking"])
        pre_count = len(signal.inferred_reasoning)
        enriched  = enrich_with_simulation(signal)
        assert len(enriched.inferred_reasoning) == pre_count

    def test_inferred_reasoning_content_identical(self):
        """inferred_reasoning items are identical after simulation."""
        signal   = _trek_enriched_signal(severity=0.75, tags=["banking"])
        enriched = enrich_with_simulation(signal)
        for orig, after in zip(signal.inferred_reasoning, enriched.inferred_reasoning):
            assert orig == after

    def test_causal_chain_unchanged(self):
        """causal_chain is not modified by simulation."""
        signal   = _trek_enriched_signal()
        enriched = enrich_with_simulation(signal)
        assert enriched.causal_chain == signal.causal_chain

    def test_reasoning_summary_unchanged(self):
        """reasoning_summary is not modified by simulation."""
        signal   = _trek_enriched_signal()
        enriched = enrich_with_simulation(signal)
        assert enriched.reasoning_summary == signal.reasoning_summary

    def test_simulation_on_non_trek_signal_has_zero_inferred(self):
        """When applied directly on JN signal (no TREK), inferred stays at 0."""
        signal   = _jn_signal(severity=0.75)
        enriched = enrich_with_simulation(signal)
        assert len(enriched.inferred_reasoning) == 0

    def test_full_pipeline_preserves_trek_inferences(self):
        """Full JN→TREK→Simulation pipeline preserves all TREK inferences."""
        jn_signal      = _jn_signal(severity=0.75, tags=["banking"])
        trek_signal    = enrich_with_trek(jn_signal)
        sim_signal     = enrich_with_simulation(trek_signal)
        assert len(sim_signal.inferred_reasoning) == len(trek_signal.inferred_reasoning)
        for orig, after in zip(trek_signal.inferred_reasoning, sim_signal.inferred_reasoning):
            assert orig == after


# ─── Scenario 4: propagation_paths populated ─────────────────────────────────

class TestPropagationPathsPopulated:
    """Required scenario 4: propagation_paths populated in simulation_context."""

    def test_propagation_paths_in_master_projection(self):
        """Master SCENARIO_PROPAGATION carries a propagation_paths list."""
        enriched = enrich_with_simulation(_banking_signal())
        master   = next(
            p for p in enriched.simulation_context
            if p.simulation_type == SimulationType.SCENARIO_PROPAGATION
        )
        paths = master.simulation_payload["propagation_paths"]
        assert isinstance(paths, list)

    def test_banking_propagates_to_insurance(self):
        """Banking seed domain produces banking→insurance propagation path."""
        signal   = enrich_with_simulation(_jn_signal(severity=0.75, tags=["banking"]))
        master   = next(
            p for p in signal.simulation_context
            if p.simulation_type == SimulationType.SCENARIO_PROPAGATION
        )
        paths      = master.simulation_payload["propagation_paths"]
        path_pairs = [(p["from_domain"], p["to_domain"]) for p in paths]
        assert ("banking", "insurance") in path_pairs

    def test_banking_propagates_to_fintech(self):
        """Banking seed domain produces banking→fintech propagation path."""
        signal   = enrich_with_simulation(_jn_signal(severity=0.75, tags=["banking"]))
        master   = next(
            p for p in signal.simulation_context
            if p.simulation_type == SimulationType.SCENARIO_PROPAGATION
        )
        paths      = master.simulation_payload["propagation_paths"]
        path_pairs = [(p["from_domain"], p["to_domain"]) for p in paths]
        assert ("banking", "fintech") in path_pairs

    def test_fintech_propagates_to_payments(self):
        """Fintech in propagated domains triggers fintech→payments path."""
        # fintech is propagated from banking → then payments is propagated from fintech
        signal   = enrich_with_simulation(_jn_signal(severity=0.75, tags=["banking"]))
        master   = next(
            p for p in signal.simulation_context
            if p.simulation_type == SimulationType.SCENARIO_PROPAGATION
        )
        paths      = master.simulation_payload["propagation_paths"]
        path_pairs = [(p["from_domain"], p["to_domain"]) for p in paths]
        assert ("fintech", "payments") in path_pairs

    def test_propagation_paths_have_required_fields(self):
        """Each propagation path carries all required fields."""
        enriched = enrich_with_simulation(_banking_signal())
        master   = next(
            p for p in enriched.simulation_context
            if p.simulation_type == SimulationType.SCENARIO_PROPAGATION
        )
        for path in master.simulation_payload["propagation_paths"]:
            for field in ("from_domain", "to_domain", "transmission_weight",
                          "transmitted_severity", "hop_depth", "rule"):
                assert field in path, f"Missing field '{field}' in propagation path"

    def test_transmission_weights_in_range(self):
        """All transmission_weight values are in (0, 1]."""
        enriched = enrich_with_simulation(_banking_signal())
        master   = next(
            p for p in enriched.simulation_context
            if p.simulation_type == SimulationType.SCENARIO_PROPAGATION
        )
        for path in master.simulation_payload["propagation_paths"]:
            assert 0.0 < path["transmission_weight"] <= 1.0

    def test_transmitted_severity_does_not_exceed_original(self):
        """Transmitted severity is always ≤ original signal severity."""
        original_sev = 0.75
        enriched     = enrich_with_simulation(_jn_signal(severity=original_sev, tags=["banking"]))
        master       = next(
            p for p in enriched.simulation_context
            if p.simulation_type == SimulationType.SCENARIO_PROPAGATION
        )
        for path in master.simulation_payload["propagation_paths"]:
            assert path["transmitted_severity"] <= original_sev + 1e-6  # float tolerance

    def test_sector_stress_items_per_propagated_domain(self):
        """SECTOR_STRESS items are produced for propagated domains."""
        enriched = enrich_with_simulation(_banking_signal())
        stress_items = [
            p for p in enriched.simulation_context
            if p.simulation_type == SimulationType.SECTOR_STRESS
        ]
        assert len(stress_items) >= 1

    def test_no_duplicate_domains_in_propagation(self):
        """all_domains_reached in simulation_payload has no duplicates."""
        enriched = enrich_with_simulation(_banking_signal())
        master   = next(
            p for p in enriched.simulation_context
            if p.simulation_type == SimulationType.SCENARIO_PROPAGATION
        )
        all_d = master.simulation_payload["all_domains_reached"]
        assert len(all_d) == len(set(all_d)), "Duplicate domains in all_domains_reached"

    def test_scenario_label_banking_disruption(self):
        """banking + disruption/escalation → 'banking_propagation_stress' label."""
        enriched = enrich_with_simulation(_jn_signal(
            severity=0.75, event_type="supply_disruption", tags=["banking"],
        ))
        master = next(
            p for p in enriched.simulation_context
            if p.simulation_type == SimulationType.SCENARIO_PROPAGATION
        )
        assert master.simulation_payload["scenario_label"] == "banking_propagation_stress"

    def test_scenario_label_cross_sector_contagion(self):
        """3+ SEED domain signal → 'cross_sector_contagion' scenario label.

        Contagion is triggered by 3+ seed domains (original affected_domains),
        NOT by the propagated domain set. A banking-only signal propagating to
        fintech/insurance is 'banking_propagation_stress', not contagion.
        Tags: banking + fintech + insurance → 3 distinct seed domains.
        """
        signal   = _jn_signal(
            severity=0.75,
            tags=["banking", "fintech", "insurance", "reinsur"],
        )
        enriched = enrich_with_simulation(signal)
        master   = next(
            p for p in enriched.simulation_context
            if p.simulation_type == SimulationType.SCENARIO_PROPAGATION
        )
        # 3 seed domains: banking, fintech, insurance → cross_sector_contagion
        assert master.simulation_payload["scenario_label"] == "cross_sector_contagion"

    def test_scenario_label_recovery_trajectory(self):
        """recovery signal_type → 'recovery_trajectory' scenario label."""
        signal   = _jn_signal(severity=0.75, event_type="recovery", tags=["banking"])
        enriched = enrich_with_simulation(signal)
        master   = next(
            p for p in enriched.simulation_context
            if p.simulation_type == SimulationType.SCENARIO_PROPAGATION
        )
        assert master.simulation_payload["scenario_label"] == "recovery_trajectory"


# ─── Scenario 5: Trace includes SIMULATED entries ────────────────────────────

class TestTraceIncludesSimulatedEntries:
    """Required scenario 5: trace_payload shows SIMULATED entries from Observatory."""

    def test_trace_payload_has_simulation_enrichment_section(self):
        """Enriched signal trace_payload contains 'simulation_enrichment' key."""
        enriched = enrich_with_simulation(_banking_signal())
        assert "simulation_enrichment" in enriched.trace_payload

    def test_simulation_trace_has_expected_keys(self):
        """simulation_enrichment section has standard TraceBuilder fields."""
        enriched = enrich_with_simulation(_banking_signal())
        sim_section = enriched.trace_payload["simulation_enrichment"]
        for key in ("trace_id", "adapter_version", "notes", "warnings", "violations"):
            assert key in sim_section

    def test_simulation_trace_has_notes(self):
        """simulation_enrichment trace contains notes (engine decision messages)."""
        enriched    = enrich_with_simulation(_banking_signal())
        sim_section = enriched.trace_payload["simulation_enrichment"]
        assert len(sim_section["notes"]) >= 1

    def test_simulation_trace_records_scenario_label(self):
        """Notes in simulation trace mention the scenario label."""
        enriched    = enrich_with_simulation(_banking_signal())
        sim_section = enriched.trace_payload["simulation_enrichment"]
        note_texts  = " ".join(n.get("message", "") for n in sim_section["notes"])
        assert "Scenario" in note_texts or "scenario" in note_texts

    def test_simulation_trace_records_propagation(self):
        """Notes in simulation trace mention propagation paths."""
        enriched    = enrich_with_simulation(_banking_signal())
        sim_section = enriched.trace_payload["simulation_enrichment"]
        note_texts  = " ".join(n.get("message", "") for n in sim_section["notes"])
        assert "propagation" in note_texts.lower() or "banking→" in note_texts

    def test_original_source_trace_preserved(self):
        """Original JN trace in trace_payload is not overwritten."""
        signal   = _jn_signal()
        original_trace_id = signal.trace_payload.get("trace_id")
        enriched = enrich_with_simulation(signal)
        assert enriched.trace_payload.get("trace_id") == original_trace_id

    def test_trek_trace_preserved_after_simulation(self):
        """TREK enrichment trace is not overwritten when simulation runs after TREK."""
        trek_signal  = enrich_with_trek(_jn_signal(severity=0.75, tags=["banking"]))
        sim_signal   = enrich_with_simulation(trek_signal)
        assert "trek_enrichment" in sim_signal.trace_payload
        assert "simulation_enrichment" in sim_signal.trace_payload

    def test_simulation_trace_adapter_version_is_set(self):
        """simulation_enrichment trace carries the IO adapter version."""
        enriched    = enrich_with_simulation(_banking_signal())
        sim_section = enriched.trace_payload["simulation_enrichment"]
        assert sim_section["adapter_version"] == IO_ADAPTER_VERSION

    def test_simulation_trace_source_family_includes_simulation_marker(self):
        """TREK trace source_family has '+simulation' suffix."""
        enriched    = enrich_with_simulation(_banking_signal())
        sim_section = enriched.trace_payload["simulation_enrichment"]
        assert "+simulation" in sim_section["source_family"]

    def test_master_projection_has_rules_applied_in_payload(self):
        """Master SCENARIO_PROPAGATION simulation_payload carries rules_applied list."""
        enriched = enrich_with_simulation(_banking_signal())
        master   = next(
            p for p in enriched.simulation_context
            if p.simulation_type == SimulationType.SCENARIO_PROPAGATION
        )
        assert "rules_applied" in master.simulation_payload
        assert isinstance(master.simulation_payload["rules_applied"], list)

    def test_master_projection_has_simulation_assumptions(self):
        """Master SCENARIO_PROPAGATION carries simulation_assumptions list."""
        enriched = enrich_with_simulation(_banking_signal())
        master   = next(
            p for p in enriched.simulation_context
            if p.simulation_type == SimulationType.SCENARIO_PROPAGATION
        )
        assumptions = master.simulation_payload["simulation_assumptions"]
        assert isinstance(assumptions, list)
        assert len(assumptions) >= 1


# ─── Scenario 6: Bridge preview still valid ───────────────────────────────────

class TestBridgePreviewStillValid:
    """Required scenario 6: Bridge preview still valid after simulation enrichment."""

    def test_simulated_signal_passes_assert_bridge_eligible(self):
        """assert_bridge_eligible does not raise for simulation-enriched signal."""
        enriched = enrich_with_simulation(_banking_signal())
        assert_bridge_eligible(enriched)  # must not raise

    def test_simulated_signal_has_normalized_or_partial_status(self):
        """Enriched signal has NORMALIZED or PARTIAL status (never REJECTED)."""
        enriched = enrich_with_simulation(_banking_signal())
        assert enriched.normalization_status.value in ("NORMALIZED", "PARTIAL")

    def test_bridge_produces_live_signal_from_simulated_nis(self):
        """Full pipeline: JN → TREK → Simulation → Bridge → LiveSignal."""
        signal   = _jn_signal(severity=0.75)
        trek_s   = enrich_with_trek(signal)
        sim_s    = enrich_with_simulation(trek_s)
        live     = SignalBridge.to_live_signal(sim_s)
        assert live.signal_id.startswith("sig-")

    def test_bridge_live_signal_payload_has_simulation_context(self):
        """LiveSignal.payload contains simulation_context section."""
        enriched = enrich_with_simulation(_banking_signal())
        live     = SignalBridge.to_live_signal(enriched)
        assert "simulation_context" in live.payload
        assert len(live.payload["simulation_context"]) >= 1

    def test_bridge_live_signal_payload_preserves_all_three_semantic_sections(self):
        """LiveSignal payload has observed_evidence, inferred_reasoning, simulation_context."""
        trek_s   = enrich_with_trek(_jn_signal(severity=0.75, tags=["banking"]))
        sim_s    = enrich_with_simulation(trek_s)
        live     = SignalBridge.to_live_signal(sim_s)
        assert "observed_evidence"  in live.payload
        assert "inferred_reasoning" in live.payload
        assert "simulation_context" in live.payload

    def test_bridge_does_not_submit_to_hitl(self):
        """Bridge preview with simulation does NOT submit to HITL."""
        from app.signals import hitl
        pending_before = list(hitl._pending.keys())
        enriched = enrich_with_simulation(_banking_signal())
        SignalBridge.to_live_signal(enriched)
        pending_after = list(hitl._pending.keys())
        assert pending_before == pending_after

    def test_bridge_severity_matches_enriched_signal(self):
        """LiveSignal.severity_raw matches enriched signal severity_score."""
        enriched = enrich_with_simulation(_banking_signal())
        live     = SignalBridge.to_live_signal(enriched)
        assert live.severity_raw == enriched.severity_score

    def test_signal_bridge_eligible_without_trek(self):
        """Simulation enrichment alone (no TREK) still produces bridge-eligible signal."""
        signal   = _jn_signal(severity=0.75, tags=["banking"])
        enriched = enrich_with_simulation(signal)
        assert_bridge_eligible(enriched)


# ─── Pipeline tests ───────────────────────────────────────────────────────────

class TestFullPipeline:
    """Full 3-layer pipeline: JN → TREK → Simulation."""

    def test_normalize_with_simulation_end_to_end(self):
        """normalize_with_simulation() convenience function works end-to-end."""
        raw      = {"source_family": "jet_nexus", **_jn_raw(severity=0.75)}
        enriched = normalize_with_simulation(raw, enable_trek=True)
        assert len(enriched.observed_evidence)  >= 1
        assert len(enriched.inferred_reasoning) >= 1
        assert len(enriched.simulation_context) >= 1

    def test_normalize_with_simulation_without_trek(self):
        """normalize_with_simulation(enable_trek=False) skips TREK but runs simulation."""
        raw      = {"source_family": "jet_nexus", **_jn_raw(severity=0.75)}
        enriched = normalize_with_simulation(raw, enable_trek=False)
        assert len(enriched.inferred_reasoning) == 0
        assert len(enriched.simulation_context) >= 1

    def test_normalize_for_preview_enable_simulation(self):
        """normalize_for_preview(enable_simulation=True) returns success with simulations."""
        raw    = {"source_family": "jet_nexus", **_jn_raw(severity=0.75)}
        result = normalize_for_preview(raw, enable_trek=True, enable_simulation=True)
        assert result["success"] is True
        assert result["semantic_summary"]["simulated"] >= 1

    def test_normalize_for_preview_without_simulation_has_no_projections(self):
        """normalize_for_preview(enable_simulation=False) returns 0 simulated."""
        raw    = {"source_family": "jet_nexus", **_jn_raw(severity=0.75)}
        result = normalize_for_preview(raw, enable_trek=True, enable_simulation=False)
        assert result["success"] is True
        assert result["semantic_summary"]["simulated"] == 0

    def test_semantic_summary_correct_after_full_pipeline(self):
        """semantic_summary() returns correct counts after all 3 enrichment layers."""
        enriched = _full_pipeline_signal(severity=0.75)
        summary  = enriched.semantic_summary()
        assert summary["observed"]  == len(enriched.observed_evidence)
        assert summary["inferred"]  == len(enriched.inferred_reasoning)
        assert summary["simulated"] == len(enriched.simulation_context)

    def test_three_semantic_sections_all_populated_full_pipeline(self):
        """Full pipeline produces non-zero observed, inferred, and simulated."""
        enriched = _full_pipeline_signal(severity=0.75, tags=["banking"])
        assert len(enriched.observed_evidence)  >= 1
        assert len(enriched.inferred_reasoning) >= 1
        assert len(enriched.simulation_context) >= 1

    def test_all_three_semantic_types_distinct(self):
        """observed, inferred, and simulated sections never share the same items."""
        enriched = _full_pipeline_signal(severity=0.75, tags=["banking"])
        obs_ids  = {id(e) for e in enriched.observed_evidence}
        inf_ids  = {id(e) for e in enriched.inferred_reasoning}
        sim_ids  = {id(e) for e in enriched.simulation_context}
        assert obs_ids.isdisjoint(inf_ids)
        assert obs_ids.isdisjoint(sim_ids)
        assert inf_ids.isdisjoint(sim_ids)


# ─── Stub and backward compat ────────────────────────────────────────────────

class TestStubAndBackwardCompat:
    """Backward compat: adapt_impact_observatory_payload raises NotImplementedError."""

    def test_adapt_impact_observatory_payload_raises_not_implemented(self):
        """adapt_impact_observatory_payload(raw) raises NotImplementedError."""
        with pytest.raises(NotImplementedError) as exc_info:
            adapt_impact_observatory_payload({"some": "payload"})
        assert "enrich_with_simulation" in str(exc_info.value)

    def test_validate_impact_observatory_payload_errors_on_empty(self):
        """validate_impact_observatory_payload({}) lists all required field errors."""
        errors = validate_impact_observatory_payload({})
        assert len(errors) == len(IO_REQUIRED_FIELDS)

    def test_validate_impact_observatory_payload_valid(self):
        """validate_impact_observatory_payload returns empty list for valid payload."""
        payload = {
            "run_id":               "run-001",
            "scenario_id":          "sc-001",
            "model_version":        "v1.0",
            "simulation_type":      "scenario_propagation",
            "projected_severity":   0.75,
            "confidence":           0.80,
            "horizon_hours":        72,
            "affected_domains":     ["banking"],
            "simulated_at":         "2026-04-04T10:00:00Z",
        }
        errors = validate_impact_observatory_payload(payload)
        assert errors == []

    def test_validate_detects_severity_out_of_range(self):
        """validate_impact_observatory_payload flags projected_severity > 1.0."""
        payload = {
            "run_id":               "run-001",
            "scenario_id":          "sc-001",
            "model_version":        "v1.0",
            "simulation_type":      "scenario_propagation",
            "projected_severity":   1.5,
            "confidence":           0.80,
            "horizon_hours":        72,
            "affected_domains":     ["banking"],
            "simulated_at":         "2026-04-04T10:00:00Z",
        }
        errors = validate_impact_observatory_payload(payload)
        assert any("projected_severity" in e for e in errors)

    def test_simulation_rejects_rejected_signal(self):
        """enrich_with_simulation raises ImpactObservatoryAdapterError for REJECTED signal."""
        signal = _jn_signal().model_copy(update={"normalization_status": NormalizationStatus.REJECTED})
        with pytest.raises(ImpactObservatoryAdapterError) as exc_info:
            enrich_with_simulation(signal)
        assert "REJECTED" in str(exc_info.value)

    def test_impact_observatory_adapter_error_is_adapter_error_subclass(self):
        """ImpactObservatoryAdapterError is a subclass of AdapterError."""
        from app.intelligence.trace import AdapterError
        assert issubclass(ImpactObservatoryAdapterError, AdapterError)
