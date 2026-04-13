"use client";

/**
 * SovereignBriefing — Vertical Intelligence Reading Surface
 *
 * Implements all 8 architectural fixes in a single scrollable briefing.
 * NOT a dashboard. NOT a simulation tool. NOT a SaaS UI.
 * This is a sovereign intelligence briefing — an economic decision surface.
 *
 * Vertical reading sequence:
 *   Macro → Signal → Propagation → Decision → Exposure → Monitoring
 *
 * Each section = ONE idea. CEO-readable. No chrome. No widgets.
 */

import React, { useMemo, useState } from "react";
import type {
  SovereignBriefing as SovereignBriefingType,
  SignalBrief,
  PropagationProseStep,
  DirectiveItem,
  CountrySectorExposure,
  MonitoringBrief,
  TemporalHorizon,
  ConfidenceBasis,
  CounterfactualBaseline,
} from "@/lib/intelligence/sovereignBriefingEngine";
import {
  type IntelligencePerspective,
  ALL_PERSPECTIVES,
  PERSPECTIVE_LABELS,
  type PerspectiveNarrative,
} from "@/lib/intelligence/perspectiveEngine";

/* ═══════════════════════════════════════════════════════════════════════
 * Section Primitives
 * ═══════════════════════════════════════════════════════════════════════ */

function SectionDivider({ label }: { label: string }) {
  return (
    <div className="flex items-center gap-3 pt-10 pb-4">
      <div className="h-px flex-1 bg-white/[0.06]" />
      <span className="text-[10px] font-semibold text-slate-600 uppercase tracking-[0.2em]">
        {label}
      </span>
      <div className="h-px flex-1 bg-white/[0.06]" />
    </div>
  );
}

function Prose({ children }: { children: React.ReactNode }) {
  return (
    <p className="text-[13px] text-slate-300 leading-[1.75] tracking-wide">
      {children}
    </p>
  );
}

function ProseSecondary({ children }: { children: React.ReactNode }) {
  return (
    <p className="text-[12px] text-slate-500 leading-[1.7] tracking-wide">
      {children}
    </p>
  );
}

function Label({ children }: { children: React.ReactNode }) {
  return (
    <p className="text-[10px] font-semibold text-slate-600 uppercase tracking-[0.15em] mb-2">
      {children}
    </p>
  );
}

/* ═══════════════════════════════════════════════════════════════════════
 * Section 1: MACRO
 * ═══════════════════════════════════════════════════════════════════════ */

function MacroSection({ posture, advisory }: { posture: string; advisory: string }) {
  return (
    <div>
      <div className="mb-4">
        <p className="text-[15px] font-semibold text-white tracking-wide leading-snug">
          {posture}
        </p>
      </div>
      <Prose>{advisory}</Prose>
    </div>
  );
}

/* ═══════════════════════════════════════════════════════════════════════
 * Section 2: SIGNAL (FIX 2 — dual signal with selection rationale)
 * ═══════════════════════════════════════════════════════════════════════ */

function SignalSection({ signal }: { signal: SignalBrief }) {
  return (
    <div className="space-y-4">
      {/* Dominant signal */}
      <div>
        <Label>Dominant Signal</Label>
        <p className="text-[14px] font-semibold text-white leading-snug mb-1">
          {signal.dominantSignal}
        </p>
        {signal.dominantType && (
          <span className="inline-block text-[10px] font-semibold text-blue-400 bg-blue-400/10 px-2 py-0.5 rounded tracking-wider uppercase mb-3">
            {signal.dominantType} · {Math.round(signal.dominantIntensity * 100)}%
          </span>
        )}
      </div>

      {/* Selection basis */}
      <Prose>{signal.selectionBasis}</Prose>

      {/* Second signal */}
      {signal.secondSignal && (
        <div className="border-l-2 border-white/[0.06] pl-4">
          <Label>Runner-up Signal</Label>
          <p className="text-[12px] text-slate-400 leading-relaxed">
            {signal.secondSignal}
            <span className="text-slate-600 ml-2">
              ({signal.secondType} · {Math.round(signal.secondIntensity * 100)}%)
            </span>
          </p>
        </div>
      )}

      <ProseSecondary>
        {signal.activeCount} signals active · {signal.peakCount} at peak intensity
      </ProseSecondary>
    </div>
  );
}

/* ═══════════════════════════════════════════════════════════════════════
 * Section 3: PROPAGATION (FIX 3 — numbered prose, no visuals)
 * ═══════════════════════════════════════════════════════════════════════ */

