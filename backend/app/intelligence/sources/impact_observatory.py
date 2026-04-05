"""
Intelligence Adapter — Impact Observatory Simulation Enrichment Adapter

INTEGRATION STATUS: IMPLEMENTED (v1.0.0)

The Impact Observatory is the simulation layer of the Intelligence Adapter pipeline.
It operates on an already-normalized NormalizedIntelligenceSignal (ideally TREK-enriched)
and produces an ENRICHED signal with simulated impact projections.

POSITION IN PIPELINE:
    Jet Nexus → adapt_jet_nexus_payload → [NIS]
        → enrich_with_trek            → [NIS + inferred]
        → enrich_with_simulation      → [NIS + inferred + simulated]

NON-NEGOTIABLE CONTRACTS:
    1. SIMULATED output NEVER overwrites observed_evidence
    2. SIMULATED output NEVER overwrites inferred_reasoning
    3. All simulation output is clearly labeled EvidenceType.SIMULATED
    4. Simulation MUST NOT write to decisions / outcomes / values
    5. Simulation is ADVISORY — it projects consequences, not ground truth
    6. All outputs carry full trace metadata (TraceBuilder, rules applied, assumptions)
    7. No black-box — every inference step is documented in simulation_payload

SIMULATION STRUCTURE:
    Each SimulatedProjection.simulation_payload carries:
        scenario_label        — human-readable label for the simulated scenario
        impact_score          — [0, 1] composite impact severity estimate
        propagation_paths     — ordered list of domain→domain transmission paths
        exposure_estimates    — per-domain estimated exposure weights
        time_horizon_hours    — simulation forecast window
        simulation_assumptions — explicit list of modelling assumptions
        rules_applied         — rules that fired (full audit trail)

DETERMINISTIC RULES (v1):
    Propagation graph:
        banking    → insurance    (weight 0.65)
        banking    → fintech      (weight 0.70)
        fintech    → payments     (weight 0.80)
        insurance  → reinsurance  (weight 0.55)

    Impact scoring:
        base      = signal.severity_score
        domain multiplier = weighted average of primary domain exposure weights
        propagation uplift = 1.10 for 2+ domains, 1.15 for 3+ domains
        impact_score = min(1.0, base × domain_multiplier × propagation_uplift)

    Exposure weights:
        banking:     0.80
        fintech:     0.75
        insurance:   0.65
        payments:    0.60
        reinsurance: 0.55
        regulatory:  0.50
        other:       0.45

    Scenario labels:
        banking + disruption/escalation → "banking_propagation_stress"
        multi-domain (3+)               → "cross_sector_contagion"
        fintech dominant                → "fintech_payment_disruption"
        insurance dominant              → "insurance_counterparty_stress"
        alert type                      → "regulatory_impact_watch"
        recovery type                   → "recovery_trajectory"
        fallback                        → "generic_impact_projection"

SIMULATION OUTPUT (SimulatedProjection items produced per call):
    1. SCENARIO_PROPAGATION — master simulation context (always, if sev >= threshold)
    2. SECTOR_STRESS        — per secondary (propagated) domain
    3. RECOVERY_TRAJECTORY  — projected recovery window (for non-recovery signal types)

MODEL VERSION: v1.0.0-deterministic
    Rule-based. No ML. No external I/O. Same input always → same output.

For backward compatibility, adapt_impact_observatory_payload(raw: dict) still exists.
It raises NotImplementedError — Observatory does not accept raw dict payloads.
Observatory receives NIS via enrich_with_simulation(signal).
"""

from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone
from typing import Any

from app.intelligence.models import (
    ADAPTER_VERSION,
    NormalizationStatus,
    NormalizedIntelligenceSignal,
    SimulatedProjection,
    SimulationType,
    SourceFamily,
    _now_utc,
)
from app.intelligence.trace import AdapterError, TraceBuilder

logger = logging.getLogger("observatory.intelligence.simulation")

