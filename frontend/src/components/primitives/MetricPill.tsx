/**
 * MetricPill — inline metric display with label and value.
 */

interface MetricPillProps {
  label: string;
  value: string;
  className?: string;
}

export function MetricPill({ label, value, className }: MetricPillProps) {
  return (
    <div className={`flex flex-col ${className ?? ""}`}>
      <span className="text-micro text-tx-tertiary uppercase tracking-wider">
        {label}
      </span>
      <span className="text-card-title text-tx-primary tabular-nums mt-0.5">
        {value}
      </span>
    </div>
  );
}