function PropagationSection({ steps }: { steps: PropagationProseStep[] }) {
  if (steps.length === 0) {
    return <ProseSecondary>No propagation chain detected at current scenario progress.</ProseSecondary>;
  }

  return (
    <div className="space-y-4">
      {steps.map((step) => (
        <div key={step.stepNumber} className="flex gap-4">
          <span className="text-[13px] font-bold text-slate-600 tabular-nums flex-shrink-0 w-5 text-right">
            {step.stepNumber}.
          </span>
          <Prose>{step.prose}</Prose>
        </div>
      ))}
    </div>
  );
}

/* ═══════════════════════════════════════════════════════════════════════
 * Section 4: DECISION (FIX 5 — directive prose + consequence)
 * ═══════════════════════════════════════════════════════════════════════ */

function DecisionSection({ directives }: { directives: DirectiveItem[] }) {
  if (directives.length === 0) {
    return <ProseSecondary>No active directives. System in monitoring posture.</ProseSecondary>;
  }

  return (
    <div className="space-y-6">
      {directives.map((d, i) => (
        <div key={i} className="space-y-2">
          <p className="text-[13px] font-semibold text-white leading-snug">
            {d.directive}
          </p>
          <p className="text-[11px] text-slate-500">
            <span className="text-slate-600">{d.owner}</span>
            <span className="text-slate-700 mx-2">·</span>
            <span className="text-slate-600">{d.sector}</span>
          </p>
          <p className="text-[12px] text-amber-400/80 leading-[1.7]">
            {d.consequence}
          </p>
        </div>
      ))}
    </div>
  );
}

/* ═══════════════════════════════════════════════════════════════════════
 * Section 5: EXPOSURE (FIX 4 — country-specific, no aggregation)
 * ═══════════════════════════════════════════════════════════════════════ */

function ExposureSection({ exposures }: { exposures: CountrySectorExposure[] }) {
  if (exposures.length === 0) {
    return <ProseSecondary>No country-sector exposures above threshold.</ProseSecondary>;
  }

  return (
    <div className="space-y-3">
      {exposures.slice(0, 12).map((e, i) => (
        <div key={i} className="flex gap-3 items-baseline">
          <span className="text-[12px] font-semibold text-slate-300 whitespace-nowrap flex-shrink-0" style={{ minWidth: '180px' }}>
            {e.country} {e.sector}:
          </span>
          <p className="text-[12px] text-slate-400 leading-[1.6]">
            {e.exposure}
          </p>
        </div>
      ))}
    </div>
  );
}

/* ═══════════════════════════════════════════════════════════════════════
 * Section 6: MONITORING (FIX 6 — owner/escalation/review only)
 * ═══════════════════════════════════════════════════════════════════════ */

