/**
 * Dominant Signal — Intelligence Component
 *
 * Two-signal architecture:
 *   1. Primary signal — the initiating event with signal basis
 *      (why THIS is the dominant signal, not just "highest stress")
 *   2. Secondary signal — the next-most-important event
 *      that either confirms or complicates the primary
 *
 * Perspective-aware: executive sees financial consequence,
 * analyst sees mechanism detail, regulator sees threshold breach.
 *
 * Reads from: useCommandCenterStore, useAppStore (persona).
 */

"use client";

import { useCommandCenterStore } from "@/features/command-center/lib/command-store";
import { useAppStore } from "@/store/app-store";

// ── Helpers ────────────────────────────────────────────────────────────

function formatUsd(n: number): string {
  if (n >= 1_000_000_000) return `$${(n / 1_000_000_000).toFixed(1)}B`;
  if (n >= 1_000_000) return `$${(n / 1_000_000).toFixed(0)}M`;
  if (n > 0) return `$${n.toLocaleString()}`;
  return "";
}

function stressColor(v: number): string {
  if (v >= 0.7) return "text-status-red";
  if (v >= 0.4) return "text-status-amber";
  return "text-status-olive";
}

/**
 * Signal basis — WHY this signal is dominant.
 * Computes a sentence explaining the analytical reason.
 */
function signalBasis(
  signal: { entity_label: string; stress_delta: number; impact_usd: number; mechanism: string },
  chainLength: number,
  headline: { totalLossUsd: number; propagationDepth: number } | null,
): string {
  const pct = headline && headline.totalLossUsd > 0
    ? Math.round((signal.impact_usd / headline.totalLossUsd) * 100)
    : 0;

  const reasons: string[] = [];

  // Highest stress delta
  if (signal.stress_delta >= 0.7) {
    reasons.push(`stress delta of ${Math.round(signal.stress_delta * 100)}% exceeds critical threshold`);
  } else if (signal.stress_delta >= 0.4) {
    reasons.push(`stress delta of ${Math.round(signal.stress_delta * 100)}% at elevated level`);
  }

  // Proportional loss
  if (pct > 20) {
    reasons.push(`accounts for ${pct}% of total projected loss`);
  }

  // Chain origination
  if (chainLength > 2) {
    reasons.push(`initiates a ${chainLength}-stage propagation chain`);
  }

  if (reasons.length === 0) {
    return `Highest-weight signal in the current observation window.`;
  }
  return reasons.join(", ") + ".";
}

/**
 * Perspective-specific signal framing.
 */
function signalFrame(
  persona: "executive" | "analyst" | "regulator",
  label: string,
  event: string,
  impact: number,
  mechanism: string,
): string {
  switch (persona) {
    case "executive":
      return event + (impact > 0 ? ` Financial exposure: ${formatUsd(impact)}.` : "");

    case "analyst":
      return event +
        ` Transmission mechanism: ${mechanism.replace(/_/g, " ")}.` +
        (impact > 0 ? ` Impact: ${formatUsd(impact)}.` : "");

    case "regulator":
      return `Supervisory trigger at ${label}: ` + event +
        (impact > 0 ? ` Regulatory exposure: ${formatUsd(impact)}.` : "");
  }
}

// ── Component ──────────────────────────────────────────────────────────

