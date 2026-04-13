/**
 * TransmissionFlow — how the signal propagates across entities.
 *
 * Transmission section. Vertical chain of causal steps.
 * Each step: entity, event description, impact, stress delta.
 * Business language. No graph jargon.
 */

import type { CausalStep } from "@/types/observatory";
import { fmtUsd } from "@/lib/copy";

interface TransmissionFlowProps {
  chain: CausalStep[];
}

function stressColor(delta: number): string {
  if (delta >= 0.7) return "text-status-red";
  if (delta >= 0.5) return "text-status-amber";
  return "text-tx-secondary";
}

export function TransmissionFlow({ chain }: TransmissionFlowProps) {
  return (
    <section className="py-12 border-t border-border-muted">
      {/* Section label */}
      <p className="text-[0.625rem] font-medium uppercase tracking-[0.12em] text-tx-tertiary mb-3">
        Transmission
      </p>
      <h2 className="text-[1.5rem] font-semibold tracking-[-0.02em] text-charcoal mb-2">
        How the signal propagates
      </h2>
      <p className="text-[0.9375rem] leading-[1.6] text-tx-secondary max-w-[520px] mb-10">
        Each step represents a causal link in the transmission chain,
        from the initial shock to downstream institutional pressure.
      </p>

      {/* Chain */}
      <div className="max-w-[640px]" role="list">
        {chain.map((step, idx) => (
          <div
            key={step.step}
            className="relative flex gap-5 group"
            role="listitem"
          >
            {/* Left rail */}
            <div className="flex flex-col items-center flex-shrink-0 w-9">
              <div
                className="
                  relative z-10 w-9 h-9 rounded-lg
                  flex items-center justify-center
                  bg-bg-surface border border-border-muted
                  text-[0.75rem] font-semibold tabular-nums text-tx-secondary
                  transition-all duration-200
                  group-hover:bg-charcoal group-hover:text-white
                  group-hover:border-charcoal
                "
              >
                {String(step.step).padStart(2, "0")}
              </div>
              {idx < chain.length - 1 && (
                <div
                  className="w-px flex-1 bg-border-muted min-h-[16px]"
                  aria-hidden="true"
                />
              )}
            </div>

            {/* Content */}
            <div className="pb-8 pt-1 min-w-0">
              <h3 className="text-[0.9375rem] font-semibold text-tx-primary leading-[1.3] mb-1">
                {step.entity_label}
              </h3>
              <p className="text-[0.875rem] leading-[1.6] text-tx-secondary mb-3">
                {step.event}
              </p>

              {/* Metrics */}
              <div className="flex items-center gap-6">
                {step.impact_usd > 0 && (
                  <span className="text-[0.75rem] font-medium tabular-nums text-tx-tertiary">
                    {fmtUsd(step.impact_usd)} exposure
                  </span>
                )}
                <span
                  className={`text-[0.75rem] font-medium tabular-nums ${stressColor(step.stress_delta)}`}
                >
                  +{Math.round(step.stress_delta * 100)}% stress
                </span>
              </div>
            </div>
          </div>
        ))}
      </div>
    </section>
  );
}
