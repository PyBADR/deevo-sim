/**
 * ScenarioCard — single scenario preview in the gallery.
 *
 * Visual rules:
 *   - domain label top-left, severity badge top-right
 *   - title in card-title weight
 *   - description clamped to 2 lines
 *   - bottom row: loss estimate + sector count + horizon
 *   - hover lifts border, shows soft shadow
 *   - no blue, no heavy colors
 */

import { QuietCard } from "@/components/primitives/QuietCard";
import { Badge } from "@/components/primitives/Badge";

export interface ScenarioCardData {
  title: string;
  domain: string;
  severity: number;
  description: string;
  slug: string;
  estimatedLoss: string;
  sectorsAffected: number;
  horizonDays: number;
}

function severityVariant(s: number): "red" | "amber" | "olive" {
  if (s >= 0.7) return "red";
  if (s >= 0.5) return "amber";
  return "olive";
}

function severityLabel(s: number): string {
  if (s >= 0.7) return "High";
  if (s >= 0.5) return "Elevated";
  return "Moderate";
}

export function ScenarioCard({
  title,
  domain,
  severity,
  description,
  slug,
  estimatedLoss,
  sectorsAffected,
  horizonDays,
}: ScenarioCardData) {
  return (
    <a href={`/command-center?scenario=${slug}`} className="block group">
      <QuietCard hover className="h-full flex flex-col">
        {/* Header row: domain + severity */}
        <div className="flex items-start justify-between gap-3 mb-4">
          <span className="text-micro text-tx-tertiary uppercase tracking-[0.06em]">
            {domain}
          </span>
          <Badge variant={severityVariant(severity)}>
            {severityLabel(severity)}
          </Badge>
        </div>

        {/* Title */}
        <h3 className="text-card-title text-tx-primary mb-2 group-hover:text-charcoal transition-colors duration-150">
          {title}
        </h3>

        {/* Description — clamped */}
        <p className="text-card-body text-tx-secondary line-clamp-2 mb-5 flex-1">
          {description}
        </p>

        {/* Metrics row */}
        <div className="pt-4 border-t border-border-muted flex items-center gap-6">
          <div className="flex flex-col">
            <span className="text-micro text-tx-tertiary uppercase tracking-wider">
              Est. Loss
            </span>
            <span className="text-label text-tx-primary font-semibold tabular-nums">
              {estimatedLoss}
            </span>
          </div>
          <div className="flex flex-col">
            <span className="text-micro text-tx-tertiary uppercase tracking-wider">
              Sectors
            </span>
            <span className="text-label text-tx-primary font-semibold tabular-nums">
              {sectorsAffected}
            </span>
          </div>
          <div className="flex flex-col">
            <span className="text-micro text-tx-tertiary uppercase tracking-wider">
              Horizon
            </span>
            <span className="text-label text-tx-primary font-semibold tabular-nums">
              {horizonDays}d
            </span>
          </div>
        </div>
      </QuietCard>
    </a>
  );
}