function MonitoringSection({ monitoring }: { monitoring: MonitoringBrief }) {
  return (
    <div className="space-y-4">
      <Prose>{monitoring.statusSummary}</Prose>

      {monitoring.assignments.length > 0 && (
        <div className="space-y-3 pt-2">
          {monitoring.assignments.map((a, i) => (
            <div key={i} className="border-l-2 border-white/[0.06] pl-4">
              <p className="text-[12px] text-slate-300 font-medium mb-1">{a.action}</p>
              <div className="flex flex-wrap gap-x-4 gap-y-1 text-[11px] text-slate-500">
                <span>Owner: <span className="text-slate-400">{a.owner}</span></span>
                <span>Escalation: <span className="text-slate-400">{a.escalationAuthority}</span></span>
                <span>Review: <span className="text-slate-400">every {a.reviewCycleHours}h</span></span>
                <span className={a.status === 'escalated' ? 'text-red-400' : a.status === 'at_risk' ? 'text-amber-400' : ''}>
                  Status: {a.status} · {Math.round(a.hoursRemaining)}h remaining
                </span>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

/* ═══════════════════════════════════════════════════════════════════════
 * FIX 8: Missing Intelligence Layers
 * ═══════════════════════════════════════════════════════════════════════ */

function TemporalSection({ horizon }: { horizon: TemporalHorizon }) {
  return (
    <div className="space-y-4">
      <div>
        <Label>Now</Label>
        <Prose>{horizon.now}</Prose>
      </div>
      <div>
        <Label>72 Hours</Label>
        <ProseSecondary>{horizon.hours72}</ProseSecondary>
      </div>
      <div>
        <Label>30 Days</Label>
        <ProseSecondary>{horizon.days30}</ProseSecondary>
      </div>
    </div>
  );
}

function ConfidenceSection({ basis }: { basis: ConfidenceBasis }) {
  return (
    <div>
      <Prose>{basis.explanation}</Prose>
    </div>
  );
}

function CounterfactualSection({ baseline }: { baseline: CounterfactualBaseline }) {
  return (
    <div className="bg-red-500/[0.04] border border-red-500/10 rounded-lg px-5 py-4">
      <Label>Without Action</Label>
      <p className="text-[13px] text-red-400/80 leading-[1.75]">{baseline.withoutAction}</p>
    </div>
  );
}

/* ═══════════════════════════════════════════════════════════════════════
 * FIX 1: Perspective Switcher
 * ═══════════════════════════════════════════════════════════════════════ */

function PerspectivePanel({
  perspectives,
  active,
  onSwitch,
}: {
  perspectives: PerspectiveNarrative[];
  active: IntelligencePerspective;
  onSwitch: (p: IntelligencePerspective) => void;
}) {
  const current = perspectives.find(p => p.perspective === active) ?? perspectives[0];
  if (!current) return null;

  return (
    <div className="space-y-4">
      {/* Switcher tabs */}
      <div className="flex flex-wrap gap-2">
        {ALL_PERSPECTIVES.map((p) => (
          <button
            key={p}
            onClick={() => onSwitch(p)}
            className={`px-3 py-1.5 text-[10px] font-semibold uppercase tracking-wider rounded-md transition-colors ${
              active === p
                ? "bg-blue-500/15 text-blue-400 border border-blue-500/30"
                : "text-slate-600 hover:text-slate-400 border border-transparent"
            }`}
          >
            {PERSPECTIVE_LABELS[p].en}
          </button>
        ))}
      </div>

      {/* Active perspective narrative */}
      <div className="space-y-4">
        <div>
          <Label>Transmission Framing</Label>
          <Prose>{current.transmissionFraming}</Prose>
        </div>
        <div>
          <Label>Exposure Narrative</Label>
          <Prose>{current.exposureNarrative}</Prose>
        </div>
        <div>
          <Label>Decision Rationale</Label>
          <Prose>{current.decisionRationale}</Prose>
        </div>
      </div>
    </div>
  );
}

/* ═══════════════════════════════════════════════════════════════════════
 * Main Component — FIX 7: Vertical Reading Sequence
 * ═══════════════════════════════════════════════════════════════════════ */

interface SovereignBriefingProps {
  briefing: SovereignBriefingType;
  onPerspectiveChange?: (p: IntelligencePerspective) => void;
}

export function SovereignBriefing({ briefing, onPerspectiveChange }: SovereignBriefingProps) {
  const [activePerspective, setActivePerspective] = useState<IntelligencePerspective>(
    briefing.activePerspective,
  );

  const handlePerspectiveSwitch = (p: IntelligencePerspective) => {
    setActivePerspective(p);
    onPerspectiveChange?.(p);
  };

  return (
    <div className="max-w-3xl mx-auto px-6 py-8 text-left">
      {/* ── MACRO ──────────────────────────────────────────────── */}
      <SectionDivider label="Macro" />
      <MacroSection posture={briefing.macro.posture} advisory={briefing.macro.advisory} />

      {/* ── SIGNAL ─────────────────────────────────────────────── */}
      <SectionDivider label="Signal" />
      <SignalSection signal={briefing.signal} />

      {/* ── PROPAGATION ────────────────────────────────────────── */}
      <SectionDivider label="Propagation" />
      <PropagationSection steps={briefing.propagation} />

      {/* ── DECISION ───────────────────────────────────────────── */}
      <SectionDivider label="Decision" />
      <DecisionSection directives={briefing.directives} />

      {/* ── EXPOSURE ───────────────────────────────────────────── */}
      <SectionDivider label="Exposure" />
      <ExposureSection exposures={briefing.macroExposures} />

      {/* ── MONITORING ─────────────────────────────────────────── */}
      <SectionDivider label="Monitoring" />
      <MonitoringSection monitoring={briefing.monitoring} />

      {/* ── TEMPORAL HORIZON (FIX 8A) ──────────────────────────── */}
      <SectionDivider label="Temporal Horizon" />
      <TemporalSection horizon={briefing.temporalHorizon} />

      {/* ── CONFIDENCE (FIX 8B) ────────────────────────────────── */}
      <SectionDivider label="Confidence" />
      <ConfidenceSection basis={briefing.confidenceBasis} />

      {/* ── COUNTERFACTUAL (FIX 8C) ────────────────────────────── */}
      <SectionDivider label="Counterfactual" />
      <CounterfactualSection baseline={briefing.counterfactual} />

      {/* ── PERSPECTIVE (FIX 1) ────────────────────────────────── */}
      <SectionDivider label="Intelligence Perspective" />
      <PerspectivePanel
        perspectives={briefing.perspectives}
        active={activePerspective}
        onSwitch={handlePerspectiveSwitch}
      />

      {/* Footer */}
      <div className="mt-16 pt-6 border-t border-white/[0.04]">
        <p className="text-[10px] text-slate-700 tracking-wider">
          Generated {new Date(briefing.timestamp).toLocaleString()} · Scenario: {briefing.scenarioId}
        </p>
      </div>
    </div>
  );
}
