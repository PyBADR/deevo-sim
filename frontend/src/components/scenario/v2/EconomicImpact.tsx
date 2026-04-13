/**
 * EconomicImpact — headline loss numbers and recovery timeline.
 *
 * Impact section. Three key numbers: total loss, recovery, entities affected.
 * Plus a loss range band showing confidence interval.
 */

import { fmtUsd } from "@/lib/copy";

interface EconomicImpactProps {
  totalLoss: number;
  lossLow: number;
  lossHigh: number;
  confidencePct: number;
  recoveryDays: number;
  peakDay: number;
  entitiesAffected: number;
  criticalCount: number;
  elevatedCount: number;
}

export function EconomicImpact({
  totalLoss,
  lossLow,
  lossHigh,
  confidencePct,
  recoveryDays,
  peakDay,
  entitiesAffected,
  criticalCount,
  elevatedCount,
}: EconomicImpactProps) {
  return (
    <section className="py-12 border-t border-border-muted">
      {/* Section label */}
      <p className="text-[0.625rem] font-medium uppercase tracking-[0.12em] text-tx-tertiary mb-3">
        Impact
      </p>
      <h2 className="text-[1.5rem] font-semibold tracking-[-0.02em] text-charcoal mb-10">
        Economic exposure
      </h2>

      {/* Primary metric */}
      <div className="mb-8">
        <span className="text-[0.625rem] font-medium uppercase tracking-[0.08em] text-tx-tertiary">
          Total Estimated Loss
        </span>
        <p className="mt-1 text-[2.5rem] font-semibold tabular-nums tracking-[-0.03em] text-charcoal leading-none">
          {fmtUsd(totalLoss)}
        </p>
        <p className="mt-2 text-[0.8125rem] text-tx-tertiary tabular-nums">
          {fmtUsd(lossLow)} &ndash; {fmtUsd(lossHigh)} ({confidencePct}% confidence)
        </p>
      </div>

      {/* Secondary metrics */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-8 max-w-[640px]">
        <ImpactStat label="Recovery" value={`${recoveryDays} days`} />
        <ImpactStat label="Peak Stress" value={`Day ${peakDay}`} />
        <ImpactStat label="Critical" value={String(criticalCount)} accent />
        <ImpactStat label="Elevated" value={String(elevatedCount)} />
      </div>

      {/* Entity summary */}
      <p className="mt-8 text-[0.875rem] leading-[1.6] text-tx-secondary max-w-[520px]">
        {entitiesAffected} entities affected across the GCC,
        with {criticalCount} in critical status and {elevatedCount} elevated.
        Full recovery estimated at {recoveryDays} days assuming baseline intervention.
      </p>
    </section>
  );
}

function ImpactStat({
  label,
  value,
  accent,
}: {
  label: string;
  value: string;
  accent?: boolean;
}) {
  return (
    <div className="flex flex-col">
      <span className="text-[0.625rem] font-medium uppercase tracking-[0.08em] text-tx-tertiary">
        {label}
      </span>
      <span
        className={`
          mt-1 text-[1.25rem] font-semibold tabular-nums tracking-[-0.01em]
          ${accent ? "text-status-red" : "text-charcoal"}
        `}
      >
        {value}
      </span>
    </div>
  );
}
