"""
Intelligence Adapter — TREK Enrichment Adapter

INTEGRATION STATUS: IMPLEMENTED (v1.0.0)

TREK is the reasoning/enrichment layer of the Intelligence Adapter pipeline.
It operates on an already-normalized NormalizedIntelligenceSignal and produces
an ENRICHED signal with:
    - inferred_reasoning  — risk-type analysis items (TREK-generated)
    - reasoning_summary   — narrative summary of TREK's conclusions
    - causal_chain        — ordered list of causal reasoning steps
    - adjusted scores     — severity/confidence updated based on TREK inference

CRITICAL CONTRACT:
    TREK is NOT a source adapter. It does NOT accept raw external payloads.
    TREK operates on NormalizedIntelligenceSignal only.
    TREK output is INFERRED — it must NEVER be presented as observed fact.
    All TREK intelligence enters InferredReasoning containers only.
    TREK MUST NOT overwrite observed_evidence from the original signal.

Pipeline position:
    Jet Nexus → adapt_jet_nexus_payload → [NIS] → enrich_with_trek → [enriched NIS]

Entry point:
    enrich_with_trek(signal: NormalizedIntelligenceSignal) -> NormalizedIntelligenceSignal

Reasoning engine:
    Rule-based, deterministic, fully traceable. No ML. No external I/O.
    All inference rules are documented inline. Same input always → same output.

TREK analysis types → InferredReasoning mapping:
    LIQUIDITY_STRESS    — high-severity banking disruption/escalation
    CREDIT_EXPOSURE     — banking domain + supply/geopolitical disruption
    COUNTERPARTY_RISK   — insurance sector exposure
    MARKET_DISRUPTION   — fintech sector exposure
    CONTAGION_RISK      — multi-sector exposure at elevated severity
    REGULATORY_SIGNAL   — alert signal type with regulatory indicators
    GENERIC_INFERENCE   — fallback when severity is elevated but no specific rule matches

Score adjustment:
    severity_score  = max(original, max inferred_severity across TREK items)
    confidence_score = confidence_score * TREK_CONFIDENCE_WEIGHT when
                       TREK infers something (never increases confidence above original)

For backward compatibility, adapt_trek_payload(raw: dict) still exists as a stub.
It raises NotImplementedError — TREK does not accept raw payloads.
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
    InferredReasoning,
    ReasoningType,
    SourceFamily,
    _now_utc,
)
from app.intelligence.trace import AdapterError, TraceBuilder

logger = logging.getLogger("observatory.intelligence.trek")

TREK_ADAPTER_VERSION: str = "1.0.0"


# ─── Error ────────────────────────────────────────────────────────────────────

class TREKAdapterError(AdapterError):
    """Raised when TREK enrichment fails due to a malformed or invalid input."""


# ─── Constants ────────────────────────────────────────────────────────────────

# Confidence weight applied to all TREK inferences.
# TREK infers from already-normalized signals — some information loss is assumed.
TREK_CONFIDENCE_WEIGHT: float = 0.85

# Severity thresholds for rule activation
_SEV_HIGH:   float = 0.65   # triggers LIQUIDITY_STRESS, CONTAGION_RISK
_SEV_MEDIUM: float = 0.45   # triggers CREDIT_EXPOSURE, MARKET_DISRUPTION, COUNTERPARTY_RISK

# Minimum severity for any TREK inference to activate
_SEV_MINIMUM: float = 0.25

# Signal types that indicate active disruption/escalation
_DISRUPTION_TYPES: frozenset[str] = frozenset({"disruption", "escalation"})
_ALERT_TYPES:      frozenset[str] = frozenset({"alert"})

# Regulatory keyword set (case-insensitive substring match against title+summary)
_REGULATORY_KEYWORDS: frozenset[str] = frozenset({
    "regulat", "compliance", "sanction", "restriction", "directive",
    "policy", "oversight", "mandate", "prohibition",
})

# Mapping from TREK analysis type string → ReasoningType enum
TREK_ANALYSIS_TYPE_MAP: dict[str, ReasoningType] = {
    "liquidity":    ReasoningType.LIQUIDITY_STRESS,
    "credit":       ReasoningType.CREDIT_EXPOSURE,
    "counterparty": ReasoningType.COUNTERPARTY_RISK,
    "regulatory":   ReasoningType.REGULATORY_SIGNAL,
    "market":       ReasoningType.MARKET_DISRUPTION,
    "contagion":    ReasoningType.CONTAGION_RISK,
}

# Required fields if someone ever submits a "trek" native payload (stub contract)
TREK_REQUIRED_FIELDS: tuple[str, ...] = (
    "trek_signal_id",
    "analysis_type",
    "severity",
    "confidence",
    "reasoning",
    "analysis_timestamp",
    "horizon_hours",
    "domain",
)

TREK_SOURCE_FAMILY: SourceFamily = SourceFamily.TREK


# ─── Rule engine ──────────────────────────────────────────────────────────────

class _TREKRuleEngine:
    """Deterministic, rule-based reasoning engine.

    Accepts a NormalizedIntelligenceSignal and produces InferredReasoning items.
    Rules are evaluated independently — multiple rules can fire per signal.
    """

    def __init__(self, signal: NormalizedIntelligenceSignal, tb: TraceBuilder):
        self._signal = signal
        self._tb = tb
        self._domains = set(d.lower() for d in signal.affected_domains)
        self._sev = signal.severity_score
        self._conf = signal.confidence_score
        self._stype = signal.signal_type.lower()
        self._title = signal.title.lower()
        self._summary = signal.summary.lower()
        self._now = _now_utc()

    def run(self) -> list[InferredReasoning]:
        """Evaluate all rules and return the list of inferred reasoning items."""
        if self._sev < _SEV_MINIMUM:
            self._tb.note(
                "trek.rules",
                f"Severity {self._sev:.3f} below minimum threshold "
                f"{_SEV_MINIMUM} — no TREK inferences generated",
            )
            return []

        items: list[InferredReasoning] = []

        items.extend(self._rule_liquidity_stress())
        items.extend(self._rule_credit_exposure())
        items.extend(self._rule_counterparty_risk())
        items.extend(self._rule_market_disruption())
        items.extend(self._rule_contagion_risk())
        items.extend(self._rule_regulatory_signal())

        if not items and self._sev >= _SEV_MEDIUM:
            items.extend(self._rule_generic_inference())

        self._tb.note(
            "trek.rules",
            f"Rule engine completed: {len(items)} inference(s) generated "
            f"from severity={self._sev:.3f} stype='{self._stype}' domains={sorted(self._domains)}",
        )
        return items

    # ── Rules ─────────────────────────────────────────────────────────────────

    def _rule_liquidity_stress(self) -> list[InferredReasoning]:
        """LIQUIDITY_STRESS: high-severity banking disruption or escalation."""
        if (
            self._sev >= _SEV_HIGH
            and "banking" in self._domains
            and self._stype in _DISRUPTION_TYPES
        ):
            inferred_sev = min(1.0, self._sev * 1.10)
            summary = (
                f"High-severity {self._stype} event in banking domain signals "
                f"potential liquidity pressure. Observed severity {self._sev:.0%} "
                f"exceeds threshold {_SEV_HIGH:.0%}. TREK assesses elevated "
                f"short-term liquidity stress risk."
            )
            self._tb.note("trek.LIQUIDITY_STRESS", f"fired: sev={self._sev:.3f} domains={sorted(self._domains)}")
            return [self._build(
                reasoning_type   = ReasoningType.LIQUIDITY_STRESS,
                summary          = summary,
                inferred_sev     = inferred_sev,
                confidence       = self._conf * TREK_CONFIDENCE_WEIGHT,
                supporting_ids   = list(self._signal.source_event_ids),
            )]
        return []

    def _rule_credit_exposure(self) -> list[InferredReasoning]:
        """CREDIT_EXPOSURE: banking domain + disruption/escalation at medium+ severity."""
        if (
            self._sev >= _SEV_MEDIUM
            and "banking" in self._domains
            and self._stype in _DISRUPTION_TYPES
        ):
            inferred_sev = self._sev * 0.90
            summary = (
                f"{self._stype.title()} event creates credit exposure risk for "
                f"banking counterparties. Disruption at severity {self._sev:.0%} "
                f"is likely to affect trade finance and credit extension chains."
            )
            self._tb.note("trek.CREDIT_EXPOSURE", f"fired: sev={self._sev:.3f}")
            return [self._build(
                reasoning_type = ReasoningType.CREDIT_EXPOSURE,
                summary        = summary,
                inferred_sev   = inferred_sev,
                confidence     = self._conf * TREK_CONFIDENCE_WEIGHT,
                supporting_ids = list(self._signal.source_event_ids),
            )]
        return []

    def _rule_counterparty_risk(self) -> list[InferredReasoning]:
        """COUNTERPARTY_RISK: insurance sector exposure at medium+ severity."""
        if self._sev >= _SEV_MEDIUM and "insurance" in self._domains:
            inferred_sev = self._sev
            summary = (
                f"Insurance sector exposure identified at severity {self._sev:.0%}. "
                f"TREK assesses counterparty concentration risk: {self._stype} events "
                f"affecting insurance create knock-on claims and reinsurance pressure."
            )
            self._tb.note("trek.COUNTERPARTY_RISK", f"fired: sev={self._sev:.3f}")
            return [self._build(
                reasoning_type = ReasoningType.COUNTERPARTY_RISK,
                summary        = summary,
                inferred_sev   = inferred_sev,
                confidence     = self._conf * TREK_CONFIDENCE_WEIGHT,
                supporting_ids = list(self._signal.source_event_ids),
            )]
        return []

    def _rule_market_disruption(self) -> list[InferredReasoning]:
        """MARKET_DISRUPTION: fintech sector exposure at medium+ severity."""
        if self._sev >= _SEV_MEDIUM and "fintech" in self._domains:
            inferred_sev = self._sev * 0.95
            summary = (
                f"Fintech sector exposure at severity {self._sev:.0%} elevates "
                f"market disruption risk. Payment rails and digital infrastructure "
                f"face stress under {self._stype} conditions."
            )
            self._tb.note("trek.MARKET_DISRUPTION", f"fired: sev={self._sev:.3f}")
            return [self._build(
                reasoning_type = ReasoningType.MARKET_DISRUPTION,
                summary        = summary,
                inferred_sev   = inferred_sev,
                confidence     = self._conf * TREK_CONFIDENCE_WEIGHT,
                supporting_ids = list(self._signal.source_event_ids),
            )]
        return []

    def _rule_contagion_risk(self) -> list[InferredReasoning]:
        """CONTAGION_RISK: multi-sector exposure at high severity."""
        if len(self._domains) >= 2 and self._sev >= _SEV_HIGH:
            domain_list = sorted(self._domains)
            inferred_sev = min(1.0, self._sev * 1.05)
            summary = (
                f"Multi-sector exposure ({', '.join(domain_list)}) with severity "
                f"{self._sev:.0%} indicates a potential contagion pathway. "
                f"TREK identifies cross-sector transmission risk as elevated."
            )
            self._tb.note("trek.CONTAGION_RISK", f"fired: domains={domain_list} sev={self._sev:.3f}")
            return [self._build(
                reasoning_type = ReasoningType.CONTAGION_RISK,
                summary        = summary,
                inferred_sev   = inferred_sev,
                confidence     = self._conf * 0.75,  # lower confidence for contagion (complex pathway)
                supporting_ids = list(self._signal.source_event_ids),
            )]
        return []

    def _rule_regulatory_signal(self) -> list[InferredReasoning]:
        """REGULATORY_SIGNAL: alert type + regulatory keyword in title/summary."""
        if self._stype not in _ALERT_TYPES:
            return []
        combined_text = f"{self._title} {self._summary}"
        has_regulatory = any(kw in combined_text for kw in _REGULATORY_KEYWORDS)
        if not has_regulatory:
            return []
        inferred_sev = self._sev * 0.85
        summary = (
            f"Regulatory alert signal detected at severity {self._sev:.0%}. "
            f"TREK identifies compliance monitoring and regulatory watch obligations. "
            f"Operational adjustments may be required."
        )
        self._tb.note("trek.REGULATORY_SIGNAL", f"fired: sev={self._sev:.3f} stype='{self._stype}'")
        return [self._build(
            reasoning_type = ReasoningType.REGULATORY_SIGNAL,
            summary        = summary,
            inferred_sev   = inferred_sev,
            confidence     = self._conf * 0.90,
            supporting_ids = list(self._signal.source_event_ids),
        )]

    def _rule_generic_inference(self) -> list[InferredReasoning]:
        """GENERIC_INFERENCE: elevated severity but no specific rule matched."""
        summary = (
            f"Elevated severity {self._sev:.0%} signal of type '{self._stype}' "
            f"in domain(s) {sorted(self._domains) or ['unknown']}. "
            f"No specific risk pathway identified — elevated general risk posture."
        )
        self._tb.note("trek.GENERIC_INFERENCE", f"fired as fallback: sev={self._sev:.3f}")
        return [self._build(
            reasoning_type = ReasoningType.GENERIC_INFERENCE,
            summary        = summary,
            inferred_sev   = self._sev * 0.80,
            confidence     = self._conf * 0.70,
            supporting_ids = list(self._signal.source_event_ids),
        )]

    # ── Builder ───────────────────────────────────────────────────────────────

    def _build(
        self,
        reasoning_type: ReasoningType,
        summary: str,
        inferred_sev: float,
        confidence: float,
        supporting_ids: list[str],
    ) -> InferredReasoning:
        return InferredReasoning(
            reasoning_type      = reasoning_type,
            source_system       = "trek",
            inferred_at         = self._now,
            confidence          = round(min(1.0, max(0.0, confidence)), 4),
            summary             = summary[:1000],
            supporting_event_ids = supporting_ids[:10],
            inferred_severity   = round(min(1.0, max(0.0, inferred_sev)), 4),
            affected_entities   = [],
            reasoning_payload   = {
                "trek_adapter_version": TREK_ADAPTER_VERSION,
                "rule":                 reasoning_type.value,
                "original_severity":    self._sev,
                "original_confidence":  self._conf,
                "signal_type":          self._stype,
                "domains":              sorted(self._domains),
            },
        )


# ─── Causal chain builder ─────────────────────────────────────────────────────

def _build_causal_chain(
    signal: NormalizedIntelligenceSignal,
    trek_inferences: list[InferredReasoning],
) -> list[str]:
    """Build an ordered causal chain from JN observation + TREK inferences.

    The causal chain reads as a narrative: what was observed, what TREK inferred.
    Existing causal_chain steps (if any) are preserved first.
    """
    chain: list[str] = list(signal.causal_chain)  # preserve original (usually empty for JN)

    # Step 1: observed anchor
    chain.append(
        f"OBSERVED [{signal.source_family.upper()}]: {signal.title} "
        f"(severity={signal.severity_score:.0%}, type={signal.signal_type})"
    )

    # Step 2+: TREK inference steps
    for item in trek_inferences:
        chain.append(
            f"INFERRED [TREK/{item.reasoning_type.value}]: "
            f"{item.summary[:200]}"
        )

    return chain


# ─── Score adjuster ───────────────────────────────────────────────────────────

def _compute_enriched_scores(
    original_signal: NormalizedIntelligenceSignal,
    trek_inferences: list[InferredReasoning],
) -> tuple[float, float]:
    """Compute enriched severity and confidence scores.

    severity  = max(original, max TREK inferred_severity)
                Rationale: TREK can only RAISE the alarm, not lower it.
                The original observation is factual; TREK adds risk context.

    confidence = original * TREK_CONFIDENCE_WEIGHT  (when TREK fires)
                 Rationale: TREK inferences add a confidence discount because
                 they introduce a second inference step. Never increases confidence.
                 When no TREK inferences fire, scores are unchanged.

    Returns:
        (severity_score, confidence_score) — both clamped to [0.0, 1.0]
    """
    if not trek_inferences:
        return original_signal.severity_score, original_signal.confidence_score

    max_inferred_sev = max(item.inferred_severity for item in trek_inferences)
    new_severity = round(min(1.0, max(original_signal.severity_score, max_inferred_sev)), 4)
    new_confidence = round(
        min(original_signal.confidence_score, original_signal.confidence_score * TREK_CONFIDENCE_WEIGHT),
        4,
    )
    return new_severity, new_confidence


# ─── Reasoning summary ────────────────────────────────────────────────────────

def _build_reasoning_summary(
    signal: NormalizedIntelligenceSignal,
    trek_inferences: list[InferredReasoning],
) -> str:
    """Build a concise reasoning summary from TREK inferences."""
    if not trek_inferences:
        return ""

    risk_types = [item.reasoning_type.value for item in trek_inferences]
    domain_list = sorted(set(signal.affected_domains))
    return (
        f"TREK analysis of {signal.source_family.upper()} signal '{signal.title}': "
        f"{len(trek_inferences)} risk pathway(s) identified — "
        f"{', '.join(risk_types)}. "
        f"Domains: {', '.join(domain_list) or 'unspecified'}. "
        f"Enriched severity: {max(item.inferred_severity for item in trek_inferences):.0%}."
    )[:2000]


# ─── Main enrichment entry point ──────────────────────────────────────────────

def enrich_with_trek(
    signal: NormalizedIntelligenceSignal,
) -> NormalizedIntelligenceSignal:
    """Enrich a NormalizedIntelligenceSignal with TREK reasoning.

    This is the ONLY authorized TREK entry point.
    TREK does NOT accept raw external payloads — it receives a NIS.

    Pipeline: adapt_jet_nexus_payload → [NIS] → enrich_with_trek → [enriched NIS]

    What TREK adds:
        - inferred_reasoning:  list[InferredReasoning] — risk-type analysis items
        - reasoning_summary:   narrative summary of TREK's conclusions
        - causal_chain:        ordered causal narrative (observed → inferred steps)
        - severity_score:      may be raised (never lowered) based on TREK inference
        - confidence_score:    may be reduced (TREK adds inference layer discount)
        - trace_payload:       extended with TREK enrichment trace section

    What TREK preserves (NEVER modified):
        - observed_evidence:  original JN/source evidence — untouched
        - source_family:      still reflects the original source (e.g. jet_nexus)
        - source_systems:     still the original source systems
        - evidence_payload:   verbatim original payload
        - all source provenance fields

    Args:
        signal: A NormalizedIntelligenceSignal from any source adapter.
                Must have normalization_status NORMALIZED or PARTIAL.

    Returns:
        Enriched NormalizedIntelligenceSignal. The returned signal is a NEW
        object — the input signal is never mutated (frozen Pydantic model).

    Raises:
        TREKAdapterError: if the input signal is in REJECTED state.
    """
    if signal.normalization_status.value == "REJECTED":
        raise TREKAdapterError(
            f"TREK will not enrich a REJECTED signal (id={signal.normalized_signal_id}). "
            "Resolve validation violations on the source signal first.",
            violations=[],
        )

    tb = TraceBuilder(
        source_family   = f"{signal.source_family.value}+trek",
        source_systems  = list(signal.source_systems) + ["trek"],
        adapter_version = TREK_ADAPTER_VERSION,
    )
    tb.note("trek.enrich", f"Enriching signal id={signal.normalized_signal_id}")
    tb.note("trek.input", (
        f"source_family={signal.source_family} "
        f"signal_type={signal.signal_type} "
        f"severity={signal.severity_score:.3f} "
        f"confidence={signal.confidence_score:.3f} "
        f"domains={signal.affected_domains}"
    ))

    # ── Run rule engine ───────────────────────────────────────────────────────
    engine = _TREKRuleEngine(signal, tb)
    trek_inferences = engine.run()

    # ── Merge with existing inferred_reasoning (from prior sources) ──────────
    merged_inferred = list(signal.inferred_reasoning) + trek_inferences

    # ── Causal chain and summary ──────────────────────────────────────────────
    causal_chain     = _build_causal_chain(signal, trek_inferences)
    reasoning_summary = _build_reasoning_summary(signal, trek_inferences)

    # ── Score adjustment ──────────────────────────────────────────────────────
    new_severity, new_confidence = _compute_enriched_scores(signal, trek_inferences)

    if trek_inferences:
        tb.note("trek.scores", (
            f"Scores adjusted: "
            f"severity {signal.severity_score:.4f}→{new_severity:.4f}, "
            f"confidence {signal.confidence_score:.4f}→{new_confidence:.4f}"
        ))
    else:
        tb.note("trek.scores", "No TREK inferences — scores unchanged")

    # ── Status: keep or upgrade to PARTIAL if warnings ────────────────────────
    trek_status = tb.derived_status()
    if trek_status == "REJECTED":
        # TREK trace should never produce violations — but guard defensively
        original_status = signal.normalization_status
    elif trek_status == "PARTIAL" and signal.normalization_status.value == "NORMALIZED":
        original_status = type(signal.normalization_status)("PARTIAL")
    else:
        original_status = signal.normalization_status

    # ── Build TREK trace and merge into signal trace ───────────────────────────
    trek_trace = tb.build()
    tb.set_semantic_counts(
        observed  = len(signal.observed_evidence),
        inferred  = len(merged_inferred),
        simulated = len(signal.simulation_context),
    )
    merged_trace = dict(signal.trace_payload)
    merged_trace["trek_enrichment"] = trek_trace

    # ── Return enriched NIS (model_copy preserves all original fields) ────────
    enriched = signal.model_copy(update={
        "inferred_reasoning":  merged_inferred,
        "reasoning_summary":   reasoning_summary,
        "causal_chain":        causal_chain,
        "severity_score":      new_severity,
        "confidence_score":    new_confidence,
        "normalization_status": original_status,
        "trace_payload":       merged_trace,
    })

    logger.info(
        "trek.enrich completed id=%s inferences=%d "
        "severity %.3f→%.3f confidence %.3f→%.3f",
        signal.normalized_signal_id,
        len(trek_inferences),
        signal.severity_score,
        new_severity,
        signal.confidence_score,
        new_confidence,
    )

    return enriched


# ─── Backward-compat stub (raw dict path) ────────────────────────────────────

def adapt_trek_payload(raw: dict[str, Any]) -> NormalizedIntelligenceSignal:
    """STUB — TREK does not accept raw external payloads.

    TREK is an enrichment adapter that operates on NormalizedIntelligenceSignal.
    To enrich a signal with TREK, use enrich_with_trek(signal) instead.

    This stub is retained so that the source adapter registry in adapter.py
    does not crash when TREK is listed. Any call with a raw dict will raise.

    Raises:
        NotImplementedError: always — use enrich_with_trek(signal) instead.
    """
    raise NotImplementedError(
        "TREK does not accept raw payloads. "
        "TREK is an enrichment adapter — call enrich_with_trek(signal) "
        "with a NormalizedIntelligenceSignal from a prior source adapter. "
        "Pipeline: adapt_jet_nexus_payload(raw) → enrich_with_trek(signal)"
    )


def validate_trek_payload(raw: dict[str, Any]) -> list[str]:
    """Validate a raw TREK payload against the stub contract.

    Returns:
        list of error messages (non-empty = invalid).
    """
    errors: list[str] = []
    for field_name in TREK_REQUIRED_FIELDS:
        if field_name not in raw or raw[field_name] is None:
            errors.append(f"Missing required field: '{field_name}'")
    return errors
