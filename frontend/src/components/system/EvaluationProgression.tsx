/**
 * Impact Observatory | مرصد الأثر — Evaluation Progression Layer
 *
 * Client component that shows progressive evaluation data
 * accumulation when a scenario is active.
 *
 * When idle: invisible. Static evaluation reads as completed review.
 * When running: shows data collection progress — starts empty,
 *   populates incrementally as the simulation advances.
 * When resolved: shows full evaluation dataset readiness.
 *
 * Does NOT replace static evaluation content. Adds a live progress layer.
 */

'use client';

import { useSystemState } from '@/lib/systemState';

interface Props {
  scenarioId: string;
}

const EVALUATION_STAGES = [
  'Observing initial conditions',
  'Collecting transmission data',
  'Measuring impact propagation',
  'Validating decision effectiveness',
  'Compiling analyst observations',
  'Finalising correctness assessment',
];

export function EvaluationProgression({ scenarioId }: Props) {
  const { activeScenarioId, status, snapshot } = useSystemState();

  if (status === 'idle') return null;
  if (activeScenarioId !== scenarioId) return null;

  const dataPoints = snapshot.evaluationDataPoints;
  const t = snapshot.elapsedHours / Math.max(snapshot.horizonHours, 1);

  return (
    <section className="py-8 border-b border-[var(--io-border-muted)]">
      <div className="max-w-3xl">
        <div className="flex items-baseline gap-4 mb-3">
          <p className="io-label">Evaluation Status</p>
          <span className="text-[0.75rem] tabular-nums text-[var(--io-text-tertiary)]">
            {dataPoints} / {EVALUATION_STAGES.length} stages
          </span>
        </div>

        {/* Before data collection begins */}
        {dataPoints === 0 && (
          <p className="text-[0.875rem] leading-[1.7] text-[var(--io-text-tertiary)]">
            Evaluation layer is observing. Data collection begins after initial
            transmission propagation completes.
          </p>
        )}

        {/* Progressive stage display */}
        {dataPoints > 0 && (
          <div className="space-y-2.5">
            {EVALUATION_STAGES.slice(0, dataPoints).map((stage, i) => (
              <p
                key={i}
                className="text-[0.8125rem] leading-[1.6] text-[var(--io-text-secondary)]"
              >
                <span className="text-[var(--io-text-tertiary)] mr-2">
                  {i + 1}.
                </span>
                {stage}
                <span className="text-[var(--io-status-olive)] ml-2">
                  Complete
                </span>
              </p>
            ))}

            {/* Current stage in progress */}
            {dataPoints < EVALUATION_STAGES.length && (
              <p className="text-[0.8125rem] leading-[1.6] text-[var(--io-text-tertiary)]">
                <span className="text-[var(--io-text-tertiary)] mr-2">
                  {dataPoints + 1}.
                </span>
                {EVALUATION_STAGES[dataPoints]}
                <span className="text-[var(--io-status-amber)] ml-2">
                  In progress
                </span>
              </p>
            )}
          </div>
        )}

        {/* Resolved state */}
        {status === 'resolved' && (
          <p className="text-[0.875rem] leading-[1.7] text-[var(--io-text-secondary)] mt-4">
            Evaluation dataset complete. All stages have been observed.
            Static evaluation below reflects the full post-decision assessment.
          </p>
        )}
      </div>
    </section>
  );
}
