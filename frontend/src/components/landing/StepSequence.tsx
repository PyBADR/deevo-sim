/**
 * StepSequence — the product narrative as a numbered progression.
 *
 * Signal → Transmission → Exposure → Pressure →
 * Action → Expected Outcome → Actual Outcome → Evaluation
 *
 * Two columns on desktop. Vertical rhythm with soft connectors.
 * Business language. No technical jargon.
 */

import { Container } from "@/components/layout/Container";
import { steps } from "@/lib/copy";

/** Visual phase grouping — maps each step to a narrative phase */
const PHASE_MAP: Record<string, string> = {
  "01": "Detect",
  "02": "Transmit",
  "03": "Expose",
  "04": "Pressure",
  "05": "Decide",
  "06": "Project",
  "07": "Measure",
  "08": "Learn",
};

function StepRow({
  number,
  title,
  description,
  isLast,
}: {
  number: string;
  title: string;
  description: string;
  isLast: boolean;
}) {
  const phase = PHASE_MAP[number];

  return (
    <div className="relative flex gap-5 sm:gap-7 group" role="listitem">
      {/* Left rail: number + connector */}
      <div className="flex flex-col items-center flex-shrink-0 w-11">
        {/* Number badge */}
        <div
          className="
            relative z-10 w-11 h-11 rounded-[10px]
            flex items-center justify-center
            bg-bg-surface border border-border-muted
            text-[0.8125rem] font-semibold tabular-nums text-tx-secondary
            transition-all duration-200 ease-out
            group-hover:bg-charcoal group-hover:text-white
            group-hover:border-charcoal group-hover:shadow-card
          "
        >
          {number}
        </div>

        {/* Vertical connector */}
        {!isLast && (
          <div
            className="w-px flex-1 bg-border-muted min-h-[20px]"
            aria-hidden="true"
          />
        )}
      </div>

      {/* Content */}
      <div className="pb-10 sm:pb-12 pt-2 min-w-0">
        {/* Phase label */}
        {phase && (
          <span
            className="
              inline-block mb-2
              text-[0.625rem] font-medium uppercase tracking-[0.1em]
              text-tx-tertiary
            "
          >
            {phase}
          </span>
        )}

        <h3
          className="
            text-[1.0625rem] font-semibold leading-[1.3]
            tracking-[-0.01em] text-tx-primary mb-2
          "
        >
          {title}
        </h3>

        <p
          className="
            text-[0.9375rem] leading-[1.65] text-tx-secondary
            max-w-[380px]
          "
        >
          {description}
        </p>
      </div>
    </div>
  );
}

export function StepSequence() {
  const items = steps.items;
  const midpoint = Math.ceil(items.length / 2);
  const left = items.slice(0, midpoint);
  const right = items.slice(midpoint);

  return (
    <Container>
      {/* Section header */}
      <div className="mb-14 max-w-[560px]">
        <p
          className="
            text-[0.6875rem] font-medium uppercase tracking-[0.12em]
            text-tx-tertiary mb-4
          "
        >
          Process
        </p>
        <h2
          className="
            text-[2rem] font-semibold leading-[1.15]
            tracking-[-0.025em] text-tx-primary text-balance
          "
        >
          {steps.heading}
        </h2>
        <p className="mt-3 text-[1.0625rem] leading-[1.65] text-tx-secondary">
          From initial signal detection through to post-decision evaluation
          — eight stages that turn macro intelligence into institutional action.
        </p>
      </div>

      {/* Step grid */}
      <div
        className="grid grid-cols-1 lg:grid-cols-2 gap-x-16 xl:gap-x-24"
        role="list"
      >
        {/* Column 1: Signal → Pressure (01–04) */}
        <div>
          {left.map((step, idx) => (
            <StepRow
              key={step.number}
              number={step.number}
              title={step.title}
              description={step.description}
              isLast={idx === left.length - 1}
            />
          ))}
        </div>

        {/* Column 2: Action → Evaluation (05–08) */}
        <div>
          {right.map((step, idx) => (
            <StepRow
              key={step.number}
              number={step.number}
              title={step.title}
              description={step.description}
              isLast={idx === right.length - 1}
            />
          ))}
        </div>
      </div>

      {/* Closing statement */}
      <div className="mt-6 pt-8 border-t border-border-muted max-w-[560px]">
        <p className="text-[0.9375rem] leading-[1.65] text-tx-tertiary">
          Each stage is traceable. Every decision carries provenance — who
          recommended it, what data supported it, and whether the outcome
          matched expectations.
        </p>
      </div>
    </Container>
  );
}