IO_ADAPTER_VERSION: str = "1.0.0-deterministic"

# ─── Error ────────────────────────────────────────────────────────────────────

class ImpactObservatoryAdapterError(AdapterError):
    """Raised when the simulation adapter cannot enrich the input signal."""


# ─── Constants ────────────────────────────────────────────────────────────────

# Minimum severity for any simulation to run
_SIM_MINIMUM_SEVERITY: float = 0.20

# Confidence model assigns to its own projections (deterministic but simplified)
_BASE_SIMULATION_CONFIDENCE: float = 0.70

# Per-domain base exposure weights — reflect systemic importance
_DOMAIN_EXPOSURE_WEIGHTS: dict[str, float] = {
    "banking":     0.80,
    "fintech":     0.75,
    "insurance":   0.65,
    "payments":    0.60,
    "reinsurance": 0.55,
    "regulatory":  0.50,
}
_DEFAULT_DOMAIN_WEIGHT: float = 0.45

# Propagation graph: (source_domain, target_domain, transmission_weight)
# Ordered list; traversed depth-first up to _MAX_PROPAGATION_DEPTH hops.
_PROPAGATION_GRAPH: list[tuple[str, str, float]] = [
    ("banking",   "insurance",   0.65),
    ("banking",   "fintech",     0.70),
    ("fintech",   "payments",    0.80),
    ("insurance", "reinsurance", 0.55),
]

_MAX_PROPAGATION_DEPTH: int = 2

# Propagation uplift multipliers for multi-domain exposure
_PROPAGATION_UPLIFT: dict[int, float] = {
    1: 1.00,   # single domain — no uplift
    2: 1.10,   # two domains — moderate amplification
    3: 1.15,   # three+ domains — elevated cross-sector amplification
}

# Scenario label rules (checked in order, first match wins)
_SCENARIO_LABEL_RULES: list[tuple[str, str, str]] = [
    # (condition, signal_type_pattern, label)
    ("multi_domain_3plus", "",                  "cross_sector_contagion"),
    ("banking",            "disruption",        "banking_propagation_stress"),
    ("banking",            "escalation",        "banking_propagation_stress"),
    ("fintech",            "",                  "fintech_payment_disruption"),
    ("insurance",          "",                  "insurance_counterparty_stress"),
    ("any",                "alert",             "regulatory_impact_watch"),
    ("any",                "recovery",          "recovery_trajectory"),
]
_DEFAULT_SCENARIO_LABEL: str = "generic_impact_projection"

# Recovery horizon multipliers per number of propagated domains
_RECOVERY_HORIZON_FACTOR: dict[int, float] = {
    1: 0.75,
    2: 1.25,
    3: 1.75,
}

# Mapping for validate stub
IO_SIMULATION_TYPE_MAP: dict[str, SimulationType] = {
    "scenario_propagation": SimulationType.SCENARIO_PROPAGATION,
    "sector_stress":        SimulationType.SECTOR_STRESS,
    "entity_impact":        SimulationType.ENTITY_IMPACT,
    "recovery":             SimulationType.RECOVERY_TRAJECTORY,
    "monte_carlo":          SimulationType.MONTE_CARLO_RUN,
}

IO_REQUIRED_FIELDS: tuple[str, ...] = (
    "run_id",
    "scenario_id",
    "model_version",
    "simulation_type",
    "projected_severity",
    "confidence",
    "horizon_hours",
    "affected_domains",
    "simulated_at",
)

IO_SOURCE_FAMILY: SourceFamily = SourceFamily.IMPACT_OBSERVATORY


# ─── Propagation engine ───────────────────────────────────────────────────────