export function CriticalSignal() {
  const causalChain = useCommandCenterStore((s) => s.causalChain);
  const graphNodes = useCommandCenterStore((s) => s.graphNodes);
  const sectorImpacts = useCommandCenterStore((s) => s.sectorImpacts);
  const headline = useCommandCenterStore((s) => s.headline);
  const macroContext = useCommandCenterStore((s) => s.macroContext);
  const status = useCommandCenterStore((s) => s.status);
  const persona = useAppStore((s) => s.persona);

  if (status !== "ready") return null;
  if (causalChain.length === 0 && graphNodes.length === 0) return null;

  // ---- Primary signal: highest stress_delta in chain ----
  const sorted = [...causalChain].sort((a, b) => b.stress_delta - a.stress_delta);
  const primary = sorted[0] ?? null;

  // ---- Second signal: next-highest that is a DIFFERENT entity ----
  const secondary = sorted.find((s) => s.entity_id !== primary?.entity_id) ?? null;

  // ---- Macro signals from MacroContext (if backend provided them) ----
  const macroSignals = macroContext?.macro_signals ?? [];
  const topMacroSignal = macroSignals.length > 0
    ? [...macroSignals].sort((a, b) => b.raw_value - a.raw_value)[0]
    : null;

  // ---- Top sector ----
  const topSector = sectorImpacts.length > 0
    ? [...sectorImpacts].sort((a, b) => b.maxImpact - a.maxImpact)[0]
    : null;

  if (!primary) return null;

  const basis = signalBasis(primary, causalChain.length, headline);

  return (
    <section>
      <p className="text-[0.625rem] font-medium uppercase tracking-[0.12em] text-tx-tertiary mb-4">
        Dominant Signal
      </p>

      {/* Primary signal */}
      <p className="text-[1.0625rem] font-semibold leading-[1.3] text-tx-primary">
        {primary.entity_label}
        <span className={`ml-3 tabular-nums ${stressColor(primary.stress_delta)}`}>
          {Math.round(primary.stress_delta * 100)}%
        </span>
      </p>

      {/* Signal basis — why this signal, not another */}
      <p className="mt-2 text-[0.8125rem] leading-[1.65] text-tx-tertiary">
        Signal basis: {basis}
      </p>

      {/* Perspective-framed event */}
      <p className="mt-4 text-[0.9375rem] leading-[1.7] text-tx-primary">
        {signalFrame(persona, primary.entity_label, primary.event, primary.impact_usd, primary.mechanism)}
      </p>

      {/* Sector context */}
      {topSector && (
        <p className="mt-3 text-[0.9375rem] leading-[1.7] text-tx-secondary">
          Primary transmission enters the {topSector.sectorLabel} sector
          where {topSector.nodeCount} entities carry an average stress
          of {Math.round(topSector.avgImpact * 100)}%,
          peaking at {Math.round(topSector.maxImpact * 100)}%.
        </p>
      )}

      {/* Macro signal reinforcement (if available from backend) */}
      {topMacroSignal && (
        <p className="mt-3 text-[0.9375rem] leading-[1.7] text-tx-secondary">
          Macro indicator: {topMacroSignal.name_en} at {topMacroSignal.value}{topMacroSignal.unit ? ` ${topMacroSignal.unit}` : ""}
          {topMacroSignal.impact === "high" ? " — high-impact signal" : ""}.
        </p>
      )}

      {/* ── Second Signal ── */}
      {secondary && (
        <div className="mt-10">
          <p className="text-[0.6875rem] font-medium uppercase tracking-[0.08em] text-tx-tertiary mb-3">
            Secondary Signal
          </p>

          <p className="text-[0.9375rem] font-semibold leading-[1.3] text-tx-primary">
            {secondary.entity_label}
            <span className={`ml-3 tabular-nums text-[0.8125rem] font-medium ${stressColor(secondary.stress_delta)}`}>
              {Math.round(secondary.stress_delta * 100)}%
            </span>
          </p>

          <p className="mt-2 text-[0.9375rem] leading-[1.7] text-tx-secondary">
            {secondary.event}
            {secondary.impact_usd > 0 && (
              <> — {formatUsd(secondary.impact_usd)} exposure.</>
            )}
          </p>

          {/* Relationship to primary */}
          <p className="mt-2 text-[0.8125rem] leading-[1.65] text-tx-tertiary">
            {secondary.step > primary.step
              ? `Downstream from ${primary.entity_label}. Confirms transmission is active through the ${secondary.mechanism.replace(/_/g, " ")} channel.`
              : secondary.step < primary.step
                ? `Upstream of ${primary.entity_label}. This signal precedes the primary event in the causal sequence.`
                : `Concurrent with ${primary.entity_label}. Independent transmission channel via ${secondary.mechanism.replace(/_/g, " ")}.`
            }
          </p>
        </div>
      )}
    </section>
  );
}
