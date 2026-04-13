/**
 * ScenarioHeader — scenario title, domain, severity, and loss range.
 *
 * Top of the scenario detail page. Quiet, institutional.
 * Domain label, title, one-line description, severity badge, loss estimate.
 */

import { Badge } from "@/components/primitives/Badge";

interface ScenarioHeaderProps {
  title: string;
  domain: string;
  severity: number;
  description: string;
  estimatedLoss: string;
  horizonDays: number;
  peakDay: number;
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

export function ScenarioHeader({
  title,
  domain,
  severity,
  description,
  estimatedLoss,
  horizonDays,
  peakDay,
}: ScenarioHeaderProps) {
  return (
    <header className="pb-10 border-b border-border-muted">
      {/* Domain + Severity */}
      <div className="flex items-center gap-4 mb-5">
        <span className="text-[0.6875rem] font-medium uppercase tracking-[0.1em] text-tx-tertiary">
          {domain}
        </span>
        <Badge variant={severityVariant(severity)}>
          {severityLabel(severity)}
        </Badge>
      </div>

      {/* Title */}
      <h1
        className="
          text-[clamp(1.75rem,4vw,2.75rem)] font-semibold
          leading-[1.1] tracking-[-0.03em]
          text-charcoal text-balance max-w-[640px]
        "
      >
        {title}
      </h1>

      {/* Description */}
      <p className="mt-5 text-[1.0625rem] leading-[1.6] text-tx-secondary max-w-[560px]">
        {description}
      </p>

      {/* Key metrics row */}
      <div className="mt-8 flex items-center gap-10 flex-wrap">
        <Metric label="Est. Loss" value={estimatedLoss} />
        <Metric label="Horizon" value={`${horizonDays} days`} />
        <Metric label="Peak Stress" value={`Day ${peakDay}`} />
      </div>
    </header>
  );
}

function Metric({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex flex-col">
      <span className="text-[0.625rem] font-medium uppercase tracking-[0.08em] text-tx-tertiary">
        {label}
      </span>
      <span className="mt-1 text-[1.125rem] font-semibold tabular-nums text-charcoal tracking-[-0.01em]">
        {value}
      </span>
    </div>
  );
}