def _compute_propagation_paths(
    seed_domains: list[str],
    severity: float,
    tb: TraceBuilder,
) -> list[dict[str, Any]]:
    """Traverse the propagation graph from seed_domains, up to _MAX_PROPAGATION_DEPTH.

    Returns an ordered list of propagation path dicts.  Each path describes:
        from_domain        — originating domain
        to_domain          — receiving domain
        transmission_weight — probability weight of this transmission
        transmitted_severity — estimated severity at the receiving domain
        hop_depth          — distance from seed domain (1 = direct)
        rule               — human-readable rule description

    The traversal is breadth-first, de-duplicating visited domains.
    Only paths from the CURRENT signal's seed domains are followed.
    """
    seed_set   = set(d.lower() for d in seed_domains)
    visited    = set(seed_set)
    paths: list[dict[str, Any]] = []

    current_wave = list(seed_set)

    for depth in range(1, _MAX_PROPAGATION_DEPTH + 1):
        next_wave: list[str] = []
        for src in current_wave:
            for graph_src, graph_tgt, weight in _PROPAGATION_GRAPH:
                if graph_src == src and graph_tgt not in visited:
                    transmitted_sev = round(min(1.0, severity * weight), 4)
                    path = {
                        "from_domain":           graph_src,
                        "to_domain":             graph_tgt,
                        "transmission_weight":   weight,
                        "transmitted_severity":  transmitted_sev,
                        "hop_depth":             depth,
                        "rule":                  f"{graph_src}→{graph_tgt} (w={weight})",
                        "simulation_model":      IO_ADAPTER_VERSION,
                    }
                    paths.append(path)
                    visited.add(graph_tgt)
                    next_wave.append(graph_tgt)
                    tb.note(
                        "simulation.propagation",
                        f"Depth {depth}: {graph_src}→{graph_tgt} "
                        f"weight={weight} transmitted_sev={transmitted_sev:.3f}",
                    )
        current_wave = next_wave

    if not paths:
        tb.note(
            "simulation.propagation",
            f"No propagation paths from seed_domains={sorted(seed_set)} "
            "(no matching edges in propagation graph)",
        )

    return paths


def _compute_all_domains(
    seed_domains: list[str],
    propagation_paths: list[dict[str, Any]],
) -> list[str]:
    """Return all domains (seed + propagated), preserving seed-first order."""
    all_d: list[str] = list(dict.fromkeys(d.lower() for d in seed_domains))
    for path in propagation_paths:
        tgt = path["to_domain"]
        if tgt not in all_d:
            all_d.append(tgt)
    return all_d


def _compute_exposure_estimates(
    all_domains: list[str],
    severity: float,
    propagation_paths: list[dict[str, Any]],
) -> dict[str, float]:
    """Compute per-domain exposure estimates.

    Each domain's exposure = base_weight × effective_severity.
    Propagated domains use transmitted_severity from the path (lower than seed).
    Seed domains use full severity.
    """
    # Build domain → effective severity map
    path_sev: dict[str, float] = {}
    for path in propagation_paths:
        domain = path["to_domain"]
        if domain not in path_sev or path["transmitted_severity"] > path_sev[domain]:
            path_sev[domain] = path["transmitted_severity"]

    estimates: dict[str, float] = {}
    for domain in all_domains:
        base_weight = _DOMAIN_EXPOSURE_WEIGHTS.get(domain, _DEFAULT_DOMAIN_WEIGHT)
        eff_severity = path_sev.get(domain, severity)  # seed domains use full severity
        estimates[domain] = round(min(1.0, base_weight * eff_severity), 4)

    return estimates


def _compute_impact_score(
    seed_domains: list[str],
    severity: float,
    all_domains: list[str],
) -> float:
    """Compute composite impact score [0.0, 1.0].

    impact_score = severity × domain_multiplier × propagation_uplift

    domain_multiplier = average of seed domain exposure weights
    propagation_uplift = _PROPAGATION_UPLIFT[min(domain_count, 3)]
    """
    if not seed_domains:
        return round(severity * _DEFAULT_DOMAIN_WEIGHT, 4)

    domain_weights = [
        _DOMAIN_EXPOSURE_WEIGHTS.get(d.lower(), _DEFAULT_DOMAIN_WEIGHT)
        for d in seed_domains
    ]
    domain_multiplier = sum(domain_weights) / len(domain_weights)
    depth_key         = min(len(all_domains), 3)
    uplift            = _PROPAGATION_UPLIFT.get(depth_key, 1.15)
    return round(min(1.0, severity * domain_multiplier * uplift), 4)


