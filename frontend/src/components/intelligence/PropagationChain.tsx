/**
 * Causal Propagation — Intelligence Component
 *
 * Numbered prose paragraphs. Not a timeline rail. Not a dot-connector.
 * Each step is a complete sentence that a central bank governor reads
 * top-to-bottom without scanning.
 *
 * Each paragraph contains:
 *   - What happened at this entity
 *   - How much financial exposure it created
 *   - What mechanism transmitted the pressure
 *   - Where it goes next (if not the last step)
 *
 * Perspective-aware: executive sees directional summary,
 * analyst sees mechanism detail, regulator sees threshold data.
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

function stressWord(delta: number): string {
  if (delta >= 0.8) return "severe";
  if (delta >= 0.65) return "critical";
  if (delta >= 0.5) return "elevated";
  if (delta >= 0.35) return "moderate";
  return "contained";
}

function stressColor(delta: number): string {
  if (delta >= 0.7) return "text-status-red";
  if (delta >= 0.4) return "text-status-amber";
  return "text-status-olive";
}

/**
 * Build a prose paragraph for one causal step.
 * The paragraph reads as a complete sentence — no metadata rows.
 */
function stepParagraph(
  persona: "executive" | "analyst" | "regulator",
  step: { entity_label: string; event: string; impact_usd: number; stress_delta: number; mechanism: string },
  nextStep: { entity_label: string } | null,
  isFirst: boolean,
  isLast: boolean,
): string {
  const stressLevel = stressWord(step.stress_delta);
  const impact = step.impact_usd > 0 ? formatUsd(step.impact_usd) : null;
  const mechanism = step.mechanism.replace(/_/g, " ");
  const forward = nextStep
    ? ` This transmits directly to ${nextStep.entity_label}.`
    : "";

  switch (persona) {
    case "executive":
      return (
        step.event +
        (impact ? ` Exposure: ${impact}.` : "") +
        forward +
        (isLast ? " This is the current terminal point of the propagation chain." : "")
      );

    case "analyst":
      return (
        step.event +
        ` Stress delta: ${Math.round(step.stress_delta * 100)}% (${stressLevel}).` +
        ` Mechanism: ${mechanism}.` +
        (impact ? ` Financial impact: ${impact}.` : "") +
        forward
      );

    case "regulator":
      return (
        (isFirst ? `Initiating event at ${step.entity_label}: ` : `${step.entity_label}: `) +
        step.event +
        ` Stress at ${Math.round(step.stress_delta * 100)}%` +
        (step.stress_delta >= 0.65 ? " — exceeds supervisory threshold." : ".") +
        (impact ? ` Regulatory exposure: ${impact}.` : "") +
        forward
      );
  }
}

// ── Component ──────────────────────────────────────────────────────────

export function PropagationChain() {
  const causalChain = useCommandCenterStore((s) => s.causalChain);
  const headline = useCommandCenterStore((s) => s.headline);
  const counterfactual = useCommandCenterStore((s) => s.counterfactual);
  const confidence = useCommandCenterStore((s) => s.confidence);
  const status = useCommandCenterStore((s) => s.status);
  const persona = useAppStore((s) => s.persona);

  if (status !== "ready" || causalChain.length === 0) return null;

  const chainImpact = causalChain.reduce((sum, s) => sum + s.impact_usd, 0);

  return (
    <section>
      <p className="text-[0.625rem] font-medium uppercase tracking-[0.12em] text-tx-tertiary mb-4">
        Causal Propagation
      </p>

      {/* Context sentence */}
      <p className="text-[0.9375rem] leading-[1.7] text-tx-secondary mb-10">
        The disruption propagates through {causalChain.length} stages
        {chainImpact > 0 ? ` with ${formatUsd(chainImpact)} in traced financial impact` : ""}.
        {headline
          ? ` Propagation depth reaches ${headline.propagationDepth} layers with peak stress on day ${headline.peakDay}.`
          : ""}
        {headline && headline.maxRecoveryDays > 0
          ? ` Recovery baseline: ${headline.maxRecoveryDays} days without intervention.`
          : ""}
      </p>

      {/* Numbered prose paragraphs — one idea per paragraph */}
      <ol className="space-y-8">
        {causalChain.map((step, idx) => {
          const next = idx < causalChain.length - 1 ? causalChain[idx + 1] : null;
          const isFirst = idx === 0;
          const isLast = idx === causalChain.length - 1;

          return (
            <li key={step.entity_id + idx}>
              {/* Step number + entity */}
              <p className="text-[0.9375rem] leading-[1.65] text-tx-primary">
                <span className="font-semibold tabular-nums text-tx-tertiary mr-2">
                  {String(step.step).padStart(2, "0")}
                </span>
                <span className="font-semibold">{step.entity_label}</span>
                <span className={`ml-3 tabular-nums text-[0.8125rem] font-medium ${stressColor(step.stress_delta)}`}>
                  {Math.round(step.stress_delta * 100)}%
                </span>
              </p>

              {/* Prose paragraph — the complete narrative for this step */}
              <p className="mt-2 text-[0.875rem] leading-[1.7] text-tx-secondary">
                {stepParagraph(persona, step, next, isFirst, isLast)}
              </p>
            </li>
          );
        })}
      </ol>

      {/* Counterfactual baseline at chain terminus */}
      {counterfactual?.narrative && (
        <p className="mt-10 text-[0.9375rem] leading-[1.7] text-tx-secondary">
          {counterfactual.narrative}
        </p>
      )}

      {/* Confidence basis */}
      {confidence > 0 && (
        <p className="mt-3 text-[0.8125rem] leading-[1.65] text-tx-tertiary">
          Propagation model confidence: {Math.round(confidence * 100)}%.
          {counterfactual?.consistency_flag === "CONSISTENT"
            ? " Counterfactual analysis is consistent with the primary projection."
            : counterfactual?.consistency_flag === "CORRECTED_COSTLY"
              ? " Counterfactual correction applied — alternative pathway carries higher cost."
              : counterfactual?.consistency_flag === "CORRECTED_INCONSISTENCY"
                ? " Counterfactual correction applied — initial projection adjusted for consistency."
                : ""}
        </p>
      )}
    </section>
  );
}
