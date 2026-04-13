/**
 * Monitoring & Review — Intelligence Component
 *
 * Post-decision accountability without technical system metadata.
 * No pipeline versions. No audit hashes. No provenance blocks.
 *
 * Shows:
 *   - Execution owners and their deadlines (who must act)
 *   - Monitoring owners (who watches and when)
 *   - Review cycle (temporal cadence)
 *   - Escalation thresholds (what triggers mandatory response)
 *   - Temporal horizon (when the window closes)
 *
 * Perspective-aware:
 *   executive → accountability chain + deadline summary
 *   analyst   → review cadence + threshold detail
 *   regulator → mandatory obligations + escalation sequence
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

// ── Component ──────────────────────────────────────────────────────────

export function MonitoringBlock() {
  const decisionActions = useCommandCenterStore((s) => s.decisionActions);
  const headline = useCommandCenterStore((s) => s.headline);
  const scenario = useCommandCenterStore((s) => s.scenario);
  const confidence = useCommandCenterStore((s) => s.confidence);
  const counterfactual = useCommandCenterStore((s) => s.counterfactual);
  const status = useCommandCenterStore((s) => s.status);
  const persona = useAppStore((s) => s.persona);

  if (status !== "ready" || decisionActions.length === 0) return null;

  // ---- Derive execution owners ----
  const owners = new Map<string, { actions: string[]; earliestHours: number; sectors: Set<string>; totalLossAvoided: number }>();
  for (const a of decisionActions) {
    const owner = a.owner ?? "Unassigned";
    const hours = a.deadline_hours ?? 0;
    const existing = owners.get(owner);
    if (existing) {
      existing.actions.push(a.action);
      existing.sectors.add(a.sector);
      existing.totalLossAvoided += a.loss_avoided_usd ?? 0;
      if (hours > 0 && (existing.earliestHours === 0 || hours < existing.earliestHours)) {
        existing.earliestHours = hours;
      }
    } else {
      owners.set(owner, {
        actions: [a.action],
        earliestHours: hours,
        sectors: new Set([a.sector]),
        totalLossAvoided: a.loss_avoided_usd ?? 0,
      });
    }
  }

  // ---- Escalation triggers ----
  const triggers = decisionActions
    .filter((a) => a.escalation_trigger && a.escalation_trigger.length > 0)
    .map((a) => ({
      trigger: a.escalation_trigger!,
      owner: a.owner,
      sector: a.sector,
      deadlineHours: a.deadline_hours ?? 0,
    }));

  // ---- Review cycle ----
  const deadlines = decisionActions
    .map((a) => a.deadline_hours ?? 0)
    .filter((h) => h > 0);
  const earliestDeadline = deadlines.length > 0 ? Math.min(...deadlines) : 24;
  const reviewCycleHours = earliestDeadline <= 12 ? 4 : earliestDeadline <= 24 ? 8 : 12;

  // ---- Temporal horizon ----
  const horizonHours = scenario?.horizonHours ?? 168;
  const recoveryDays = headline?.maxRecoveryDays ?? 0;
  const peakDay = headline?.peakDay ?? 0;

  return (
    <section>
      <p className="text-[0.625rem] font-medium uppercase tracking-[0.12em] text-tx-tertiary mb-4">
        Monitoring &amp; Review
      </p>

      {/* Perspective-aware framing */}
      <p className="text-[0.9375rem] leading-[1.7] text-tx-primary mb-4">
        {persona === "executive" && (
          <>
            {owners.size} decision owner{owners.size !== 1 ? "s" : ""} are accountable
            for {decisionActions.length} actions over a {horizonHours}-hour scenario horizon.
            Reassessment every {reviewCycleHours} hours until resolution.
            {recoveryDays > 0 && ` Full recovery timeline: ${recoveryDays} days.`}
          </>
        )}
        {persona === "analyst" && (
          <>
            Monitoring cadence: {reviewCycleHours}-hour review cycle across
            {" "}{decisionActions.length} actions and {owners.size} execution owners.
            {peakDay > 0 && ` Peak stress day ${peakDay}.`}
            {recoveryDays > 0 && ` Recovery baseline: ${recoveryDays} days.`}
            {` Scenario horizon: ${horizonHours}h.`}
          </>
        )}
        {persona === "regulator" && (
          <>
            Supervisory monitoring: {owners.size} regulated entit{owners.size !== 1 ? "ies" : "y"} carry
            mandatory obligations across {decisionActions.length} actions.
            Review cycle every {reviewCycleHours} hours.
            {triggers.length > 0 && ` ${triggers.length} escalation threshold${triggers.length !== 1 ? "s" : ""} defined.`}
          </>
        )}
      </p>

      {/* Counterfactual: cost of inaction */}
      {counterfactual?.baseline && counterfactual.baseline.projected_loss_usd > 0 && (
        <p className="text-[0.9375rem] leading-[1.7] text-tx-secondary mb-10">
          If no action is taken, losses accumulate to{" "}
          {formatUsd(counterfactual.baseline.projected_loss_usd)}
          {counterfactual.baseline.recovery_days > 0
            ? ` with a ${counterfactual.baseline.recovery_days}-day recovery period`
            : ""}.
          Each missed deadline extends exposure and narrows the window
          for effective intervention.
        </p>
      )}

      {/* Execution Owners — prose, not metadata */}
      <div className="mb-12">
        <p className="text-[0.6875rem] font-medium uppercase tracking-[0.08em] text-tx-tertiary mb-4">
          Execution Owners
        </p>

        <div className="border-t border-border-muted">
          {Array.from(owners.entries()).map(([owner, data]) => (
            <div key={owner} className="py-5 border-b border-border-muted">
              <p className="text-[0.9375rem] leading-[1.7] text-tx-primary">
                <span className="font-semibold">{owner}</span>
                {" is responsible for "}
                {data.actions.length} action{data.actions.length !== 1 ? "s" : ""}
                {" across "}
                {Array.from(data.sectors).join(", ")}
                {data.earliestHours > 0 && (
                  <>. First deadline in {data.earliestHours} hours</>
                )}.
                {data.totalLossAvoided > 0 && (
                  <> Combined value at stake: {formatUsd(data.totalLossAvoided)}.</>
                )}
              </p>
            </div>
          ))}
        </div>
      </div>

      {/* Escalation Thresholds — prose sentences */}
      {triggers.length > 0 && (
        <div className="mb-12">
          <p className="text-[0.6875rem] font-medium uppercase tracking-[0.08em] text-tx-tertiary mb-4">
            Escalation Thresholds
          </p>

          <ol className="space-y-6">
            {triggers.map((t, idx) => (
              <li key={idx}>
                <p className="text-[0.9375rem] leading-[1.7] text-tx-primary">
                  <span className="font-semibold tabular-nums text-tx-tertiary mr-2">
                    {String(idx + 1).padStart(2, "0")}
                  </span>
                  If {t.trigger.charAt(0).toLowerCase()}{t.trigger.slice(1)},
                  the response escalates from recommended to mandatory.
                  {t.owner && ` ${t.owner} carries primary accountability.`}
                  {t.deadlineHours > 0 && ` Window: ${t.deadlineHours} hours.`}
                </p>
              </li>
            ))}
          </ol>
        </div>
      )}

      {/* Review Cycle — temporal accountability */}
      <div>
        <p className="text-[0.6875rem] font-medium uppercase tracking-[0.08em] text-tx-tertiary mb-3">
          Review Schedule
        </p>

        <p className="text-[0.9375rem] leading-[1.7] text-tx-secondary">
          Situation reassessment every {reviewCycleHours} hours for the duration
          of the {horizonHours}-hour scenario horizon.
          {peakDay > 0 && ` Heightened monitoring through day ${peakDay} (projected peak).`}
          {" "}Actions that miss their deadlines are reclassified as overdue
          and escalated to the next level of institutional authority.
        </p>

        {/* Confidence basis sentence */}
        {confidence > 0 && (
          <p className="mt-4 text-[0.8125rem] leading-[1.65] text-tx-tertiary">
            Monitoring thresholds calibrated at {Math.round(confidence * 100)}% model confidence.
            {counterfactual?.confidence_score
              ? ` Counterfactual analysis confidence: ${Math.round(counterfactual.confidence_score * 100)}%.`
              : ""}
          </p>
        )}
      </div>
    </section>
  );
}
