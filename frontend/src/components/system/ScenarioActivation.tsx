/**
 * Impact Observatory | مرصد الأثر — Scenario Activation Controls
 *
 * Client component that adds the "Run Scenario" action and
 * live status overlay to the scenario briefing page.
 *
 * When idle: shows a single calm activation button.
 * When running: shows elapsed time, posture, stress, and stop control.
 * When resolved: shows completion state with reset option.
 *
 * CEO sees posture (monitoring → crisis) alongside activation.
 */

'use client';

import { useScenarioEngine } from '@/hooks/useScenarioEngine';
import type { DecisionPosture } from '@/lib/intelligence/decisionEngine';

const postureLabel: Record<DecisionPosture, string> = {
  monitoring: 'Monitoring',
  advisory:  'Advisory',
  active:    'Active',
  immediate: 'Immediate',
  crisis:    'Crisis',
};

const postureColor: Record<DecisionPosture, string> = {
  monitoring: 'text-[var(--io-text-tertiary)]',
  advisory:  'text-[var(--io-text-secondary)]',
  active:    'text-[var(--io-status-olive)]',
  immediate: 'text-[var(--io-status-amber)]',
  crisis:    'text-[var(--io-status-red)]',
};

interface Props {
  scenarioId: string;
  scenarioName: string;
  horizonHours: number;
  severity: string;
}

export function ScenarioActivation({
  scenarioId,
  scenarioName,
  horizonHours,
  severity,
}: Props) {
  const { scenarioId: activeId, status, snapshot, intelligence, run, stop, isActive, isResolved } =
    useScenarioEngine();

  const isThisScenario = activeId === scenarioId;
  const anotherRunning = isActive && !isThisScenario;
  const posture = intelligence.decision.posture;

  return (
    <div className="py-8 border-b border-[var(--io-border-muted)]">
      {/* ── Idle: show activation ── */}
      {!isActive && (
        <div className="flex items-center justify-between max-w-3xl">
          <div>
            <p className="io-label mb-1">System</p>
            <p className="text-[0.8125rem] text-[var(--io-text-tertiary)]">
              Scenario loaded. Ready to activate simulation.
            </p>
          </div>
          <button
            onClick={() => run(scenarioId, scenarioName, horizonHours)}
            className="shrink-0 px-5 py-2 text-[0.8125rem] font-medium text-[var(--io-charcoal)] bg-[var(--io-bg)] border border-[var(--io-border-muted)] rounded-md hover:border-[var(--io-charcoal)]/30 transition-colors duration-200"
          >
            Run Scenario
          </button>
        </div>
      )}

      {/* ── Running on this scenario ── */}
      {isThisScenario && !isResolved && (
        <div className="max-w-3xl">
          <div className="flex items-center justify-between mb-4">
            <div>
              <div className="flex items-baseline gap-3 mb-1">
                <p className="io-label">Active Simulation</p>
                <span className={`text-[0.6875rem] font-semibold uppercase tracking-[0.05em] ${postureColor[posture]}`}>
                  {postureLabel[posture]}
                </span>
              </div>
              <p className="text-[0.8125rem] text-[var(--io-text-secondary)]">
                {intelligence.decision.systemSeverity}
              </p>
            </div>
            <button
              onClick={stop}
              className="shrink-0 px-4 py-1.5 text-[0.75rem] font-medium text-[var(--io-text-tertiary)] border border-[var(--io-border-muted)] rounded-md hover:text-[var(--io-status-red)] hover:border-[var(--io-status-red)]/30 transition-colors duration-200"
            >
              Stop
            </button>
          </div>

          {/* Live indicators — calm prose */}
          <p className="text-[0.8125rem] text-[var(--io-text-secondary)]">
            <span className="text-[var(--io-text-tertiary)]">Elapsed:</span>{' '}
            <span className="tabular-nums font-medium">{Math.round(snapshot.elapsedHours)}h</span>
            <span className="text-[var(--io-text-tertiary)]"> of </span>
            <span className="tabular-nums">{snapshot.horizonHours}h</span>
            <span className="mx-3 text-[var(--io-border-muted)]">·</span>
            <span className="text-[var(--io-text-tertiary)]">Stress:</span>{' '}
            <span className="font-medium">{snapshot.stressLevel}</span>
            {intelligence.summary.criticalEntityCount > 0 && (
              <>
                <span className="mx-3 text-[var(--io-border-muted)]">·</span>
                <span className="text-[var(--io-status-red)] font-medium">
                  {intelligence.summary.criticalEntityCount} entities critical
                </span>
              </>
            )}
          </p>
        </div>
      )}

      {/* ── Resolved on this scenario ── */}
      {isThisScenario && isResolved && (
        <div className="flex items-center justify-between max-w-3xl">
          <div>
            <p className="io-label mb-1">Simulation Complete</p>
            <p className="text-[0.8125rem] text-[var(--io-text-secondary)]">
              Scenario has run to horizon. Decision and evaluation layers updated.
            </p>
          </div>
          <button
            onClick={stop}
            className="shrink-0 px-5 py-2 text-[0.8125rem] font-medium text-[var(--io-text-tertiary)] border border-[var(--io-border-muted)] rounded-md hover:border-[var(--io-charcoal)]/30 transition-colors duration-200"
          >
            Reset
          </button>
        </div>
      )}

      {/* ── Another scenario is running ── */}
      {anotherRunning && (
        <div className="max-w-3xl">
          <p className="io-label mb-1">System</p>
          <p className="text-[0.8125rem] text-[var(--io-text-tertiary)]">
            Another scenario is active. Stop it before activating this one.
          </p>
        </div>
      )}
    </div>
  );
}
