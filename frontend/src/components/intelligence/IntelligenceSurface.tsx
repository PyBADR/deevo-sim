/**
 * Intelligence Surface — Unified Reading Sequence
 *
 * Single scrollable document composing 6 intelligence sections
 * in the mandated vertical reading order:
 *
 *   01  Macro Context
 *   02  Dominant Signal
 *   03  Causal Propagation
 *   04  Required Decision
 *   05  Exposed Entities
 *   06  Monitoring / Review
 *
 * One block = one idea. No scanning puzzle.
 * Perspective-aware via useAppStore persona.
 *
 * Reads from: useCommandCenterStore (status).
 */

"use client";

import { useCommandCenterStore } from "@/features/command-center/lib/command-store";
import { MacroStrip } from "./MacroStrip";
import { CriticalSignal } from "./CriticalSignal";
import { PropagationChain } from "./PropagationChain";
import { DecisionIntelligence } from "./DecisionIntelligence";
import { EntityExposure } from "./EntityExposure";
import { MonitoringBlock } from "./MonitoringBlock";

export function IntelligenceSurface() {
  const status = useCommandCenterStore((s) => s.status);
  const scenario = useCommandCenterStore((s) => s.scenario);

  if (status !== "ready") {
    return (
      <div className="pt-10 pb-24 max-w-[720px]">
        <p className="text-[0.9375rem] text-tx-tertiary">
          {status === "loading"
            ? "Preparing intelligence briefing\u2026"
            : status === "error"
              ? "Intelligence briefing unavailable."
              : "Select a scenario to generate the intelligence briefing."}
        </p>
      </div>
    );
  }

  return (
    <article className="pt-10 pb-24 max-w-[720px]">

      {/* Document header */}
      {scenario && (
        <div className="mb-16">
          <p className="text-[0.625rem] font-medium uppercase tracking-[0.12em] text-tx-tertiary mb-3">
            Intelligence Briefing
          </p>
          <h1
            className="
              text-[clamp(1.75rem,4vw,2.75rem)] font-semibold
              leading-[1.08] tracking-[-0.03em]
              text-charcoal text-balance
            "
          >
            {scenario.label}
          </h1>
        </div>
      )}

      {/* ── 01  Macro Context ── */}
      <div className="mb-20">
        <MacroStrip />
      </div>

      {/* ── 02  Dominant Signal ── */}
      <div className="mb-20">
        <CriticalSignal />
      </div>

      {/* ── 03  Causal Propagation ── */}
      <div className="mb-20">
        <PropagationChain />
      </div>

      {/* ── 04  Required Decision ── */}
      <div className="mb-20">
        <DecisionIntelligence />
      </div>

      {/* ── 05  Exposed Entities ── */}
      <div className="mb-20">
        <EntityExposure />
      </div>

      {/* ── 06  Monitoring / Review ── */}
      <div>
        <MonitoringBlock />
      </div>

      {/* Footer */}
      <footer className="mt-24 pt-6 border-t border-border-muted flex items-end justify-between">
        <span className="text-[0.6875rem] text-tx-tertiary tracking-[0.02em]">
          GCC Macro Financial Intelligence
        </span>
        <span className="text-[0.6875rem] text-tx-tertiary tabular-nums">
          2026
        </span>
      </footer>
    </article>
  );
}
