/**
 * Required Decision — Intelligence Component
 *
 * Directive prose. Not a WHY/HOW/WHAT framework.
 * Each action reads as a complete institutional directive:
 *   who must act, what they must do, by when, and what happens if they do not.
 *
 * Perspective-aware:
 *   executive → financial consequence + owner accountability
 *   analyst   → mechanism + confidence + cost/benefit
 *   regulator → regulatory obligation + escalation threshold
 *
 * Includes:
 *   - Temporal horizon (deadline_hours per action)
 *   - Counterfactual cost (loss if action is NOT taken)
 *   - Confidence basis per action
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

function urgencyWord(u: number): string {
  if (u >= 90) return "immediate";
  if (u >= 75) return "urgent";
  if (u >= 50) return "priority";
  return "standard";
}

/**
 * Build a complete directive sentence.
 * No framework labels. No bullet metadata.
 * The paragraph IS the directive.
 */
function directiveProse(
  persona: "executive" | "analyst" | "regulator",
  action: {
    action: string;
    owner: string;
    sector: string;
    urgency: number;
    loss_avoided_usd: number;
    cost_usd: number;
    confidence: number;
    deadline_hours?: number;
    escalation_trigger?: string;
  },
): string {
  const deadline = action.deadline_hours && action.deadline_hours > 0
    ? `within ${action.deadline_hours} hours`
    : "immediately";
  const saved = action.loss_avoided_usd > 0 ? formatUsd(action.loss_avoided_usd) : "";
  const cost = action.cost_usd > 0 ? formatUsd(action.cost_usd) : "";
  const conf = Math.round(action.confidence * 100);

  switch (persona) {
    case "executive":
      return (
        `${action.owner} must ${action.action.charAt(0).toLowerCase()}${action.action.slice(1)} ${deadline}.` +
        (saved ? ` This preserves an estimated ${saved} in institutional value.` : "") +
        (action.escalation_trigger ? ` If this threshold is breached — ${action.escalation_trigger.charAt(0).toLowerCase()}${action.escalation_trigger.slice(1)} — the response becomes mandatory.` : "")
      );

    case "analyst":
      return (
        `${action.owner} must ${action.action.charAt(0).toLowerCase()}${action.action.slice(1)} ${deadline}.` +
        (saved ? ` Loss avoided: ${saved}.` : "") +
        (cost ? ` Intervention cost: ${cost}.` : "") +
        ` Confidence: ${conf}%.` +
        ` Urgency score: ${action.urgency}/100 (${urgencyWord(action.urgency)}).` +
        (action.escalation_trigger ? ` Escalation trigger: ${action.escalation_trigger}.` : "")
      );

    case "regulator":
      return (
        `Regulatory directive: ${action.owner} must ${action.action.charAt(0).toLowerCase()}${action.action.slice(1)} ${deadline}.` +
        ` ${action.sector.charAt(0).toUpperCase()}${action.sector.slice(1)} sector.` +
        (action.escalation_trigger ? ` Mandatory threshold: ${action.escalation_trigger}.` : "") +
        (saved ? ` Projected regulatory exposure avoided: ${saved}.` : "") +
        ` Action confidence: ${conf}%.`
      );
  }
}

// ── Component ──────────────────────────────────────────────────────────

export function DecisionIntelligence() {
  const decisionActions = useCommandCenterStore((s) => s.decisionActions);
  const headline = useCommandCenterStore((s) => s.headline);
  const causalChain = useCommandCenterStore((s) => s.causalChain);
  const counterfactual = useCommandCenterStore((s) => s.counterfactual);
  const confidence = useCommandCenterStore((s) => s.confidence);
  const status = useCommandCenterStore((s) => s.status);
  const persona = useAppStore((s) => s.persona);

  if (status !== "ready" || decisionActions.length === 0) return null;

  const sorted = [...decisionActions].sort((a, b) => (b.priority ?? 0) - (a.priority ?? 0));
  const totalLossAvoided = sorted.reduce((s, a) => s + (a.loss_avoided_usd ?? 0), 0);
  const totalCost = sorted.reduce((s, a) => s + (a.cost_usd ?? 0), 0);
  const earliestDeadline = Math.min(
    ...sorted.map((a) => a.deadline_hours ?? 999).filter((h) => h > 0 && h < 999),
    999,
  );

  // Counterfactual: what happens without action
  const baselineLoss = counterfactual?.baseline?.projected_loss_usd ?? headline?.totalLossUsd ?? 0;
  const recommendedLoss = counterfactual?.recommended?.projected_loss_usd ?? 0;

  return (
    <section>
      <p className="text-[0.625rem] font-medium uppercase tracking-[0.12em] text-tx-tertiary mb-4">
        Required Decision
      </p>

      {/* Framing paragraph — why these actions exist */}
      <p className="text-[0.9375rem] leading-[1.7] text-tx-primary mb-4">
        {sorted.length} coordinated intervention{sorted.length !== 1 ? "s" : ""} recommended
        across {new Set(sorted.map((a) => a.sector)).size} sector{new Set(sorted.map((a) => a.sector)).size !== 1 ? "s" : ""}.
        {earliestDeadline < 999 && ` First action deadline: ${earliestDeadline} hours.`}
        {totalLossAvoided > 0 && ` Combined value preserved: ${formatUsd(totalLossAvoided)}.`}
        {totalCost > 0 && ` Total intervention cost: ${formatUsd(totalCost)}.`}
      </p>

      {/* Counterfactual baseline sentence */}
      {baselineLoss > 0 && recommendedLoss > 0 && (
        <p className="text-[0.9375rem] leading-[1.7] text-tx-secondary mb-10">
          Without these interventions, projected losses reach {formatUsd(baselineLoss)}
          {counterfactual?.baseline?.recovery_days
            ? ` over ${counterfactual.baseline.recovery_days} days`
            : ""}.
          With coordinated execution, losses reduce to {formatUsd(recommendedLoss)}
          {counterfactual?.delta?.loss_reduction_pct
            ? ` — a ${Math.round(counterfactual.delta.loss_reduction_pct)}% reduction`
            : ""}.
        </p>
      )}
      {baselineLoss > 0 && recommendedLoss === 0 && (
        <p className="text-[0.9375rem] leading-[1.7] text-tx-secondary mb-10">
          Without these interventions, projected losses reach {formatUsd(baselineLoss)}.
          Each action below targets a specific node in the propagation chain to reduce cumulative exposure.
        </p>
      )}

      {/* Directive list — numbered prose paragraphs, not metadata rows */}
      <ol className="border-t border-border-muted">
        {sorted.map((action, idx) => (
          <li
            key={action.id ?? idx}
            className="py-6 border-b border-border-muted"
          >
            {/* Directive prose — one complete paragraph per action */}
            <p className="text-[0.9375rem] leading-[1.7] text-tx-primary">
              <span className="font-semibold tabular-nums text-tx-tertiary mr-2">
                {String(idx + 1).padStart(2, "0")}
              </span>
              {directiveProse(persona, action)}
            </p>
          </li>
        ))}
      </ol>

      {/* Confidence basis */}
      {confidence > 0 && (
        <p className="mt-6 text-[0.8125rem] leading-[1.65] text-tx-tertiary">
          Decision model confidence at {Math.round(confidence * 100)}%.
          {causalChain.length > 0
            ? ` Actions target ${causalChain.length} identified propagation stages.`
            : ""}
        </p>
      )}
    </section>
  );
}
