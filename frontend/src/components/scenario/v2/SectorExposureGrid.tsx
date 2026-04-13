/**
 * SectorExposureGrid — per-sector breakdown of exposure.
 *
 * Impact section, part 2. Grid of sector cards showing
 * stress level, loss, entity count, and top driver.
 */

import type { SectorRollup } from "@/types/observatory";
import { QuietCard } from "@/components/primitives/QuietCard";
import { Badge } from "@/components/primitives/Badge";
import { fmtUsd } from "@/lib/copy";

interface SectorDetail {
  key: string;
  label: string;
  rollup: SectorRollup;
  topDriver?: string;
}

interface SectorExposureGridProps {
  sectors: SectorDetail[];
}

function classificationVariant(
  c: string
): "red" | "amber" | "olive" | "default" {
  if (c === "CRITICAL" || c === "ELEVATED") return "red";
  if (c === "MODERATE") return "amber";
  if (c === "LOW") return "olive";
  return "default";
}

export function SectorExposureGrid({ sectors }: SectorExposureGridProps) {
  return (
    <section className="py-12 border-t border-border-muted">
      {/* Section label */}
      <p className="text-[0.625rem] font-medium uppercase tracking-[0.12em] text-tx-tertiary mb-3">
        Sector Exposure
      </p>
      <h2 className="text-[1.5rem] font-semibold tracking-[-0.02em] text-charcoal mb-2">
        Exposure by sector
      </h2>
      <p className="text-[0.9375rem] leading-[1.6] text-tx-secondary max-w-[520px] mb-10">
        How each sector absorbs the shock, ranked by aggregate stress.
      </p>

      {/* Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
        {sectors.map((s) => (
          <QuietCard key={s.key} hover>
            {/* Header */}
            <div className="flex items-start justify-between gap-3 mb-4">
              <span className="text-[0.75rem] font-medium text-tx-tertiary uppercase tracking-[0.04em]">
                {s.label}
              </span>
              <Badge variant={classificationVariant(s.rollup.classification)}>
                {s.rollup.classification}
              </Badge>
            </div>

            {/* Metrics */}
            <div className="space-y-3">
              <div className="flex justify-between items-baseline">
                <span className="text-[0.75rem] text-tx-tertiary">
                  Aggregate Stress
                </span>
                <span className="text-[0.9375rem] font-semibold tabular-nums text-charcoal">
                  {Math.round(s.rollup.aggregate_stress * 100)}%
                </span>
              </div>
              <div className="flex justify-between items-baseline">
                <span className="text-[0.75rem] text-tx-tertiary">
                  Est. Loss
                </span>
                <span className="text-[0.9375rem] font-semibold tabular-nums text-charcoal">
                  {fmtUsd(s.rollup.total_loss)}
                </span>
              </div>
              <div className="flex justify-between items-baseline">
                <span className="text-[0.75rem] text-tx-tertiary">
                  Entities
                </span>
                <span className="text-[0.9375rem] font-semibold tabular-nums text-charcoal">
                  {s.rollup.node_count}
                </span>
              </div>
            </div>

            {/* Top driver */}
            {s.topDriver && (
              <p className="mt-4 pt-3 border-t border-border-muted text-[0.75rem] leading-[1.55] text-tx-secondary">
                {s.topDriver}
              </p>
            )}
          </QuietCard>
        ))}
      </div>
    </section>
  );
}
