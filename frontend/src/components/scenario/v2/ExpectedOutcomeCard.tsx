/**
 * ExpectedOutcomeCard — projected outcome if recommended actions are taken.
 *
 * Outcome section. Shows loss with vs. without intervention,
 * recovery timeline, and value preserved.
 */

import { fmtUsd } from "@/lib/copy";

interface ExpectedOutcomeCardProps {
  totalLoss: number;
  lossAvoided: number;
  totalCost: number;
  recoveryDays: number;
  actionsCount: number;
  confidence: number;
}

export function ExpectedOutcomeCard({
  totalLoss,
  lossAvoided,
  totalCost,
  recoveryDays,
  actionsCount,
  confidence,
}: ExpectedOutcomeCardProps) {
  const netLoss = totalLoss - lossAvoided;
  const roi = lossAvoided / Math.max(totalCost, 1);

  return (
    <section className="py-12 border-t border-border-muted">
      {/* Section label */}
      <p className="text-[0.625rem] font-medium uppercase tracking-[0.12em] text-tx-tertiary mb-3">
        Outcome
      </p>
      <h2 className="text-[1.5rem] font-semibold tracking-[-0.02em] text-charcoal mb-2">
        Expected outcome
      </h2>
      <p className="text-[0.9375rem] leading-[1.6] text-tx-secondary max-w-[520px] mb-10">
        Projected financial position if all {actionsCount} recommended actions
        are executed within their deadlines.
      </p>

      {/* Outcome comparison */}
      <div className="max-w-[640px]">
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-8 mb-10">
          {/* Without intervention */}
          <div>
            <span className="text-[0.625rem] font-medium uppercase tracking-[0.08em] text-tx-tertiary">
              Without Action
            </span>
            <p className="mt-1 text-[1.75rem] font-semibold tabular-nums text-status-red tracking-[-0.02em] leading-none">
              {fmtUsd(totalLoss)}
            </p>
          </div>

          {/* With intervention */}
          <div>
            <span className="text-[0.625rem] font-medium uppercase tracking-[0.08em] text-tx-tertiary">
              With Action
            </span>
            <p className="mt-1 text-[1.75rem] font-semibold tabular-nums text-charcoal tracking-[-0.02em] leading-none">
              {fmtUsd(netLoss)}
            </p>
          </div>

          {/* Value preserved */}
          <div>
            <span className="text-[0.625rem] font-medium uppercase tracking-[0.08em] text-tx-tertiary">
              Value Preserved
            </span>
            <p className="mt-1 text-[1.75rem] font-semibold tabular-nums text-status-olive tracking-[-0.02em] leading-none">
              {fmtUsd(lossAvoided)}
            </p>
          </div>
        </div>

        {/* Supporting metrics */}
        <div className="pt-6 border-t border-border-muted grid grid-cols-2 sm:grid-cols-4 gap-6">
          <OutcomeStat label="Intervention Cost" value={fmtUsd(totalCost)} />
          <OutcomeStat label="ROI" value={`${roi.toFixed(1)}x`} />
          <OutcomeStat label="Recovery" value={`${recoveryDays} days`} />
          <OutcomeStat
            label="Confidence"
            value={`${Math.round(confidence * 100)}%`}
          />
        </div>
      </div>

      {/* Provenance */}
      <p className="mt-10 text-[0.8125rem] leading-[1.6] text-tx-tertiary max-w-[520px]">
        All projections are traceable. Each action carries provenance
        &mdash; who recommended it, what data supported it, and the
        expected outcome if executed.
      </p>
    </section>
  );
}

function OutcomeStat({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex flex-col">
      <span className="text-[0.625rem] font-medium uppercase tracking-[0.08em] text-tx-tertiary">
        {label}
      </span>
      <span className="mt-1 text-[1rem] font-semibold tabular-nums text-charcoal">
        {value}
      </span>
    </div>
  );
}
