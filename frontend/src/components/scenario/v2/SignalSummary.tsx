/**
 * SignalSummary — the initial signal that triggers the scenario.
 *
 * Context section. What happened, in business language.
 * Single narrative block with supporting data points.
 */

interface SignalSummaryProps {
  narrative: string;
  confidence: number;
  methodology: string;
  assumptions: string[];
}

export function SignalSummary({
  narrative,
  confidence,
  methodology,
  assumptions,
}: SignalSummaryProps) {
  return (
    <section className="py-12">
      {/* Section label */}
      <p className="text-[0.625rem] font-medium uppercase tracking-[0.12em] text-tx-tertiary mb-5">
        Context
      </p>

      {/* Narrative */}
      <div className="max-w-[640px]">
        <p className="text-[1.0625rem] leading-[1.7] text-tx-primary">
          {narrative}
        </p>
      </div>

      {/* Supporting detail */}
      <div className="mt-10 grid grid-cols-1 sm:grid-cols-2 gap-8 max-w-[640px]">
        {/* Confidence */}
        <div>
          <span className="text-[0.625rem] font-medium uppercase tracking-[0.08em] text-tx-tertiary">
            Model Confidence
          </span>
          <p className="mt-1 text-[1.375rem] font-semibold tabular-nums text-charcoal">
            {Math.round(confidence * 100)}%
          </p>
        </div>

        {/* Methodology */}
        <div>
          <span className="text-[0.625rem] font-medium uppercase tracking-[0.08em] text-tx-tertiary">
            Methodology
          </span>
          <p className="mt-1.5 text-[0.875rem] leading-[1.6] text-tx-secondary">
            {methodology}
          </p>
        </div>
      </div>

      {/* Assumptions */}
      {assumptions.length > 0 && (
        <div className="mt-8 max-w-[640px]">
          <span className="text-[0.625rem] font-medium uppercase tracking-[0.08em] text-tx-tertiary">
            Key Assumptions
          </span>
          <ul className="mt-2 space-y-1.5">
            {assumptions.map((a, i) => (
              <li
                key={i}
                className="text-[0.8125rem] leading-[1.6] text-tx-secondary pl-4 relative before:content-[''] before:absolute before:left-0 before:top-[0.55em] before:w-1.5 before:h-1.5 before:rounded-full before:bg-border-muted"
              >
                {a}
              </li>
            ))}
          </ul>
        </div>
      )}
    </section>
  );
}