def _determine_scenario_label(
    seed_domains: list[str],
    signal_type: str,
    all_domains: list[str],
) -> str:
    """Determine human-readable scenario label from seed domains + signal_type.

    Label priority (checked in order, first match wins):
        1. cross_sector_contagion      — 3+ SEED domains (signal itself is multi-sector)
        2. banking_propagation_stress  — banking seed + disruption/escalation
        3. fintech_payment_disruption  — fintech is seed domain
        4. insurance_counterparty_stress — insurance is seed domain
        5. regulatory_impact_watch     — alert signal type
        6. recovery_trajectory         — recovery signal type
        7. generic_impact_projection   — fallback

    Note: 'cross_sector_contagion' is based on SEED domains (the signal's own
    affected_domains), not the full propagated domain set. A banking-only signal
    that propagates to fintech/insurance is "banking_propagation_stress", not
    contagion — the contagion scenario requires the original event to span 3+
    sectors simultaneously.
    """
    domain_set = set(d.lower() for d in seed_domains)
    stype      = signal_type.lower()

    if len(seed_domains) >= 3:
        return "cross_sector_contagion"
    if "banking" in domain_set and stype in ("disruption", "escalation"):
        return "banking_propagation_stress"
    if "fintech" in domain_set:
        return "fintech_payment_disruption"
    if "insurance" in domain_set:
        return "insurance_counterparty_stress"
    if stype == "alert":
        return "regulatory_impact_watch"
    if stype == "recovery":
        return "recovery_trajectory"
    return _DEFAULT_SCENARIO_LABEL


# ─── Simulation rule engine ───────────────────────────────────────────────────

