/**
 * DecisionStrip — recommended actions with ownership and deadlines.
 *
 * Decision section. Each action card shows:
 * owner, deadline, escalation trigger, cost-benefit ratio.
 * Prioritized by urgency. Institutional tone.
 */

import type { DecisionActionV2 } from "@/types/observatory";
import { QuietCard } from "@/components/primitives/QuietCard";
import { Badge } from "@/components/primitives/Badge";
import { fmtUsd } from "@/lib/copy";

interface DecisionStripProps {
  actions: DecisionActionV2[];
}

function deadlineColor(hours?: number): string {
  if (!hours) return "text-tx-secondary";
  if (hours <= 8) return "text-status-red";
  if (hours <= 16) return "text-status-amber";
  return "text-tx-secondary";
}

function urgencyVariant(u: number): "red" | "amber" | "olive" {
  if (u >= 85) return "red";
  if (u >= 70) return "amber";
  return "olive";
}

export function DecisionStrip({ actions }: DecisionStripProps) {
  const sorted = [...actions].sort((a, b) => b.priority - a.priority);

  return (
    <section className="py-12 border-t border-border-muted">
      {/* Section label */}
      <p className="text-[0.625rem] font-medium uppercase tracking-[0.12em] text-tx-tertiary mb-3">
        Decision
      </p>
      <h2 className="text-[1.5rem] font-semibold tracking-[-0.02em] text-charcoal mb-2">
        Recommended actions
      </h2>
      <p className="text-[0.9375rem] leading-[1.6] text-tx-secondary max-w-[520px] mb-10">
        Prioritized interventions with cost-benefit analysis,
        ownership, and escalation conditions.
      </p>

      {/* Action cards */}
      <div className="space-y-4 max-w-[720px]">
        {sorted.map((action) => (
          <QuietCard key={action.id} hover>
            {/* Top row: priority badge + owner + deadline */}
            <div className="flex items-start justify-between gap-4 mb-4">
              <div className="flex items-center gap-3 min-w-0">
                <Badge variant={urgencyVariant(action.urgency)}>
                  P{action.priority}
                </Badge>
                <span className="text-[0.75rem] font-medium text-tx-tertiary truncate">
                  {action.owner}
                </span>
              </div>
              {action.deadline_hours && (
                <span
                  className={`text-[0.75rem] font-semibold tabular-nums whitespace-nowrap ${deadlineColor(action.deadline_hours)}`}
                >
                  {action.deadline_hours}h deadline
                </span>
              )}
            </div>

            {/* Action description */}
            <p className="text-[0.9375rem] font-medium leading-[1.5] text-tx-primary mb-4">
              {action.action}
            </p>

            {/* Escalation trigger */}
            {action.escalation_trigger && (
              <div className="mb-4 px-3 py-2.5 rounded-md bg-bg-muted">
                <span className="text-[0.625rem] font-medium uppercase tracking-[0.08em] text-tx-tertiary block mb-1">
                  Escalation Trigger
                </span>
                <p className="text-[0.8125rem] leading-[1.5] text-tx-secondary">
                  {action.escalation_trigger}
                </p>
              </div>
            )}

            {/* Metrics row */}
            <div className="pt-3 border-t border-border-muted flex items-center gap-8 flex-wrap">
              <ActionMetric
                label="Loss Avoided"
                value={fmtUsd(action.loss_avoided_usd)}
              />
              <ActionMetric
                label="Cost"
                value={fmtUsd(action.cost_usd)}
              />
              <ActionMetric
                label="Confidence"
                value={`${Math.round(action.confidence * 100)}%`}
              />
              <ActionMetric
                label="Sector"
                value={action.sector}
              />
            </div>
          </QuietCard>
        ))}
      </div>
    </section>
  );
}

function ActionMetric({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex flex-col">
      <span className="text-[0.625rem] font-medium uppercase tracking-[0.06em] text-tx-tertiary">
        {label}
      </span>
      <span className="mt-0.5 text-[0.8125rem] font-semibold tabular-nums text-charcoal">
        {value}
      </span>
    </div>
  );
}