class _SimulationEngine:
    """Deterministic simulation engine.

    Produces SimulatedProjection items from a NormalizedIntelligenceSignal.
    All outputs are SIMULATED — never presented as observed fact.
    """

    MODEL_VERSION: str = IO_ADAPTER_VERSION

    def __init__(
        self,
        signal: NormalizedIntelligenceSignal,
        tb: TraceBuilder,
    ):
        self._signal      = signal
        self._tb          = tb
        self._severity    = signal.severity_score
        self._confidence  = signal.confidence_score
        self._domains     = [d.lower() for d in signal.affected_domains]
        self._stype       = signal.signal_type.lower()
        self._horizon     = signal.time_horizon_hours
        self._now         = _now_utc()
        self._scenario_id = f"sim-{uuid.uuid4().hex[:12]}"

    def run(self) -> list[SimulatedProjection]:
        """Execute simulation rules. Returns list of SimulatedProjection items.

        Returns empty list when signal severity is below _SIM_MINIMUM_SEVERITY.
        Otherwise produces:
            1. SCENARIO_PROPAGATION  — master simulation context
            2. SECTOR_STRESS         — one per propagated domain (max 3)
            3. RECOVERY_TRAJECTORY   — projected recovery window
        """
        if self._severity < _SIM_MINIMUM_SEVERITY:
            self._tb.note(
                "simulation.engine",
                f"Severity {self._severity:.3f} below minimum threshold "
                f"{_SIM_MINIMUM_SEVERITY} — no simulation projections generated",
            )
            return []

        projections: list[SimulatedProjection] = []

        # Core simulation
        propagation_paths = _compute_propagation_paths(
            self._domains, self._severity, self._tb
        )
        all_domains       = _compute_all_domains(self._domains, propagation_paths)
        exposure_estimates = _compute_exposure_estimates(
            all_domains, self._severity, propagation_paths
        )
        impact_score      = _compute_impact_score(
            self._domains, self._severity, all_domains
        )
        scenario_label    = _determine_scenario_label(
            self._domains, self._stype, all_domains
        )

        self._tb.note("simulation.engine", (
            f"Scenario: '{scenario_label}' "
            f"impact_score={impact_score:.3f} "
            f"propagation_paths={len(propagation_paths)} "
            f"all_domains={all_domains}"
        ))

        # ── 1. SCENARIO_PROPAGATION — master simulation ──────────────────────
        master = self._build_scenario_propagation(
            propagation_paths  = propagation_paths,
            impact_score       = impact_score,
            exposure_estimates = exposure_estimates,
            scenario_label     = scenario_label,
            all_domains        = all_domains,
        )
        projections.append(master)

        # ── 2. SECTOR_STRESS — per propagated domain ─────────────────────────
        # Produce one SECTOR_STRESS item per domain reached by propagation,
        # limited to 3 to avoid overwhelming the signal payload.
        stress_items = self._build_sector_stress_projections(
            propagation_paths  = propagation_paths,
            scenario_label     = scenario_label,
        )
        projections.extend(stress_items)

        # ── 3. RECOVERY_TRAJECTORY — for non-recovery signals ────────────────
        if self._stype != "recovery":
            recovery = self._build_recovery_trajectory(
                all_domains    = all_domains,
                scenario_label = scenario_label,
            )
            projections.append(recovery)

        self._tb.note(
            "simulation.engine",
            f"Engine completed: {len(projections)} projection(s) produced "
            f"[1 SCENARIO_PROPAGATION, {len(stress_items)} SECTOR_STRESS, "
            f"{'1' if self._stype != 'recovery' else '0'} RECOVERY_TRAJECTORY]",
        )
        self._tb.set_semantic_counts(
            observed  = len(self._signal.observed_evidence),
            inferred  = len(self._signal.inferred_reasoning),
            simulated = len(projections),
        )

        return projections

    # ── Builders ──────────────────────────────────────────────────────────────

    def _build_scenario_propagation(
        self,
        propagation_paths:  list[dict[str, Any]],
        impact_score:       float,
        exposure_estimates: dict[str, float],
        scenario_label:     str,
        all_domains:        list[str],
    ) -> SimulatedProjection:
        """Build the master SCENARIO_PROPAGATION SimulatedProjection."""
        depth_key   = min(len(all_domains), 3)
        uplift      = _PROPAGATION_UPLIFT.get(depth_key, 1.15)
        assumptions = [
            "Propagation weights are empirically calibrated — not stochastic",
            "Severity transmission assumes linear decay per hop",
            f"Propagation depth limited to {_MAX_PROPAGATION_DEPTH} hops",
            "Sector interconnection graph is static (v1 deterministic model)",
            "Recovery horizon assumes no additional exogenous shocks",
        ]
        rules_applied = [p["rule"] for p in propagation_paths]
        if not rules_applied:
            rules_applied = ["no_propagation (no matching edges from seed domains)"]

        summary = (
            f"Impact Observatory v1 projects {scenario_label} scenario from "
            f"'{self._signal.title}'. Estimated impact score: {impact_score:.2f}. "
            f"Propagation: {len(propagation_paths)} path(s) across {len(all_domains)} domain(s). "
            f"Horizon: {self._horizon}h."
        )

        self._tb.note(
            "simulation.SCENARIO_PROPAGATION",
            f"Built: scenario_label='{scenario_label}' "
            f"impact_score={impact_score:.4f} domains={all_domains}",
        )

        return SimulatedProjection(
            simulation_type     = SimulationType.SCENARIO_PROPAGATION,
            source_system       = "impact_observatory",
            simulated_at        = self._now,
            model_version       = self.MODEL_VERSION,
            confidence          = round(
                min(1.0, _BASE_SIMULATION_CONFIDENCE * (self._confidence ** 0.5)), 4
            ),
            horizon_hours       = self._horizon,
            summary             = summary[:1000],
            scenario_id         = self._scenario_id,
            run_id              = None,
            projected_severity  = round(min(1.0, impact_score), 4),
            affected_domains    = list(all_domains),
            simulation_payload  = {
                "scenario_label":           scenario_label,
                "impact_score":             impact_score,
                "propagation_paths":        propagation_paths,
                "exposure_estimates":       exposure_estimates,
                "time_horizon_hours":       self._horizon,
                "simulation_assumptions":   assumptions,
                "rules_applied":            rules_applied,
                "propagation_depth":        _MAX_PROPAGATION_DEPTH,
                "propagation_uplift":       uplift,
                "seed_domains":             list(self._domains),
                "all_domains_reached":      all_domains,
                "model_version":            self.MODEL_VERSION,
                "original_severity":        self._severity,
                "original_confidence":      self._confidence,
            },
        )

    def _build_sector_stress_projections(
        self,
        propagation_paths: list[dict[str, Any]],
        scenario_label:    str,
    ) -> list[SimulatedProjection]:
        """Build one SECTOR_STRESS projection per propagated (non-seed) domain."""
        stress_items: list[SimulatedProjection] = []
        seen: set[str] = set(self._domains)

        for path in propagation_paths[:3]:  # cap at 3 to limit payload size
            tgt_domain = path["to_domain"]
            if tgt_domain in seen:
                continue
            seen.add(tgt_domain)

            transmitted_sev = path["transmitted_severity"]
            base_weight     = _DOMAIN_EXPOSURE_WEIGHTS.get(tgt_domain, _DEFAULT_DOMAIN_WEIGHT)
            sector_impact   = round(min(1.0, transmitted_sev * base_weight), 4)
            summary = (
                f"SECTOR_STRESS projection: '{tgt_domain}' domain faces "
                f"transmitted severity {transmitted_sev:.2f} via "
                f"'{path['from_domain']}→{tgt_domain}' propagation path "
                f"(weight {path['transmission_weight']}). "
                f"Estimated sector exposure: {sector_impact:.2f}."
            )

            self._tb.note(
                "simulation.SECTOR_STRESS",
                f"Domain '{tgt_domain}': transmitted_sev={transmitted_sev:.3f} "
                f"sector_impact={sector_impact:.4f}",
            )

            stress_items.append(SimulatedProjection(
                simulation_type    = SimulationType.SECTOR_STRESS,
                source_system      = "impact_observatory",
                simulated_at       = self._now,
                model_version      = self.MODEL_VERSION,
                confidence         = round(
                    _BASE_SIMULATION_CONFIDENCE * path["transmission_weight"], 4
                ),
                horizon_hours      = self._horizon,
                summary            = summary[:1000],
                scenario_id        = self._scenario_id,
                run_id             = None,
                projected_severity = sector_impact,
                affected_domains   = [tgt_domain],
                simulation_payload = {
                    "sector":                  tgt_domain,
                    "propagation_path":        path,
                    "sector_impact_score":     sector_impact,
                    "scenario_label":          scenario_label,
                    "transmitted_severity":    transmitted_sev,
                    "domain_exposure_weight":  base_weight,
                    "model_version":           self.MODEL_VERSION,
                },
            ))

        return stress_items

    def _build_recovery_trajectory(
        self,
        all_domains:    list[str],
        scenario_label: str,
    ) -> SimulatedProjection:
        """Build RECOVERY_TRAJECTORY projection.

        Estimated recovery horizon = signal_horizon × (1 - severity) × domain_factor.
        Higher severity and more domains → longer recovery.
        """
        depth_key      = min(len(all_domains), 3)
        domain_factor  = _RECOVERY_HORIZON_FACTOR.get(depth_key, 1.75)
        recovery_hours = int(round(self._horizon * (1.0 - self._severity) * domain_factor))
        recovery_hours = max(12, min(recovery_hours, 8760))  # clamp [12h, 1yr]

        summary = (
            f"RECOVERY_TRAJECTORY: estimated recovery window for '{scenario_label}' "
            f"is approximately {recovery_hours}h. "
            f"Based on severity {self._severity:.0%}, {len(all_domains)} affected domain(s), "
            f"and domain_factor={domain_factor}. Advisory only."
        )

        self._tb.note(
            "simulation.RECOVERY_TRAJECTORY",
            f"recovery_hours={recovery_hours} "
            f"(horizon={self._horizon} × (1-{self._severity:.3f}) × {domain_factor})",
        )

        return SimulatedProjection(
            simulation_type    = SimulationType.RECOVERY_TRAJECTORY,
            source_system      = "impact_observatory",
            simulated_at       = self._now,
            model_version      = self.MODEL_VERSION,
            confidence         = round(_BASE_SIMULATION_CONFIDENCE * 0.80, 4),
            horizon_hours      = recovery_hours,
            summary            = summary[:1000],
            scenario_id        = self._scenario_id,
            run_id             = None,
            projected_severity = round(self._severity * 0.30, 4),  # recovery = residual stress
            affected_domains   = list(all_domains),
            simulation_payload = {
                "recovery_horizon_hours":       recovery_hours,
                "domain_factor":                domain_factor,
                "original_horizon_hours":       self._horizon,
                "original_severity":            self._severity,
                "scenario_label":               scenario_label,
                "model_version":                self.MODEL_VERSION,
                "simulation_assumption":        (
                    "Recovery horizon is deterministic. "
                    "Assumes no additional exogenous shocks during recovery window."
                ),
            },
        )


# ─── Main enrichment entry point ──────────────────────────────────────────────

def enrich_with_simulation(
    signal: NormalizedIntelligenceSignal,
) -> NormalizedIntelligenceSignal:
    """Enrich a NormalizedIntelligenceSignal with Impact Observatory simulation projections.

    This is the ONLY authorized Impact Observatory entry point.
    The Observatory does NOT accept raw external payloads.
    It receives a NIS and returns an ENRICHED NIS.

    Non-negotiable contracts:
        - NEVER overwrites observed_evidence (immutable)
        - NEVER overwrites inferred_reasoning (immutable)
        - All outputs enter simulation_context ONLY
        - All outputs carry EvidenceType.SIMULATED
        - All outputs are advisory — never authoritative
        - Full trace embedded in trace_payload["simulation_enrichment"]

    Pipeline: adapt_jet_nexus_payload → enrich_with_trek → enrich_with_simulation

    Args:
        signal: A NormalizedIntelligenceSignal in NORMALIZED or PARTIAL status.
                Best results when TREK enrichment has already been applied.

    Returns:
        Enriched NormalizedIntelligenceSignal. New object — input never mutated.

    Raises:
        ImpactObservatoryAdapterError: if input signal is REJECTED.
    """
    if signal.normalization_status.value == "REJECTED":
        raise ImpactObservatoryAdapterError(
            f"Impact Observatory will not simulate a REJECTED signal "
            f"(id={signal.normalized_signal_id}). "
            "Resolve validation violations on the source signal first.",
            violations=[],
        )

    tb = TraceBuilder(
        source_family   = f"{signal.source_family.value}+simulation",
        source_systems  = list(signal.source_systems) + ["impact_observatory"],
        adapter_version = IO_ADAPTER_VERSION,
    )
    tb.note(
        "simulation.enrich",
        f"Enriching signal id={signal.normalized_signal_id} "
        f"[observed={len(signal.observed_evidence)} "
        f"inferred={len(signal.inferred_reasoning)} "
        f"pre-existing-simulated={len(signal.simulation_context)}]",
    )
    tb.note("simulation.contract", (
        "observed_evidence is immutable. "
        "inferred_reasoning is immutable. "
        "All simulation output → simulation_context only."
    ))
    tb.note("simulation.input", (
        f"source_family={signal.source_family} "
        f"signal_type={signal.signal_type} "
        f"severity={signal.severity_score:.3f} "
        f"confidence={signal.confidence_score:.3f} "
        f"domains={signal.affected_domains} "
        f"trek_enriched={len(signal.inferred_reasoning) > 0}"
    ))

    # ── Run simulation engine ─────────────────────────────────────────────────
    engine      = _SimulationEngine(signal, tb)
    new_sims    = engine.run()

    # ── Merge with any pre-existing simulation_context ────────────────────────
    merged_sims = list(signal.simulation_context) + new_sims

    # ── Build simulation trace and merge into signal trace ────────────────────
    sim_trace    = tb.build()
    merged_trace = dict(signal.trace_payload)
    merged_trace["simulation_enrichment"] = sim_trace

    # ── Derive status ─────────────────────────────────────────────────────────
    # Simulation cannot downgrade signal status — it only observes, not validates.
    # Status stays at original unless TREK already set PARTIAL.
    enriched_status = signal.normalization_status

    # ── Return enriched NIS (model_copy preserves frozen model) ──────────────
    enriched = signal.model_copy(update={
        "simulation_context": merged_sims,
        "trace_payload":      merged_trace,
        "normalization_status": enriched_status,
    })

    logger.info(
        "simulation.enrich completed id=%s projections=%d "
        "[%d SCENARIO_PROPAGATION, %d SECTOR_STRESS, %d RECOVERY_TRAJECTORY]",
        signal.normalized_signal_id,
        len(new_sims),
        sum(1 for p in new_sims if p.simulation_type == SimulationType.SCENARIO_PROPAGATION),
        sum(1 for p in new_sims if p.simulation_type == SimulationType.SECTOR_STRESS),
        sum(1 for p in new_sims if p.simulation_type == SimulationType.RECOVERY_TRAJECTORY),
    )

    return enriched


# ─── Backward-compat stub (raw dict path) ────────────────────────────────────

def adapt_impact_observatory_payload(raw: dict[str, Any]) -> NormalizedIntelligenceSignal:
    """STUB — Impact Observatory does not accept raw external payloads.

    Impact Observatory is an enrichment adapter that operates on NIS.
    To enrich a signal, use enrich_with_simulation(signal) instead.

    This stub is retained so the source adapter registry in adapter.py does not
    crash when Observatory is listed. Any raw dict call will raise.

    Raises:
        NotImplementedError: always — use enrich_with_simulation(signal).
    """
    raise NotImplementedError(
        "Impact Observatory does not accept raw payloads. "
        "It is an enrichment adapter — call enrich_with_simulation(signal) "
        "with a NormalizedIntelligenceSignal from the prior pipeline stage. "
        "Pipeline: adapt_jet_nexus_payload → enrich_with_trek → enrich_with_simulation"
    )


def validate_impact_observatory_payload(raw: dict[str, Any]) -> list[str]:
    """Validate a raw Observatory payload against the stub contract.

    Returns:
        list of error messages (non-empty = invalid).
    """
    errors: list[str] = []
    for field_name in IO_REQUIRED_FIELDS:
        if field_name not in raw or raw[field_name] is None:
            errors.append(f"Missing required field: '{field_name}'")
    if "projected_severity" in raw and raw["projected_severity"] is not None:
        try:
            v = float(raw["projected_severity"])
            if not (0.0 <= v <= 1.0):
                errors.append(f"projected_severity must be in [0.0, 1.0], got {v}")
        except (TypeError, ValueError):
            errors.append(f"projected_severity is not numeric: {raw['projected_severity']!r}")
    if "confidence" in raw and raw["confidence"] is not None:
        try:
            v = float(raw["confidence"])
            if not (0.0 <= v <= 1.0):
                errors.append(f"confidence must be in [0.0, 1.0], got {v}")
        except (TypeError, ValueError):
            errors.append(f"confidence is not numeric: {raw['confidence']!r}")
    return errors
